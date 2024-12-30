#!/usr/bin/env python3
import re
import shutil
from pathlib import Path
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC


def update_mp3_tags(filepath: str, cover_path: Path):
    filename = Path(filepath).stem
    match = re.match(r"(\d+)\s+(.+)", filename)
    if match:
        track_num, title = match.groups()
        try:
            audio = EasyID3(filepath)
        except:
            audio = EasyID3()
            audio.save(filepath)

        audio["title"] = title
        audio["tracknumber"] = track_num
        audio["artist"] = "Jeremy Soule"
        audio["album"] = "Star Wars: Knights of the Old Republic Original Soundtrack"
        audio.save()

        # Add cover art
        audio = ID3(filepath)
        with open(cover_path, "rb") as cover_file:
            audio["APIC"] = APIC(
                encoding=3,
                mime="image/png",
                type=3,  # Cover (front)
                desc="Cover",
                data=cover_file.read(),
            )
        audio.save()


def get_target_subfolder(filename: str, has_been_renamed: bool) -> str:
    if filename.startswith("al_"):
        return "al"
    elif has_been_renamed:
        return "Star Wars - Knights of the Old Republic"
    else:
        return "other"


def convert_files(base_path: Path):
    temp_dir = Path("temp")
    mp3_patterns = ["[0-5]*.wav", "mus_[abt]*.wav", "evil_ending.wav", "credits.wav"]
    wav_patterns = ["al_*.wav", "mus_loadscreen.wav"]

    for pattern in mp3_patterns:
        for src_path in base_path.glob(pattern):
            target_path = temp_dir / f"{src_path.stem}.mp3"
            print(f"fixing {src_path} -> {target_path}")
            process_file(src_path, target_path, 58)

    for pattern in wav_patterns:
        for src_path in base_path.glob(pattern):
            target_path = temp_dir / src_path.name
            print(f"fixing {src_path} -> {target_path}")
            process_file(src_path, target_path, 470)


def rename_files(cover_path: Path):
    temp_dir = Path("temp")
    renamed_files = set()

    rename_map = {}
    try:
        with open(Path(__file__).parent / "conversion.csv", "r") as f:
            for i, line in enumerate(f, 1):
                old_name, title = line.strip().split(",")
                old_name = Path(old_name).stem
                rename_map[old_name] = (i, title)
    except FileNotFoundError:
        print("Warning: conversion.csv not found, skipping rename step")
        return renamed_files

    for src_path in temp_dir.glob("*"):
        new_data = rename_map.get(src_path.stem)
        if new_data:
            track_num, title = new_data
            new_name = f"{track_num:02d} {title}{src_path.suffix}"
            target_path = temp_dir / new_name
            print(f"renaming {src_path} -> {target_path}")
            src_path.rename(target_path)
            renamed_files.add(target_path.name)

            if target_path.suffix == ".mp3":
                update_mp3_tags(str(target_path), cover_path)

    return renamed_files


def organize_files(renamed_files: set, cover_path: Path):
    temp_dir = Path("temp")
    output_dir = Path("output")

    for src_path in temp_dir.glob("*"):
        subfolder = get_target_subfolder(src_path.stem, src_path.name in renamed_files)
        target_dir = output_dir / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy cover art to KotOR directory
        if subfolder == "Star Wars - Knights of the Old Republic":
            shutil.copy2(cover_path, target_dir / cover_path.name)

        target_path = target_dir / src_path.name
        print(f"moving {src_path} -> {target_path}")
        shutil.move(str(src_path), str(target_path))


def process_file(src_path: Path, target_path: Path, skip_bytes: int):
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with open(src_path, "rb") as src, open(target_path, "wb") as dest:
        src.seek(skip_bytes)
        while chunk := src.read(10 * 1024 * 1024):
            dest.write(chunk)


def main(base_path: str = "."):
    base_path = Path(base_path)
    cover_path = Path(__file__).parent / "cover.png"

    if not cover_path.exists():
        print("Warning: cover.png not found in script directory")
        return

    # Clear output directory if it exists
    output_dir = Path("output")
    if output_dir.exists():
        shutil.rmtree(output_dir)

    print("Step 1: Converting files to temp directory...")
    convert_files(base_path)

    print("\nStep 2: Renaming files...")
    renamed_files = rename_files(cover_path)

    print("\nStep 3: Organizing files into output directories...")
    organize_files(renamed_files, cover_path)

    print("\nStep 4: Cleaning up...")
    Path("temp").rmdir()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert and rename audio files")
    parser.add_argument(
        "--path",
        default=r"C:\Program Files (x86)\Steam\steamapps\common\swkotor\streammusic",
        help="Base path to search for audio files",
    )
    args = parser.parse_args()
    main(args.path)
