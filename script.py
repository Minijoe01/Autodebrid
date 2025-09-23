import os
import csv
import requests

# Récupération des clés API depuis les secrets GitHub
ALLDEBRID_API_KEY = os.getenv("ALLDEBRID_API_KEY")
FICHIER_API_KEY = os.getenv("FICHIER_API_KEY")

# URL du dossier 1fichier (modifiable selon besoin)
FICHIER_DIR_URL = "https://1fichier.com/dir/GwAVeQxR?e=1"

# Nom du fichier M3U généré
OUTPUT_FILE = "formule2.m3u"

def get_1fichier_links():
    """Télécharge le CSV du dossier 1fichier et filtre les fichiers contenant 'Course'"""
    resp = requests.get(FICHIER_DIR_URL)
    resp.raise_for_status()

    decoded = resp.content.decode("utf-8").splitlines()
    reader = csv.DictReader(decoded, delimiter=";")

    links = []
    for row in reader:
        filename = row.get("Nom", "")
        link = row.get("Lien", "")
        if "Course" in filename and link:
            links.append((filename, link))

    # Tri par nom de fichier
    links.sort(key=lambda x: x[0])
    return links

def debrid_link(url):
    """Débride un lien 1fichier via l’API AllDebrid"""
    api_url = "https://api.alldebrid.com/v4/link/unlock"
    params = {"agent": "AutodebridScript", "apikey": ALLDEBRID_API_KEY, "link": url}
    resp = requests.get(api_url, params=params)
    data = resp.json()

    if data.get("status") == "success":
        return data["data"]["link"]
    else:
        print(f"Erreur debrid: {url} → {data}")
        return None

def generate_m3u(links):
    """Crée un fichier M3U avec les liens débridés"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for filename, url in links:
            debrid = debrid_link(url)
            if debrid:
                f.write(f"#EXTINF:-1,{filename}\n{debrid}\n\n")
    print(f"✅ Fichier M3U généré: {OUTPUT_FILE}")

def main():
    if not ALLDEBRID_API_KEY:
        print("Erreur: Clé API AllDebrid manquante (ALLDEBRID_API_KEY)")
        return
    if not FICHIER_API_KEY:
        print("Erreur: Clé API 1fichier manquante (FICHIER_API_KEY)")
        return

    print("1) Extraction fichiers 1fichier...")
    links = get_1fichier_links()

    if not links:
        print("Aucun fichier trouvé avec le mot clé: Course")
        return

    print(f"2) {len(links)} fichiers trouvés. Débridage en cours...")
    generate_m3u(links)

if __name__ == "__main__":
    main()
