# Migration guide: django-munigeo 0.2 to 1.0

This guide covers PostgreSQL databases that use the django-munigeo 0.2
migration history. It applies to databases that already contain 0.2 munigeo
data. Fresh databases can run the normal 1.0 migration chain directly.

The target migration is:

```text
munigeo.0010_postalcodearea_address_full_name_en_and_more
```

Do not run the normal 1.0 munigeo migrations against an existing 0.2 database
without first rewriting its migration history and adding the consumer bridge
described below.

## Before migration

1. Update the application dependency to the django-munigeo 1.0 migration line.
   Use the target checkout's lockfile and rebuild the application environment.
2. Use Python 3.10 or newer, Django 5.2 or newer, and `urllib3` 2 or newer.
3. Stop application replicas, scheduled imports, and other jobs that write
   munigeo data.
4. Take a database backup.
5. Apply the application code changes below before starting the new image.

### Application code

The translated base attributes are removed. Update application code,
management commands, raw SQL, fixtures, factories, and tests:

| 0.2 | 1.0 |
| --- | --- |
| `municipality.name` | `municipality.name_fi` |
| `division.name` | `division.name_fi` |
| `street.name` | `street.name_fi` |
| `address.full_name` | `address.full_name_fi` |
| `filter(name=...)` | `filter(name_fi=...)` |
| `filter(name__iexact=...)` | `filter(name_fi__iexact=...)` |
| `Model(name="...")` | `Model(name_fi="...")` |
| `filter(municipality__name=...)` | `filter(municipality__name_fi=...)` |

Remove imports from `munigeo.translation`. `AdministrativeDivisionType.name` and
`POI.name` are ordinary fields and are not part of this change.

Update application migration dependencies as follows:

- Keep dependencies on `munigeo.0001_initial` through
  `munigeo.0004_building`. The 1.0 squash migration replaces those names.
- Change dependencies on 0.2-only migrations after `0004` to the appropriate
  1.0 migration. In smbackend, dependencies on 0.2 migration `0014` changed to
  `munigeo.0010_postalcodearea_address_full_name_en_and_more`.

Search dependencies with:

```bash
grep -R "munigeo\." path/to/your_app/migrations
```

## Existing 0.2 database

### 1. Preflight and backup

```bash
pg_dump --format=custom --no-owner --no-acl \
  --dbname="$DATABASE_URL" > db_backup_pre_munigeo1.dump
```

Check the database state:

```sql
SELECT to_regclass('public.django_migrations') AS migration_table;

SELECT name
FROM django_migrations
WHERE app = 'munigeo'
ORDER BY name;
```

An existing 0.2 database normally has migration rows through
`0017_administrativedivision_munigeo_administrativedivi8660`. If the migration
table is missing, do not run this bookkeeping procedure; a fresh database can
run the normal 1.0 migration chain directly. Stop if the history is not a
known 0.2 history.

### 2. Rewrite migration history

Run the following SQL directly against the target database. Do not use
`manage.py migrate --fake`; Django checks migration consistency before handling
the fake request.

```sql
BEGIN;

DELETE FROM django_migrations
WHERE app = 'munigeo';

INSERT INTO django_migrations (app, name, applied)
VALUES
    ('munigeo', '0001_initial', CURRENT_TIMESTAMP),
    ('munigeo', '0002_auto_20150608_1607', CURRENT_TIMESTAMP),
    ('munigeo', '0003_add_modified_time_to_address_and_street', CURRENT_TIMESTAMP),
    ('munigeo', '0004_building', CURRENT_TIMESTAMP),
    ('munigeo', '0002_add_parler_translations', CURRENT_TIMESTAMP),
    ('munigeo', '0003_migrate_translations_to_parler', CURRENT_TIMESTAMP),
    ('munigeo', '0004_delete_old_translations', CURRENT_TIMESTAMP),
    ('munigeo', '0005_update_translation_foreign_keys', CURRENT_TIMESTAMP),
    ('munigeo', '0006_add_name_fields', CURRENT_TIMESTAMP),
    ('munigeo', '0007_migrate_translation_data', CURRENT_TIMESTAMP),
    ('munigeo', '0008_remove_translation_tables', CURRENT_TIMESTAMP),
    ('munigeo', '0009_alter_administrativedivision_name_en_and_more', CURRENT_TIMESTAMP),
    ('munigeo', '0010_postalcodearea_address_full_name_en_and_more', CURRENT_TIMESTAMP);

COMMIT;
```

Verify the rewrite:

```sql
SELECT COUNT(*) AS munigeo_migrations
FROM django_migrations
WHERE app = 'munigeo';
```

The count must be 13 before running Django. Do not insert the squash migration
name `0001_squashed_0004_building`; Django records it after the replacement
rows are present.

### 3. Add the consumer bridge migration

Generate an empty migration in the consuming application:

```bash
python manage.py makemigrations --empty your_app \
  --name munigeo_1_0_schema_bridge
```

Edit the generated file. Keep its dependency on the previous `your_app`
migration and add the final munigeo migration:

```python
dependencies = [
    ("munigeo", "0010_postalcodearea_address_full_name_en_and_more"),
    ("your_app", "00xx_previous_migration"),
]
```

Set `operations` to the following `RunSQL` operation. It copies legacy values
to Finnish fields, adds the 1.0 street constraint, removes the legacy columns,
and recreates `naturalsort()`. Remove the final function block if the
application does not use `naturalsort()` in raw SQL.

