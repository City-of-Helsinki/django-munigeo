[![codecov](https://codecov.io/gh/City-of-Helsinki/django-munigeo/branch/master/graph/badge.svg)](https://codecov.io/gh/City-of-Helsinki/django-munigeo)

munigeo
=======

`munigeo` is a reusable Django application for storing and accessing
municipality-related geospatial data. It can manage following categories of
data:
* Municipalities as containers of everything below
* Administrative divisions (with parent-child relationships and links to Municipalities)
* Streets and address locations on those Streets
* Buildings with 2D-geometries and addresses
* PoIs (Points of Interest) with location and type

If you are using Django Rest Framework (DRF), munigeo also provides you with serializers
for including these in your API.

For actually getting the data into your database application, munigeo provides importer
framework. Currently we only have actual importers for City of Helsinki, but
other are welcome.

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

## Code format

This project uses [Ruff](https://docs.astral.sh/ruff/) for code formatting and quality checking.

Basic `ruff` commands:

* lint: `ruff check`
* apply safe lint fixes: `ruff check --fix`
* check formatting: `ruff format --check`
* format: `ruff format`

[`pre-commit`](https://pre-commit.com/) can be used to install and
run all the formatting tools as git hooks automatically before a
commit.
