import sqlite3
from pathlib import Path

DB_PATH = Path('retrieval/index/trails.db')

bios = [
  {
    "name": "Van Arkride",
    "phrase": "This is how my work is. Good thing you're still in school, 'cause you got a lot to learn.",
    "biography": "A young man with dark-colored hair and deep blue eyes. He works out of a small office in the Old Town district of Calvard's capital city, Edith. Known as a spriggan, he takes on jobs that can't be brought to the police or the bracers. He'll sometimes come across as being dry, and even a bit cynical, but he's level-headed and surprisingly attentive to others. Because of his job, he has a wide network of contacts across a number of different industries. Despite all these friendly acquaintances, it sometimes seems as though he's reluctant to let anyone see the deepest parts of his heart. He may have stumbled into his line of work almost by accident, but he seems satisfied with his way of life. Even when he gets crummy jobs, he might complain, but he completes them without fail."
  },
  {
    "name": "Agnès Claudel",
    "phrase": "I understand you have your way of doing things, but I have my own pride to satisfy, you know. You'll just have to compromise, Van.",
    "biography": "A first-year student at the renowned Aramis Academy, one of the most prestigious schools in Edith. She has long, lustrous blonde hair, and a graceful, gentle demeanor, but behind her eyes lies a strong determination. At school, she enrolled in an orbal staff self-defense course. She also serves as a member of the Student Council alongside her friends. After discovering that someone has stolen an orbment that belonged to her late great-grandfather, she decides not to go to the police or the Bracer Guild for help. Instead, she travels to Old Town, where a business called Arkride Solutions Office is said to accept any kind of request..."
  },
  {
    "name": "Feri Al-Fayed",
    "phrase": "I'll keep you safe. Now may Arusha watch over us!",
    "biography": "A young jaeger belonging to the elite jaeger corps, the Warriors of Kruga. She has received intense combat training ever since she was little. Though she is relentless in battle, living on the edge of society all her life as a jaeger has left her unfamiliar with many aspects of the city. Outside of combat situations, she tends to react with innocent, naive curiosity to the sights and sounds of Edith. Upon receiving word that another jaeger corps she had known for a long time had suddenly gone missing, Feri begins searching. She also tries to make contact with a certain problem-solver in Edith who she had heard will take on any job."
  },
  {
    "name": "Aaron Wei",
    "phrase": "Stay outta this, old fart. We've got our own way of handling things around here.",
    "biography": "A rowdy playboy who leads a local gang in Langport's Eastern Quarter. He practices the Gekka school of swordsmanship and is known across the city by colorful titles like \"the prodigy of Langport\" and \"the Little Conqueror of Luozhou.\" He spends his time acting in female roles at the local theater, where he performs sword dances, and hitting up the casino. Though he's got a bit of an edge to his personality, he has an undeniable charisma that draws people to him. The crime syndicate, Heiyue, which controls the Eastern Quarter has been trying to recruit him as one of their executives, but Aaron seems to have little interest in the organization."
  },
  {
    "name": "Risette Twinings",
    "phrase": "Supporting our clients is my primary duty. And one I take great pride in.",
    "biography": "A woman dressed as a maid who works as a service concierge for Marduk Total Security Company. Befitting her choice of clothes, she is very even-tempered, good-natured, and polite, though every now and then, her sense of humor will betray a more mischievous side to her. Despite her elegant appearance, she possesses superhuman speed and power, and her combat ability is so great that she surpasses even top-class jaegers. She's established a business relationship with Van and supplies him with special weapons and apps for his orbment from Marduk in exchange for his help testing said products."
  },
  {
    "name": "Quatre Salision",
    "phrase": "Come on, FIO, XEROS. While the professor's away, we'll protect her home.",
    "biography": "A researcher who is enrolled in the Basel Institute of Science's master's program, despite only being fifteen years old. His neatly-trimmed silver hair and androgynous features give him a distinct look, but he has an aloof air to him that makes him a bit unapproachable. He specializes in the research, development, and operation of orbal drones, which are based on the AI installed in the new Xipha orbments. However, he will also often help the physics and bioengineering labs as a research assistant. He has a particular passion for the observatory that serves as the Institute's symbol. As a child, he was taken in by Professor Latoya Hamilton, the mother of the Republic's Orbal Revolution. Ever since then, he's looked up to her and aspired to follow in her footsteps."
  },
  {
    "name": "Judith Lanster",
    "phrase": "Even I can't handle a job like this alone, so I'm going to give you the honor of helping me! You better not have any problems with that!",
    "biography": "One of the top actresses in the entire orbal film industry, her skilled acting and flowing hair captivate fans across the country. She has a friendly, casual personality, but when it comes to acting, she's highly professional, never compromising in her work. She also has a very strong sense of justice and won't hesitate to confront those who prey on the weak, no matter who they are. Though she's publicly known as an actress, she also seems to have another, behind-the-scenes job that she pursues between acting gigs. She tries to keep this second job as under wraps as possible, but she can be surprisingly terrible about keeping the secret at times."
  },
  {
    "name": "Bergard Zeman",
    "phrase": "Hahaha! It is far too late to be caring about such things, my young friend. ...I genuinely believe that the more people you know and interact with, the better.",
    "biography": "A muscular old man who is a master of the Kunlun style, one of the East's three great martial arts schools. He has a number of disciples scattered across the continent. He used to travel around Zemuria for his job, but he has since left his old organization and abandoned his former name. Now, he leisurely travels around the country, living a comfortable retirement. Years ago, he took Van on as one of his apprentices and taught him proper martial arts. He didn't seem to have any objections to Van starting work as a spriggan. When the war between the Erebonia and Calvard began, Van received news that Bergard had lost his life in an incident, but that seems to have not been the case..."
  }
]

def ingest():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Use Source ID from Registry
    source_id = "official:nisa_daybreak_bios"

    for b in bios:
        name = b["name"]
        slug = name.lower().replace(" ", "_")
        chunk_id = f"chk_nisa_day_{slug}"
        text = f"Official Bio - {name}\nQuote: {b['phrase']}\n\n{b['biography']}"
        
        cursor.execute('''
            INSERT OR REPLACE INTO chunks (chunk_id, source_id, text_content, language, game, trust_tier, spoiler_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (chunk_id, source_id, text, 'en', 'Trails through Daybreak', 0, 10)) # Daybreak is safe

    conn.commit()
    conn.close()
    print(f"Successfully ingested {len(bios)} Official Daybreak Bios into the Registry Registry.")

if __name__ == "__main__":
    ingest()
