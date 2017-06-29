[![Build status](https://travis-ci.org/City-of-Helsinki/django-munigeo.svg?branch=master)](https://travis-ci.org/City-of-Helsinki/django-munigeo)
[![codecov](https://codecov.io/gh/City-of-Helsinki/django-munigeo/branch/master/graph/badge.svg)](https://codecov.io/gh/City-of-Helsinki/django-munigeo)
[![Requirements](https://requires.io/github/City-of-Helsinki/django-munigeo/requirements.svg?branch=master)](https://requires.io/github/City-of-Helsinki/django-munigeo/requirements/?branch=master)

munigeo
=======

`munigeo` is a reusable Django application for storing and accessing
municipality-related geospatial data.

## Usage
Install this to your project with `pip install django-munigeo`,
add `munigeo` to your `INSTALLED_APPS` setting.

### Helsinki example
Before you can get Helsinki, you will need the data for Finland first:
```
python manage.py geo_import finland --municipalities
```
then
```
python manage.py geo_import helsinki --divisions
```
