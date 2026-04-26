from bs4 import BeautifulSoup
from pathlib import Path
import json

HTML_PATH = Path('corpus/raw/Steam Community ： Guide ： The Legend of Heroes： Trails Supplemental Material Guide.html')

def analyze_steam_guide():
    if not HTML_PATH.exists():
        print(f"File not found: {HTML_PATH}")
        return

    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    results = {
        "sections": [],
        "links": []
    }

    # Extract Sections (usually h1, h2, or guide section headers)
    # Steam guides use <div class="subSectionTitle">
    for section in soup.find_all('div', class_='subSectionTitle'):
        results["sections"].append(section.get_text().strip())

    # Extract all links and their parent text
    for link in soup.find_all('a'):
        href = link.get('href', '')
        if href and not href.startswith('javascript:'):
            parent_text = link.parent.get_text().strip()[:200] # Context
            results["links"].append({
                "text": link.get_text().strip(),
                "url": href,
                "context": parent_text
            })

    output_path = Path('scratch/steam_guide_analysis.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Analysis complete. Found {len(results['sections'])} sections and {len(results['links'])} links.")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    analyze_steam_guide()
