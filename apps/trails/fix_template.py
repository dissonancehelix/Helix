import re

file_path = r'C:\Users\dissonance\Desktop\Infobox gridiron football biography.txt'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Blocks to replace
new_header1 = r'''| header1 = {{#if:{{{position|}}}{{{title|}}}{{{Position|}}}{{{position1|}}}{{{currentposition|}}}{{{career_position|}}}{{{career_number|}}}{{{number|}}}{{{uniform_number|}}}{{{currentnumber|}}}
| {{Separated entries|separator={{space}}–{{space}}
    | {{#if:{{{current_team|}}}{{{currentteam|}}}{{{team|}}}{{{school|}}}
        | {{#if:{{#switch:{{if empty|{{{number|}}}|{{{uniform_number|}}}|{{{currentnumber|}}}}}|--|-|–|=|#default=1}}
            | No. {{if empty|{{{number|}}}|{{{uniform_number|}}}|{{{currentnumber|}}}}}
            | {{#if:{{#switch:{{lc:{{if empty|{{{current_team|}}}|{{{currentteam|}}}|{{{team|}}}|{{{school|}}}}}}}|free agent|fa|=|#default=1}} | | Profile}}
          }}
        | {{#if:{{{career_number|}}}|No. {{{career_number}}}}}
      }}
    | {{#switch:{{lc:{{if empty|{{{current_team|}}}|{{{currentteam|}}}|{{{team|}}}|{{{school|}}}}}}}
        | free agent|fa=
        | #default = {{#if:{{{current_team|}}}{{{currentteam|}}}{{{team|}}}{{{school|}}}
            | <span class="org">{{if empty|{{{current_team|}}}|{{{currentteam|}}}|{{{team|}}}|{{{school|}}}}}</span>
          }}
      }}
  }}
}}'''

new_label2 = r'''| label2 = {{#if:{{{current_team|}}}{{{currentteam|}}}{{{team|}}}{{{school|}}}
  | {{#if:{{{title|}}}|Title|{{#if:{{{position|}}}{{{Position|}}}{{{position1|}}}{{{currentposition|}}}|Position{{pluralize from text|{{if empty|{{{position|}}}|{{{Position|}}}|{{{position1|}}}|{{{currentposition|}}}}}|plural=s}}{{#if:{{{position_2|}}}{{{position2|}}}{{{position_3|}}}{{{position3|}}}|s}}}}}}
  | {{#if:{{{career_number|}}}
      | {{#if:{{{career_position|}}}{{{position|}}}{{{Position|}}}{{{position1|}}}{{{currentposition|}}}|Position{{pluralize from text|{{if empty|{{{career_position|}}}|{{{position|}}}|{{{Position|}}}|{{{position1|}}}|{{{currentposition|}}}}}|plural=s}}{{#if:{{{career_position_2|}}}{{{career_position2|}}}{{{position_2|}}}{{{position2|}}}{{{career_position_3|}}}{{{career_position3|}}}{{{position_3|}}}{{{position3|}}}|s}}}}
      | {{#if:{{{title|}}}|Title|{{#if:{{{position|}}}{{{Position|}}}{{{position1|}}}{{{currentposition|}}}|Position{{pluralize from text|{{if empty|{{{position|}}}|{{{Position|}}}|{{{position1|}}}|{{{currentposition|}}}}}|plural=s}}{{#if:{{{position_2|}}}{{{position2|}}}{{{position_3|}}}{{{position3|}}}|s}}}}}}
    }}
}}'''

new_data2 = r'''| data2 = {{#if:{{{current_team|}}}{{{currentteam|}}}{{{team|}}}{{{school|}}}
  | {{#if:{{{title|}}}|{{{title|}}}|{{#if:{{{position|}}}{{{Position|}}}{{{position1|}}}{{{currentposition|}}}|{{Infobox gridiron football biography/position|{{if empty|{{{position|}}}|{{{Position|}}}|{{{position1|}}}|{{{currentposition|}}}}}}}}}{{#if:{{{position_2|}}}{{{position2|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{position_2|}}}|{{{position2|}}}}} }}}}}}{{#if:{{{position_3|}}}{{{position_3|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{position_3|}}}|{{{position3|}}}}} }}}}}}}}
  | {{#if:{{{career_number|}}}
      | {{#if:{{{career_position|}}}{{{position|}}}{{{Position|}}}{{{position1|}}}{{{currentposition|}}}
          | {{Infobox gridiron football biography/position|{{if empty|{{{career_position|}}}|{{{position|}}}|{{{Position|}}}|{{{position1|}}}|{{{currentposition|}}}}}}}{{#if:{{{career_position_2|}}}{{{career_position2|}}}{{{position_2|}}}{{{position2|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{career_position_2|}}}|{{{career_position2|}}}|{{{position_2|}}}|{{{position2|}}}}} }}}}}}{{#if:{{{career_position_3|}}}{{{career_position3|}}}{{{position_3|}}}{{{position3|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{career_position_3|}}}|{{{career_position3|}}}|{{{position_3|}}}|{{{position3|}}}}} }}}}}}
        }}
      | {{#if:{{{title|}}}|{{{title|}}}|{{#if:{{{position|}}}{{{Position|}}}{{{position1|}}}{{{currentposition|}}}|{{Infobox gridiron football biography/position|{{if empty|{{{position|}}}|{{{Position|}}}|{{{position1|}}}|{{{currentposition|}}}}}}}}}{{#if:{{{position_2|}}}{{{position2|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{position_2|}}}|{{{position2|}}}}} }}}}}}{{#if:{{{position_3|}}}{{{position_3|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{position_3|}}}|{{{position3|}}}}} }}}}}}}}
    }}
}}'''

