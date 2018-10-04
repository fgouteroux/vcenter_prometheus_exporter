# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
Vcenter Prometheus Exporter

Licence
```````
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
__author__ = "Francois Gouteroux <francois.gouteroux@gmail.com>"

from setuptools import setup, find_packages

from pipenv.project import Project
from pipenv.utils import convert_deps_to_pip

from vcenter_exporter.release import __version__

pfile = Project(chdir=False).parsed_pipfile
requirements = convert_deps_to_pip(pfile['packages'], r=False)
test_requirements = convert_deps_to_pip(pfile['dev-packages'], r=False)

setup(
    name='vcenter-prometheus-exporter',
    version=__version__,
    description='Export prometheus metrics from vcenter host',
    long_description=open('README.md').read(),
    url='https://github.com/fgouteroux/vcenter_prometheus_exporter.git',
    author='Francois Gouteroux',
    author_email='francois.gouteroux@gmail.com',
    license='License :: OSI Approved :: Apache Software License',
    keywords=['VMWare', 'VCenter', 'Prometheus'],
    packages=find_packages(),
    package_data = {'': ['README.md']},
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'vcenter_exporter = vcenter_exporter.__main__:main'
        ],
    }
)
