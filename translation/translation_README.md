# Translation Pipeline

This folder contains the end-to-end pipeline that turns an input book in english into a translated PDF in italian, using `gemini-2.5-flash`. The process orchestrates text extraction, sentence segmentation, translation, and document generation with a focus on reproducibility and cost awareness.

## Workflow Overview

- **Book to Text** (`BookToText`): Locates the first PDF/EPUB in `input_book/`, converts it to plain text, and trims the output from a user-provided opening sentence.
- **Sentence Segmentation** (`SentenceSegmenter`): Splits the extracted text into paragraph-preserving JSON stored under `translation/segmented_text/`.
- **Chunk Planning** (`ChunkMapper`): Groups paragraphs into API-friendly chunks while staying within the model’s token limits.
- **Translation** (`BookTranslator` + `Translator`): Sends each chunk to `gemini-2.5-flash`, producing translated text files in `translation/translated_text/`.
- **PDF Generation** (`TextToPDFConverter`): Builds a printable PDF from the translated text inside `translation/pdf_output/`.

## Usage

Run the full pipeline from the project root:

```
python -m translation.run_translation_pipeline
```

During execution you will be prompted for the first sentence of the book so the extractor can trim down unnecessary book introduction.

## Configuration

- `translation/models_info.yaml` stores the `gemini-2.5-flash` token limits and on-demand pricing in USD per million tokens. Adjust values here whenever Google updates rates.
- Output folders (`text_output/`, `translation/segmented_text/`, `translation/translated_text/`, `translation/pdf_output/`) are created automatically if they do not exist.

## Cost Estimation

Run the estimator directly:

```
python -m translation.book_cost_estimator
```

The script now auto-detects the first supported book in `input_book/`, converts it to text (or copies an existing `.txt`), segments it, and then computes token + dollar totals for every pricing profile in `models_info.yaml`. Behind the scenes it chains `BookToText`, `SentenceSegmenter`, `TokenCounter`, `ChunkMapper`, and `CostCalculator`, so you always get a fresh forecast without touching any file paths.

This pre-flight step lets you gauge API spend before launching the full translation pipeline and compare configurations such as Gemini vs. DeepSeek, standard vs. batch pricing, or thinking vs. no-thinking settings.

