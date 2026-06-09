import os
from pathlib import Path

workspaces = [
    r"C:\Users\Administrator\Downloads\BOT_FINALBOT\BOT_FINALBOT",
    r"C:\Users\Administrator\Downloads\ProjectsAI_FinalBOT_File"
]

md_files = []
for ws in workspaces:
    p = Path(ws)
    if not p.exists():
        continue
    for root, dirs, files in os.walk(p):
        for file in files:
            if file.endswith(".md"):
                md_files.append(Path(root) / file)

print(f"Found {len(md_files)} markdown files:")
for f in md_files:
    print(f" - {f} ({f.stat().st_size} bytes)")
