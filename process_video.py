#!/usr/bin/env python3
"""
Télécharge une vidéo en très haute qualité et applique
une légère modification aléatoire de vitesse (±1–3%).
"""

import subprocess
import sys
import os
import random
import re
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "videos")


def download(url: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    result = subprocess.run(
        [
            "yt-dlp",
            "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "--output", os.path.join(OUTPUT_DIR, "%(title)s.%(ext)s"),
            "--print", "after_move:filepath",
            url,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    # last non-empty line is the final file path
    path = result.stdout.strip().splitlines()[-1].strip()
    return path


def apply_speed_tweak(input_path: str) -> str:
    # Random speed factor between 0.97 and 1.03 (±3%), never exactly 1.0
    while True:
        factor = round(random.uniform(0.97, 1.03), 4)
        if abs(factor - 1.0) >= 0.005:
            break

    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_mod{ext}"

    # atempo only accepts [0.5, 2.0], but our range is well inside that
    cmd = [
        FFMPEG, "-y",
        "-i", input_path,
        "-filter_complex", f"[0:v]setpts={1/factor:.6f}*PTS[v];[0:a]atempo={factor:.6f}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        output_path,
    ]
    print(f"Applying speed factor {factor:.4f}x …")
    subprocess.run(cmd, check=True)

    os.remove(input_path)
    os.rename(output_path, input_path)
    return input_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python process_video.py <URL> [URL …]")
        sys.exit(1)

    for url in sys.argv[1:]:
        print(f"\n=== Téléchargement : {url} ===")
        path = download(url)
        size_mb = os.path.getsize(path) / 1_048_576
        print(f"Téléchargé : {path} ({size_mb:.1f} Mo)")

        print("Application de la modification de vitesse …")
        path = apply_speed_tweak(path)
        size_mb = os.path.getsize(path) / 1_048_576
        print(f"Fichier final : {path} ({size_mb:.1f} Mo)")


if __name__ == "__main__":
    main()
