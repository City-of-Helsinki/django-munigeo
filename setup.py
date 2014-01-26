#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-munigeo',
    version='0.1',
    packages=['munigeo'],
    include_package_data=True,
    license='AGPLv3',
    description='A Django app for processing municipality-related geospatial data.',
    long_description=README,
    author='Juha Yrjölä',
    author_email='juha.yrjola@iki.fi',
    requires=[
        'Django (>=1.4.0)',
        'django_tastypie',
        'requests',
        'requests_cache',
        'django-mptt',
        'django-modeltranslation',
        'six'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)'
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Scientific/Engineering :: GIS',
    ],
)
