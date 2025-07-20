#il tempo di esecuzione dello script è lineare rispetto an numero dei caratteri.
# Per ogni 100 caratteri ci vuole un secondo.

import os

# Remove FILE_NAME and update get_first_txt_file to search in the correct folder
def get_first_txt_file(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.txt'):
            return os.path.join(folder_path, filename)
    return None

def main():
    folder_path = os.path.dirname(os.path.abspath(__file__))
    txt_file = get_first_txt_file(folder_path)
    if not txt_file:
        print("No .txt file found in the directory.")
        return

    try:
        with open(txt_file, 'r', encoding='utf-8') as file:
            text = file.read()
    except UnicodeDecodeError:
        with open(txt_file, 'r', encoding='latin-1') as file:
            text = file.read()

    num_characters = len(text)
    seconds = num_characters / 100
    minutes = seconds / 60
    hours = minutes / 60

    print(f"File: {txt_file}")
    print(f"Number of characters: {num_characters}")
    print(f"Estimated time: {seconds} seconds")
    print(f"Estimated time: {minutes:.2f} minutes")
    print(f"Estimated time: {hours:.2f} hours")

if __name__ == "__main__":
    main()

