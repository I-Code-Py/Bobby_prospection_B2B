#!/usr/bin/env bash
# Lance l'outil : crée l'environnement Python, installe les dépendances,
# puis exécute le téléchargeur. Réutilise l'environnement aux lancements suivants.
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 n'est pas installé. Télécharge-le sur https://www.python.org/downloads/"
  exit 1
fi

if [ ! -d .venv ]; then
  echo "Première installation (environnement Python)…"
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

python ig_downloader.py "$@"
