# Audio Generation Pipeline

This folder contains the end-to-end tooling that turns a book file into narrated audio in chunked and merged formats. The current pipeline supports English and Spanish voices powered by [Coqui TTS](https://github.com/coqui-ai/TTS); Italian voices are under investigation and **are not available yet**.

## Folder Structure

- `run_pipeline_v4.py` – orchestrates the complete workflow.
- `text_to_speech_chunks.py` – utilities and concrete implementations for Coqui TTS and gTTS.
- `merge_audio_chunks.py` – merges individual audio chunks into longer segments of configurable length.
- `audiobook_config.yaml` – runtime configuration (language, merged file length, test mode).
- `audio_output/` – temporary chunked audio created during synthesis.
- `merged_audio_output/` – final audio files after merging.
- `audio_requirements.txt` & `install_tts.ps1` – dependency helpers, especially for Windows.
- `run_audiobook_pipeline.sh` – bash wrapper that auto-detects Python on macOS/Linux.

## Prerequisites

- Python 3.10 or 3.11 (required by the `TTS` library).
- FFmpeg (required by `moviepy`) – install via your package manager or [ffmpeg.org](https://ffmpeg.org/download.html).
- On Windows, the *Microsoft C++ Build Tools* workload is needed before installing `TTS`. You can obtain it from [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022).
- A GPU is optional; the pipeline auto-detects CUDA and falls back to CPU.

Install Python dependencies once per environment:

```bash
python -m pip install -r "audio generation/audio_requirements.txt"
```

## Preparing Content

1. Visit [Open Library](https://openlibrary.org/) or another legal source to download a book in PDF or EPUB format.
2. Place the file inside the project-level `input_book/` directory.
3. Adjust `audiobook_config.yaml`:
   - `language`: `en` (English) or `es` (Spanish). Other language codes will abort the run.
   - `target_duration_minutes`: length of each merged output file.
   - `test`: set to `true` to skip cleanup so intermediate files remain for inspection.

## Running the Pipeline

From the project root (`book-audio-translate/`):

```bash
python "audio generation/run_pipeline_v4.py"
```

During execution you will be prompted to type the first sentence of the actual story. Everything before that sentence is trimmed to remove front matter.

The pipeline performs the following stages:

1. **Dependency check** – installs `TTS` and `pydub` if missing.
2. **Book to text** – detects PDF/EPUB and converts to a cleaned `.txt` in `text_output/`.
3. **Front-matter trim** – uses your supplied first sentence to cut introductions, tables of contents, etc.
4. **Text to chunks** – splits the text (~5,000 chars each) and synthesizes `chunk_XX.wav` or `.mp3` files in `audio_output/`.
5. **Merge** – combines chunks into ~`target_duration_minutes` files stored in `merged_audio_output/`.
6. **Cleanup** – deletes temporary text/audio files unless `test: true`.

## Output

- Final merged files: `audio generation/merged_audio_output/merged_part_###.wav` (or `.mp3` when chunks are mp3).
- Intermediate chunks: `audio generation/audio_output/chunk_*.wav` (Coqui) or `.mp3` (gTTS) Only available when test configuration is set to true.


## Troubleshooting

- **Model download failures**: ensure you have internet connectivity when the script loads the Coqui model (`tts_models/en/ljspeech/fast_pitch` for English, `tts_models/es/css10/vits` for Spanish).
- **Out of memory**: lower the chunk size inside `text_to_speech_chunks.py` or close other GPU-intensive apps.
- **FFmpeg errors**: confirm `ffmpeg` is installed and available on your `PATH`.
- **Voice quality tweaks**: adjust `skip_lines` directly in `text_to_speech_chunks.py` if you need to bypass front-matter differently; configuration support is planned.

## Roadmap

- Configurable speech rate.
- Simplified handling of the skip-lines logic.
- Additional language voices once validated (Italian remains experimental for now).