import os
import threading
import ctypes
from ctypes import wintypes

import tkinter as tk
from tkinter import ttk, messagebox

import keyboard
import mss
import pytesseract
import pyperclip
from PIL import Image

# ---- Gemini (google-genai) ----
from google import genai  # correct import for the new SDK

# ---------- CONFIG ----------
# Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Gemini API key (prefer env var; fallback to hardcoded if you insist)
GEMINI_API_KEY = "AIzaSyA1qfTDeVWhPreQwrd4WOPTfEYkDTOeXcM"
MODEL_NAME = "gemini-2.0-flash"  # fast + capable

# ---------- Windows click-through helpers ----------
import win32gui, win32con, win32api

WS_EX_LAYERED      = 0x00080000
WS_EX_TRANSPARENT  = 0x00000020
WS_EX_TOOLWINDOW   = 0x00000080  # hides from Alt+Tab
GWL_EXSTYLE        = -20
LWA_COLORKEY       = 0x00000001
LWA_ALPHA          = 0x00000002

# ---------- App ----------
class StealthOverlay:
    def __init__(self, root):
        self.root = root
        self.root.title("")  # no title
        self.root.overrideredirect(True)           # frameless
        self.root.attributes("-topmost", True)     # always on top

        # Transparent background via color key (Windows Tk 8.6+)
        self.TRANSPARENT_COLOR = "magenta"
        self.root.configure(bg=self.TRANSPARENT_COLOR)
        try:
            self.root.wm_attributes("-transparentcolor", self.TRANSPARENT_COLOR)
        except tk.TclError:
            # Fallback if not supported (will still be semi-stealth)
            self.root.attributes("-alpha", 0.85)

        # Build UI (use black panels so magenta bg is fully transparent)
        self._build_ui()

        # Make it click-through by default
        self.hwnd = self.root.winfo_id()
        self._apply_click_through(True)

        # Hotkeys
        keyboard.add_hotkey("alt+x", self.capture_and_solve)
        keyboard.add_hotkey("alt+`", self.toggle_click_through)
        keyboard.add_hotkey("esc", self.quit)

        # Gemini client
        self.client = genai.Client(api_key=GEMINI_API_KEY)

        # Position overlay near right edge
        self._place_default()

        self.status("Ready")

    def _build_ui(self):
        style = ttk.Style()
        style.configure("Stealth.TFrame", background="black")
        style.configure("Stealth.TLabel", background="black", foreground="#00FF00", font=("Consolas", 10))
        style.configure("Stealth.TButton", padding=6)

        wrapper = tk.Frame(self.root, bg="black", bd=0, highlightthickness=0)
        wrapper.pack(fill="both", expand=True)

        header = tk.Frame(wrapper, bg="black")
        header.pack(fill="x", padx=8, pady=(6, 4))

        self.status_var = tk.StringVar(value="")
        tk.Label(header, text="Alt+X capture  |  Alt+` toggle  |  Esc quit",
                 fg="#00FF00", bg="black", font=("Consolas", 9, "bold")).pack(side="left")
        tk.Label(header, textvariable=self.status_var,
                 fg="#00FF00", bg="black", font=("Consolas", 9)).pack(side="right")

        # Solution box
        self.text = tk.Text(wrapper,
                            wrap="word",
                            bg="black",
                            fg="#00FF00",
                            insertbackground="#00FF00",
                            relief="flat",
                            font=("Consolas", 10),
                            height=14,
                            width=56)
        self.text.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        # Buttons row
        buttons = tk.Frame(wrapper, bg="black")
        buttons.pack(fill="x", padx=8, pady=(0, 8))

        ttk.Button(buttons, text="Copy", command=self.copy_solution).pack(side="left")
        ttk.Button(buttons, text="Clear", command=lambda: self.text.delete("1.0", tk.END)).pack(side="left", padx=6)

    def _place_default(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = sw - w - 30
        y = int(sh * 0.2)
        self.root.geometry(f"+{x}+{y}")

    def status(self, msg):
        self.status_var.set(msg)
        self.root.update_idletasks()

    # ---- Click-through control ----
    def _apply_click_through(self, enable: bool):
        exstyle = win32gui.GetWindowLong(self.hwnd, GWL_EXSTYLE)
        exstyle |= WS_EX_LAYERED | WS_EX_TOOLWINDOW
        if enable:
            exstyle |= WS_EX_TRANSPARENT
        else:
            exstyle &= ~WS_EX_TRANSPARENT
        win32gui.SetWindowLong(self.hwnd, GWL_EXSTYLE, exstyle)

        # Make magenta fully transparent via colorkey (background only)
        win32gui.SetLayeredWindowAttributes(self.hwnd, win32api.RGB(255, 0, 255), 0, LWA_COLORKEY)

        self.click_through = enable
        self.status("Click-through ON" if enable else "Click-through OFF")

    def toggle_click_through(self):
        self._apply_click_through(not getattr(self, "click_through", True))

    # ---- Main flow ----
    def capture_and_solve(self):
        # Run in background to avoid blocking UI
        threading.Thread(target=self._capture_and_solve_impl, daemon=True).start()

    def _capture_and_solve_impl(self):
        try:
            self.status("Hiding & capturing...")
            # Hide overlay so it never appears in the screenshot
            self.root.withdraw()

            # Capture screen
            with mss.mss() as sct:
                shot = sct.grab(sct.monitors[1])  # primary monitor
                img = Image.frombytes("RGB", shot.size, shot.rgb)

            # OCR
            question_text = pytesseract.image_to_string(img).strip()

            # Bring overlay back
            self.root.deiconify()

            if not question_text:
                self.status("No text found")
                return

            self.status("Calling Gemini...")
            prompt = (
                "Analyze this coding question and respond in EXACTLY this format:\n"
                "1) First line: ONLY the programming language name (e.g., Python, JavaScript, Java)\n"
                "2) Then a complete working code solution with clear comments\n"
                "3) A line with ---\n"
                "4) A short explanation\n\n"
                f"Question:\n{question_text}"
            )

            # Gemini call
            resp = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            solution = getattr(resp, "text", None) or "No response generated."

            # Update UI + copy
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", solution)
            pyperclip.copy(solution)
            self.status("Done (copied)")

        except Exception as e:
            self.root.deiconify()
            self.status("Error")
            messagebox.showerror("Error", str(e))

    def copy_solution(self):
        data = self.text.get("1.0", tk.END).strip()
        if data:
            pyperclip.copy(data)
            self.status("Copied")

    def quit(self):
        self.root.destroy()


if __name__ == "__main__":
    # Sanity checks: fail fast if API key still placeholder
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("[!] Set GOOGLE_API_KEY env var or hardcode GEMINI_API_KEY.")
    root = tk.Tk()
    app = StealthOverlay(root)
    root.mainloop()
