#!/usr/bin/env python3
"""
autodebrid.py - Version GitHub Actions

- Récupère la liste de fichiers dans un dossier public 1fichier
- Filtre ceux contenant le mot clé "course"
- Débride chaque lien via l'API AllDebrid
- Construit une playlist M3U
- (Optionnel) upload FTP -> si tu ajoutes secrets FTP_USER et FTP_PASS
"""

import os
import re
import time
import json
import logging
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ---------------------------
# CONFIG - lit depuis secrets/env
# ---------------------------
CONFIG = {
    "onefichier_dir_url": "https://1fichier.com/dir/GwAVeQxR",
    "keyword": "course",
    "m3u_filename": "playlist_course.m3u",
    "user_agent": "AutoDebridScript/1.0 (+https://github.com)",
    "dry_run": False,
}

# secrets GitHub
ALD_TOKEN = os.getenv("ALD_TOKEN")
FICHIER_API = os.getenv("FICHIER_API")
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")

session = requests.Session()
session.headers.update({"User-Agent": CONFIG["user_agent"]})

# ---------------------------
# Helpers
# ---------------------------
def fetch_1fichier_dir_links(dir_url: str) -> List[Dict]:
    """Parse la page 1fichier /dir/ et extrait les fichiers"""
    logging.info("Téléchargement du listing 1fichier...")
    r = session.get(dir_url, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = (a.get_text() or "").strip()
        if "1fichier.com" in href and "/file/" in href:
            results.append({"name": text or href.split("/")[-1], "url": href})
    logging.info("Fichiers trouvés: %d", len(results))
    return results

def filter_by_keyword(items: List[Dict], keyword: str) -> List[Dict]:
    kw = keyword.lower()
    return [it for it in items if kw in it["name"].lower() or kw in it["url"].lower()]

ALD_BASE = "https://api.alldebrid.com/v4"

def alldebrid_unlock(link: str) -> Optional[str]:
    url = f"{ALD_BASE}/link/unlock"
    params = {"agent": "AutoDebridScript", "token": ALD_TOKEN, "link": link}
    try:
        r = session.post(url, params=params, timeout=20)
        data = r.json()
        if data.get("status") == "success":
            return data["data"].get("link") or data["data"].get("download")
        else:
            logging.warning("Unlock échoué: %s -> %s", link, data)
            return None
    except Exception as e:
        logging.exception("Erreur unlock: %s", e)
        return None

def build_m3u(entries: List[Dict]) -> str:
    lines = ["#EXTM3U"]
    for e in entries:
        lines.append(f"#EXTINF:-1,{e['title']}")
        lines.append(e["url"])
    return "\n".join(lines)

# ---------------------------
# Workflow principal
# ---------------------------
def main():
    if not ALD_TOKEN or not FICHIER_API:
        logging.error("Clés API manquantes (ALD_TOKEN / FICHIER_API)")
        return

    # 1) lister
    items = fetch_1fichier_dir_links(CONFIG["onefichier_dir_url"])
    filtered = filter_by_keyword(items, CONFIG["keyword"])
    logging.info("Fichiers filtrés contenant '%s': %d", CONFIG["keyword"], len(filtered))

    # 2) débrider
    m3u_entries = []
    for it in filtered:
        link = it["url"]
        title = it["name"]
        logging.info("Débridage: %s", title)
        unlocked = alldebrid_unlock(link)
        if unlocked:
            m3u_entries.append({"title": title, "url": unlocked})
        time.sleep(1)

    if not m3u_entries:
        logging.warning("Aucun lien débridé trouvé.")
        return

    # 3) créer M3U
    m3u_text = build_m3u(m3u_entries)
    with open(CONFIG["m3u_filename"], "w", encoding="utf-8") as f:
        f.write(m3u_text)
    logging.info("Playlist générée: %s (%d entrées)", CONFIG["m3u_filename"], len(m3u_entries))

    # (Optionnel) upload FTP si creds fournis
    if FTP_USER and FTP_PASS:
        try:
            from ftplib import FTP_TLS
            ftps = FTP_TLS("ftp.1fichier.com")
            ftps.login(FTP_USER, FTP_PASS)
            ftps.prot_p()
            with open(CONFIG["m3u_filename"], "rb") as f:
                ftps.storbinary(f"STOR {CONFIG['m3u_filename']}", f)
            ftps.quit()
            logging.info("Upload FTP terminé.")
        except Exception as e:
            logging.exception("Erreur upload FTP: %s", e)

if __name__ == "__main__":
    main()
