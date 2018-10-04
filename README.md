# Vcenter Prometheus Exporter

Export prometheus metrics from vcenter host


## Installation

```bash
pip install pipenv
pipenv install vcenter_prometheus_exporter
```

## Usage

Default config file: **/etc/default/vcenter_exporter.yaml**

	vcenter_exporter run

Or

	vcenter_exporter run -c config.yaml


## How it works

This exporter read an yaml config file composed with:
- vcenter: vcenter host and credentials
- objects: objects to get from vcenter and filter properties
- metrics: metrics to generates from objects

**See config_sample.yaml**

The exporter will:
- generate an exported resource view from vcenter objects 
- set the metric type
- apply metric labels
- set metric value
- return Metric Object List to the embedded http server.

**Output:**

```
# HELP vcenter_host_cpu_cores vcenter_host_cpu_cores
# TYPE vcenter_host_cpu_cores gauge
vcenter_host_cpu_cores{hostname="my-esx.example.com"} 24.0
# HELP vcenter_host_memory_capacity vcenter_host_memory_capacity
# TYPE vcenter_host_memory_capacity gauge
vcenter_host_memory_capacity{hostname="my-esx.example.com"} 274645385216.0
# HELP vcenter_host_uptime_seconds vcenter_host_uptime_seconds
# TYPE vcenter_host_uptime_seconds gauge
vcenter_host_uptime_seconds{hostname="my-esx.example.com"} 3544985.0
# HELP vcenter_host_memory_usage vcenter_host_memory_usage
# TYPE vcenter_host_memory_usage gauge
vcenter_host_memory_usage{hostname="my-esx.example.com"} 209072.0
# HELP vcenter_host_power_state vcenter_host_power_state
# TYPE vcenter_host_power_state gauge
vcenter_host_power_state{hostname="my-esx.example.com"} 0.0
# HELP vcenter_host_cpu_frequency vcenter_host_cpu_frequency
# TYPE vcenter_host_cpu_frequency gauge
vcenter_host_cpu_frequency{hostname="my-esx.example.com"} 2195.0
# HELP vcenter_vm_memory_usage vcenter_vm_memory_usage
# TYPE vcenter_vm_memory_usage gauge
vcenter_vm_memory_usage{host="my-esx.example.com",vmname="my-testvm.example.com"} 2785.0
# HELP vcenter_vm_power_state vcenter_vm_power_state
# TYPE vcenter_vm_power_state gauge
vcenter_vm_power_state{vmname="my-testvm.example.com"} 0.0
# HELP vcenter_vm_cpu_usage vcenter_vm_cpu_usage
# TYPE vcenter_vm_cpu_usage gauge
vcenter_vm_cpu_usage{host="my-esx.example.com",vmname="my-testvm.example.com"} 6211.0
```

## Specific features

There are **four** specific features:
- States Values
- Regex Filters
- Functions
- Objects Refs

**Note**: If a value to get is not specified, the default is 0.

### States values

As the prometheus python client doesn't yet support (Enum, Info..) types,
we can map text to value.

**Example:** 

Getting the cluster heath status send three text states: **green, yellow and red**.

To have a valid metric, we map each state to an integer value.

```yaml
  metrics:
    cluster:
      vcenter_cluster_overallstatus:
        type: Gauge
        labels: ["cluster_name"]
        properties:
          labels: ["name"]
          states: {"green": 0, "yellow": 1, "red": 2}
          value: overallStatus
```

### Regex Filters

**match_filter:** get all objects which name match with the regex

```yaml
  objects:
    vm:
      type: VirtualMachine
      match_filter: ".*testvm.*"
      properties:
        - "name"
      [...]
```

**ignore_filter:** ignore all objects which name match with the regex

```yaml
  objects:
    vm:
      type: VirtualMachine
      ignore_filter: "^testvm.*"
      properties:
        - "name"
      [...]
```

### Functions

It's possible to call some object functions to get specfic info.

**Example: get the cluster storage used in MB**


Declare the function to use in:

```yaml
  objects:
    cluster:
      type: ComputeResource
      functions:
        - GetResourceUsage
```
Give the value to get in the metric:
```yaml
    vcenter_cluster_memory_capacity:
      type: Gauge
      labels: ["cluster_name"]
      properties:
        labels: ["name"]
        value: memCapacityMB
```

#### Technical view:

This will execute the function:

```
vim.ClusterComputeResource:domain-c34.GetResourceUsage()

	(vim.cluster.ResourceUsageSummary) {
	   dynamicType = <unset>,
	   dynamicProperty = (vmodl.DynamicProperty) [],
	   cpuUsedMHz = 673265,
	   cpuCapacityMHz = 842880,
	   memUsedMB = 3611287,
	   memCapacityMB = 4190768,
	   pMemAvailableMB = <unset>,
	   pMemCapacityMB = <unset>,
	   storageUsedMB = 34709118L,
	   storageCapacityMB = 60418304L
	}
```

and update the dict:

```
	{'memUsedMB': 3611336, 'storageCapacityMB': 60418304L, 'obj': 'vim.ClusterComputeResource:domain-c34', u'name': 'cluster_integration', 'dynamicProperty': (vmodl.DynamicProperty) [], 'dynamicType': None, u'summary.numEffectiveHosts': 16, 'pMemCapacityMB': None, 'cpuUsedMHz': 665617, u'summary.numHosts': 16, 'storageUsedMB': 34709118L, 'memCapacityMB': 4190768, u'overallStatus': 'green', 'pMemAvailableMB': None, 'cpuCapacityMHz': 842880}
```
### Objects Refs

In some cases, we want to get a property from an another object reference.

**Example: apply host label to vm metric**

Declare the property separated by **|** and the attribute to get:

```yaml
  metrics:
    vm:
      vcenter_vm_cpu_usage:
        type: Gauge
        labels: ["vmname", "host"]
        properties:
          labels: ["name", "runtime.host|name"]
          value: summary.quickStats.overallCpuUsage
```
We are getting the attribute **'name'** from object **'vim.HostSystem:host-6077'**.

**Note: Getting an object ref consume time as it's not an view resource.**


## References

Vcenter Prometheus Exporter uses theses libraries:
- [pyVmomi](https://github.com/vmware/pyvmomi) for VMWare connection
- Prometheus [client_python](https://github.com/prometheus/client_python) for Prometheus supervision


Inspired by:
- https://github.com/sapcc/vcenter-exporter
- https://github.com/pryorda/vmware_exporter
