import subprocess
import json
import base64
from pathlib import Path

OUT_DIR = Path("c:/Users/aman/Documents/meta/competitor_readmes")
OUT_DIR.mkdir(exist_ok=True)

queries = [
    'gh search repos "meta hackathon" --sort updated --order desc --limit 30 --json fullName,description,updatedAt,url',
    'gh search repos "meta global ai developer hackathon" --sort updated --order desc --limit 30 --json fullName,description,updatedAt,url',
    'gh search repos "muse hackathon" --sort updated --order desc --limit 30 --json fullName,description,updatedAt,url'
]

repos_map = {}

for q in queries:
    res = subprocess.run(q, shell=True, capture_output=True, text=False)
    if res.returncode == 0 and res.stdout:
        try:
            raw_text = res.stdout.decode("utf-8", errors="replace")
            items = json.loads(raw_text)
            for it in items:
                repos_map[it["fullName"]] = it
        except Exception as e:
            print("Error parsing json:", e)

# Sort all by updatedAt descending
all_repos = sorted(repos_map.values(), key=lambda x: x["updatedAt"], reverse=True)
print(f"Total unique competitor repos found: {len(all_repos)}")

downloaded = []
index_data = []

for repo in all_repos:
    full_name = repo["fullName"]
    clean_name = full_name.replace("/", "__")
    readme_path = OUT_DIR / f"{clean_name}__README.md"
    
    cmd = f'gh api repos/{full_name}/readme'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=False)
    
    if res.returncode == 0 and res.stdout:
        try:
            raw_text = res.stdout.decode("utf-8", errors="replace")
            data = json.loads(raw_text)
            if "content" in data and data.get("encoding") == "base64":
                raw_bytes = base64.b64decode(data["content"])
                readme_text = raw_bytes.decode("utf-8", errors="replace")
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(readme_text)
                downloaded.append(full_name)
                index_data.append({
                    "fullName": full_name,
                    "description": repo.get("description", ""),
                    "updatedAt": repo["updatedAt"],
                    "url": repo["url"],
                    "localFile": readme_path.name,
                    "sizeBytes": len(readme_text)
                })
                print(f"[SAVED] {full_name} -> {readme_path.name} (updated: {repo['updatedAt']})")
        except Exception as e:
            pass

with open(OUT_DIR / "INDEX.json", "w", encoding="utf-8") as f:
    json.dump(index_data, f, indent=2)

print(f"\nDone! Downloaded {len(downloaded)} READMEs into {OUT_DIR}")
