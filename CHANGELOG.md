# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.12] - 2025-02-27
### Fixed
- Fix broken import for Python versions >=3.10

## [0.3.11] - 2025-01-20
### Fixed
- helsinki importer: Make tolerance for divisions extending past their parents relative to parent
  area (from 300 m^2 to 0.1% of parent area)
- helsinki importer: Update `statistical_district` WFS layer value
- helsinki importer: Remove unused Helsinki WFS layers

## [0.3.10] - 2023-12-04
### Fixed
- Fix Helsinki importer urls

## [0.3.9] - 2023-08-22
### Fixed
- Fix municipality url

## [0.3.8] - 2023-02-13
### Fixed
- Use gettext_lazy instead of gettext in models

## [0.3.7] - 2023-01-25
### Added
- Support for Django 3.x.

### Changed
- Pinned the `django-parler` version to `>=2` and add a migration required to upgrade it.

### Fixed
- Add a `tzinfo` to `Street` and `Address.modified_at` migrations to fix the warning
saying that a timezone-naive date was passed to a `DateTimeField`.
- helsinki importer: Reverted the change introduced in v0.3.6 which broke Helsinki division import
- helsinki importer: Fixed empty field value handling
- helsinki importer: Fixed crash with division types without a layer
- GDAL 3.0 Coordinate transformation backwards compatibility

## [0.3.6] - 2020-05-08

### Fixed
- helsinki importer: Raised the tolerance for divisions extending past their
  parents (from 1e-6 to 300 m^2). Helsinki data could not be imported previously.

[unreleased]: https://github.com/City-of-Helsinki/django-munigeo/compare/v0.3.10...HEAD
[0.3.12]: https://github.com/City-of-Helsinki/django-munigeo/compare/v0.3.11...v0.3.12
[0.3.11]: https://github.com/City-of-Helsinki/django-munigeo/compare/v0.3.10...v0.3.11
[0.3.10]: https://github.com/City-of-Helsinki/django-munigeo/compare/v0.3.9...v0.3.10
[0.3.9]: https://github.com/City-of-Helsinki/django-munigeo/compare/v0.3.8...v0.3.9
[0.3.8]: https://github.com/City-of-Helsinki/django-munigeo/compare/v0.3.7...v0.3.8
[0.3.7]: https://github.com/City-of-Helsinki/django-munigeo/compare/v0.3.6...v0.3.7
[0.3.6]: https://github.com/City-of-Helsinki/django-munigeo/compare/v0.3.5...v0.3.6
