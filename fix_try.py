import re

with open('comprehensive_test.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace standalone test_X() calls with try/except wrapped versions
# Match lines that are just "test_xxx()" with optional leading spaces
def replace_call(match):
    indent = match.group(1)
    func_name = match.group(2)
    return (f'{indent}try:\n'
            f'{indent}    {func_name}()\n'
            f'{indent}except Exception as _e:\n'
            f'{indent}    _log(f"[FAIL] {func_name} crashed: {{_e}}")\n'
            f'{indent}    import traceback as _tb\n'
            f'{indent}    _tb.print_exc(file=_output_file)\n'
            f'{indent}    _output_file.flush()')

# Match: optional whitespace + test_word() at end of line
pattern = r'^(\s*)(test_\w+)\(\)\s*$'
content = re.sub(pattern, replace_call, content, flags=re.MULTILINE)

with open('comprehensive_test.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
