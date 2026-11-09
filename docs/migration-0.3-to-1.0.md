# Migration guide: django-munigeo 0.3.12 to 1.0

This guide covers PostgreSQL databases at the released django-munigeo 0.3.12
migration state, with munigeo migrations applied through
`0005_update_translation_foreign_keys`. Older 0.3 histories are outside this
guide's scope. Fresh databases can run the normal 1.0 migration chain directly.

A 0.3.12 database uses the normal 1.0 migration chain. Do not rewrite migration
history, use `--fake`, or add a consumer bridge as described in
[the 0.2 guide](MIGRATION-0.2-to-1.0.md).

## Application code

Update the application dependency to django-munigeo 1.0 and rebuild the
application environment before deploying the updated code.

The 0.3.12 models use django-parler translation tables. In 1.0, translated
values are ordinary fields on the main models, and the translation tables are
removed by migration `0008`.

Update application code, management commands, raw SQL, fixtures, factories,
serializers, and tests:

| 0.3.12 | 1.0 |
| --- | --- |
| `obj.set_current_language("fi"); obj.name` | `obj.name_fi` |
| `obj.set_current_language(language); obj.name` | `getattr(obj, f"name_{language}", None) or obj.name_fi` |
| `filter(name=...)` on a translated munigeo model | `filter(name_fi=...)` or an explicit language `Q` expression |
| `filter(translations__name=...)` | `filter(name_fi=...)`, `filter(name_sv=...)`, or `filter(name_en=...)` |
| `prefetch_related("translations")` | Remove the translation prefetch |
| `switch_language(division, "en")` followed by `division.name = ...` | `division.name_en = ...` |

For queries that should match all supported languages, combine the explicit
`name_fi`, `name_sv`, and `name_en` fields instead of relying on parler's
current-language behavior.

Remove munigeo-specific imports from `parler`, `parler_rest`, or
`munigeo.translation`. Keep django-parler only if another application feature
still uses it.

Replace parler-specific serializer fields and `translations` output with the
1.0 munigeo serializer/API shape.

If the application uses `Address`, update it for the new fields:

- `municipality` is populated from `street.municipality`.
- `full_name_fi`, `full_name_sv`, and `full_name_en` are explicit language
  fields.
- `postal_code_area` is an optional new relation.

Existing application migration dependencies on
`munigeo.0001_squashed_0004_building` and
`munigeo.0005_update_translation_foreign_keys` remain valid. Do not edit
already-applied migrations. If a new application migration needs fields
introduced by 1.0, create a new migration depending on the previous application
migration and `munigeo.0010_postalcodearea_address_full_name_en_and_more`.

## Migration

After updating the application code and dependency, run the usual Django
migration from the application environment:

> **Back up first.** Take and verify a complete PostgreSQL backup before
> running the migration. It removes the parler translation tables, and reverse
> migrations are not a reliable rollback path. Do not proceed without a backup
> that can be restored.

```bash
python manage.py migrate
```

The migration chain copies the parler values into the new fields and applies the
remaining schema changes. It removes the translation tables, so do not run the
previous application image after the migration.
