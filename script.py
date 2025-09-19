import os
import requests
from bs4 import BeautifulSoup

FICHIER_API = os.getenv("FICHIER_API")
ALD_TOKEN = os.getenv("ALD_TOKEN")

# 1fichier : dossier public
DIR_URL = "https://1fichier.com/dir/GwAVeQxR"
KEYWORD = "Course"

session = requests.Session()
session.headers.update({"User-Agent": "github-m3u-bot"})

# -------------------------
# 1) Récupérer tous les liens fichiers
# -------------------------
resp = session.get(DIR_URL)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

file_links = []
for a in soup.find_all("a", href=True):
    href = a["href"]
    text = a.get_text().strip()
    if "/file/" in href.lower() and KEYWORD.lower() in text.lower():
        file_links.append({"name": text, "url": href})

if not file_links:
    print("Aucun fichier trouvé avec le mot clé 'Course'.")
    exit(0)

print(f"{len(file_links)} fichiers trouvés correspondant au mot clé '{KEYWORD}'.")

# -------------------------
# 2) Débrider chaque lien avec AllDebrid
# -------------------------
debrid_links = []
for f in file_links:
    link = f["url"]
    title = f["name"]
    r = requests.get("https://api.alldebrid.com/v4/link/unlock", params={
        "agent": "github-m3u-bot",
        "apikey": ALD_TOKEN,
        "link": link
    })
    r.raise_for_status()
    data = r.json()
    if data["status"] == "success":
        unlocked = data["data"].get("link") or data["data"].get("download")
        debrid_links.append({"title": title, "url": unlocked})
        print(f"Débridé: {title}")
    else:
        print(f"Erreur debrid: {link}, message: {data.get('error', {}).get('message')}")

# -------------------------
# 3) Générer le fichier M3U
# -------------------------
m3u_text = "#EXTM3U\n"
for entry in debrid_links:
    m3u_text += f"#EXTINF:-1,{entry['title']}\n{entry['url']}\n"

with open("playlist_Course.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_text)

print(f"Playlist générée: playlist_Course.m3u ({len(debrid_links)} entrées)")

# -------------------------
# 4) Upload vers AllDebrid Saved Links
# -------------------------
files = {"files[]": ("playlist_Course.m3u", open("playlist_Course.m3u", "rb"), "text/plain")}
upload = requests.post("https://api.alldebrid.com/v4/user/links/save", params={
    "agent": "github-m3u-bot",
    "apikey": ALD_TOKEN
}, files=files)

print("Upload AllDebrid:", upload.text)

