import sqlite3
from pathlib import Path

DB_PATH = Path('retrieval/index/trails.db')

sky_bios = [
  {
    "name": "Estelle Bright",
    "biography": "A bright and determined bracer trainee of the Guild. A girl from Liberl Kingdom training to become a bracer in order to protect the safety of civilians and peace of cities. A bright, outgoing, and optimistic girl who never gives up, no matter the situation. Her sincere nature leads her to trust others easily, and her actions are often impulsive."
  },
  {
    "name": "Joshua Bright",
    "biography": "A boy taken in by the Bright family 5 years ago. With jet-black hair and amber eyes, he always appears cool and composed. His hobbies include reading and playing the harmonica. Highly intelligent and level-headed, he often finds himself supporting the impulsive Estelle, keeping her in check."
  },
  {
    "name": "Scherazard Harvey",
    "biography": "A Senior bracer known by the name of \"Silver Streak\". Possesses a powerful and well-trained physique with an alluring beauty. A former apprentice of Estelle's father, Cassius, and serves as a big sister figure to Estelle and the others. Has a caring and protective personality, but is also known for her love of alcohol and she tends to get a bit too clingy when drunk."
  },
  {
    "name": "Olivier Lenheim",
    "biography": "A mysterious traveling musician from the great northern nation, the Erebonian Empire. Musically gifted, he can play everything from the piano to the lute, but tends to be extremely self-absorbed. Often confuses those around him with his unpredictable words and actions, but that same unpredictability also comes in handy at times."
  },
  {
    "name": "Agate Crosner",
    "biography": "A young bracer with the strength to wield a massive sword, earning him the nickname 'Heavy Blade'. Blunt and ill-mannered, he tends to treat the inexperienced Estelle and Joshua harshly. However, his skill as a bracer is undeniable, and is deeply trusted by those around him."
  },
  {
    "name": "Kloe Rinz",
    "biography": "A student at the prestigious Jenis Royal Academy in the Ruan region. On her days off, she helps out at a nearby orphanage, where her kind and gentle nature has earned her the trust of the children and the headmistress. She is always accompanied by her falcon friend, Sieg, and they share a bond that goes beyond simple friendship."
  },
  {
    "name": "Tita Russell",
    "biography": "The granddaughter of the orbment scientist, Professor Russell. Warm and cheerful, she has an earnest, pure-hearted nature that makes her beloved by all. Born into a family of engineers, she has a deep love for machines. Her only flaw is that she loses sight of her surroundings while tinkering with them."
  },
  {
    "name": "Zin Vathek",
    "biography": "A veteran bracer from the Calvard Republic who has mastered the Taito Style, one of the three great eastern martial arts styles. Despite his massive, bear-like build, he has a warm and easygoing personality. He is a reliable, big brother figure."
  },
  {
    "name": "Cassius Bright",
    "biography": "Estelle's father. A dashing middle-aged man with a strong build and a striking mustache. As a veteran bracer, he has been active not only in Liberl but across the entire continent. In addition to Estelle and Joshua, he is also the mentor of Scherazard. His bold decision to adopt Joshua, along with his amiable and mischievous personality, earned him the nickname of 'deadbeat dad' by his daughter Estelle."
  }
]

def ingest():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    source_id = "official:sky_remake_1st"

    for b in sky_bios:
        name = b["name"]
        slug = name.lower().replace(" ", "_")
        chunk_id = f"chk_sky_remake_{slug}"
        text = f"Official Remake Bio - {name}\n\n{b['biography']}"
        
        cursor.execute('''
            INSERT OR REPLACE INTO chunks (chunk_id, source_id, text_content, language, game, trust_tier, spoiler_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (chunk_id, source_id, text, 'en', 'Trails in the Sky the 1st', 0, 0)) # Safe

        # Map to Backbone
        cursor.execute('''
            UPDATE entities SET trust_tier = 0, creation_status = 'curated'
            WHERE display_name = ?
        ''', (name,))

    conn.commit()
    conn.close()
    print(f"Successfully ingested {len(sky_bios)} Official Sky Remake Bios.")

if __name__ == "__main__":
    ingest()
