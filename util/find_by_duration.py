#!/usr/bin/env python3
from pathlib import Path
from mutagen.mp3 import MP3
import sys


def time_to_seconds(time_str: str) -> float:
    minutes, seconds = map(int, time_str.split(":"))
    return minutes * 60 + seconds


def seconds_to_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes}:{seconds:02d}"


def find_closest_duration(target_duration: str, directory: str) -> tuple[Path, float]:
    target_seconds = time_to_seconds(target_duration)
    print(f"Looking for duration: {target_duration} ({target_seconds}s)")

    closest_file = None
    smallest_diff = float("inf")

    for file_path in Path(directory).glob("*.mp3"):
        try:
            audio = MP3(file_path)
            duration = audio.info.length
            formatted_duration = seconds_to_time(duration)
            print(f"{file_path}: {formatted_duration} ({duration:.2f}s)")

            diff = abs(duration - target_seconds)
            if diff < smallest_diff:
                smallest_diff = diff
                closest_file = file_path
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)

    return closest_file, smallest_diff


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("duration", help="Target duration in MM:SS format")
    parser.add_argument("directory", help="Directory to search")
    args = parser.parse_args()

    closest_file, time_diff = find_closest_duration(args.duration, args.directory)
    if closest_file:
        audio = MP3(closest_file)
        print(f"\nClosest match: {closest_file}")
        print(
            f"Duration: {seconds_to_time(audio.info.length)} ({audio.info.length:.2f}s)"
        )
        print(f"Time difference: {time_diff:.2f} seconds")
    else:
        print("No MP3 files found")


if __name__ == "__main__":
    main()