new_label12 = r'''| label12 = {{#if:{{{current_team|}}}{{{currentteam|}}}{{{team|}}}{{{school|}}}
  | {{#if:{{{career_position|}}}{{{career_position1|}}}|Position{{pluralize from text|{{if empty|{{{career_position|}}}|{{{career_position1|}}}}}|plural=s}}{{#if:{{{career_position_2|}}}{{{career_position2|}}}{{{career_position_3|}}}{{{career_position3|}}}|s}}|{{#if:{{Both|{{{title|}}}|{{if empty|{{{position|}}}|{{{Position|}}}|{{{position1|}}}|{{{currentposition|}}}}}}}|Position{{pluralize from text|{{if empty|{{{position|}}}|{{{Position|}}}|{{{position1|}}}|{{{currentposition|}}}}}|plural=s}}{{#if:{{{position_2|}}}{{{position2|}}}{{{position_3|}}}{{{position3|}}}|s}}}}}}
  | {{#if:{{{career_number|}}} | | {{#if:{{{career_position|}}}{{{career_position1|}}}|Position{{pluralize from text|{{if empty|{{{career_position|}}}|{{{career_position1|}}}}}|plural=s}}{{#if:{{{career_position_2|}}}{{{career_position2|}}}{{{career_position_3|}}}{{{career_position3|}}}|s}}}} }}
}}'''

new_data12 = r'''| data12  = {{#if:{{{current_team|}}}{{{currentteam|}}}{{{team|}}}{{{school|}}}
  | {{#if:{{{career_position|}}}{{{career_position1|}}}|{{Infobox gridiron football biography/position|{{if empty|{{{career_position|}}}|{{{career_position1|}}}}}}}{{#if:{{{career_position_2|}}}{{{career_position2|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{career_position_2|}}}|{{{career_position2|}}}}} }}}}}}{{#if:{{{career_position_3|}}}{{{career_position3|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{career_position_3|}}}|{{{career_position3|}}}}} }}}}}}{{#if:{{{career_number|}}}|{{space}}(No. {{{career_number}}})}}|{{#if:{{Both|{{{title|}}}|{{if empty|{{{position|}}}|{{{Position|}}}|{{{position1|}}}|{{{currentposition|}}}}}}}|{{Infobox gridiron football biography/position|{{if empty|{{{position|}}}|{{{Position|}}}|{{{position1|}}}|{{{currentposition|}}}}}}}{{#if:{{{position_2|}}}{{{position2|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{position_2|}}}|{{{position2|}}}}} }}}}}}{{#if:{{{position_3|}}}{{{position_3|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{position_3|}}}|{{{position3|}}}}} }}}}}}{{#if:{{{career_number|}}}|{{space}}(No. {{{career_number}}})}}}}}}
  | {{#if:{{{career_number|}}} | | {{#if:{{{career_position|}}}{{{career_position1|}}}|{{Infobox gridiron football biography/position|{{if empty|{{{career_position|}}}|{{{career_position1|}}}}}}}{{#if:{{{career_position_2|}}}{{{career_position2|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{career_position_2|}}}|{{{career_position2|}}}}} }}}}}}{{#if:{{{career_position_3|}}}{{{career_position3|}}}|, {{Nocaps|{{Infobox gridiron football biography/position|{{if empty|{{{career_position_3|}}}|{{{career_position3|}}}}} }}}}}}{{#if:{{{career_number|}}}|{{space}}(No. {{{career_number}}})}} }}
}}'''

def replace_block(text, start_label, next_label, new_content):
    idx = text.find(start_label)
    if idx == -1: return text
    next_idx = text.find(next_label, idx + len(start_label))
    if next_idx == -1:
        next_idx = text.find('\n}}', idx)
    
    if next_idx != -1:
        return text[:idx] + new_content + "\n" + text[next_idx:]
    return text

content = replace_block(content, '| header1 =', '| label2 =', new_header1)
content = replace_block(content, '| label2 =', '| data2 =', new_label2)
content = replace_block(content, '| data2 =', '| label3', new_data2)
content = replace_block(content, '| label12 =', '| data12', new_label12)
if '| data12  =' in content:
    content = replace_block(content, '| data12  =', '| label13', new_data12)
else:
    content = replace_block(content, '| data12 =', '| label13', new_data12)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Template fixed.")
