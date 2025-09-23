import os
import csv
import requests

# Clés API depuis GitHub Secrets
ALLDEBRID_API_KEY = os.getenv("ALLDEBRID_API_KEY")
FICHIER_API_KEY = os.getenv("FICHIER_API_KEY")

# URL du dossier 1fichier (modifiable selon besoin)
FICHIER_DIR_URL = "https://1fichier.com/dir/GwAVeQxR?e=1"

# Nom du fichier M3U généré
OUTPUT_FILE = "formule2.m3u"

def get_1fichier_links():
    """Télécharge le CSV du dossier 1fichier et filtre les fichiers contenant 'Course' (insensible à la casse)"""
    print("Téléchargement du CSV...")
    resp = requests.get(FICHIER_DIR_URL)
    resp.raise_for_status()

    decoded = resp.content.decode("utf-8").splitlines()
    reader = csv.reader(decoded, delimiter=';')

    links = []
    for row in reader:
        if len(row) < 2:
            continue
        url, nom_fichier = row[0], row[1]
        if "course" in nom_fichier.lower():  # insensible à la casse
            links.append((nom_fichier, url))

    # Tri par nom de fichier
    links.sort(key=lambda x: x[0])
    print(f"{len(links)} fichiers trouvés avec 'Course'.")
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
        for nom_fichier, url in links:
            debrid = debrid_link(url)
            if debrid:
                f.write(f"#EXTINF:-1,{nom_fichier}\n{debrid}\n\n")
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

    print("2) Débridage des fichiers et création du M3U...")
    generate_m3u(links)

if __name__ == "__main__":
    main()
