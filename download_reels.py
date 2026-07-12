#!/usr/bin/env python3
"""
Lance: python download_reels.py
Nécessite: pip install yt-dlp imageio-ffmpeg
"""

import subprocess
import sys
import os
import random

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = "ffmpeg"

URLS = [
    "https://www.instagram.com/reel/DYrHzAstb8J/?igsh=Y2t2dmEzd3NqbW02",
    "https://www.instagram.com/reel/DYtvjGftqWc/?igsh=amE3eHpyeWZodWgy",
    "https://www.instagram.com/reel/DZYkEdwgeYb/?igsh=bjZ6dGpvbHBpNXBn",
    "https://www.instagram.com/reel/DXg6NabDS1k/?igsh=MWRpYWQwZjV5MHdzMg==",
    "https://www.instagram.com/reel/DXrR0hDDZwg/?igsh=NXpmYXFjcG5vNm9k",
    "https://www.instagram.com/reel/DXAc4v1DShK/?igsh=MXBlMWk1cm5ra2d4dw==",
    "https://www.instagram.com/reel/DXrSYPqjZb0/?igsh=dGJ2ODAxbTlib3Vh",
    "https://www.instagram.com/reel/DX7fx1Ktsn5/?igsh=bzR1aDQxMHZ6NjBm",
    "https://www.instagram.com/reel/DXSWPzYja-7/?igsh=MXFvYXhpd283dzlvdg==",
]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos")


def download(url: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    result = subprocess.run(
        [
            "yt-dlp",
            "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "--output", os.path.join(OUTPUT_DIR, "%(id)s_%(title).40s.%(ext)s"),
            "--print", "after_move:filepath",
            url,
        ],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  ERREUR: {result.stderr.strip()}", file=sys.stderr)
        return None
    path = result.stdout.strip().splitlines()[-1].strip()
    return path


def apply_speed_tweak(input_path: str) -> str:
    while True:
        factor = round(random.uniform(0.97, 1.03), 4)
        if abs(factor - 1.0) >= 0.005:
            break

    base, ext = os.path.splitext(input_path)
    tmp = f"{base}_tmp{ext}"

    cmd = [
        FFMPEG, "-y", "-i", input_path,
        "-filter_complex",
        f"[0:v]setpts={1/factor:.6f}*PTS[v];[0:a]atempo={factor:.6f}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        tmp,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.replace(tmp, input_path)
    print(f"  Vitesse modifiée : {factor:.4f}x")
    return input_path


def main():
    print(f"Téléchargement de {len(URLS)} reels → {OUTPUT_DIR}\n")
    ok, fail = 0, 0
    for i, url in enumerate(URLS, 1):
        print(f"[{i}/{len(URLS)}] {url.split('/reel/')[1][:15]}…")
        path = download(url)
        if not path:
            fail += 1
            continue
        size = os.path.getsize(path) / 1_048_576
        print(f"  Téléchargé : {os.path.basename(path)} ({size:.1f} Mo)")
        apply_speed_tweak(path)
        size = os.path.getsize(path) / 1_048_576
        print(f"  Final : {size:.1f} Mo ✓")
        ok += 1

    print(f"\nTerminé : {ok} réussi(s), {fail} échoué(s).")
    print(f"Fichiers dans : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
