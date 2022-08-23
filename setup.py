#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README.md')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-munigeo',
    version='0.4.0',
    packages=['munigeo'],
    include_package_data=True,
    license='BSD License',
    description='A Django app for processing municipality-related geospatial data.',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/City-of-Helsinki/django-munigeo',
    author='City of Helsinki',
    author_email='dev@hel.fi',
    install_requires=[
        'Django',
        'requests',
        'requests_cache',
        'django_mptt',
        'django-parler>=2',
        'django-parler-rest',
        'six',
        'pyyaml',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-django'],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Scientific/Engineering :: GIS',
    ],
)
