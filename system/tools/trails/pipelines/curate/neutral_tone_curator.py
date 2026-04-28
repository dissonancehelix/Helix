import sqlite3
import re
import json
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).parent.parent.parent / 'retrieval' / 'index' / 'trails.db'

def clean_text(text):
    if not text: return ""
    # Remove MediaWiki noise
    text = re.sub(r'\{\{[^}]+\}\}', '', text)
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    # Remove TV Tropes artifacts like [edit]
    text = text.replace('[edit]', '')
    return text.strip()

def apply_dissident93_style(name, jp_name, chunks, entity_type="character"):
    """
    Dissident93 Signature Style:
    1. Sentinel Identification
    2. Narrative Trajectory
    3. Trait-Rich Summary (Synthesis of Wiki bio + Trope perspective)
    """
    
    # 1. Lead Sentence
    # Determine role from text or type
    combined_raw = " ".join([c['text'] for c in chunks])
    clean_combined = clean_text(combined_raw)
    
    if entity_type == "location":
        lead = f"'''{name}''' is a location in the *Trails* series."
    elif entity_type == "faction":
        lead = f"'''{name}''' is an organization in the *Trails* series."
    elif entity_type == "concept":
        lead = f"'''{name}''' is a concept in the *Trails* series."
    else:
        # Character role search
        role_match = re.search(r'is a ([\w\s\-]+?)(?:in|who|based|\.)', clean_combined, re.I)
        role = role_match.group(1).strip() if role_match else "character"
        lead = f"'''{name}''' is a {role} in the *Trails* series."
    
    # 2. Narrative Trajectory (Game coverage scan)
    games = re.findall(r'\b(Trails in the Sky|Trails from Zero|Trails to Azure|Trails of Cold Steel|Trails into Reverie|Trails through Daybreak|Trails Beyond the Horizon)\b', clean_combined)
    trajectory = ""
    if games:
        first, last = games[0], games[-1]
        if first != last:
            trajectory = f" Introduced in *{first}*, their arc spans through to *{last}*."
        else:
            trajectory = f" They appear primarily within the *{first}* arc."

    # 3. Trait Synthesis (Identify tropes vs hard facts)
    wiki_bio = next((c['text'] for c in chunks if c['type'] == 'raw_bio'), "")
    tropes = next((c['text'] for c in chunks if c['type'] == 'character_tropes'), "")
    
    # Take 2-3 strongest sentences from wiki bio
    wiki_sentences = re.split(r'(?<=[.!?]) +', clean_text(wiki_bio))
    selected_wiki = [s for s in wiki_sentences if len(s.split()) > 5][:2]
    
    # Take 1-2 key traits from tropes
    trope_sentences = re.split(r'(?<=[.!?]) +', clean_text(tropes))
    selected_tropes = [s for s in trope_sentences if len(s.split()) > 5][:1]
    
    # Assemble
    body_prose = " ".join(selected_wiki + selected_tropes)
    # Neutralize self-references
    body_prose = re.sub(rf'\b{re.escape(name)}\b', 'the character', body_prose, flags=re.I)
    
    final_prose = f"{lead}{trajectory} {body_prose}".strip()
    
    # Canonical italics mapping
    game_list = ['Trails in the Sky', 'Trails from Zero', 'Trails to Azure', 
                 'Trails of Cold Steel', 'Trails into Reverie', 
                 'Trails through Daybreak', 'Trails Beyond the Horizon', 
                 'The Legend of Nayuta: Boundless Trails']
    for g in game_list:
        final_prose = re.sub(rf'\b{re.escape(g)}\b', f'*{g}*', final_prose)

    return final_prose

def run_dissonance_final_pass():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Executing Curation Pass 5.1 (Multi-Source Synthesis)...")
    
    # Get all entities
    cursor.execute('SELECT entity_id, english_display_name, japanese_name, entity_type FROM entity_registry')
    entities = cursor.fetchall()
    
    curated_count = 0
    for entity in entities:
        eid = entity['entity_id']
        name = entity['english_display_name']
        jp_name = entity['japanese_name']
        etype = entity['entity_type']
        
        # Get all chunks associated with this entity
        cursor.execute('''
            SELECT text_content, chunk_type, spoiler_band 
            FROM chunk_registry 
            WHERE linked_entity_ids LIKE ? OR chunk_id LIKE ?
        ''', (f'%"{eid}"%', f'%:{eid}%'))
        chunks = [{'text': row['text_content'], 'type': row['chunk_type'], 'band': row['spoiler_band']} for row in cursor.fetchall()]
        
        if not chunks:
            continue
            
        curated_text = apply_dissident93_style(name, jp_name, chunks, etype)
        
        # Save curated result
        curated_id = f"curated:{eid}"
        max_band = max([c['band'] for c in chunks])
        
        cursor.execute('''
            INSERT OR REPLACE INTO chunk_registry (
                chunk_id, source_id, text_content, language, chunk_type, spoiler_band, linked_entity_ids
            ) VALUES (?, 'system:dissident93_curator_v5_synth', ?, 'en', 'curated_bio', ?, ?)
        ''', (curated_id, curated_text, max_band, json.dumps([eid])))
        
        # Update entity note for quick preview
        cursor.execute('UPDATE entity_registry SET notes = ? WHERE entity_id = ?', (curated_text, eid))
        
        curated_count += 1
        if curated_count % 100 == 0:
            print(f" -> Curated {curated_count} entries...")

    conn.commit()
    conn.close()
    print(f"\n[SUCCESS] Multi-source curation complete.")
    print(f" -> Generated {curated_count} synthesized summaries.")

if __name__ == "__main__":
    run_dissonance_final_pass()
