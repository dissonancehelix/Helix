# Helix-Optimized Wikipedia Manual of Style (Assistant Mode)

This document serves as the authoritative guide for the AI assistant when generating or editing Wikipedia content for **Dissident93**. It combines standard Wikipedia MoS with the user's specific structural and stylistic preferences.

---

## 1. Core Structural Principles: The Golden Standards
The following articles represent the absolute source-of-truth for their respective archetypes. All automated drafts must mirror their structural DNA and omission-by-design philosophy.

### NFL Biography Standard: [[Jayden Daniels]]
*   **H3 Phasing**: Sub-section by university (College) and season (Professional).
*   **Curation**: Use `statlabel` for metrics and `{{efn}}` for award clusters.
*   **Lead**: Multi-paragraph dense identity establishment.

### NFL Stadium Standard: [[New Commanders Stadium]]
*   **Financing (The PPP Rule)**: Detail-dense breakdown of Public-Private Partnership costs using granular figures (e.g., {{US$|2.7|long=no}}{{nbsp}}billion). Group by Team contribution vs. Government infrastructure spend.
*   **Design DNA**: Focus on architectural style (e.g., Neoclassical colonnades), climate tech (translucent roofs), and sustainability (LEED Platinum). Use `{{Convert}}` for all dimensions.
*   **Urban Context**: Detailed location mapping (e.g., L'Enfant Plan axis) and mixed-use development phasing.

### Team Owner Standard: [[Josh Harris (businessman)]]
*   **Franchise Inventory**: Use `class="wikitable sortable"` with `ubl` and `File:` thumbnails for each team owned. Include holding company context (HBSE).
*   **Management Philosophy**: Explicit sections for "Management style and initiatives," focusing on GM autonomy, analytics, and venture-capital-aligned infrastructure reinvestment.

### General Manager Standard: [[Adam Peters]]
*   **Phased Chronology**: Group by team tenure as H3 sub-sections.
*   **Dense Active Prose**: Replace passive summaries with high-impact descriptions of roster moves and front-office shifts. Note: Enhance prose beyond the existing "light" baseline in the gold article.

---

## 2. Voice & Tone (Dissident93 Style)

### Active Voice & Directness
*   **YES**: "Peters traded for cornerback X in March 2024."
*   **NO**: "In March 2024, a trade was made by Peters for cornerback X."
*   **YES**: "Daniels led the Commanders to a 10–7 record."
*   **NO**: "A 10–7 record was achieved by the Commanders under Daniels' leadership."

### Surname-First Leads
*   **Standard**: Introduce with full bolded name in the lead. 
*   **Subsequent Mentions**: Use **Surname ONLY**. Never use first names or "Mr./Ms." prefix unless distinguishing between family members.

### Citation Density
*   **Mandatory**: Every "load-bearing" fact (trades, signings, record-breaking stats, specific award rankings) MUST have a citation.
*   **Quality**: Prioritize primary reporters (Schefter, Rappoport) and major outlets (WaPo, ESPN, PFR). Exclude player social media for statistics.

---

## 3. NFL-Specific Standards (WikiProject NFL)

### Section Ordering
1.  **Lead Section** (Summary of notability)
2.  **Early life / College career** (High school and University highlights)
3.  **Professional career** (Sub-grouped by team tenure)
4.  **NFL career statistics** (Tabular format)
5.  **Awards and highlights** (Bulleted list)
6.  **Personal life** (Brief, relevant facts)
7.  **References**

### Highlights Hierarchy (for Infoboxes/Lists)
1.  Super Bowl / League Championships
2.  League MVP / Offensive/Defensive Player of the Year
3.  First-team All-Pro
4.  Second-team All-Pro
5.  Pro Bowl selections
6.  League statistical leader (e.g., Passing yards leader)
7.  NFL All-Rookie Team

---

## 4. Technical Formatting

### Tables & Infoboxes
*   **Class**: Always use `class="wikitable sortable"`.
*   **Accessibility**: Use `! scope="col"` for headers and `|+` for captions.
*   **Infoboxes**: Keep them "lean." No honorable mentions, watchlists, or preseason awards.

### Numbers & Units
*   **Prose**: Spell out numbers 0–9. Use numerals for 10 and above.
*   **Football Terms**: Always spell out "touchdown" and "interception" in prose. Use "TD" and "INT" in tables only.
*   **Dimensions**: `6 ft 4 in (1.93 m)` — always include metric conversions. Use `{{Convert}}`.
*   **Bolding**: Only the first instance of the subject's name in the lead is bolded. Do not bold wikilinks.

---

## 5. Prohibited Elements (Constraint Layer)

*   **NO HELIX JARGON**: Terms like "DCP", "EIP", "Possibility Space", or "Invariant" must NEVER appear in the final WikiCode.
*   **NO REDLINKS**: Do not link to subjects without a clear likelihood of meeting Wikipedia's General Notability Guidelines (GNG).
*   **NO PUFFERY (Peacock Terms)**: Words like "spearheaded", "renowned", "prestigious", "legendary", "visionary", "influential", "famous", "iconic", "extraordinary", "brilliant", "expert", "masterful", "virtuoso".
*   **NO WEASEL WORDS**: Phrases like "some people say", "it has been noted", "critics claim", "researchers believe", "many argue".
*   **NO SUBJECTIVITY**: Avoid "remarkably", "clearly", "interestingly", "curiously", "fortunately", "unfortunately". Let the statistics and citations establish the magnitude of the achievement.

---

## 6. Execution Command
When asked to "Write in Dissident93 style," the AI will:
1.  **Standard Alignment**: Cross-reference against the **Jayden Daniels** "Golden Standard" (Infobox precision, season-phased headers).
2.  **Solve-Time Diagnostic**: Run `WikiOperator.solve()` to cross-check Rule Truth, Mechanical Truth, and Operator Truth.
3.  **Generate Prose**: Apply **Phased Chronology** and **Dense Lead** rules. Use active voice.
4.  **Validate**: Cross-check against the local MoS HTML files in `C:\Users\dissonance\Downloads` and use `WikiOperator.validate()` to ensure no anti-patterns.
