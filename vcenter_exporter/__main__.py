#!/usr/bin/python
# -*- coding: utf-8 -*-

# pylint: disable=line-too-long
r"""
Export prometheus metrics from vcenter host

Authors:
    - Francois Gouteroux <francois.gouteroux@gmail.com>

Usage:
    vcenter_exporter (-h | --help)
    vcenter_exporter run [-c <configfile>]

Options:
    -h, --help
        Show this screen.
    --version
        Show version.
    -c <configfile>, --config <configfile>
        YAML config file [default: /etc/default/vcenter_exporter.yaml].

"""
from __future__ import (unicode_literals, absolute_import, print_function,)

# standard
import sys
import logging

# third-party
import yaml
from docopt import docopt, DocoptExit

# local
from vcenter_exporter import exporter
from vcenter_exporter.release import __version__


def init_logger(level):
    """init the logger

    Args:
        level (str): level of log (debug, info, warn, error)
    """
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger("vcenter_exporter")
    logger.addHandler(console_handler)
    logger.setLevel(getattr(logging, level.upper()))


def main():
    """Main function"""
    try:
        arguments = docopt(__doc__, version="1.0.0")
    except DocoptExit:
        print(__doc__)
        sys.exit(1)

    with open(arguments['--config']) as cfg:
        config = yaml.safe_load(cfg)

    init_logger(config['log_level'])

    if arguments.get("run"):
        exporter.run(config)


if __name__ == '__main__':
    main()
