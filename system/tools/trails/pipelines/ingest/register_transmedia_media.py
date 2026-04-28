import sqlite3
import datetime

def register_media():
    conn = sqlite3.connect('retrieval/index/trails.db')
    cur = conn.cursor()
    
    # media_registry structure:
    # media_id, media_type, english_title, japanese_title, aliases, publisher, 
    # release_date_jp, release_date_en, internal_chronology, release_chronology, 
    # spoiler_band, is_main_series, canonical_notes, technical_id

    new_media = [
        (
            'drama_advanced', 'drama_cd', 'Trails in the Sky Drama CD: Advanced Chapter', 
            '空の軌跡 ドラマCD： 進化（アドバンスド）チャプター', 'Advanced Chapter', 'Falcom', 
            '2009-07-25', None, 'Post-FC / Pre-SC', 100, 1, 0, 
            'Bridge story between FC and SC focusing on Joshua.', 'drama_sky_adv'
        ),
        (
            'drama_future', 'drama_cd', 'Trails to Azure Drama CD: Road to the Future', 
            '碧の軌跡 ドラマCD： 未来（ロード）への道', 'Road to the Future', 'Falcom', 
            '2011-09-29', None, 'Pre-Azure', 101, 1, 0, 
            'Bridge story between Zero and Azure.', 'drama_ao_road'
        ),
        (
            'ss_snowlight', 'side_story', "Trails of Cold Steel II Side Story: Alister's Snowlight", 
            '閃の軌跡II 外伝： アリスターの雪光', 'Alister\'s Snowlight, Memoirs', 'Falcom', 
            '2014-09-25', None, 'During CS2 Part 1', 102, 2, 0, 
            'Official supplemental story for Cold Steel II.', 'ss_cs2_snowlight'
        )
    ]
    
    print("--- Registering Transmedia ---")
    for media in new_media:
        cur.execute("""
            INSERT OR REPLACE INTO media_registry 
            (media_id, media_type, english_title, japanese_title, aliases, publisher, 
             release_date_jp, release_date_en, internal_chronology, release_chronology, 
             spoiler_band, is_main_series, canonical_notes, technical_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, media)
        print(f"Registered: {media[2]}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    register_media()
