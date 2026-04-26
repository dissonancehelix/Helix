#!/usr/bin/env python3
"""
Register Faction, Location, Staff, Entity tables in cargo_tables
so the Cargo API (action=cargoquery) can query them.
"""
import subprocess

DB_USER = "wiki_user"
DB_PASS = "trailsdb2026"
DB_NAME = "trails_wiki"

def sql(query):
    result = subprocess.run(
        ["bash", "-c", f"mariadb -u {DB_USER} -p{DB_PASS} {DB_NAME}"],
        input=query, capture_output=True, text=True, encoding='utf-8'
    )
    return result.stdout.strip()

# PHP-serialize a simple {field: {type: String/Integer}} schema
def php_schema(fields):
    # fields: list of (name, type) where type is 'String' or 'Integer'
    parts = []
    for name, ftype in fields:
        sname = f's:{len(name)}:"{name}";'
        stype = f's:{len(ftype)}:"{ftype}";'
        parts.append(f'{sname}a:1:{{s:4:"type";{stype}}}')
    inner = "".join(parts)
    return f'a:{len(fields)}:{{{inner}}}'

tables = [
    ('Faction', 5, [
        ('entity_id', 'String'),
        ('name_en', 'String'),
        ('name_ja', 'String'),
        ('arc', 'String'),
        ('spoiler_band', 'Integer'),
    ]),
    ('Location', 6, [
        ('entity_id', 'String'),
        ('name_en', 'String'),
        ('name_ja', 'String'),
        ('region', 'String'),
        ('arc', 'String'),
        ('spoiler_band', 'Integer'),
    ]),
    ('Staff', 7, [
        ('entity_id', 'String'),
        ('name_en', 'String'),
        ('name_ja', 'String'),
        ('spoiler_band', 'Integer'),
    ]),
    ('Entity', 8, [
        ('entity_id', 'String'),
        ('entity_type', 'String'),
        ('name_en', 'String'),
        ('name_ja', 'String'),
        ('spoiler_band', 'Integer'),
    ]),
]

for table_name, template_id, fields in tables:
    schema = php_schema(fields)
    stmt = (
        f"INSERT IGNORE INTO cargo_tables (template_id, main_table, field_tables, field_helper_tables, table_schema) "
        f"VALUES ({template_id}, '{table_name}', 'a:0:{{}}', 'a:0:{{}}', '{schema}');"
    )
    result = sql(stmt)
    print(f"Registered: {table_name}")

# Verify
out = sql("SELECT main_table FROM cargo_tables ORDER BY main_table;")
print("\ncargo_tables now contains:")
for line in out.split('\n'):
    if line.strip() and line.strip() != 'main_table':
        print(f"  {line.strip()}")
