# A Personal Journey in AI Development: Creating Tools I Actually Wanted to Use

As a personal challenge I wanted to explore the capabilities of AI and sharpen my programming skills at the same time. I wanted also to build something meaningful that it would be helpful for myself or someonelse.
Here's are the tools that I found suiting all those needs.


### 🔊 Audio Book Generator 
As a book lover, and like everybody else, having time constrains, i recently got into audiobooks, which I could listen to while doing other stuff, like driving or cooking. I looked for solutions where I could both have the audio and the digital paper version to interchange them, but I'm afraid the only solution is purchause a book two times.
My solution: the audio book generator it converts PDF or EPUB files into natural-sounding audio files, letting you seamlessly switch between reading and listening to the same book—for free.

Technical usage [here](https://github.com/silvired/book-audio-translate/blob/main/audio%20generation/README.md)

### 🌍 Book Translator  
Me and my mother are very much into thriller books, we love to discuss our latest reading and suggest to each other the next one. We are both Italians, and my mom is not enough confortable in english as I am, so I usually read books in english because there are much choice and she in Italian. Countless time I wanted to suggest her a book that I know she would have loved but a professional translation was not provided.
My  solution: the book transaltor, it converts PDF or EPUB files in english into PDF in Italian.

Technical usage [here](https://github.com/silvired/book-audio-translate/blob/main/translation/translation_README.md)
## 🔧 Technical approches

### 🎧Audio Book Generator

I implemented this using **CoquiTTS**, an open-source model that delivers surprisingly natural-sounding narration at zero cost. I've personally converted and listened to several complete books. Currently supports English and Spanish, with Italian in development.

**Current limitations I'm addressing:** The pacing could be improved — it needs better pausing after punctuation for more natural flow. The Italian version still sounds too robotic with CoquiTTS; I experimented with Google's GTTS API, which sounds better, but hit rate limits around 33 chunks (out of 214 in my test book). I'm actively researching alternative models to solve this.

### Book Translator

Unlike the free audio generator, this pipeline requires paid API access. I extensively tested free, open-source models (specifically **MarianMT**), but sentence-level translation fails for full books. You need models with broader context windows to maintain narrative coherence and stylistic consistency.

**Evaluation**

I take quality seriously. For the translation pipeline, I tested five models:

- Gemini 2.5 Flash (thinking and non-thinking modes)
- Qwen-MT-Turbo
- GPT-4o-mini
- DeepSeek V3 (thinking and non-thinking modes)

The testing process involved:

1. Translate 5 pages of a book using each model
2. Use Gemini 2.5 Flash to score translations (1-5) on accuracy, fluency, cultural appropriateness, terminology, and style
3. Conducted human evaluation (native Italian speaker) on the top two performers

**Winner:** **Gemini 2.5 Flash** delivered clear, natural Italian that reads fluently to native speakers. Translation cost: approximately **$0.60 per book** (varies with length)—remarkably cost-effective.

**Room for improvement:** Some terminology could be more precise. Testing more sophisticated models might enhance accuracy, but Gemini strikes an excellent balance between quality and affordability.

