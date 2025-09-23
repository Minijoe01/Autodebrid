import os
import requests

# Variables
ALLDEBRID_API_KEY = os.getenv("ALLDEBRID_API_KEY")
M3U_FILE = "formule2.m3u"         # fichier généré directement par script.py
ALLDEBRID_FOLDER = "links"         # dossier AllDebrid pour sauvegarde

# Vérifie que la clé est présente
if not ALLDEBRID_API_KEY:
    raise ValueError("❌ Clé API AllDebrid manquante (ALLDEBRID_API_KEY)")

# Vérifie que le fichier existe
if not os.path.exists(M3U_FILE):
    raise FileNotFoundError(f"❌ Fichier {M3U_FILE} introuvable")

# Upload vers AllDebrid
url = "https://api.alldebrid.com/v4/file/upload"

with open(M3U_FILE, 'rb') as f:
    files = {'file': f}
    data = {
        "apikey": ALLDEBRID_API_KEY,
        "folder": ALLDEBRID_FOLDER,
        "overwrite": "true"   # écrase le fichier si déjà présent
    }
    resp = requests.post(url, files=files, data=data)
    resp_data = resp.json()

if resp_data.get("status") == "success":
    print(f"✅ M3U uploadé et sauvegardé dans AllDebrid: {resp_data['data']['link']}")
    print(f"➡️ Tu peux utiliser ce lien dans Kodi: {resp_data['data']['link']}")
else:
    print(f"❌ Erreur upload AllDebrid: {resp_data}")
