#!/usr/bin/env python3
"""
Télécharge des reels Instagram en haute qualité puis applique une légère
modification de vitesse aléatoire (±1-3%) pour désynchroniser l'empreinte
de la vidéo.

Deux méthodes essayées automatiquement pour chaque URL :
  1. yt-dlp (rapide, gère la meilleure qualité) — avec cookies si dispo
  2. Page d'intégration "embed" (secours, sans cookies, pour reels publics)

Usage :
    python ig_downloader.py                 # lit urls.txt
    python ig_downloader.py URL1 URL2 ...    # URLs en argument
    python ig_downloader.py --browser safari # utilise les cookies de Safari
    python ig_downloader.py --min 0.95 --max 1.05   # amplitude de vitesse
"""

import argparse
import os
import random
import re
import subprocess
import sys
import urllib.request

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = "ffmpeg"

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(HERE, "videos")
URLS_FILE = os.path.join(HERE, "urls.txt")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")


# ---------- utilitaires ----------

def shortcode(url: str) -> str:
    m = re.search(r"/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else None


def read_urls_file() -> list:
    if not os.path.exists(URLS_FILE):
        return []
    urls = []
    with open(URLS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


# ---------- méthode 1 : yt-dlp ----------

def try_ytdlp(url: str, code: str, browser: str) -> str:
    out_tmpl = os.path.join(OUTPUT_DIR, f"{code}.%(ext)s")
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
        "-o", out_tmpl,
        "--print", "after_move:filepath",
        "--no-warnings",
    ]
    if browser:
        cmd += ["--cookies-from-browser", browser]
    cmd.append(url)

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and res.stdout.strip():
        return res.stdout.strip().splitlines()[-1].strip()
    return None


# ---------- méthode 2 : page embed ----------

def fetch(u: str) -> str:
    req = urllib.request.Request(u, headers={
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def try_embed(code: str) -> str:
    endpoints = [
        f"https://www.instagram.com/reel/{code}/embed/captioned/",
        f"https://www.instagram.com/p/{code}/embed/captioned/",
        f"https://www.instagram.com/reel/{code}/embed/",
    ]
    for ep in endpoints:
        try:
            page = fetch(ep)
        except Exception:
            continue
        clean = page.replace("\\u0026", "&").replace("\\/", "/").replace('\\"', '"')
        found = re.findall(r'https://[^\s"\'<>\\]+\.mp4[^\s"\'<>\\]*', clean)
        cdn = [u for u in found if "cdninstagram" in u or "fbcdn" in u]
        if cdn:
            dest = os.path.join(OUTPUT_DIR, f"{code}.mp4")
            req = urllib.request.Request(cdn[0], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
                while True:
                    chunk = r.read(1 << 16)
                    if not chunk:
                        break
                    f.write(chunk)
            return dest
    return None


# ---------- modification de vitesse ----------

def apply_speed_tweak(path: str, lo: float, hi: float):
    while True:
        factor = round(random.uniform(lo, hi), 4)
        if abs(factor - 1.0) >= 0.005:
            break
    base, ext = os.path.splitext(path)
    tmp = f"{base}_tmp.mp4"
    cmd = [
        FFMPEG, "-y", "-i", path,
        "-filter_complex",
        f"[0:v]setpts={1/factor:.6f}*PTS[v];[0:a]atempo={factor:.6f}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        tmp,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.replace(tmp, os.path.splitext(path)[0] + ".mp4")
    return factor


# ---------- programme principal ----------

def main():
    ap = argparse.ArgumentParser(description="Téléchargeur de reels Instagram + modif vitesse")
    ap.add_argument("urls", nargs="*", help="URLs (sinon lit urls.txt)")
    ap.add_argument("--browser", help="Navigateur pour les cookies : safari, chrome, firefox…")
    ap.add_argument("--min", type=float, default=0.97, help="Facteur de vitesse minimum")
    ap.add_argument("--max", type=float, default=1.03, help="Facteur de vitesse maximum")
    ap.add_argument("--no-tweak", action="store_true", help="Ne pas modifier la vitesse")
    args = ap.parse_args()

    urls = args.urls or read_urls_file()
    if not urls:
        print("Aucune URL. Ajoute des liens dans urls.txt ou passe-les en argument.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"{len(urls)} vidéo(s) à traiter → {OUTPUT_DIR}\n")

    ok, fail = 0, 0
    for i, url in enumerate(urls, 1):
        code = shortcode(url) or f"video{i}"
        print(f"[{i}/{len(urls)}] {code}")

        path = None
        try:
            path = try_ytdlp(url, code, args.browser)
            if path:
                print("  ✓ récupéré via yt-dlp")
        except Exception as e:
            print(f"  yt-dlp: {e}")

        if not path:
            try:
                path = try_embed(code)
                if path:
                    print("  ✓ récupéré via embed")
            except Exception as e:
                print(f"  embed: {e}")

        if not path or not os.path.exists(path):
            print("  ✗ ÉCHEC — reel privé, supprimé, ou Instagram a verrouillé l'accès")
            fail += 1
            continue

        size = os.path.getsize(path) / 1_048_576
        print(f"  Téléchargé : {size:.1f} Mo")

        if not args.no_tweak:
            try:
                factor = apply_speed_tweak(path, args.min, args.max)
                final = os.path.splitext(path)[0] + ".mp4"
                size = os.path.getsize(final) / 1_048_576
                print(f"  Vitesse modifiée {factor:.4f}x — final {size:.1f} Mo ✓")
            except Exception as e:
                print(f"  (modif vitesse échouée : {e} — fichier brut conservé)")
        ok += 1

    print(f"\nTerminé : {ok} réussi(s), {fail} échoué(s).")
    print(f"Fichiers dans : {OUTPUT_DIR}")
    if fail:
        print("\nAstuce : pour les échecs, relance avec tes cookies de navigateur :")
        print("   ./run.sh --browser safari      (ou chrome / firefox)")


if __name__ == "__main__":
    main()
