#!/usr/bin/env python3
"""
Seed JA (katakana/kanji) name aliases into the aliases table.
These allow ingest_ja_wiki.py to match JA Wikipedia character blocks to entity_ids.

Mappings derived from cross-referencing unmatched JA names against known entity_ids.
"""
import sqlite3

DB = 'C:/Users/dissonance/Desktop/Trails/retrieval/index/trails.db'
conn = sqlite3.connect(DB)
c = conn.cursor()

# (ja_name, entity_id) pairs
# Verified against entity_registry display names
JA_ALIASES = [
    # Sky arc
    ('シェラザード・ハーヴェイ',  'char:scherazard_harvey'),
    ('シェラザード・アルノール',  'char:scherazard_harvey'),   # married name in later arcs
    ('クローゼ・リンツ',          'char:kloe_rinz'),
    ('ティータ・ラッセル',        'char:tita_russell'),
    ('ミーシャ・クロスナー',      'char:mischa_crosner'),
    ('カシウス・ブライト',        'char:cassius_bright'),
    ('アルバート・フォン・バルトロメウス', 'char:albarea'),   # approximate
    ('アルベルト・ライゼ・アルノール',    'char:albert_reise_arnor'),
    ('オルトロス・ライゼ・アルノール',    'char:orthos_reise_arnor'),
    ('グンナル・ライゼ・アルノール',      'char:gunnar_reise_arnor'),
    ('セレスト・D・アウスレーゼ', 'char:celeste_d_auslese'),
    ('フィリップ・ルナール',      'char:phillip_runall'),
    ('アラミス・ゲンズブール',    'char:aramis_gensbourg'),
    ('ウルガー・アトキンソン',    'char:vulgar_atkinson'),
    ('オーギュスト・アルダン',    'char:august_aldan'),
    ('ラグン・カーン',            'char:ragun_khan'),
    ('カルナ',                    'char:carna'),
    ('セリーヌ',                  'char:celine'),

    # Zero/Azure arc
    ('エリィ・マクダエル',        'char:elie_macdowell'),
    ('ランディ・オルランド',       'char:randy_orlando'),
    ('ティオ・プラット',           'char:tio_plato'),
    ('シギュン・ルウ',             'char:sigrun_lu'),
    ('シン・ルウ',                 'char:xin_lu'),
    ('ギエン・ルウ',               'char:guen_lu'),
    ('セルゲイ・ロウ',             'char:sergei_lou'),
    ('センダー',                   'char:sanda'),
    ('アレックス・ダドリー',       'char:alex_dudley'),
    ('ウォレス・バルディアス',     'char:wallace_bardias'),
    ('ジミー・バーネット',         'char:jimmy_barnett'),
    ('コーディ・マクミラン',       'char:cody_mcmillan'),

    # Cold Steel arc
    ('エリゼ・シュバルツァー',     'char:elise_schwarzer'),
    ('アルティナ・オライオン',     'char:altina_orion'),
    ('クルト・ヴァンダール',       'char:kurt_vander'),
    ('クロワール・ド・カイエン',   'char:crow_armbrust'),
    ('オーレリア・ルグィン',       'char:aurelia_le_guin'),
    ('アリアンロード',             'char:arianrhod'),
    ('ゲルハルト・シュミット',     'char:gerhard_schmidt'),
    ('クロード・エプスタイン',     'char:claude_epstein'),
    ('《C》',                      'char:c_(reverie)'),
    ('《C》（シー）',              'char:c_(reverie)'),
    ('シズナ・レム・ミスルギ',     'char:shizuna_rem_misurugi'),
    ('ゼクトール',                 'char:zector'),
    ('アシュ・カーバイド',         'char:ash_carbide'),
    ('アッシュ・カーバイド',       'char:ash_carbide'),
    ('イサラ・アーヴィング',       'char:isara_irving'),
    ('エドモン・オークレール',     'char:edmond_auclair'),
    ('エミリア・ハーリング',       'char:emilia_haling'),
    ('グレイ・アーノルド',         'char:grey_arnaud'),
    ('ゲラント・レイガー',         'char:gerald_reiger'),
    ('ウィリアム・レイクロード',   'char:william_lakelord'),
    ('ジョン・レイクロード',       'char:john_lakelord'),

    # Daybreak arc
    ('クウガ・カーファイ',         'char:khyarga'),
    ('アルム',                     'char:alm'),
    ('アナベル',                   'char:annabel'),

    # Series-wide
    ('アルヴィス',                 'char:alvis'),
    ('アイカ',                     'char:aika'),
]

# Insert into aliases table
inserted = 0
skipped = 0
for ja_name, entity_id in JA_ALIASES:
    # Verify entity_id exists
    c.execute('SELECT 1 FROM entity_registry WHERE entity_id=?', (entity_id,))
    if not c.fetchone():
        print(f'  SKIP (entity not found): {entity_id}')
        skipped += 1
        continue

    c.execute("""
        INSERT OR IGNORE INTO aliases (entity_id, alias, is_official, language)
        VALUES (?, ?, 0, 'ja')
    """, (entity_id, ja_name))
    if c.rowcount:
        inserted += 1

conn.commit()
print(f'Inserted {inserted} JA aliases, skipped {skipped} (entity not found)')

# Show current aliases count by language
c.execute('SELECT language, COUNT(*) FROM aliases GROUP BY language ORDER BY COUNT(*) DESC')
print('\nAliases by language:')
for r in c.fetchall():
    print(f'  {r[0]}: {r[1]}')

conn.close()
