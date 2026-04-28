#!/usr/bin/env python3
import subprocess

DB_USER = "wiki_user"
DB_PASS = "trailsdb2026"
DB_NAME = "trails_wiki"

def sql(q):
    r = subprocess.run(
        ["bash", "-c", f"mariadb -u {DB_USER} -p{DB_PASS} {DB_NAME}"],
        input=q, capture_output=True, text=True, encoding='utf-8'
    )
    return r.stdout.strip(), r.returncode, r.stderr[:200]

def php_schema(fields):
    parts = []
    for name, ftype in fields:
        sname = f's:{len(name)}:"{name}";'
        stype = f's:{len(ftype)}:"{ftype}";'
        parts.append(f'{sname}a:1:{{s:4:"type";{stype}}}')
    inner = "".join(parts)
    return f'a:{len(fields)}:{{{inner}}}'

fields = [('entity_id', 'String'), ('name_en', 'String'), ('name_ja', 'String'), ('arc', 'String'), ('spoiler_band', 'Integer')]
schema = php_schema(fields)
print("Generated schema:", schema)
print()

stmt = (
    "INSERT IGNORE INTO cargo_tables (template_id, main_table, field_tables, field_helper_tables, table_schema) "
    f"VALUES (99, 'TestFaction', 'a:0:{{}}', 'a:0:{{}}', '{schema}');"
)
print("INSERT stmt (first 300):", stmt[:300])
print()

out, rc, err = sql(stmt)
print("INSERT rc:", rc, "err:", err[:100])

out2, rc2, err2 = sql("SELECT main_table, table_schema FROM cargo_tables WHERE main_table='TestFaction';")
print("Stored schema:", out2)

sql("DELETE FROM cargo_tables WHERE main_table='TestFaction';")
