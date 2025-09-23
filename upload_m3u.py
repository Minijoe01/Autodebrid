import os
import requests
import zipfile

# Variables
ALLDEBRID_API_KEY = os.getenv("ALLDEBRID_API_KEY")
M3U_ZIP = "formule2-m3u.zip"         # nom exact du ZIP généré par script.py
M3U_FILE_IN_ZIP = "formule2.m3u"     # nom exact dans le ZIP
ALLDEBRID_FOLDER = "links"            # dossier AllDebrid pour sauvegarde

# --- Vérifie que la clé est présente ---
if not ALLDEBRID_API_KEY:
    raise ValueError("❌ Clé API AllDebrid manquante (ALLDEBRID_API_KEY)")

# --- Extraction du M3U depuis le ZIP ---
with zipfile.ZipFile(M3U_ZIP, 'r') as zip_ref:
    zip_ref.extract(M3U_FILE_IN_ZIP)
print(f"✅ {M3U_FILE_IN_ZIP} extrait depuis {M3U_ZIP}")

# --- Upload vers AllDebrid ---
url = "https://api.alldebrid.com/v4/file/upload"

with open(M3U_FILE_IN_ZIP, 'rb') as f:
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
