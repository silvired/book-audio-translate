# PDF to Audio Pipeline

This project converts PDF ebooks to high-quality audio files using advanced Text-to-Speech (TTS) models. The pipeline is fully automated, object-oriented, and supports multiple languages.

## Quick Start (Recommended)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Place your PDF file
- Put your PDF(s) in the `input_book/` folder.

### 3. Run the pipeline
```bash
./run_pipeline.sh
```
- The script will:
  - Detect and use the best available Python version (3.10+ required)
  - Install all required dependencies automatically
  - Run the full object-oriented pipeline:
    - Convert the first PDF in `input_book/` to text using `PDFToText` class
    - Convert the text to audio chunks using `CoquiTTS` class
    - Merge audio chunks into ~30-minute `.wav` files using `MergeAudioChunks` class
    - Clean up temporary files and `__pycache__` folders

## Manual Usage

If you prefer to run manually:

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run the pipeline**:
   ```bash
   python run_pipeline_v4.py
   ```

## Setup Verification

To verify your setup is working correctly:
```bash
python verify_setup.py
```
This will check:
- Python version compatibility
- All required dependencies
- Project structure
- Input files
- Class imports

## Project Structure

```
ebook to audio/
├── input_book/               # Place your PDF files here
├── text_output/              # Temporary text files (auto-cleaned)
├── audio_output/             # Temporary audio chunks (auto-cleaned)
├── merged_audio_output/      # Final merged audio files
├── run_pipeline.sh           # Main shell script (recommended)
├── run_pipeline_v4.py        # Object-oriented Python pipeline
├── book_to_text.py           # PDF to text conversion classes
├── text_to_speech_chunks.py  # Text to speech conversion classes
├── merge_audio_chunks.py     # Audio merging classes
├── requirements.txt          # Python dependencies
├── verify_setup.py           # Setup verification script
├── check_merged_durations.py # Utility: check merged audio durations
```

## Supported Languages

- **English** (default): `tts_models/en/ljspeech/fast_pitch`
- **Italian**: Uses Google TTS (gTTS) for Italian
- **Spanish**: `tts_models/es/css10/vits` (Coqui TTS)

To change the language, edit the `language` field in `config.yaml`:
```yaml
language: es  # for Spanish
language: it  # for Italian  
language: en  # for English
```

## Output

- **Merged audio files**: `merged_audio_output/merged_part_XXX.wav` (~30 min each)
- **Temporary audio chunks**: `audio_output/` (auto-cleaned)
- **Temporary text files**: `convert ebook to text/` (auto-cleaned)

## Utilities

- **Check merged audio durations**:
  ```bash
  python check_merged_durations.py
  ```
  - Reports duration and size of each merged audio file.

## Customization

- **Change language**: Edit the `language` field in `config.yaml`
- **Change chunk size**: Edit the `chunk_size` parameter in `split_text_into_chunks()` in `text_to_speech_chunks.py`
- **Change merged audio duration**: Edit the `target_duration_minutes` field in `config.yaml`
- **Skip lines**: Edit the `skip_lines` field in `config.yaml` to skip header lines

## Requirements

- **Python 3.10 or 3.11** (Python 3.9 is NOT supported due to TTS library compatibility issues)
- Internet connection (for TTS model download)
- Sufficient disk space for audio files

**Important**: The pipeline requires Python 3.10+ to work correctly. Python 3.9 will cause import errors with the TTS library.

## Troubleshooting

- **Python Version**: The pipeline requires Python 3.10+. If you have Python 3.9 or lower, you'll need to upgrade. The shell script will guide you if your Python version is incompatible.
- **TTS Model Download**: The first run will download the TTS model (~150MB).
- **Audio Quality**: Uses high-quality models for each language. Some special characters may be discarded but do not affect audio quality.
- **Import Errors**: If you see "unsupported operand type(s) for |: 'type' and 'NoneType'", this indicates you're using Python 3.9. Upgrade to Python 3.10+.

---

For advanced usage or issues, see the comments in each script. System files like `.DS_Store` can be ignored. 