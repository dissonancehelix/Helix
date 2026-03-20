# HELIX MUSIC LIBRARY - INGESTION WORKFLOW

## 1. Overview
The Helix Music Library is seeded from a Foobar2000 SQLite database and a `playcount.json` exports to ensure 100% accurate metadata and play statistics.

## 2. Purity Constraints
Only files located within `C:\Users\dissonance\Music\` are ingested. All temporary crossfeed tests, download fragments, and external Foobar components are automatically white-listed out for substrate purity.

## 3. Delimitation Strategy
The ingestion engine uses a surgical splitting policy for multi-artist tracks:
- **Separators**: `/`, `;`, `,`
- **Preserved**: `and`, `&` (Bands like *The Bird and the Bee* remain unified).

## 4. Title Normalization
Album/Game titles undergo a multi-step "Hierarchical Rescue" to resolve generic volume markers:
1.  **Tag Discovery**: Extract `%album%` tag.
2.  **Junk Filter**: If the name is generic (e.g., `2`, `Disc 1`, `S/`), the system elevates up the directory tree.
3.  **Deep-Hop Rescue**: Up to 5 levels of elevation to find the real game directory (e.g., *64 Ozumo 2*).
4.  **Strip Logic**: Leading years and volume markers are cleaned, while preserving embedded numbers in game titles.

## 5. Maintenance Commands
To perform a complete wipe and reload of the music substrate:
```powershell
# 1. Clear existing substrate (Preserve manifest and sources)
cd c:\Users\dissonance\Desktop\Helix\core\library\music\
dir | Where-Object { $_.Name -ne "source" -and $_.Name -ne "music.zip" } | Remove-Item -Recurse -Force

# 2. Run the Purity Ingestor
python c:\Users\dissonance\Desktop\Helix\core\bin\maintenance\ingest_foobar_library.py
```

## 6. Phase 2 (Future)
The next phase for this library is **Axiomatic Signal Analysis**:
- Computing CCS capability vectors for each artist.
- Analyzing chip usage patterns (if available).
- Linking Library metadata to Atlas research artifacts.
