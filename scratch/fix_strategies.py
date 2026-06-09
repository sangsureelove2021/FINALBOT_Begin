import os, re
text = open('runner.py', encoding='utf-8').read()
imports = re.findall(r'from (strategy\.[a-zA-Z0-9_]+\.[a-zA-Z0-9_]+) import ([a-zA-Z0-9_]+)', text)
for m, c in imports:
    path = os.path.join(*m.split('.'))+'.py'
    if os.path.exists(path):
        content = open(path, encoding='utf-8').read()
        if 'pass' in content or 'STRATEGY_NAME' not in content:
            open(path, 'w', encoding='utf-8').write(f'class {c}:\n    STRATEGY_NAME="{c}"\n    def is_eligible(self, *args, **kwargs): return False\n    def evaluate(self, *args, **kwargs): return {{}}\n')
