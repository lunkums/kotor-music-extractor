#!/usr/bin/env python3
import re
import shutil
import subprocess
from pathlib import Path
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC


class GameConfig:
    def __init__(self, name: str, composer: str, album: str):
        self.name = name
        self.composer = composer
        self.album = album


KOTOR1_CONFIG = GameConfig(
    "kotor1",
    "Jeremy Soule",
    "Star Wars: Knights of the Old Republic Original Soundtrack",
)

KOTOR2_CONFIG = GameConfig(
    "kotor2",
    "Mark Griskey",
    "Star Wars: Knights of the Old Republic II - The Sith Lords Original Soundtrack",
)


def update_mp3_tags(filepath: str, cover_path: Path, config: GameConfig):
    filename = Path(filepath).stem
    match = re.match(r"(\d+)\s+(.+)", filename)
    if match:
        track_num, title = match.groups()
        try:
            audio = EasyID3(filepath)
        except:
            audio = EasyID3()
            audio.save(filepath)
            audio = EasyID3(filepath)

        audio["title"] = title
        audio["tracknumber"] = track_num
        audio["artist"] = config.composer
        audio["album"] = config.album
        audio.save()

        audio = ID3(filepath)
        with open(cover_path, "rb") as cover_file:
            audio["APIC"] = APIC(
                encoding=3,
                mime="image/png",
                type=3,
                desc="Cover",
                data=cover_file.read(),
            )
        audio.save()


def get_target_subfolder(filename: str, has_been_renamed: bool) -> str:
    if filename.startswith("al_"):
        return "al"
    elif filename.startswith("bed_"):
        return "bed"
    elif filename.startswith("mus_s_"):
        return "mus_s"
    elif filename.startswith("mus_sbat_"):
        return "mus_sbat"
    elif has_been_renamed:
        return "soundtrack"
    else:
        return "other"


def find_xing_offset(filepath: Path) -> int:
    try:
        result = subprocess.run(
            ["grep", "-ab", "-e", "Xing", "-e", "Info", str(filepath)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            offset = int(result.stdout.split(":")[0])
            return offset + 4
        return 58  # Fallback for files without Xing/Info headers
    except Exception:
        return 58  # Fallback if grep fails


def process_kotor2_file(src_path: Path, target_path: Path):
    target_path.parent.mkdir(parents=True, exist_ok=True)

    offset = find_xing_offset(src_path)
    with open(src_path, "rb") as src, open(target_path, "wb") as dest:
        if offset > 4:  # If we found Xing/Info header
            # Write MP3 header
            dest.write(
                bytes.fromhex(
                    "FFFB94640000000000000000000000000000000000000000000000000000000000000000496E666F"
                )
            )
        src.seek(offset)
        while chunk := src.read(10 * 1024 * 1024):
            dest.write(chunk)


def process_kotor1_file(src_path: Path, target_path: Path, skip_bytes: int):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(src_path, "rb") as src, open(target_path, "wb") as dest:
        src.seek(skip_bytes)
        while chunk := src.read(10 * 1024 * 1024):
            dest.write(chunk)


def convert_files(base_path: Path, game_config: GameConfig):
    temp_dir = Path("temp") / game_config.name

    if game_config == KOTOR1_CONFIG:
        mp3_patterns = [
            "[0-5]*.wav",
            "mus_[abt]*.wav",
            "evil_ending.wav",
            "credits.wav",
        ]
        wav_patterns = ["al_*.wav", "mus_loadscreen.wav"]

        for pattern in mp3_patterns:
            for src_path in base_path.glob(pattern):
                target_path = temp_dir / f"{src_path.stem}.mp3"
                print(f"fixing {src_path} -> {target_path}")
                process_kotor1_file(src_path, target_path, 58)

        for pattern in wav_patterns:
            for src_path in base_path.glob(pattern):
                target_path = temp_dir / src_path.name
                print(f"fixing {src_path} -> {target_path}")
                process_kotor1_file(src_path, target_path, 470)
    else:
        for src_path in base_path.glob("*.wav"):
            target_path = temp_dir / f"{src_path.stem}.mp3"
            print(f"fixing {src_path} -> {target_path}")
            process_kotor2_file(src_path, target_path)


def rename_files(game_config: GameConfig, cover_path: Path):
    temp_dir = Path("temp") / game_config.name
    renamed_files = set()

    conversion_file = Path("assets") / f"conversion_{game_config.name}.csv"
    rename_map = {}
    try:
        with open(conversion_file, "r") as f:
            for i, line in enumerate(f, 1):
                old_name, title = line.strip().split(",")
                old_name = Path(old_name).stem
                rename_map[old_name] = (i, title)
    except FileNotFoundError:
        print(f"Warning: {conversion_file} not found, skipping rename step")
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
                update_mp3_tags(str(target_path), cover_path, game_config)

    return renamed_files


def organize_files(game_config: GameConfig, renamed_files: set, cover_path: Path):
    temp_dir = Path("temp") / game_config.name
    output_dir = Path("output")

    for src_path in temp_dir.glob("*"):
        subfolder = get_target_subfolder(src_path.stem, src_path.name in renamed_files)
        target_dir = output_dir / game_config.name / subfolder
        target_dir.mkdir(parents=True, exist_ok=True)

        if "soundtrack" in subfolder:
            shutil.copy2(cover_path, target_dir / "cover.png")

        target_path = target_dir / src_path.name
        print(f"moving {src_path} -> {target_path}")
        shutil.move(str(src_path), str(target_path))


def process_game(game_path: Path, game_config: GameConfig):
    output_folder = Path("output") / game_config.name
    if output_folder.exists():
        shutil.rmtree(output_folder)
    output_folder.mkdir(parents=True)

    cover_path = Path("assets") / f"cover_{game_config.name}.png"
    if not cover_path.exists():
        print(f"Warning: {cover_path} not found in script directory")
        return

    temp_dir = Path("temp") / game_config.name
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nProcessing {game_config.name.upper()}...")
    print("Converting files to temp directory...")
    convert_files(game_path, game_config)

    print("\nRenaming files...")
    renamed_files = rename_files(game_config, cover_path)

    print("\nOrganizing files into output directories...")
    organize_files(game_config, renamed_files, cover_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert and rename audio files from KotOR 1/2"
    )
    parser.add_argument(
        "--kotor1-path",
        help="Path to KotOR 1 streammusic directory",
    )
    parser.add_argument(
        "--kotor2-path",
        help="Path to KotOR 2 streammusic directory",
    )
    args = parser.parse_args()

    if not args.kotor1_path and not args.kotor2_path:
        parser.error("At least one of --kotor1-path or --kotor2-path must be specified")

    if args.kotor1_path:
        process_game(Path(args.kotor1_path), KOTOR1_CONFIG)

    if args.kotor2_path:
        process_game(Path(args.kotor2_path), KOTOR2_CONFIG)

    print("\nCleaning up...")
    shutil.rmtree("temp", ignore_errors=True)


if __name__ == "__main__":
    main()
