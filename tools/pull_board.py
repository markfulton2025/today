"""Pull the newest encrypted Today board from a public-link Drive folder.

Usage: python3 tools/pull_board.py <drive_folder_id> data.enc.json

Lists the folder via Drive's public embedded folder view (no API key needed),
picks the newest file named enc-*.json, downloads it, checks it is a valid
encrypted envelope ({"v","stamp","iv","ct"}), and overwrites the target only
if its stamp is newer. Writes updated=true/false and stamp to GITHUB_OUTPUT.
"""
import json, os, re, sys, urllib.request

UA = {"User-Agent": "today-robot"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def out(**kv):
    path = os.environ.get("GITHUB_OUTPUT")
    lines = "".join(f"{k}={v}\n" for k, v in kv.items())
    if path:
        with open(path, "a") as f:
            f.write(lines)
    print(lines, end="")


def note(msg):
    # Public run annotation; never include file contents.
    print(f"::notice::{msg}")


def list_folder(folder):
    html = get(f"https://drive.google.com/embeddedfolderview?id={folder}#list").decode("utf-8", "replace")
    note(f"folder view {len(html)} chars, file links {len(re.findall(r'/file/d/', html))}, titles {len(re.findall(r'flip-entry-title', html))}, entries {len(re.findall(r'id=\"entry-', html))}")
    # Each entry: <a href="https://drive.google.com/file/d/<ID>/view..."> ... <div class="flip-entry-title">NAME</div>
    files = {}
    for m in re.finditer(r'/file/d/([A-Za-z0-9_-]{20,})/.*?flip-entry-title">([^<]+)<', html, re.S):
        files[m.group(2).strip()] = m.group(1)
    return files


def main(folder, target):
    if not folder:
        sys.exit("TODAY_DRIVE_FOLDER repo variable is not set")
    try:
        listing = list_folder(folder)
    except Exception as e:
        # Folder not shared yet or Drive hiccup: skip quietly, try again next run.
        note(f"could not list folder: {e}")
        return out(updated="false", stamp="")
    files = {n: i for n, i in listing.items() if re.fullmatch(r"enc-\d{12,14}\.json", n)}
    if not files:
        note(f"no enc-*.json files matched; names seen: {sorted(listing)[:5]}")
        return out(updated="false", stamp="")
    newest = max(files)
    raw = get(f"https://drive.usercontent.google.com/download?id={files[newest]}&export=download")
    env = json.loads(raw)
    if not all(k in env for k in ("v", "stamp", "iv", "ct")):
        sys.exit(f"{newest} is not an encrypted envelope; refusing to publish")
    cur = ""
    if os.path.exists(target):
        try:
            cur = json.load(open(target)).get("stamp", "")
        except Exception:
            pass
    if str(env["stamp"]) <= str(cur):
        note(f"{newest} stamp {env['stamp']} not newer than live {cur}")
        return out(updated="false", stamp=cur)
    with open(target, "w") as f:
        json.dump(env, f, separators=(",", ":"))
    out(updated="true", stamp=env["stamp"])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("FOLDER_ID", ""), sys.argv[2] if len(sys.argv) > 2 else "data.enc.json")
