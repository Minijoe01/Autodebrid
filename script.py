import csv
import requests
import os

# ==========================
# CONFIGURATION
# ==========================
# CSV_URL doit être défini dans les secrets GitHub Actions
CSV_URL = os.environ.get('CSV_URL')
M3U_FILENAME = "formule2.m3u"
KEYWORD = "Course"

# ==========================
# FONCTIONS
# ==========================
def fetch_csv(csv_url):
    resp = requests.get(csv_url)
    resp.raise_for_status()
    content = resp.text
    # Split by line and parse manually car CSV 1fichier est séparé par ";"
    reader = csv.reader(content.splitlines(), delimiter=';')
    return list(reader)

def filter_course_files(csv_data):
    # csv_data format: [lien, nom_fichier, taille]
    filtered = [row for row in csv_data if KEYWORD.lower() in row[1].lower()]
    # Tri par nom de fichier
    filtered.sort(key=lambda x: x[1])
    return filtered

def generate_m3u(filtered_list, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n\n")
        for row in filtered_list:
            url, name, _ = row
            f.write(f"#EXTINF:-1,{name}\n{url}\n\n")
    print(f"✅ Fichier M3U généré: {filename}")

# ==========================
# SCRIPT PRINCIPAL
# ==========================
def main():
    if not CSV_URL:
        print("❌ CSV_URL non défini !")
        return
    print("1) Extraction fichiers 1fichier...")
    csv_data = fetch_csv(CSV_URL)
    filtered = filter_course_files(csv_data)
    if not filtered:
        print(f"Aucun fichier trouvé avec le mot clé: {KEYWORD}")
        return
    print(f"{len(filtered)} fichiers trouvés avec '{KEYWORD}'.")
    print("2) Création du M3U...")
    generate_m3u(filtered, M3U_FILENAME)

if __name__ == "__main__":
    main()
