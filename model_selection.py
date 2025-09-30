import time
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


texts_to_translate = [
    "not so long ago, a monster came to the small town of Castle Rock, Maine.",
    "He killed a waitress named Alma Frechette in 1970; a woman named Pauline Toothaker and a junior high school student named Cheryl Moody in 1971; a pretty girl named Carol Dunbarger in 1974; a teacher named Etta Ringgold in the fall of 1975; finally, a grade-schooler named Mary Kate Hendrasen in the early winter of that same year.",
    "He was not werewolf, vampire, ghoul, or unnameable creature from the enchanted forest or from the snowy wastes; he was only a cop named Frank Dodd with mental and sexual problems.",
    "A good man named John Smith uncovered his name by a kind of magic, but before he could be captured—perhaps it was just as well—Frank Dodd killed himself."
]

models_to_test = [
    "Anhptp/opus-mt-en-it-BDS-G1", 
    "Helsinki-NLP/opus-mt-en-it",
    "callmyname/marian-finetuned-kde4-en-to-it", 
    "Nextcloud-AI/opus-mt-en-it"
]


for model in models_to_test:
    start_time = time.time()
    tokenizer = AutoTokenizer.from_pretrained(model)
    model = AutoModelForSeq2SeqLM.from_pretrained(model)
    end_time = time.time()
    print(f"Model {model} loaded in {end_time - start_time} seconds")
    for i, text in enumerate(texts_to_translate):
        start_time = time.time()
        translated_text = tokenizer.encode(text, return_tensors="pt")
        translated_text = model.generate(translated_text)
        translation = tokenizer.decode(translated_text[0], skip_special_tokens=True)
        end_time = time.time()
        print(f"Translation {i+1} took {end_time - start_time} seconds")
        print(translation)
