#!/usr/bin/env python3
import ffmpeg
import sys


def get_duration(file_path):
    try:
        probe = ffmpeg.probe(file_path)
        duration = float(probe["format"]["duration"])
        return duration
    except ffmpeg.Error as e:
        print(e.stderr.decode(), file=sys.stderr)
        return None


if __name__ == "__main__":
    duration = get_duration(sys.argv[1])
    if duration:
        print(f"Duration: {duration:.2f} seconds")
