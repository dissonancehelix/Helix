"""
taste_report.py — Helix Music: Domain-driven Taste Analysis.

Summarizes the operator's musical taste based on 'Loved' tracks and structural tags.
"""
import sqlite3
from pathlib import Path
import collections

db_path = Path("C:/Users/dissonance/Desktop/Helix/domains/music/ingestion/data/helix_music.db")

def run_report():
    if not db_path.exists():
        print("DB not found")
        return
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # 1. Total Loved Tracks
    loved_count = conn.execute("SELECT COUNT(*) FROM tracks WHERE loved=1").fetchone()[0]
    
    # 2. Top Structural Tags (Taste Profile)
    # Join Loved tracks with semantic_tags
    tags_query = """
        SELECT s.tag_name, COUNT(*) as frequency
        FROM semantic_tags s
        JOIN tracks t ON s.track_id = t.id
        WHERE t.loved = 1
        GROUP BY s.tag_name
        ORDER BY frequency DESC
        LIMIT 10
    """
    top_tags = conn.execute(tags_query).fetchall()
    
    # 3. Top Composers (Artist Override)
    # Priority: ARTIST > ALBUM ARTIST
    composer_query = """
        SELECT COALESCE(artist, album_artist, 'Unknown') as composer, 
               COUNT(*) as count
        FROM tracks
        WHERE loved = 1
        GROUP BY composer
        ORDER BY count DESC
        LIMIT 10
    """
    top_composers = conn.execute(composer_query).fetchall()

    # 4. Partition Distribution
    partition_query = """
        SELECT 
            CASE 
                WHEN file_path LIKE '%VGM%' THEN 'VGM'
                WHEN file_path LIKE '%Anime%' THEN 'Anime'
                WHEN file_path LIKE '%Film%' THEN 'Film'
                ELSE 'Others'
            END as partition,
            COUNT(*) as count
        FROM tracks
        WHERE loved = 1
        GROUP BY partition
        ORDER BY count DESC
    """
    partitions = conn.execute(partition_query).fetchall()

    print("=== Helix Music: Domain-Driven Taste Profile ===")
    print(f"Sample Size: {loved_count} Loved Tracks")
    
    print("\n[ Structural Taste-Space ]")
    if not top_tags:
        print("  (No structural tags indexed for loved tracks yet. Sync still in progress.)")
    else:
        for row in top_tags:
            print(f"  {row['frequency']:>4}x  {row['tag_name']}")
    
    print("\n[ Top Composers / Anchors ]")
    for row in top_composers:
        print(f"  {row['count']:>4}x  {row['composer']}")
        
    print("\n[ Corpus Partitions ]")
    for row in partitions:
        pct = (row['count'] / loved_count * 100) if loved_count else 0
        print(f"  {pct:>5.1f}%  {row['partition']} ({row['count']})")
        
    conn.close()

if __name__ == "__main__":
    run_report()
