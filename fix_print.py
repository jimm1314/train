import re

with open('comprehensive_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Replace lines that start with print( (with optional leading spaces)
    # But NOT inside function bodies or string literals
    stripped = line.lstrip()
    if stripped.startswith('print('):
        indent = line[:len(line) - len(stripped)]
        new_line = indent + '_log(' + stripped[6:]
        new_lines.append(new_line)
    elif stripped.startswith('traceback.print_exc()'):
        new_lines.append(line)  # Keep traceback.print_exc() as is
    else:
        new_lines.append(line)

with open('comprehensive_test.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Replacement done')
