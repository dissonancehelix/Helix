import os
import sqlite3
import uuid
from bs4 import BeautifulSoup

# Mapping of file patterns to media_id
MEDIA_MAP = {
    "Advanced Chapter": "drama_advanced",
    "Road to the Future": "drama_future",
    "Trails of Cold Steel II": "ss_snowlight"
}

DB_PATH = "retrieval/index/trails.db"
CORPUS_DIR = "corpus/raw"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def resolve_entity(cur, name):
    """Attempt to resolve a character name to an entity_id."""
    if not name:
        return None
    name = name.strip().rstrip(':').split('(')[0].strip() # Handle "Narration (Lloyd)"
    
    # Try direct match on english_display_name
    cur.execute("SELECT entity_id FROM entity_registry WHERE english_display_name = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    
    # Try alias match
    cur.execute("SELECT entity_id FROM aliases WHERE alias = ?", (name,))
    row = cur.fetchone()
    if row:
        return row[0]
    
    # Try case-insensitive fallback 
    cur.execute("SELECT entity_id FROM entity_registry WHERE english_display_name LIKE ? COLLATE NOCASE", (name,))
    row = cur.fetchone()
    if row:
        return row[0]

    return None

def parse_geofront(soup):
    """Parser for Geofront bootstrap-based scripts."""
    chunks = []
    content_elements = soup.find_all("div", class_=["cont-name", "cont-dialogue", "cont-pause", "cont-se"])
    
    current_speaker = None
    for el in content_elements:
        cls = el.get("class", [])
        if "cont-name" in cls:
            current_speaker = el.get_text(strip=True)
        elif "cont-dialogue" in cls:
            text = el.get_text(strip=True, separator="\n")
            if current_speaker:
                chunks.append({"speaker": current_speaker, "text": text, "type": "dialogue"})
            else:
                chunks.append({"speaker": "UNKNOWN", "text": text, "type": "dialogue"})
        elif "cont-pause" in cls or "cont-se" in cls:
            text = el.get_text(strip=True)
            chunks.append({"speaker": "SYSTEM", "text": text, "type": "stage_direction"})
            current_speaker = None
            
    return chunks

def parse_blogger(soup):
    """Parser for EiyuuTrans (Blogger) format scripts."""
    chunks = []
    post_body = soup.find("div", class_="post-body") or soup
    
    for b_tag in post_body.find_all("b"):
        speaker = b_tag.get_text(strip=True).rstrip(':')
        if not speaker or len(speaker) > 40:
            continue
            
        next_node = b_tag.next_sibling
        text = ""
        while next_node and next_node.name not in ["b", "h3", "h2"]:
            if isinstance(next_node, str):
                text += next_node.strip()
            elif next_node.name == "br":
                text += "\n"
            else:
                text += next_node.get_text(strip=True)
            next_node = next_node.next_sibling
        
        text = text.strip()
        if text:
            chunks.append({"speaker": speaker, "text": text, "type": "dialogue"})
            
    for u_tag in post_body.find_all("u"):
        text = u_tag.get_text(strip=True)
        if text:
            chunks.append({"speaker": "SYSTEM", "text": text, "type": "header"})
            
    return chunks

def parse_official(soup):
    """Parser for Official Site (Cold Steel II) format."""
    chunks = []
    paragraphs = soup.find_all("p")
    for p in paragraphs:
        strong_tag = p.find("strong")
        if strong_tag:
            speaker = strong_tag.get_text(strip=True).rstrip(':')
            full_text = p.get_text(strip=True)
            strong_text = strong_tag.get_text(strip=True)
            text = full_text.replace(strong_text, "").strip()
            if text:
                chunks.append({"speaker": speaker, "text": text, "type": "dialogue"})
        elif "stage-direction" in p.get("class", []):
            text = p.get_text(strip=True)
            chunks.append({"speaker": "SYSTEM", "text": text, "type": "stage_direction"})
    return chunks

def process_file(file_path, media_id, cur):
    print(f"Processing: {os.path.basename(file_path)} -> {media_id}")
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    soup = BeautifulSoup(content, "html.parser")
    
    # Improved Detection Logic
    if soup.find("div", class_="cont-name") or soup.find("div", class_="cont-dialogue"):
        # Geofront
        raw_chunks = parse_geofront(soup)
    elif "eiyuutrans.blogspot" in content or soup.find("div", class_="post-body"):
        # Blogger (EiyuuTrans)
        raw_chunks = parse_blogger(soup)
    elif soup.find("strong") and media_id == "ss_snowlight":
        # Official Site (Cold Steel II)
        raw_chunks = parse_official(soup)
    else:
        # Fallback to blogger if <b> is found
        if soup.find("b"):
            raw_chunks = parse_blogger(soup)
        else:
            print(f"Skipping {file_path}: Unknown format.")
            return

    print(f"  Extracted {len(raw_chunks)} chunks.")

    # Ingest chunks
    for rc in raw_chunks:
        chunk_id = str(uuid.uuid4())
        source_id = os.path.basename(file_path)
        speaker = rc["speaker"]
        text = rc["text"]
        chunk_type = rc["type"]
        
        linked_entity = resolve_entity(cur, speaker) if speaker != "SYSTEM" else None
        
        cur.execute("""
            INSERT INTO chunk_registry 
            (chunk_id, source_id, media_id, linked_entity_ids, text_content, language, spoiler_band, chunk_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (chunk_id, source_id, media_id, linked_entity, text, "en", 1, chunk_type))
        
        if linked_entity:
            cur.execute("""
                INSERT OR IGNORE INTO appearance_registry 
                (entity_id, media_id, appearance_type, debut_flag, canonical_weight, spoiler_band)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (linked_entity, media_id, 'dialogue', 0, 10, 1))

def run_ingestion():
    conn = get_db_connection()
    cur = conn.cursor()
    
    for m_id in MEDIA_MAP.values():
        cur.execute("DELETE FROM chunk_registry WHERE media_id = ?", (m_id,))
    
    files = os.listdir(CORPUS_DIR)
    for f in files:
        if not f.endswith(".html"):
            continue
            
        file_path = os.path.join(CORPUS_DIR, f)
        media_id = None
        
        for pattern, m_id in MEDIA_MAP.items():
            if pattern in f:
                media_id = m_id
                break
        
        if media_id:
            process_file(file_path, media_id, cur)
            
    conn.commit()
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    run_ingestion()
