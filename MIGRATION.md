# Migrating to django-munigeo 1.0

This guide covers upgrading to django-munigeo 1.0 from either of the two
previously maintained branches:

- [Upgrading from 0.3 (parler)](#upgrading-from-03) - Linked Events and
  other consumers on the 0.3 chain
- [Upgrading from 0.2 (modeltranslation)](#upgrading-from-02) - Palvelukartta/
  smbackend

## What's new in 1.0

1.0 unifies the two branches into a single codebase. Translation fields are
now explicit columns on the model (`name_fi`, `name_sv`, `name_en`) with no
dependency on django-parler or django-modeltranslation.

See [New features](#new-features) and [Breaking changes](#breaking-changes)
for the complete list of changes.

---

## Upgrading from 0.3

For consumers already on the 0.3 chain, upgrading is straightforward:

```bash
pip install django-munigeo==1.0
python manage.py migrate
```

Migration 0010 adds several new fields and tables. All new columns are either
nullable or have safe defaults, except `Address.municipality` which is
automatically populated from `Address.street.municipality` via a data migration.

Review the [breaking changes](#breaking-changes) section below - most of them
affect 0.3 consumers specifically (parler removal, `.name` attribute, etc.).

---

## Upgrading from 0.2

This section is for consumers on the 0.2 (modeltranslation) branch, which
used a different migration chain (applied through 0017).

### Background

django-munigeo previously maintained two parallel migration chains:

- **0.2 chain** (modeltranslation): used by Palvelukartta/smbackend
- **0.3 chain** (parler, then direct fields): used by Linked Events and others

1.0 uses a single canonical chain based on the 0.3 branch. The old 0.2
migrations no longer exist in the repository.

### Schema differences

The final schema is nearly identical to what 0.2 consumers already have:

| Change | Details |
|--------|---------|
| `name` column dropped | Removed from `AdministrativeDivision`, `Municipality`, `Street` |
| `full_name` column dropped | Removed from `Address` |
| `name_fi/sv/en` widened | `AdministrativeDivision` changed from VARCHAR(100) to VARCHAR(200) |
| Street unique constraint | Changed from `(municipality, name)` to `(municipality, name_fi)` |

The `name` and `full_name` columns are replaced by `name_fi`/`name_sv`/
`name_en`. No data is lost - the content of `name` was always identical
to `name_fi` in production.

### Prerequisites

- Back up your database
- Ensure you are on the **latest 0.2 migration** (0017) before upgrading:
  ```bash
  python manage.py showmigrations munigeo
  ```
  All migrations through `0017_administrativedivision_munigeo_administrativedivi8660`
  should show `[X]`.

### Step 1: Apply schema changes

Run the following SQL against your database:

```sql
BEGIN;

-- 1. Copy name -> name_fi where name_fi is NULL (safety backfill)
UPDATE munigeo_administrativedivision SET name_fi = name WHERE name_fi IS NULL AND name IS NOT NULL;
UPDATE munigeo_municipality SET name_fi = name WHERE name_fi IS NULL AND name IS NOT NULL;
UPDATE munigeo_street SET name_fi = name WHERE name_fi IS NULL AND name IS NOT NULL;
UPDATE munigeo_address SET full_name_fi = full_name WHERE full_name_fi IS NULL AND full_name IS NOT NULL;

-- 2. Drop the base name/full_name columns
ALTER TABLE munigeo_administrativedivision DROP COLUMN name;
ALTER TABLE munigeo_municipality DROP COLUMN name;
ALTER TABLE munigeo_street DROP COLUMN name;
ALTER TABLE munigeo_address DROP COLUMN full_name;

-- 3. Widen AdministrativeDivision name fields to VARCHAR(200)
ALTER TABLE munigeo_administrativedivision ALTER COLUMN name_fi TYPE VARCHAR(200);
ALTER TABLE munigeo_administrativedivision ALTER COLUMN name_sv TYPE VARCHAR(200);
ALTER TABLE munigeo_administrativedivision ALTER COLUMN name_en TYPE VARCHAR(200);

-- 4. Update Street unique constraint
--    Drop the old constraint (name may vary - check with \d munigeo_street)
ALTER TABLE munigeo_street DROP CONSTRAINT IF EXISTS munigeo_street_municipality_id_name_39181669_uniq;
ALTER TABLE munigeo_street DROP CONSTRAINT IF EXISTS munigeo_street_municipality_id_name_b5c1564e_uniq;
--    Add the new constraint
ALTER TABLE munigeo_street ADD CONSTRAINT munigeo_street_municipality_id_name_fi_uniq UNIQUE (municipality_id, name_fi);

COMMIT;
```

> **Note:** The exact constraint name for the old Street unique_together may
> differ in your database. Run `\d munigeo_street` in psql to find it before
> executing the DROP CONSTRAINT statement.

### Step 2: Reset migration history

```sql
DELETE FROM django_migrations WHERE app = 'munigeo';
```

### Step 3: Fake-apply all new migrations

```bash
python manage.py migrate munigeo --fake
```

This records all 10 migrations as applied without executing them (since the
schema is already correct).

### Step 4: Verify

```bash
python manage.py showmigrations munigeo
```

All migrations should show `[X]`:

```
munigeo
 [X] 0001_squashed_0004_building
 [X] 0002_add_parler_translations
 [X] 0003_migrate_translations_to_parler
 [X] 0004_delete_old_translations
 [X] 0005_update_translation_foreign_keys
 [X] 0006_add_name_fields
 [X] 0007_migrate_translation_data
 [X] 0008_remove_translation_tables
 [X] 0009_alter_administrativedivision_name_en_and_more
 [X] 0010_postalcodearea_address_full_name_en_and_more
```

Then run:

```bash
python manage.py migrate --run-syncdb
python manage.py makemigrations --check
```

Both should complete without errors.

### Step 5: Update application code

Any ORM queries using the bare `name` field must be updated:

```python
# Before (0.2 with modeltranslation)
Municipality.objects.get(name="Helsinki")
AdministrativeDivision.objects.filter(name__icontains="kallio")

# After (1.0)
Municipality.objects.get(name_fi="Helsinki")
AdministrativeDivision.objects.filter(name_fi__icontains="kallio")
```

The `name` database column no longer exists after this migration. Use
`name_fi`, `name_sv`, or `name_en` for both ORM queries and attribute access.

Similarly for Address:

```python
# Before
Address.objects.filter(full_name__icontains="Mannerheim")

# After
Address.objects.filter(full_name_fi__icontains="Mannerheim")
```

### Rollback

If you need to revert, restore from your database backup. The old 0.2
migrations are no longer shipped, so downgrading the package version is not
sufficient to restore the old migration chain.

---

## Breaking changes

These primarily affect **0.3 consumers** (projects that used parler-based
translations). 0.2 consumers will have already encountered most of these
through the modeltranslation-era code.

### Parler translation tables removed

Migrations 0006-0008 add direct `name_fi`/`name_sv`/`name_en` fields, migrate
data from parler tables, and then **delete** the translation models:

- `AdministrativeDivisionTranslation`
- `MunicipalityTranslation`
- `StreetTranslation`

Any code using parler-style patterns must be rewritten:

```python
# Before (parler)
Division.objects.filter(translations__name="Helsinki")
Division.objects.prefetch_related("translations")
serializer using TranslatedFieldsField from parler_rest

# After (1.0)
Division.objects.filter(name_fi="Helsinki")
# No prefetch needed - fields are on the model directly
# Use TranslatedModelSerializer from munigeo.api
```

#### Prefetch/select_related referencing translation tables

Any `.prefetch_related("translations")` or
`.prefetch_related("municipality__translations")` calls will raise
`ProgrammingError: relation "munigeo_*_translation" does not exist` after
migration 0008 drops the tables. Remove all `*__translations` prefetches -
they are no longer needed since translated fields are directly on the model.

```python
# Before
divisions = AdministrativeDivision.objects.prefetch_related("translations")
municipalities = Municipality.objects.prefetch_related("translations")

# After - just remove the prefetch entirely
divisions = AdministrativeDivision.objects.all()
municipalities = Municipality.objects.all()
```

#### Filter lookups using `translations__name`

The old pattern `Q(translations__name__in=values)` must be replaced with
direct field lookups:

```python
# Before (parler)
Division.objects.filter(translations__name__in=["Helsinki", "Espoo"])
Municipality.objects.filter(translations__name__icontains="hels")

# After (1.0) - use explicit language fields
from django.db.models import Q
Division.objects.filter(
    Q(name_fi__in=values) | Q(name_sv__in=values) | Q(name_en__in=values)
)
Municipality.objects.filter(name_fi__icontains="hels")
```

### No `.name` attribute on model instances

There is no `name` column and no Python descriptor. Accessing `.name` on a
model instance raises `AttributeError`:

```python
# Before
division.name  # worked via parler or modeltranslation

# After - BROKEN
division.name  # AttributeError

# After - correct
division.name_fi  # or name_sv, name_en
```

ORM queries using `name=` will also fail:

```python
# Before
Municipality.objects.get(name="Helsinki")

# After
Municipality.objects.get(name_fi="Helsinki")
```

If you need language-dynamic access (e.g. based on the active language):

```python
# Before (parler)
from parler.utils.context import switch_language
with switch_language(obj, lang):
    label = obj.name

# After (1.0)
label = getattr(obj, f"name_{lang}", None)
```

### `TranslatedDictField` must be declared on serializer classes

If a serializer lists `name` (or any translated field) in `Meta.fields`, DRF
validates field names against the model before the serializer's `__init__`
runs. Since `name` is not a real model field, this causes a validation error.

The fix is declaring the field as an explicit class attribute:

```python
from munigeo.api import TranslatedDictField

class MyDivisionSerializer(serializers.ModelSerializer):
    name = TranslatedDictField(base_field="name")

    class Meta:
        model = AdministrativeDivision
        fields = ["id", "name", ...]
```

This is the single biggest gotcha when updating serializers.

### `SlugRelatedField` references

Any `SlugRelatedField(slug_field="name")` pointing at Municipality or
similar models needs updating:

```python
# Before
municipality = serializers.SlugRelatedField(slug_field="name", ...)

# After
municipality = serializers.SlugRelatedField(slug_field="name_fi", ...)
```

### Parler can be removed from dependencies

If munigeo was the only reason for the `django-parler` and `django-parler-rest`
dependencies, they can now be removed entirely:

```bash
pip uninstall django-parler django-parler-rest
```

Also remove:
- `"parler"` from `INSTALLED_APPS`
- `PARLER_LANGUAGES` from settings
- Any `from parler.utils.context import switch_language` usage in tests
  (replace with direct field assignment: `name_fi="...", name_sv="..."`)

### Query count changes in tests

Removing parler joins reduces query counts. If your tests use
`assertNumQueries`, they will likely need updating (typically fewer queries
than before).

### `Address.municipality` is now required

The `municipality` ForeignKey on `Address` is non-nullable. Code that creates
Address objects must now provide it:

```python
# Before
Address(street=street, number="1", ...)

# After
Address(street=street, number="1", municipality=street.municipality, ...)
```

### `Address.modified_at` no longer uses `auto_now=True`

The field is now a plain `DateTimeField` with a custom `save()` that sets the
timestamp. This means:

- `Address.objects.update(...)` bulk operations will **not** auto-set
  `modified_at`. You must explicitly include `modified_at=timezone.now()`.
- `save(update_fields=[...])` without `modified_at` in the list will not
  update it (previously `auto_now` force-added it).

`AdministrativeDivision.modified_at` is unchanged (`auto_now=True`).

### `TranslatedModelSerializer` reimplemented

The class still exists in `munigeo.api` and produces the same JSON shape:

```json
{"name": {"fi": "Helsinki", "sv": "Helsingfors", "en": "Helsinki"}}
```

However, it no longer uses parler internals. If your serializer inherited from
parler-rest's `TranslatableModelSerializer` and referenced munigeo models, it
must be updated to use `munigeo.api.TranslatedModelSerializer` or read from
the `name_fi`/`name_sv`/`name_en` fields directly.

### Importer: `neighborhood` and `postcode_area` moved to HSY

The `neighborhood` and `postcode_area` division types have been **removed**
from the Helsinki importer config and moved to the new HSY importer.

If your cronjob runs `geo_import helsinki --divisions` and you rely on
neighborhood or postal code area divisions, they will **silently stop being
updated**. You must add the HSY importer to your cronjob:

```bash
python manage.py geo_import hsy --divisions
```

The HSY importer requires municipalities to exist first (it looks them up by
`name_fi`), so `geo_import finland --municipalities` must run before it.

**Recommended cronjob order after upgrade:**

```bash
python manage.py geo_import finland --municipalities
python manage.py geo_import helsinki --divisions
python manage.py geo_import hsy --divisions
python manage.py geo_import helsinki --addresses
```

Other behavioral changes in the Helsinki importer (non-breaking):

- Division import now continues if one type fails (try/except per type)
- Address import creates `PostalCodeArea` objects and links them to addresses
- Address import populates `municipality`, `full_name_*`, and search columns
- ~10 new division types are imported (parking, rescue, voting, etc.)

## New features

**New models and fields:**

| Addition | Description |
|----------|-------------|
| `PostalCodeArea` | Model with postal code, multilingual name, and area geometry |
| `Address.municipality` | Direct FK to Municipality (backfilled from street) |
| `Address.full_name_fi/sv/en` | Full address string for search indexing |
| `Address.search_column_fi/sv/en` | PostgreSQL full-text search vectors |
| `Address.syllables_fi` | Finnish syllable tokenization for search |
| `Address.postal_code_area` | FK to PostalCodeArea |
| `AdministrativeDivision.extra` | JSONField for arbitrary metadata |
| `AdministrativeDivision.units` | Integer array of related service point IDs |
| `AdministrativeDivision.search_column_fi/sv/en` | Full-text search vectors |
| `Municipality.code` | Official 3-digit municipal code (e.g. "091") |
| `AdministrativeDivision.origin_id` | Max length increased from 50 to 64 |

**New API query parameters:**

| Endpoint | Parameter | Description |
|----------|-----------|-------------|
| `/division/` | `?municipality=` | Filter by municipality name |
| `/division/` | `?extra__key=value` | Filter by extra field value |
| `/address/` | `?municipality=` | Filter by municipality (OCD ID or name) |
| `/address/` | `?lat=&lon=&distance=` | Distance-based search (meters) |
| `/address/` | `?bbox=&bbox_srid=` | Bounding box filter |

**New Helsinki division types:**

- `nature_reserve` - Luonnonsuojelualue
- `resident_parking_zone` - Asukaspysakointivyohyke
- `parking_area` - Pysakointipaikka-alue
- `parking_payzone` - Pysakointimaksuvyohyke

The `neighborhood` and `postcode_area` types have moved from the Helsinki
importer to the HSY importer.

**Importer changes:**

- `IMPORT_DATA_PATH` setting for custom data file locations
- HSY importer handles neighborhood and postcode area divisions
- Helsinki address import populates `full_name_*`, search columns, municipality,
  and postal code area

**New settings:**

| Setting | Required | Description |
|---------|----------|-------------|
| `GEO_SEARCH_LOCATION` | For uusimaa/postal code importers | Base URL of the geo-search service (e.g. `"https://geo-search.example.com"`) |
| `GEO_SEARCH_API_KEY` | For uusimaa/postal code importers | API key for the geo-search service |
| `IMPORT_DATA_PATH` | No | Custom path for importer data files. Falls back to `PROJECT_ROOT/data` or `BASE_DIR/data` |

Previously existing settings (unchanged):

| Setting | Required | Description |
|---------|----------|-------------|
| `DEFAULT_SRID` | No | Default SRID for geometry output. Falls back to `PROJECTION_SRID`, then WGS-84 (4326) |
| `PROJECTION_SRID` | No | Legacy alias for `DEFAULT_SRID` |
| `DEFAULT_COUNTRY` | For OCD IDs | Country code used in OCD identifiers |
| `DEFAULT_OCD_MUNICIPALITY` | For OCD IDs | Municipality type slug for OCD identifiers |
| `AXIS_ORDER` | No | GDAL `AxisOrder` for Helsinki importer coordinate transforms (default: `TRADITIONAL`) |

## After migrating: re-run importers

New fields start empty (NULL or default). To populate them, re-run the
relevant importers:

```bash
# Populates municipality.code and division data
python manage.py geo_import finland --municipalities

# Populates address fields, search columns, postal code areas
python manage.py geo_import helsinki --addresses

# Populates neighborhood and postcode_area divisions
python manage.py geo_import hsy --divisions
```
