import os
import requests

# Récupérer les clés API depuis GitHub Secrets
FICHIER_API_KEY = os.getenv("FICHIER_API_KEY")
ALLDEBRID_API_KEY = os.getenv("ALLDEBRID_API_KEY")

# Variables fixes
FICHIER_DIR_URL = "https://1fichier.com/dir/GwAVeQxR"
M3U_FILENAME = "formule 2.m3u"

# Étape 1 - Récupération des liens du dossier 1fichier
def get_1fichier_links():
    url = f"https://api.1fichier.com/v1/dir/ls.cgi"
    headers = {"Authorization": FICHIER_API_KEY}
    resp = requests.post(url, headers=headers, json={"url": FICHIER_DIR_URL})
    data = resp.json()

    if "items" not in data:
        print("Erreur API 1fichier:", data)
        return []

    results = []
    for item in data["items"]:
        if "course" in item["filename"].lower():
            results.append({"url": item["url"], "name": item["filename"]})
    return results

# Étape 2 - Débrider un lien avec AllDebrid
def debrid_link(link):
    url = "https://api.alldebrid.com/v4/link/unlock"
    params = {"agent": "AutoDebridScript", "apikey": ALLDEBRID_API_KEY, "link": link}
    resp = requests.get(url, params=params).json()
    if resp.get("status") == "success":
        return resp["data"]["link"]
    else:
        print("Erreur debrid:", link, resp)
        return None

# Étape 3 - Générer le fichier M3U
def generate_m3u(links):
    with open(M3U_FILENAME, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for l in links:
            f.write(f"#EXTINF:-1,{l['name']}\n{l['debrid']}\n")
    print(f"{M3U_FILENAME} généré avec {len(links)} liens")

# Étape 4 - Upload sur 1fichier
def upload_to_1fichier(filepath):
    url = "https://api.1fichier.com/v1/upload.cgi"
    headers = {"Authorization": FICHIER_API_KEY}
    files = {"file": open(filepath, "rb")}
    resp = requests.post(url, headers=headers, files=files).json()
    if "url" in resp:
        return resp["url"]["full"]
    else:
        print("Erreur upload:", resp)
        return None

# Étape 5 - Sauvegarder le lien m3u débridé dans AllDebrid (dossier links)
def save_to_alldebrid(link):
    url = "https://api.alldebrid.com/v4/links/save"
    params = {
        "agent": "AutoDebridScript",
        "apikey": ALLDEBRID_API_KEY,
        "link": link,
        "folder": "links",
        "filename": M3U_FILENAME
    }
    resp = requests.get(url, params=params).json()
    print("Sauvegarde AllDebrid:", resp)
    return resp.get("status") == "success"

def main():
    print("1) Extraction fichiers 1fichier...")
    links = get_1fichier_links()
    if not links:
        print("Aucun fichier trouvé avec le mot clé: course")
        return

    print(f"{len(links)} fichiers trouvés. Débridage en cours...")
    final_links = []
    for l in links:
        debrided = debrid_link(l["url"])
        if debrided:
            final_links.append({"name": l["name"], "debrid": debrided})

    if not final_links:
        print("Aucun lien débridé valide.")
        return

    # Générer M3U
    generate_m3u(final_links)

    # Upload vers 1fichier
    uploaded_link = upload_to_1fichier(M3U_FILENAME)
    if not uploaded_link:
        return

    # Débrider ce lien m3u
    debrided_m3u = debrid_link(uploaded_link)
    if not debrided_m3u:
        return

    # Sauvegarder dans AllDebrid
    if save_to_alldebrid(debrided_m3u):
        print(f"✅ Fichier {M3U_FILENAME} sauvegardé dans ton dossier AllDebrid (links)")

if __name__ == "__main__":
    if not FICHIER_API_KEY or not ALLDEBRID_API_KEY:
        print("Erreur: Clés API manquantes.")
    else:
        main()
