-- Create Character Cargo table manually
-- Run: sudo mariadb trails_wiki < /mnt/c/Users/dissonance/Desktop/Trails/scripts/create_character_cargo.sql

INSERT IGNORE INTO cargo_tables (template_id, main_table, field_tables, field_helper_tables, table_schema)
VALUES (3, 'Character', 'a:0:{}', 'a:0:{}',
  'a:8:{s:9:"entity_id";a:1:{s:4:"type";s:6:"String";}s:7:"name_en";a:1:{s:4:"type";s:6:"String";}s:7:"name_ja";a:1:{s:4:"type";s:6:"String";}s:7:"aliases";a:1:{s:4:"type";s:6:"String";}s:20:"arc_first_appearance";a:1:{s:4:"type";s:6:"String";}s:12:"spoiler_band";a:1:{s:4:"type";s:7:"Integer";}s:8:"voice_jp";a:1:{s:4:"type";s:6:"String";}s:8:"voice_en";a:1:{s:4:"type";s:6:"String";}}');

CREATE TABLE IF NOT EXISTS cargo__Character (
  _ID              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  _pageID          INT UNSIGNED DEFAULT NULL,
  _pageName        VARCHAR(255) DEFAULT NULL,
  _pageNamespace   INT DEFAULT NULL,
  _pageIsRedirect  TINYINT(1) DEFAULT NULL,
  _sectionID       INT UNSIGNED DEFAULT NULL,
  entity_id        VARCHAR(255) DEFAULT NULL,
  name_en          VARCHAR(255) DEFAULT NULL,
  name_ja          VARCHAR(255) DEFAULT NULL,
  aliases          VARCHAR(255) DEFAULT NULL,
  arc_first_appearance VARCHAR(255) DEFAULT NULL,
  spoiler_band     INT DEFAULT NULL,
  voice_jp         VARCHAR(255) DEFAULT NULL,
  voice_en         VARCHAR(255) DEFAULT NULL
);

SELECT 'Character table ready' AS status;
SELECT main_table FROM cargo_tables ORDER BY template_id;
