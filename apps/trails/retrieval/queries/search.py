import sqlite3
import json
from pathlib import Path
import argparse

DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

# Safety Configuration
SPOILER_LOCK = ["Beyond the Horizon", "Kai no Kiseki", "kai"]

def query_corpus(query: str, game_filter: str = None, include_spoilers: bool = False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Alias Resolution Layer
    cursor.execute('''
        SELECT a_jp.alias FROM aliases a_en 
        JOIN entities e ON a_en.entity_id = e.entity_id
        JOIN aliases a_jp ON a_jp.entity_id = e.entity_id
        WHERE a_en.alias COLLATE NOCASE = ? AND a_jp.alias != a_en.alias
    ''', (query,))
    aliases = cursor.fetchall()
    
    fts_query = f'"{query}"'
    if aliases:
        jp_alias = aliases[0][0]
        fts_query = f'"{query}" OR "{jp_alias}"'
        print(f"\n--- Searching for: '{query}' (Auto-Expanded to include: {jp_alias}) ---")
    else:
        print(f"\n--- Searching for: '{query}' ---")
    
    # 2. Main Query Construction
    sql = """
        SELECT c.chunk_id, c.text_content, c.game, s.source_class, c.trust_tier
        FROM chunks_fts fts
        JOIN chunks c ON fts.chunk_id = c.chunk_id
        JOIN source_registry s ON c.source_id = s.source_id
        WHERE chunks_fts MATCH ?
    """
    params = [fts_query]
    
    # 3. Apply Spoiler Safety (Mandatory Lock)
    if not include_spoilers:
        placeholders = ', '.join(['?'] * len(SPOILER_LOCK))
        sql += f" AND (c.game NOT IN ({placeholders}) OR c.game IS NULL)"
        params.extend(SPOILER_LOCK)
        sql += " AND c.spoiler_tier < 100" # Kai content should be tagged 100+
    
    if game_filter:
        sql += " AND c.game = ?"
        params.append(game_filter)
        
    # 4. Sort by Trust Tier (Official first)
    sql += " ORDER BY c.trust_tier DESC, c.rowid ASC"
        
    cursor.execute(sql, params)
    results = cursor.fetchall()
    
    if not results:
        print("No results found.")
    
    for row in results:
        chunk_id, text, game, source_type, trust = row
        trust_label = f"T{trust}"
        print(f"[{source_type}] [{trust_label}] ({game}) | ID: {chunk_id}")
        print(f"  > {text.replace(chr(10), ' ')}")
        print("-" * 50)
        
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query the Trails corpus.")
    parser.add_argument("query", type=str, help="FTS5 match query")
    parser.add_argument("--game", type=str, help="Filter by game ID")
    parser.add_argument("--unsafe", action="store_true", help="IGNORE current safety locks (Curator only)")
    
    args = parser.parse_args()
    query_corpus(args.query, args.game, args.unsafe)
