from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("munigeo", "0012_municipality_code"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                create or replace function naturalsort(text)
                    returns bytea
                    language sql
                    immutable strict
                as $f$
                    select string_agg(convert_to(coalesce(r[2],
                    length(length(r[1])::text) || length(r[1])::text || r[1]),
                    'SQL_ASCII'),'\\x00')
                    from regexp_matches($1, '0*([0-9]+)|([^0-9]+)', 'g') r;
                $f$;            
            """,
            reverse_sql="""
                drop function naturalsort;
            """,
        ),
    ]
