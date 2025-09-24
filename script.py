import csv
import requests
import os

# ==========================
# CONFIGURATION
# ==========================
CSV_URL = os.environ.get('CSV_URL')
ALLDEBRID_API_KEY = os.environ.get('ALLDEBRID_API_KEY')
M3U_FILENAME = "formule2-debride.m3u"
KEYWORD = "Course"

# ==========================
# FONCTIONS
# ==========================
def fetch_csv(csv_url):
    resp = requests.get(csv_url)
    resp.raise_for_status()
    content = resp.text
    reader = csv.reader(content.splitlines(), delimiter=';')
    return list(reader)

def filter_course_files(csv_data):
    filtered = [row for row in csv_data if KEYWORD.lower() in row[1].lower()]
    filtered.sort(key=lambda x: x[1])
    return filtered

def debrid_link(url):
    api_url = "https://api.alldebrid.com/v4/link/unlock"
    params = {
        "agent": "script",
        "apikey": ALLDEBRID_API_KEY,
        "link": url
    }
    resp = requests.get(api_url, params=params).json()
    if resp.get("status") == "success":
        return resp["data"]["link"]["link"]
    else:
        print(f"❌ Erreur débridage pour {url}: {resp}")
        return url  # fallback

def generate_m3u(filtered_list, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n\n")
        for row in filtered_list:
            url, name, _ = row
            debrided = debrid_link(url)
            f.write(f"#EXTINF:-1,{name}\n{debrided}\n\n")
    print(f"✅ Fichier M3U généré: {filename}")

# ==========================
# SCRIPT PRINCIPAL
# ==========================
def main():
    if not CSV_URL or not ALLDEBRID_API_KEY:
        print("❌ CSV_URL ou ALLDEBRID_API_KEY non défini !")
        return
    print("1) Extraction fichiers 1fichier...")
    csv_data = fetch_csv(CSV_URL)
    filtered = filter_course_files(csv_data)
    if not filtered:
        print(f"Aucun fichier trouvé avec le mot clé: {KEYWORD}")
        return
    print(f"{len(filtered)} fichiers trouvés avec '{KEYWORD}'.")
    print("2) Débridage et création du M3U...")
    generate_m3u(filtered, M3U_FILENAME)

if __name__ == "__main__":
    main()
