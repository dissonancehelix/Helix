-- Register Faction, Location, Staff, Entity in cargo_tables

INSERT IGNORE INTO cargo_tables (template_id, main_table, field_tables, field_helper_tables, table_schema)
VALUES (
  5, 'Faction', 'a:0:{}', 'a:0:{}',
  'a:5:{s:9:"entity_id";a:1:{s:4:"type";s:6:"String";}s:7:"name_en";a:1:{s:4:"type";s:6:"String";}s:7:"name_ja";a:1:{s:4:"type";s:6:"String";}s:3:"arc";a:1:{s:4:"type";s:6:"String";}s:12:"spoiler_band";a:1:{s:4:"type";s:7:"Integer";}}'
);

INSERT IGNORE INTO cargo_tables (template_id, main_table, field_tables, field_helper_tables, table_schema)
VALUES (
  6, 'Location', 'a:0:{}', 'a:0:{}',
  'a:6:{s:9:"entity_id";a:1:{s:4:"type";s:6:"String";}s:7:"name_en";a:1:{s:4:"type";s:6:"String";}s:7:"name_ja";a:1:{s:4:"type";s:6:"String";}s:6:"region";a:1:{s:4:"type";s:6:"String";}s:3:"arc";a:1:{s:4:"type";s:6:"String";}s:12:"spoiler_band";a:1:{s:4:"type";s:7:"Integer";}}'
);

INSERT IGNORE INTO cargo_tables (template_id, main_table, field_tables, field_helper_tables, table_schema)
VALUES (
  7, 'Staff', 'a:0:{}', 'a:0:{}',
  'a:4:{s:9:"entity_id";a:1:{s:4:"type";s:6:"String";}s:7:"name_en";a:1:{s:4:"type";s:6:"String";}s:7:"name_ja";a:1:{s:4:"type";s:6:"String";}s:12:"spoiler_band";a:1:{s:4:"type";s:7:"Integer";}}'
);

INSERT IGNORE INTO cargo_tables (template_id, main_table, field_tables, field_helper_tables, table_schema)
VALUES (
  8, 'Entity', 'a:0:{}', 'a:0:{}',
  'a:5:{s:9:"entity_id";a:1:{s:4:"type";s:6:"String";}s:11:"entity_type";a:1:{s:4:"type";s:6:"String";}s:7:"name_en";a:1:{s:4:"type";s:6:"String";}s:7:"name_ja";a:1:{s:4:"type";s:6:"String";}s:12:"spoiler_band";a:1:{s:4:"type";s:7:"Integer";}}'
);
