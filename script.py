import requests
import csv
import os

ALLDEBRID_API_KEY = os.getenv("ALLDEBRID_API_KEY")  # doit être configuré dans GitHub Secrets

if not ALLDEBRID_API_KEY:
    raise Exception("❌ Clé API AllDebrid manquante !")

# URL CSV de 1fichier
CSV_URL = "https://1fichier.com/dir/GwAVeQxR?e=1"

print(f"CSV_URL utilisée : {CSV_URL}")

# Téléchargement CSV
resp = requests.get(CSV_URL)
resp.raise_for_status()

lines = resp.text.splitlines()
reader = csv.reader(lines, delimiter=';')

# Filtrer les fichiers "Course"
course_files = []
for row in reader:
    if len(row) < 2:
        continue
    url, filename = row[0], row[1]
    if "Course" in filename:
        course_files.append((filename, url))

# Trier par nom de fichier
course_files.sort(key=lambda x: x[0])

# Débrider via AllDebrid et générer le M3U
m3u_lines = ["#EXTM3U"]
for filename, url in course_files:
    r = requests.get(
        f"https://api.alldebrid.com/v4/link/unlock",
        params={"agent": "python_script", "apikey": ALLDEBRID_API_KEY, "link": url}
    )
    data = r.json()
    if data.get("status") == "success":
        debrid_url = data["data"]["link"]
        m3u_lines.append(f"#EXTINF:-1,{filename}")
        m3u_lines.append(debrid_url)
        print(f"✅ Débridé: {filename}")
    else:
        print(f"❌ Erreur debrid: {url}")

# Sauvegarder le M3U
m3u_file = "formule2-debride.m3u"
with open(m3u_file, "w") as f:
    f.write("\n".join(m3u_lines))

print(f"✅ Fichier M3U généré: {m3u_file}")
