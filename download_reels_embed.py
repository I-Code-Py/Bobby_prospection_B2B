#!/usr/bin/env python3
"""
Plan B : télécharge des reels Instagram PUBLICS sans yt-dlp ni cookies,
en lisant la page d'intégration (embed) — la même source qu'un navigateur.
Puis applique une légère modification de vitesse (±1-3%).

Lance :  python3 download_reels_embed.py
Deps   :  pip3 install imageio-ffmpeg   (ffmpeg uniquement ; le reste = stdlib)
"""

import urllib.request
import re
import os
import random
import subprocess
import sys

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = "ffmpeg"

URLS = [
    "https://www.instagram.com/reel/DYrHzAstb8J/",
    "https://www.instagram.com/reel/DYtvjGftqWc/",
    "https://www.instagram.com/reel/DZYkEdwgeYb/",
    "https://www.instagram.com/reel/DXg6NabDS1k/",
    "https://www.instagram.com/reel/DXrR0hDDZwg/",
    "https://www.instagram.com/reel/DXAc4v1DShK/",
    "https://www.instagram.com/reel/DXrSYPqjZb0/",
    "https://www.instagram.com/reel/DX7fx1Ktsn5/",
    "https://www.instagram.com/reel/DXSWPzYja-7/",
]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")


def shortcode(url: str) -> str:
    m = re.search(r"/(?:reel|reels|p|tv)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else None


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def find_video_url(code: str) -> str:
    endpoints = [
        f"https://www.instagram.com/reel/{code}/embed/captioned/",
        f"https://www.instagram.com/p/{code}/embed/captioned/",
        f"https://www.instagram.com/reel/{code}/embed/",
    ]
    for ep in endpoints:
        try:
            page = fetch(ep)
        except Exception as e:
            continue
        # normalise les échappements JSON puis cherche toute URL .mp4 du CDN
        clean = page.replace("\\u0026", "&").replace("\\/", "/").replace('\\"', '"')
        urls = re.findall(r'https://[^\s"\'<>\\]+\.mp4[^\s"\'<>\\]*', clean)
        cdn = [u for u in urls if "cdninstagram" in u or "fbcdn" in u]
        if cdn:
            return cdn[0]
    return None


def download_mp4(video_url: str, code: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dest = os.path.join(OUTPUT_DIR, f"{code}.mp4")
    req = urllib.request.Request(video_url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
    return dest


def apply_speed_tweak(path: str):
    while True:
        factor = round(random.uniform(0.97, 1.03), 4)
        if abs(factor - 1.0) >= 0.005:
            break
    base, ext = os.path.splitext(path)
    tmp = f"{base}_tmp{ext}"
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
    os.replace(tmp, path)
    print(f"  Vitesse modifiée : {factor:.4f}x")


def main():
    print(f"Téléchargement de {len(URLS)} reels → {OUTPUT_DIR}\n")
    ok, fail = 0, 0
    for i, url in enumerate(URLS, 1):
        code = shortcode(url)
        print(f"[{i}/{len(URLS)}] {code}")
        if not code:
            print("  URL invalide"); fail += 1; continue
        try:
            vurl = find_video_url(code)
            if not vurl:
                print("  Vidéo introuvable dans la page embed"); fail += 1; continue
            path = download_mp4(vurl, code)
            size = os.path.getsize(path) / 1_048_576
            print(f"  Téléchargé : {size:.1f} Mo")
            apply_speed_tweak(path)
            size = os.path.getsize(path) / 1_048_576
            print(f"  Final : {size:.1f} Mo ✓")
            ok += 1
        except Exception as e:
            print(f"  ERREUR : {e}"); fail += 1

    print(f"\nTerminé : {ok} réussi(s), {fail} échoué(s).")
    print(f"Fichiers dans : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
