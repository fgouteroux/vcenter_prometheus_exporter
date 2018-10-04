#!/usr/bin/env python
"""vcenter prometheus exporter"""

# standard
import re
import sys
import time
import atexit
import logging

# third-party
# pylint: disable=no-name-in-module
from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, SmartConnectNoSSL, Disconnect
from prometheus_client import core, start_http_server, REGISTRY

#local
from vcenter_exporter._py6 import iteritems

LOG = logging.getLogger(__name__)

# Shamelessly borrowed from:
# https://github.com/dnaeon/py-vconnector/blob/master/src/vconnector/core.py
def collect_properties(service_instance, view_ref, obj_type, path_set=None,
                       include_mors=False):
    """
    Collect properties for managed objects from a view ref
    Check the vSphere API documentation for example on retrieving
    object properties:
        - http://goo.gl/erbFDz
    Args:
        si          (ServiceInstance): ServiceInstance connection
        view_ref (vim.view.*): Starting point of inventory navigation
        obj_type      (vim.*): Type of managed object
        path_set               (list): List of properties to retrieve
        include_mors           (bool): If True include the managed objects
                                       refs in the result
    Returns:
        A list of properties for the managed objects
    """
    collector = service_instance.content.propertyCollector

    # Create object specification to define the starting point of
    # inventory navigation
    obj_spec = vmodl.query.PropertyCollector.ObjectSpec()
    obj_spec.obj = view_ref
    obj_spec.skip = True

    # Create a traversal specification to identify the path for collection
    traversal_spec = vmodl.query.PropertyCollector.TraversalSpec()
    traversal_spec.name = 'traverseEntities'
    traversal_spec.path = 'view'
    traversal_spec.skip = False
    traversal_spec.type = view_ref.__class__
    obj_spec.selectSet = [traversal_spec]

    # Identify the properties to the retrieved
    property_spec = vmodl.query.PropertyCollector.PropertySpec()
    property_spec.type = obj_type

    if not path_set:
        property_spec.all = True

    property_spec.pathSet = path_set
    # Add the object and property specification to the
    # property filter specification
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = [obj_spec]
    filter_spec.propSet = [property_spec]

    # Retrieve properties
    props = collector.RetrieveContents([filter_spec])

    data = []
    for obj in props:
        properties = {}
        for prop in obj.propSet:
            properties[prop.name] = prop.val

        if include_mors:
            properties['obj'] = obj.obj

        data.append(properties)
    return data


def _generate_metrics(data, rdata):
    """Set metrics labels and values"""

    def _get_metric_class(data):
        description = data.get("description", data["name"])
        labelsnames = rdata[data["name"]]["labels"]
        cls = getattr(core, data["type"] + "MetricFamily")
        return cls(data["name"], description, labels=labelsnames)

    metric_class = _get_metric_class(data)

    if data["type"] == "Gauge":
        metric_class.add_metric(data["labels"], data["value"])
        yield metric_class
    else:
        LOG.error("Type %s is not yet supported", data["type"])


def _get_labels_and_values(rdata, metrics, item):
    """get labels and values"""
    for name, data in iteritems(rdata):
        if "states" in data["properties"].keys():
            tmp = item.get(data["properties"]["value"])
            value = data["properties"]["states"][str(tmp)]
        elif data["properties"].get("value"):
            val = data["properties"]["value"]
            if "|" in val:
                ref_value = val.split("|")
                value = getattr(item.get(ref_value[0]), ref_value[1])
            else:
                value = item.get(val)
        else:
            value = 0

        labels = []
        for label in data["properties"]["labels"]:
            if "|" in label:
                ref_lab = label.split("|")
                labels.append(getattr(item.get(ref_lab[0]), ref_lab[1]))
            else:
                labels.append(item.get(label))

        metrics.append({
            "name": name,
            "type": data["type"],
            "labels": labels,
            "value": value
        })

def _set_metrics(name, resource, rdata):
    """Return Metric object List"""
    todos = []
    functions = resource.get("functions", [])

    if isinstance(resource["items"], list):
        for item in resource["items"]:

            if name != "vcenter":
                if not resource["match_filter"].match(item["name"])\
                and resource["ignore_filter"].match(item["name"]):
                    continue

            for function in functions:
                to_exec = getattr(item["obj"], function)
                item.update(vars(to_exec()))
                LOG.debug(item)
            _get_labels_and_values(rdata, todos, item)
    else:
        _get_labels_and_values(rdata, todos, resource["items"])

    metrics = []
    for todo in todos:
        for metric in _generate_metrics(todo, rdata):
            metrics.append(metric)

    return metrics


class VcenterCollector(object):
    """Vcenter collector"""

    def __init__(self, config):

        self.vcenter = config["vcenter"].copy()
        if self.vcenter["ignore_ssl"]:
            self.vcenter.pop("ignore_ssl")
            self.service_instance = SmartConnectNoSSL(**self.vcenter)
        else:
            self.service_instance = SmartConnect(**self.vcenter)

        atexit.register(Disconnect, self.service_instance)

        self.content = self.service_instance.RetrieveContent()
        self.container = self.content.rootFolder
        self.metrics = config["metrics"]
        self.objects = config["objects"]

        if not self.objects.keys():
            LOG.error("Nothing to collect")
            sys.exit(1)


    def _get_vc_resource(self, name, object_type):
        """get vcenter resource"""
        view_ref = self.content.viewManager.CreateContainerView(
            self.container, [getattr(vim, object_type)],
            recursive=True)

        resource = {}
        if "functions" in self.objects[name]:
            resource["functions"] = self.objects[name]["functions"]

        if "ignore_filter" in self.objects[name]:
            resource["ignore_filter"] = re.compile(\
                self.objects[name]["ignore_filter"])
        else:
            resource["ignore_filter"] = re.compile('')

        if "match_filter" in self.objects[name]:
            resource["match_filter"] = re.compile(\
                self.objects[name]["match_filter"])
        else:
            resource["match_filter"] = re.compile('')

        resource["items"] = collect_properties(
            self.service_instance,
            view_ref,
            getattr(vim, object_type),
            self.objects[name]["properties"], True)

        return resource


    def feed_vcenter(self):
        """feed dict with vcenter objects"""
        resources = {}
        for name, data in iteritems(self.objects):
            resources[name] = self._get_vc_resource(name, data["type"])

        resources["vcenter"] = {}
        resources["vcenter"]["items"] = []
        for session in self.content.sessionManager.sessionList:
            resources["vcenter"]["items"].append({
                "hostname": self.vcenter["host"],
                "session.username": session.userName,
                "session.ipaddress": session.ipAddress,
                "session.useragent": session.userAgent,
                "session.callcount": session.callCount
            })

        return resources


    def collect(self):
        """Collect metrics"""

        LOG.info("Refresh vcenter resources")
        resources = self.feed_vcenter()

        for resource, rdata in iteritems(self.metrics):

            if resource not in resources.keys():
                continue

            start_time = int(time.time())
            for metric in _set_metrics(resource, resources[resource], rdata):
                LOG.debug(metric)
                yield metric

            end_time = int(time.time())
            runtime = int(end_time - start_time)
            LOG.info("Generating %d metrics for %s in %ds", \
                 len(rdata.keys()), resource, runtime)


def run(config):
    """start http exporter server"""
    start_http_server(int(config.get("port", 9108)))
    REGISTRY.register(VcenterCollector(config.get("collector")))
    while True:
        time.sleep(1)
