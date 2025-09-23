name: Génération M3U F2

on:
  schedule:
    # Tous les jours à 7h00 UTC
    - cron: '0 7 * * *'
  workflow_dispatch:  # Permet de lancer manuellement si besoin

jobs:
  generate-m3u:
    runs-on: ubuntu-latest
    steps:
      # 1) Récupérer le code depuis le repo
      - uses: actions/checkout@v3

      # 2) Installer Python
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      # 3) Installer les dépendances
      - name: Install requests
        run: pip install requests

      # 4) Générer le M3U
      - name: Generate M3U
        env:
          ALLDEBRID_API_KEY: ${{ secrets.ALLDEBRID_API_KEY }}
          CSV_URL: "https://1fichier.com/dir/GwAVeQxR?e=1"
        run: python script.py

      # 5) Upload M3U comme artefact
      - name: Upload M3U Artifact
        uses: actions/upload-artifact@v4
        with:
          name: M3U-F2
          path: formule2-debride.m3u
