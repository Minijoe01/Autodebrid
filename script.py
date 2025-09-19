# script.py
# Génère formule 2.m3u à partir du dossier 1fichier, la pousse dans le repo,
# et enregistre l'URL raw dans les Saved Links AllDebrid (en remplaçant l'ancienne).

import os
import requests
from bs4 import BeautifulSoup
import subprocess
import json
import time

# CONFIG (lire depuis les GitHub Secrets / env)
ALLDEBRID_API_KEY = os.getenv("ALLDEBRID_API_KEY")   # Obligatoire (mettre en Secret)
FICHIER_DIR_URL = os.getenv("FICHIER_DIR_URL")      # Obligatoire (mettre en Secret)
KEYWORD = "course"
M3U_FILENAME = "formule 2.m3u"
REPO_M3U_PATH = M3U_FILENAME   # on place la m3u à la racine du repo

if not ALLDEBRID_API_KEY or not FICHIER_DIR_URL:
    print("Erreur: variables ALLDEBRID_API_KEY et/ou FICHIER_DIR_URL manquantes.")
    raise SystemExit(1)

session = requests.Session()
session.headers.update({"User-Agent": "github-autodebrid-bot/1.0"})

def fetch_file_entries_from_1fichier(dir_url, keyword):
    r = session.get(dir_url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    # 1fichier structure: trouver <a href="/?xxxxx"> liens et récupérer nom réel via title / sibling
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # on recherche entrées de type "/?xxxx" (1fichier file link) ou "/file/xxxx"
        if (href.startswith("/?") or "/file/" in href) and href.strip():
            # récupérer nom affiché (title, text, ou span voisin)
            filename = a.get("title") or a.text.strip()
            if not filename:
                s = a.find_next("span")
                if s:
                    filename = s.text.strip()
            if filename and keyword.lower() in filename.lower():
                # construire url complète si nécessaire
                if href.startswith("/"):
                    url = "https://1fichier.com" + href
                elif href.startswith("http"):
                    url = href
                else:
                    url = "https://1fichier.com/" + href
                results.append({"name": filename, "url": url})
    # dédup par url
    unique = {}
    for it in results:
        unique[it["url"]] = it
    return list(unique.values())

def alldebrid_unlock(link):
    url = "https://api.alldebrid.com/v4/link/unlock"
    headers = {"Authorization": f"Bearer {ALLDEBRID_API_KEY}"}
    # Use POST per doc; but GET also allowed — we'll POST
    try:
        r = session.post(url, headers=headers, data={"link": link}, timeout=30)
        data = r.json()
    except Exception as e:
        print("Erreur HTTP AllDebrid unlock:", e)
        return None
    if data.get("status") != "success":
        # print message for debug
        print("AllDebrid unlock failed:", data)
        return None
    # AllDebrid returns data.link or data.download etc.
    d = data.get("data", {})
    return d.get("link") or d.get("download") or d.get("stream")

def write_m3u(entries, filename):
    lines = ["#EXTM3U"]
    for e in entries:
        title = e.get("title") or e.get("name") or "unknown"
        url = e.get("url")
        lines.append(f"#EXTINF:-1,{title}")
        lines.append(url)
    text = "\n".join(lines) + "\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    return filename

def git_commit_and_push(filepath, commit_message="Update playlist"):
    # configure user (actions runner already set GH token, but set name/email)
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
    # add, commit, push
    subprocess.run(["git", "add", filepath], check=True)
    # commit even if no change: use --allow-empty? We'll only commit if changed
    # check git diff --staged to see if any change
    diff = subprocess.run(["git", "diff", "--staged", "--name-only"], capture_output=True, text=True)
    if diff.stdout.strip() == "":
        print("Aucune modification à commiter (m3u inchangée).")
        return False
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    # push using GITHUB_TOKEN-provided origin
    subprocess.run(["git", "push"], check=True)
    return True

def get_raw_github_url_for_file(repo_owner, repo_name, branch, filepath):
    # raw URL format:
    # https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}
    return f"https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/{filepath}"

def alldebrid_list_saved_links():
    url = "https://api.alldebrid.com/v4/user/links"
    headers = {"Authorization": f"Bearer {ALLDEBRID_API_KEY}"}
    r = session.get(url, headers=headers, timeout=20)
    data = r.json()
    if data.get("status") != "success":
        print("Erreur récupération saved links:", data)
        return []
    return data.get("data", {}).get("links", [])

def alldebrid_delete_saved_links(links_list):
    if not links_list:
        return {"status":"noop"}
    url = "https://api.alldebrid.com/v4/user/links/delete"
    headers = {"Authorization": f"Bearer {ALLDEBRID_API_KEY}"}
    # form fields links[]=...
    payload = []
    for l in links_list:
        payload.append(("links[]", l))
    r = session.post(url, headers=headers, data=payload, timeout=20)
    return r.json()

def alldebrid_save_links(links_list):
    url = "https://api.alldebrid.com/v4/user/links/save"
    headers = {"Authorization": f"Bearer {ALLDEBRID_API_KEY}"}
    payload = []
    for l in links_list:
        payload.append(("links[]", l))
    r = session.post(url, headers=headers, data=payload, timeout=20)
    return r.json()

def parse_repo_info_from_env():
    # GitHub Actions exposes GITHUB_REPOSITORY and GITHUB_REF
    repo = os.getenv("GITHUB_REPOSITORY")  # owner/repo
    ref = os.getenv("GITHUB_REF", "refs/heads/main")  # branch ref
    if not repo:
        raise SystemExit("GITHUB_REPOSITORY not found in env (required to build raw URL).")
    owner, name = repo.split("/")
    branch = ref.replace("refs/heads/", "")
    return owner, name, branch

def main():
    # 1) lire dossier 1fichier et filtrer
    print("1) Extraction fichiers 1fichier...")
    entries = fetch_file_entries_from_1fichier(FICHIER_DIR_URL, KEYWORD)
    if not entries:
        print("Aucun fichier trouvé avec le mot clé:", KEYWORD)
        return
    print(f"{len(entries)} fichier(s) trouvé(s).")

    # 2) débrider avec AllDebrid (obtenir liens directs)
    debrid_entries = []
    for e in entries:
        url = e["url"]
        print("Débridage:", e["name"])
        direct = alldebrid_unlock(url)
        if direct:
            debrid_entries.append({"title": e["name"], "url": direct})
            print("OK :", direct)
        else:
            print("Échec débridage pour", url)
        time.sleep(0.5)

    if not debrid_entries:
        print("Aucun lien débridé, stop.")
        return

    # 3) écrire m3u local
    m3u_local = write_m3u(debrid_entries, M3U_FILENAME)
    print("M3U écrite:", m3u_local)

    # 4) commit & push dans le repo (écrase le fichier existant)
    # ATTENTION: GITHUB_TOKEN doit être présent (automatique dans GH Actions)
    pushed = False
    try:
        pushed = git_commit_and_push(REPO_M3U_PATH, commit_message="Auto update formule 2.m3u")
    except Exception as ex:
        print("Erreur git push:", ex)
        # si push échoue on continue mais AllDebrid ne pourra pas accéder au raw url

    # 5) construire raw URL et sauvegarder dans AllDebrid Saved Links
    try:
        owner, repo_name, branch = parse_repo_info_from_env()
        raw_url = get_raw_github_url_for_file(owner, repo_name, branch, REPO_M3U_PATH)
        print("Raw URL construite:", raw_url)
    except Exception as ex:
        print("Impossible de construire raw URL:", ex)
        return

    # 6) supprimer ancien saved link correspondant (même filename or same link)
    saved = alldebrid_list_saved_links()
    to_delete = []
    for s in saved:
        filename = s.get("filename", "") or ""
        link = s.get("link", "")
        # si filename match exact ou link match raw_url => marquer à supprimer
        if filename.strip().lower() == M3U_FILENAME.lower() or link == raw_url:
            to_delete.append(link)
    if to_delete:
        print("Suppression des anciens saved links:", to_delete)
        res_del = alldebrid_delete_saved_links(to_delete)
        print("Résultat suppression:", res_del)

    # 7) enregistrer la nouvelle raw_url dans saved links
    print("Enregistrement du nouveau lien dans AllDebrid Saved Links...")
    res_save = alldebrid_save_links([raw_url])
    print("Résultat save:", res_save)

if __name__ == "__main__":
    main()
