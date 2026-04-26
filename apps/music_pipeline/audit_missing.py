from pathlib import Path
import re

vgm = Path('C:/Users/dissonance/Music/VGM')
missing = []
for cat in sorted(vgm.iterdir()):
    if not cat.is_dir(): continue
    for folder in sorted(cat.iterdir()):
        if not folder.is_dir(): continue
        if not (folder / 'cover.jpg').exists():
            missing.append((cat.name, folder.name))

print(f'Total missing: {len(missing)}')

has_and     = [(c,n) for c,n in missing if ' and ' in n.lower() or ' & ' in n]
sequel_nums = [(c,n) for c,n in missing if re.search(r'\b[2-9]\b', n) and not re.search(r'[2-9][0-9]', n)]
has_roman   = [(c,n) for c,n in missing if re.search(r'\b(II|III|IV|VI|VII|VIII|IX|XI|XII)\b', n)]
has_colon   = [(c,n) for c,n in missing if ':' in n or ' - ' in n]
has_paren   = [(c,n) for c,n in missing if '(' in n]
jp_particle = [(c,n) for c,n in missing if re.search(r'\b(no|ga|wo|ni|de|to)\b', n)]

print(f'\n=== "and" / dual versions ({len(has_and)}) ===')
for c,n in has_and: print(f'  [{c}] {n}')

print(f'\n=== Trailing sequel number (may need roman) ({len(sequel_nums)}) ===')
for c,n in sequel_nums: print(f'  [{c}] {n}')

print(f'\n=== Already has Roman numeral ({len(has_roman)}) ===')
for c,n in has_roman: print(f'  [{c}] {n}')

print(f'\n=== Has subtitle ({len(has_colon)}) ===')
for c,n in has_colon[:30]: print(f'  [{c}] {n}')

print(f'\n=== Has parens ({len(has_paren)}) ===')
for c,n in has_paren[:20]: print(f'  [{c}] {n}')

print(f'\n=== Japanese particles (no/ga/to) ({len(jp_particle)}) ===')
for c,n in jp_particle[:20]: print(f'  [{c}] {n}')
