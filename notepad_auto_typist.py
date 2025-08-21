import os
import time
import threading
import pygetwindow as gw
import pyautogui
import keyboard
import pyperclip
import google.genai as genai

# --- CONFIG ---
GEMINI_API_KEY = "AIzaSyA1qfTDeVWhPreQwrd4WOPTfEYkDTOeXcM"
MODEL_NAME = "gemini-2.5-flash"
TYPE_DELAY = 0.05
FOCUS_PAUSE = 0.15

# --- STATE ---
solution_text = ""
_solution_index = 0
_typing_active = False
_lock = threading.Lock()

def find_notepad_window():
    wins = gw.getWindowsWithTitle("Notepad")
    if not wins:
        wins = [w for w in gw.getAllWindows() if "notepad" in w.title.lower()]
    return wins[0] if wins else None

def bring_to_front(win):
    try:
        if win.isMinimized:
            win.restore()
        win.activate()
    except Exception as e:
        print(f"[!] Error bringing window to front: {e}")
    time.sleep(FOCUS_PAUSE)

def read_notepad_text(win):
    bring_to_front(win)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.1)
    return pyperclip.paste()

def call_gemini(prompt):
    # This function is corrected to fix the syntax error.
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Constructing the payload step-by-step to avoid syntax issues.
        part = {"text": prompt}
        parts_list = [part]
        content_dict = {"parts": parts_list}
        contents_list = [content_dict]
        
        resp = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents_list
        )
        return getattr(resp, "text", "").strip()
    except Exception as e:
        print(f"[!] Gemini API call failed: {e}")
        return ""

def type_solution_worker():
    global _solution_index, _typing_active
    win = find_notepad_window()
    if not win:
        print("[!] Notepad window lost.")
        with _lock:
            _typing_active = False
        return

    bring_to_front(win)

    while True:
        with _lock:
            if not _typing_active or _solution_index >= len(solution_text):
                _typing_active = False
                break
            char_to_type = solution_text[_solution_index]
            _solution_index += 1
        
        pyautogui.typewrite(char_to_type, interval=TYPE_DELAY)

    print("[!] Typing finished.")

def start_or_toggle_typing():
    global solution_text, _solution_index, _typing_active
    with _lock:
        if _typing_active:
            _typing_active = False
            print("[!] Typing paused.")
            return

        if not solution_text or _solution_index >= len(solution_text):
            # --- Start new job ---
            print("[*] No job active. Starting new capture...")
            win = find_notepad_window()
            if not win:
                print("[!] No Notepad window found.")
                return

            question_text = read_notepad_text(win).strip()
            if not question_text:
                print("[!] Notepad is empty.")
                return

            print(f"[*] Captured question: {question_text[:50]}...")
            prompt = (
                "Your task is to be a code generator. You will be given a problem description, "
                "possibly with a hint about the programming language (like 'Apex' or 'JavaScript'). "
                "Your response must be ONLY the code solution for the problem.\n\n"
                "Instructions:\n"
                "1. **Code Only**: Do not write any explanations, comments, or any text that is not code.\n"
                "2. **No Language Name**: Do not state the name of the programming language.\n"
                "3. **Start Directly**: Begin your response immediately with the code.\n"
                "4. **Human-like Style**: The code should be formatted with natural indentation and spacing, as a human would write it.\n"
                "5. **Language Hint**: If the problem mentions a language like 'Apex', prioritize that language. Apex code looks like Java, but it is not Java.\n\n"
                f"Problem:\n{question_text}\n\n"
                "Solution:"
            )
            
            solution_text = call_gemini(prompt)
            if not solution_text:
                print("[!] Failed to get a solution from the API.")
                return

            _solution_index = 0
            bring_to_front(win)
            pyautogui.hotkey('ctrl', 'end')
            pyautogui.typewrite("\n\n---\n\n", interval=0.02)
            print("[*] Solution received. Starting to type...")

        else:
            # --- Resume existing job ---
            print("[*] Resuming typing...")

        _typing_active = True
        threading.Thread(target=type_solution_worker, daemon=True).start()

def main():
    print("Hotkeys: Alt+X -> Start/Pause/Resume | Ctrl+Q -> Quit")
    keyboard.add_hotkey('alt+x', start_or_toggle_typing)
    try:
        keyboard.wait('ctrl+q')
    finally:
        print("\nExiting...")

if __name__ == "__main__":
    main()
