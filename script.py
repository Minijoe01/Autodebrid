import os
import requests

FICHIER_API = os.getenv("FICHIER_API")
ALD_TOKEN = os.getenv("ALD_TOKEN")

# 1. Récupérer la liste des fichiers du dossier 1fichier
DIR_URL = "https://1fichier.com/dir/GwAVeQxR"
resp = requests.get(DIR_URL)
resp.raise_for_status()

# Filtrage basique sur "course"
links = []
for line in resp.text.splitlines():
    if "https://1fichier.com/" in line and "course" in line.lower():
        start = line.find("https://1fichier.com/")
        end = line.find('"', start)
        url = line[start:end]
        links.append(url)

if not links:
    print("Aucun lien trouvé avec le mot clé 'course'.")
    exit(0)

# 2. Débrider chaque lien avec AllDebrid
debrid_links = []
for link in links:
    r = requests.get("https://api.alldebrid.com/v4/link/unlock", params={
        "agent": "github-m3u-bot",
        "apikey": ALD_TOKEN,
        "link": link
    })
    r.raise_for_status()
    data = r.json()
    if data["status"] == "success":
        debrid_links.append(data["data"]["link"])
    else:
        print(f"Erreur debrid: {link}")

# 3. Construire le fichier M3U
m3u_content = "#EXTM3U\n"
for link in debrid_links:
    m3u_content += f"#EXTINF:-1,{os.path.basename(link)}\n{link}\n"

with open("playlist_course.m3u", "w", encoding="utf-8") as f:
    f.write(m3u_content)

# 4. Upload vers AllDebrid "saved links"
files = {"files[]": ("playlist_course.m3u", open("playlist_course.m3u", "rb"), "text/plain")}
upload = requests.post("https://api.alldebrid.com/v4/user/links/save", params={
    "agent": "github-m3u-bot",
    "apikey": ALD_TOKEN
}, files=files)

print("Upload AllDebrid:", upload.text)
