import subprocess
import tkinter as tk
from tkinter import messagebox
import threading

def run_pipeline():
    print("Thread started.")
    start_button.config(state=tk.DISABLED)
    try:
        # 1. Run convert_pdf_to_text.py
        status_label.config(text="Running convert_pdf_to_text.py...")
        print("Running convert_pdf_to_text.py...")
        root.update()
        subprocess.run([
            "python3", "convert ebook to text/convert_pdf_to_text.py"
        ], check=True)

        # 2. Run tempo_esecuzione.py
        status_label.config(text="Running tempo_esecuzione.py...")
        print("Running tempo_esecuzione.py...")
        root.update()
        subprocess.run([
            "python3", "convert text to audio/tempo_esecuzione.py"
        ], check=True)

        # 3. Run text_to_audio.py
        status_label.config(text="Running text_to_audio.py...")
        print("Running text_to_audio.py...")
        root.update()
        subprocess.run([
            "python3", "convert text to audio/text_to_audio.py"
        ], check=True)

        status_label.config(text="All steps completed!")
        print("All steps completed!")
        messagebox.showinfo("Done", "All steps completed!")
    except subprocess.CalledProcessError as e:
        status_label.config(text="Error during processing.")
        print(f"An error occurred: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")
    except Exception as ex:
        status_label.config(text="Unexpected error.")
        print(f"Unexpected error: {ex}")
        messagebox.showerror("Error", f"Unexpected error: {ex}")
    finally:
        start_button.config(state=tk.NORMAL)

def on_start():
    print("Start button pressed.")
    threading.Thread(target=run_pipeline).start()

root = tk.Tk()
root.title("Ebook to Audio Converter")
root.geometry("350x150")

start_button = tk.Button(root, text="Start", font=("Arial", 16), command=on_start)
start_button.pack(pady=30)

status_label = tk.Label(root, text="", font=("Arial", 10))
status_label.pack()

root.mainloop() 