```python
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("munigeo", "0010_postalcodearea_address_full_name_en_and_more"),
        ("your_app", "00xx_previous_migration"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_address'
                      AND column_name = 'full_name'
                ) AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_address'
                      AND column_name = 'full_name_fi'
                ) THEN
                    EXECUTE '
                        UPDATE public.munigeo_address
                        SET full_name_fi = full_name
                        WHERE full_name IS NOT NULL
                          AND full_name_fi IS NULL
                    ';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_administrativedivision'
                      AND column_name = 'name'
                ) AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_administrativedivision'
                      AND column_name = 'name_fi'
                ) THEN
                    EXECUTE '
                        UPDATE public.munigeo_administrativedivision
                        SET name_fi = name
                        WHERE name IS NOT NULL
                          AND name_fi IS NULL
                    ';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_municipality'
                      AND column_name = 'name'
                ) AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_municipality'
                      AND column_name = 'name_fi'
                ) THEN
                    EXECUTE '
                        UPDATE public.munigeo_municipality
                        SET name_fi = name
                        WHERE name IS NOT NULL
                          AND name_fi IS NULL
                    ';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_postalcodearea'
                      AND column_name = 'name'
                ) AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_postalcodearea'
                      AND column_name = 'name_fi'
                ) THEN
                    EXECUTE '
                        UPDATE public.munigeo_postalcodearea
                        SET name_fi = name
                        WHERE name IS NOT NULL
                          AND name_fi IS NULL
                    ';
                END IF;

                IF EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_street'
                      AND column_name = 'name'
                ) AND EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'munigeo_street'
                      AND column_name = 'name_fi'
                ) THEN
                    EXECUTE '
                        UPDATE public.munigeo_street
                        SET name_fi = name
                        WHERE name IS NOT NULL
                          AND name_fi IS NULL
                    ';
                END IF;
            END
            $$;

            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_constraint
                    WHERE conrelid = 'public.munigeo_street'::regclass
                      AND conname =
                        'munigeo_street_municipality_id_name_fi_1c84aabc_uniq'
                ) THEN
                    EXECUTE '
                        ALTER TABLE public.munigeo_street
                        ADD CONSTRAINT
                            munigeo_street_municipality_id_name_fi_1c84aabc_uniq
                        UNIQUE (municipality_id, name_fi)
                    ';
                END IF;
            END
            $$;

            ALTER TABLE public.munigeo_street
                DROP CONSTRAINT IF EXISTS
                    munigeo_street_municipality_id_name_6e998d56_uniq;
            ALTER TABLE public.munigeo_address
                DROP COLUMN IF EXISTS full_name;
            ALTER TABLE public.munigeo_administrativedivision
                DROP COLUMN IF EXISTS name;
            ALTER TABLE public.munigeo_municipality
                DROP COLUMN IF EXISTS name;
            ALTER TABLE public.munigeo_postalcodearea
                DROP COLUMN IF EXISTS name;
            ALTER TABLE public.munigeo_street
                DROP COLUMN IF EXISTS name;

            CREATE OR REPLACE FUNCTION public.naturalsort(text)
            RETURNS bytea
            LANGUAGE sql
            IMMUTABLE STRICT
            AS $function$
                SELECT string_agg(
                    convert_to(
                        coalesce(
                            r[2],
                            length(length(r[1])::text) || length(r[1])::text || r[1]
                        ),
                        'SQL_ASCII'
                    ),
                    '\\x00'
                )
                FROM regexp_matches($1, '0*([0-9]+)|([^0-9]+)', 'g') r;
            $function$;
            """,
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
```

If the old street constraint has a different name, replace
`munigeo_street_municipality_id_name_6e998d56_uniq` with the name in
`pg_constraint`. The constraint definition must be
`UNIQUE (municipality_id, name)`.

### 4. Apply migrations

```bash
python manage.py migrate --plan
python manage.py migrate --noinput
```

The bridge is one-way. Do not run the previous application image against the
database after the legacy columns have been removed.

### 5. Rebuild derived data

Run the consuming application's normal data imports. If the application has
derived search fields, run its search-index rebuild command after the final
import.

## Verification

Run:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
```

`makemigrations --check --dry-run` should print `No changes detected` and exit
with status 0 after the existing database's migration history has been
rewritten and the consumer bridge has been applied.

Check that the legacy columns are gone:

```sql
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (
    (table_name = 'munigeo_address' AND column_name = 'full_name')
    OR (table_name = 'munigeo_administrativedivision' AND column_name = 'name')
    OR (table_name = 'munigeo_municipality' AND column_name = 'name')
    OR (table_name = 'munigeo_postalcodearea' AND column_name = 'name')
    OR (table_name = 'munigeo_street' AND column_name = 'name')
  );
```

The query should return no rows.

Check the street constraint and address relationships:

```sql
SELECT conname, pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid = 'public.munigeo_street'::regclass
  AND contype = 'u';

SELECT
    COUNT(*) AS address_rows,
    COUNT(*) FILTER (WHERE municipality_id IS NULL) AS missing_municipality_id
FROM munigeo_address;

SELECT COUNT(*) AS orphan_municipality_references
FROM munigeo_address AS address
LEFT JOIN munigeo_municipality AS municipality
    ON municipality.id = address.municipality_id
WHERE address.municipality_id IS NOT NULL
  AND municipality.id IS NULL;
```

The street constraint must include `UNIQUE (municipality_id, name_fi)`. The two
address counts must be zero. Verify the municipality, administrative division,
address, and search API endpoints, and confirm that a second
`python manage.py migrate --plan` is empty.

## Rollback

Restore the pre-migration backup and redeploy the previous application image.
The migration cannot restore the dropped legacy columns.
