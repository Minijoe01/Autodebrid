import os
import requests

# Variables
ALLDEBRID_API_KEY = os.getenv("ALLDEBRID_API_KEY")
CSV_URL = os.getenv("CSV_URL")  # définit dans le workflow YAML
OUTPUT_M3U = "formule2-debride.m3u"

print("1) Extraction fichiers 1fichier...")

# 1. Récupération du CSV
resp = requests.get(CSV_URL)
if resp.status_code != 200:
    raise Exception(f"Erreur téléchargement CSV: {resp.status_code}")

lines = resp.text.splitlines()

# 2. Filtrer les fichiers avec 'Course' dans le nom
course_files = []
for line in lines:
    parts = line.split(";")
    if len(parts) < 2:
        continue
    url, filename = parts[0], parts[1]
    if "Course" in filename or "course" in filename:
        course_files.append((filename, url))

if not course_files:
    print("❌ Aucun fichier trouvé avec le mot clé 'Course'.")
    exit(0)

print(f"{len(course_files)} fichiers trouvés avec 'Course'.")

# 3. Débrider chaque lien via AllDebrid
debrided_links = []
for filename, url in course_files:
    r = requests.get(
        "https://api.alldebrid.com/v4/link/unlock",
        params={"apikey": ALLDEBRID_API_KEY, "link": url}
    )
    data = r.json()
    if data.get("status") == "success":
        debrided_links.append((filename, data["data"]["download"]))
    else:
        print(f"❌ Erreur débridage: {url}")

# 4. Créer le M3U
with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n\n")
    for filename, link in debrided_links:
        f.write(f"#EXTINF:-1,{filename}\n{link}\n\n")

print(f"✅ Fichier M3U généré: {OUTPUT_M3U}")
