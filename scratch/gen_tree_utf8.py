import os
import sys
from pathlib import Path

def generate_tree(startpath, exclude_dirs={'node_modules', '__pycache__', '.git', '.venv', '.idea', '.vscode', 'logs'}, exclude_exts={'.pyc', '.pyd', '.exe', '.dll', '.so', '.dylib'}):
    lines = []
    startpath = Path(startpath).resolve()
    lines.append(str(startpath.name) + '/')
    
    def should_exclude_dir(p):
        name = p.name
        return name in exclude_dirs or name.startswith('.')
    
    def should_exclude_file(p):
        return p.suffix in exclude_exts or p.name.endswith('.pyc')
    
    def walk_dir(path, prefix=''):
        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return
        
        entries_filtered = []
        for e in entries:
            if e.is_dir():
                if not should_exclude_dir(e):
                    entries_filtered.append(e)
            else:
                if not should_exclude_file(e):
                    entries_filtered.append(e)
        
        for i, entry in enumerate(entries_filtered):
            is_last = (i == len(entries_filtered) - 1)
            connector = ' ' if is_last else ' '
            lines.append(prefix + connector + entry.name + ('/' if entry.is_dir() else ''))
            if entry.is_dir():
                extension = '    ' if is_last else '   '
                walk_dir(entry, prefix + extension)
    
    walk_dir(startpath)
    return '\n'.join(lines)

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    out_file = sys.argv[2] if len(sys.argv) > 2 else 'tree.txt'
    tree = generate_tree(root)
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(tree)
    print(f"Tree written to {out_file}")
