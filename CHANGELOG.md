# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0](https://github.com/City-of-Helsinki/django-munigeo/compare/v0.3.12...v1.0.0) (2026-10-03)


### ⚠ BREAKING CHANGES

* move automatic translation fields to model level

### Features

* Add division/address API filtering and search ([1de5023](https://github.com/City-of-Helsinki/django-munigeo/commit/1de502316c3fa86c295d26313a9d6f9910035e30))
* Add PostalCodeArea model and new Address/Division fields ([4589f8c](https://github.com/City-of-Helsinki/django-munigeo/commit/4589f8cb0a3db8aaa822bacc420c087b56135dc3))
* Improve Helsinki/Finland importers, update deps ([e5d8760](https://github.com/City-of-Helsinki/django-munigeo/commit/e5d8760c41f7ac6589dd2b5a1d90d1621e0bf0f1))
* Increase AdministrativeDivision name max_length to 200 ([11a31b7](https://github.com/City-of-Helsinki/django-munigeo/commit/11a31b784dd89ca23bac9b42233b0b14004fcb8a))
* Move automatic translation fields to model level ([fc8f691](https://github.com/City-of-Helsinki/django-munigeo/commit/fc8f691d46ea375ca9884a6dbcb17746cf8f9705))
* Remove athens importer ([e169bff](https://github.com/City-of-Helsinki/django-munigeo/commit/e169bff921fc1df9d80529e46455d908c5377da7))
* Remove turku importer ([149ce8c](https://github.com/City-of-Helsinki/django-munigeo/commit/149ce8c0f9153dad3870e2f56b54ae9ecbd3203c))


### Bug Fixes

* Add missing PostalCodeArea import in helsinki importer ([b39ac31](https://github.com/City-of-Helsinki/django-munigeo/commit/b39ac31401d073ddecdda99fd9eb83bd884d4420))
* Defer GEO_SEARCH settings access to runtime ([feca359](https://github.com/City-of-Helsinki/django-munigeo/commit/feca359e149bde04131c41573f82720414e4d3d6))
* Enable all ruff lint rules from main branch ([c3b7446](https://github.com/City-of-Helsinki/django-munigeo/commit/c3b7446977807c993d0a69b3ae89077e6c545c45))
* Fix number_end and counter increment in uusimaa importer ([3618d80](https://github.com/City-of-Helsinki/django-munigeo/commit/3618d80477f174fb0d27188fbbb36f894e37a560))
* Handle None postal_code in PostalCodeArea.__str__ ([77cb670](https://github.com/City-of-Helsinki/django-munigeo/commit/77cb6701a8b6899d40841dff6bb21ac02e145220))
* **helsinki:** Add missing row to wfs url ([63db176](https://github.com/City-of-Helsinki/django-munigeo/commit/63db17632120f99346ae28bc9e987a391c2855ca))
* Move mutable class attributes to __init__ in uusimaa importer ([c0ca511](https://github.com/City-of-Helsinki/django-munigeo/commit/c0ca511ec86923fa23678b43ba7509870ea1146e))
* Perform parler migration in bulk ([a31de4f](https://github.com/City-of-Helsinki/django-munigeo/commit/a31de4f1835402c4dbe17996f116baa5d182e41b))
* Re-raise MaxRetryError after logging ([fba7323](https://github.com/City-of-Helsinki/django-munigeo/commit/fba73238ddc2af281ee9f6e7e73061f756470322))
* Remove 400 from retry status_forcelist ([57c7e34](https://github.com/City-of-Helsinki/django-munigeo/commit/57c7e343806a04a10d0357d5584e35f94fa04921))
* Remove name_sv/name_en from Street unique_together ([91cd490](https://github.com/City-of-Helsinki/django-munigeo/commit/91cd4905affd3b143fd23a7f0d67941481391d50))
* Remove unreachable code in convert_from_gk25 ([617b6af](https://github.com/City-of-Helsinki/django-munigeo/commit/617b6af3413984d0df09d1f1b4c1a30e61327bc7))
* Rename loop variable that shadows builtin filter ([5d1d6f1](https://github.com/City-of-Helsinki/django-munigeo/commit/5d1d6f1c2325b6ccff34054a6babc686d6aa59ff))
* Use gettext_lazy instead of gettext in models ([a4aa582](https://github.com/City-of-Helsinki/django-munigeo/commit/a4aa58215ab1b5acadb95b030eeda09b00328a80))


### Dependencies

* Add support for Python 3.14, drop support for Python 3.9 ([93158ca](https://github.com/City-of-Helsinki/django-munigeo/commit/93158cad137c5d76b824c1235c886bbff113fa3d))
* Update django version support ([a1e3ce4](https://github.com/City-of-Helsinki/django-munigeo/commit/a1e3ce40a2aedd1a2830ceed5054ba07f8e03d8f))

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
