import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import mss
import pytesseract
import pyperclip
from PIL import Image, ImageTk
import os
import google.generativeai as genai
import threading
import keyboard

# Configure Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Configure the Gemini API key
genai.configure(api_key="AIzaSyA1qfTDeVWhPreQwrd4WOPTfEYkDTOeXcM")

# Initialize the model with safety settings
model = genai.GenerativeModel('gemini-2.0-flash', safety_settings=[])

class CodeHelperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📋 CodeClip")
        self.root.geometry("400x300")
        
        # Set window minimum size
        self.root.minsize(300, 200)
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        # Configure grid
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Create widgets
        self.create_widgets()

    def create_widgets(self):
        # Compact header with status and shortcut
        header = ttk.Frame(self.main_frame)
        header.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 5))
        header.columnconfigure(1, weight=1)
        
        # Shortcut label (left side)
        shortcut_label = ttk.Label(
            header, 
            text="Alt+X",
            font=('Arial', 9, 'bold')
        )
        shortcut_label.grid(row=0, column=0, padx=(0, 10))
        
        # Status (right side)
        self.status_var = tk.StringVar(value="Ready 📷")
        self.status_label = ttk.Label(
            header,
            textvariable=self.status_var,
            font=('Arial', 9),
            foreground='#666666'
        )
        self.status_label.grid(row=0, column=1, sticky='e')
        
        # Register shortcut
        keyboard.add_hotkey('alt+x', self.capture_and_solve)
        
        # Solution text area
        self.solution_text = scrolledtext.ScrolledText(
            self.main_frame,
            height=10,
            width=40,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.solution_text.grid(
            row=1, column=0, columnspan=2,
            sticky='nsew',
            pady=(0, 5)
        )
        
        # Copy button (takes full width)
        self.copy_btn = ttk.Button(
            self.main_frame,
            text="📋 Copy",
            command=self.copy_solution
        )
        self.copy_btn.grid(row=2, column=0, columnspan=2, sticky='ew')

    def capture_and_solve(self):
        self.status_var.set("Capturing...")
        self.root.update()
        
        def process():
            try:
                with mss.mss() as sct:
                    # Capture full screen
                    screenshot = sct.grab(sct.monitors[1])
                    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

                    # Extract text via OCR
                    self.status_var.set("Processing...")
                    self.root.update()
                    question_text = pytesseract.image_to_string(img)
                    
                    if not question_text.strip():
                        self.status_var.set("No text found")
                        self.root.after(2000, lambda: self.status_var.set("Ready 📷"))
                        return

                    # Ask Gemini for code solution
                    self.status_var.set("Solving...")
                    self.root.update()
                    
                    prompt = f"Solve this coding problem:\n\n{question_text}"
                    
                    try:
                        response = model.generate_content(
                            contents=[{
                                "parts": [{"text": prompt}]
                            }]
                        )
                        
                        if response and hasattr(response, 'text'):
                            solution = response.text
                        else:
                            solution = "No response generated"

                        # Update solution text
                        self.solution_text.delete('1.0', tk.END)
                        self.solution_text.insert('1.0', solution)
                        self.status_var.set("Done ✓")
                        self.root.after(2000, lambda: self.status_var.set("Ready 📷"))
                        
                    except Exception as api_error:
                        self.status_var.set("API Error")
                        self.root.after(2000, lambda: self.status_var.set("Ready 📷"))
                        messagebox.showerror("Error", str(api_error))
                    
            except Exception as e:
                self.status_var.set("Error")
                self.root.after(2000, lambda: self.status_var.set("Ready 📷"))
                messagebox.showerror("Error", str(e))
        
        # Run in background thread
        thread = threading.Thread(target=process)
        thread.daemon = True
        thread.start()
        
    def copy_solution(self):
        solution = self.solution_text.get('1.0', tk.END)
        if solution.strip():
            pyperclip.copy(solution)
            self.status_var.set("Copied ✓")
            self.root.after(2000, lambda: self.status_var.set("Ready 📷"))
        else:
            self.status_var.set("Nothing to copy")
            self.root.after(2000, lambda: self.status_var.set("Ready 📷"))

if __name__ == "__main__":
    root = tk.Tk()
    app = CodeHelperApp(root)
    root.mainloop()
