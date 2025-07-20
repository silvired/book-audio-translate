# PDF to Audio Pipeline

This project converts PDF ebooks to high-quality audio files using advanced Text-to-Speech (TTS) models. The pipeline is fully automated and supports multiple languages.

## Quick Start (Recommended)

### 1. Place your PDF file
- Put your PDF(s) in the `pdf_input/` folder.

### 2. Run the pipeline
```bash
./run_pipeline.sh
```
- The script will:
  - Detect and use the best available Python version (3.10+ required)
  - Install all required dependencies (`TTS`, `pydub`, `PyPDF2`, `pymupdf`)
  - Run the full pipeline:
    - Convert the first PDF in `pdf_input/` to text
    - Convert the text to audio chunks
    - Merge audio chunks into ~30-minute `.wav` files in `merged_audio_output/`
    - Clean up temporary files

## Manual Usage

If you prefer to run manually:

1. **Install dependencies**:
   ```bash
   pip install TTS pydub PyPDF2 pymupdf
   ```
2. **Run the pipeline**:
   ```bash
   python run_pipeline_v2.py
   ```

## Project Structure

```
ebook to audio/
├── pdf_input/                # Place your PDF files here
├── convert ebook to text/    # Temporary text files
├── audio_output/             # Temporary audio chunks (auto-cleaned)
├── merged_audio_output/      # Final merged audio files
├── run_pipeline.sh           # Main shell script (recommended)
├── run_pipeline_v2.py        # Python pipeline (manual)
├── merge_audio_chunks.py     # Audio merging script
├── check_merged_durations.py # Utility: check merged audio durations
```

## Supported Languages

- **English** (default): `tts_models/en/ljspeech/fast_pitch`
- **Italian**: Change `language = "it"` in `convert text to audio/text_to_audio_v2.py`
- **Spanish**: Change `language = "es"` in `convert text to audio/text_to_audio_v2.py`

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

- **Change language**: Edit the `language` variable in `convert text to audio/text_to_audio_v2.py`.
- **Change chunk size**: Edit the `chunk_size` parameter in `split_text_into_chunks()` in `text_to_audio_v2.py`.
- **Change merged audio duration**: Run `merge_audio_chunks.py` with the `--duration` argument (in minutes):
  ```bash
  python merge_audio_chunks.py --duration 20
  ```

## Requirements

- Python 3.10 or 3.11 (3.9 may work but is not recommended)
- Internet connection (for TTS model download)
- Sufficient disk space for audio files

## Troubleshooting

- **Python Version**: The shell script will guide you if your Python version is incompatible.
- **TTS Model Download**: The first run will download the TTS model (~150MB).
- **Audio Quality**: Uses high-quality models for each language. Some special characters may be discarded but do not affect audio quality.

---

For advanced usage or issues, see the comments in each script. System files like `.DS_Store` can be ignored. 