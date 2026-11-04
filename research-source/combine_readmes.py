import json
from pathlib import Path

COMP_DIR = Path("c:/Users/aman/Documents/meta/competitor_readmes")
INDEX_FILE = COMP_DIR / "INDEX.json"
OUT_FILE = COMP_DIR / "ALL_COMPETITOR_READMES.md"

if not INDEX_FILE.exists():
    print("Error: INDEX.json not found")
    exit(1)

with open(INDEX_FILE, "r", encoding="utf-8") as f:
    repos = json.load(f)

# Sort by updatedAt descending
repos = sorted(repos, key=lambda x: x["updatedAt"], reverse=True)

lines = []
lines.append("# Consolidated Competitor Repositories & READMEs")
lines.append(f"**Hackathon:** Meta Global AI Developer Hackathon 2026 (Cerebral Valley / Meta Muse)")
lines.append(f"**Total Repositories Collected:** {len(repos)}")
lines.append(f"**Generated At:** 2026-10-28\n")
lines.append("## Table of Contents\n")

for i, repo in enumerate(repos, 1):
    fname = repo["fullName"]
    anchor = fname.lower().replace("/", "").replace("-", "").replace("_", "").replace(".", "")
    lines.append(f"{i}. [{fname}](#{anchor}) - *Updated: {repo['updatedAt']}*")

lines.append("\n---\n")

for i, repo in enumerate(repos, 1):
    fname = repo["fullName"]
    local_file = COMP_DIR / repo["localFile"]
    anchor = fname.lower().replace("/", "").replace("-", "").replace("_", "").replace(".", "")
    
    lines.append(f"\n# {i}. {fname}")
    lines.append(f"- **GitHub URL:** {repo['url']}")
    lines.append(f"- **Last Updated:** {repo['updatedAt']}")
    lines.append(f"- **Description:** {repo.get('description', 'N/A')}")
    lines.append(f"- **Local Source:** `{repo['localFile']}`")
    lines.append("\n<details open><summary><b>Click to expand/collapse README</b></summary>\n")
    
    if local_file.exists():
        with open(local_file, "r", encoding="utf-8", errors="replace") as rf:
            content = rf.read().strip()
            lines.append(content if content else "*[README is empty]*")
    else:
        lines.append("*[README file missing]*")
        
    lines.append("\n</details>\n")
    lines.append("\n---\n")

with open(OUT_FILE, "w", encoding="utf-8") as out:
    out.write("\n".join(lines))

print(f"Successfully combined {len(repos)} competitor READMEs into {OUT_FILE}")
print(f"File size: {OUT_FILE.stat().st_size / (1024*1024):.2f} MB")
