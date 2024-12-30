# KotOR Music Extractor

Extracts and processes music files from Star Wars: Knights of the Old Republic, converting them to properly tagged MP3 files.

## Requirements

- Python 3.6+
- `mutagen` library for MP3 tagging

Install dependencies:

```bash
pip install mutagen
```

## Files Needed

- `extract.py`: Main script
- `conversion.csv`: Mapping of original filenames to track titles
- `cover.png`: Album artwork

### conversion.csv format

```
original_filename,track_title
mus_theme_rep,The Old Republic
```

NOTE: The order of the tracks in `conversion.csv` determines the track numbers.

## Usage

1. Default usage (assumes Steam installation):

```bash
python extract.py
```

2. Custom path:

```bash
python extract.py --path "/path/to/kotor_install"
```

## Output

Creates an `output` directory with three subfolders:

- `Star Wars - Knights of the Old Republic/`: Tagged MP3s with track numbers
- `al/`: Ambient and location audio
- `other/`: Other audio files (cutscene audio files, I believe)

## Features

- Converts KotOR audio files to MP3
- Adds ID3 tags (title, track number, artist, album)
- Embeds album artwork
