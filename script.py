import os
import requests
from bs4 import BeautifulSoup

# ========================
# CONFIGURATION
# ========================
FOLDER_URL = "https://1fichier.com/dir/GwAVeQxR"  # 🔹 Mets ici ton lien de dossier 1fichier
KEYWORD = "Course"  # 🔹 Mot-clé à filtrer dans les noms de fichiers

ALLDEBRID_API_KEY = os.getenv("ALLDEBRID_API_KEY")  # Clé API AllDebrid (ajoutée dans GitHub Secrets)
EMAIL_TO_NOTIFY = os.getenv("EMAIL_TO_NOTIFY", "")  # Optionnel : email pour notifier
# ========================


def get_links_from_folder(url, keyword):
    """
    Récupère les liens du dossier 1fichier
    uniquement si le mot-clé est présent dans le NOM du fichier.
    """
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]

        if "/?" in href:  # lien fichier 1fichier
            # Récupérer le vrai nom du fichier
            filename = a.get("title") or a.text.strip()

            # Si vide, essayer de trouver dans un <span> voisin
            if not filename:
                span = a.find_next("span")
                if span:
                    filename = span.text.strip()

            # Vérifier si mot-clé dans le NOM du fichier
            if filename and keyword.lower() in filename.lower():
                links.append("https://1fichier.com" + href)

    return links


def debrid_link(link):
    """
    Utilise l’API AllDebrid pour transformer un lien 1fichier en lien direct.
    """
    url = "https://api.alldebrid.com/v4/link/unlock"
    params = {"agent": "autodebrid", "apikey": ALLDEBRID_API_KEY, "link": link}
    resp = requests.get(url, params=params)
    data = resp.json()

    if data.get("status") == "success":
        return data["data"]["link"]
    else:
        print("Erreur debrid:", link)
        return None


def main():
    # Vérifier la clé API
    if not ALLDEBRID_API_KEY:
        print("Erreur: Clé API AllDebrid manquante (ALLDEBRID_API_KEY)")
        return

    # Récupérer les liens filtrés
    links = get_links_from_folder(FOLDER_URL, KEYWORD)
    if not links:
        print(f"Aucun fichier trouvé avec le mot clé '{KEYWORD}'.")
        return

    print(f"{len(links)} fichiers trouvés avec le mot clé '{KEYWORD}'.")

    # Débrider les liens
    debrided_links = []
    for link in links:
        direct = debrid_link(link)
        if direct:
            debrided_links.append(direct)

    if not debrided_links:
        print("Aucun lien débridé.")
        return

    # Sauvegarder dans un fichier texte (ou playlist M3U)
    with open("output.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for link in debrided_links:
            f.write(f"#EXTINF:-1,{link}\n{link}\n")

    print("✅ Playlist générée : output.m3u")


if __name__ == "__main__":
    main()
