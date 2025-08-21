# Notepad Auto Typist

A Python script that automates typing AI-generated code into Notepad with human-like speed and style.

## Features

*   **Question Capture**: Reads coding problems directly from Notepad.
*   **AI Code Generation**: Utilizes the Google Gemini API to generate code solutions.
*   **Human-like Typing**: Types the generated code into Notepad with configurable speed and random delays.
*   **Pause/Resume Functionality**: Allows pausing and resuming the typing process.
*   **Global Hotkeys**: Operates in the background, listening for hotkey commands.

## Installation

1.  **Clone the Repository (or download the files)**:

    ```bash
    git clone https://github.com/S4ndiipSuryarao/ClipPad.git
    cd ClipPad
    ```

2.  **Install Dependencies**:

    It's recommended to use a virtual environment.

    ```bash
    pip install -r requirements.txt
    ```

    This will install necessary libraries including `pygetwindow`, `pyautogui`, `keyboard`, `pyperclip`, and `google-generativeai`.

## Configuration

Open `notepad_auto_typist.py` in a text editor to configure the following:

*   **`GEMINI_API_KEY`**: Replace `"YOUR_API_KEY"` with your actual Google Gemini API Key.

    ```python
    GEMINI_API_KEY = "YOUR_API_KEY" # Replace with your key
    ```

*   **`MODEL_NAME`**: The Gemini model to use for code generation. Currently set to `"gemini-2.5-flash"`.

    ```python
    MODEL_NAME = "gemini-2.5-flash"
    ```

*   **`TYPE_DELAY`**: The delay (in seconds) between typing each character. Adjust this to control the typing speed.

    ```python
    TYPE_DELAY = 0.05 # Adjust for desired typing speed
    ```

## Usage

1.  **Run the Script**:

    Open your command prompt or terminal, navigate to the project directory, and run:

    ```bash
    python notepad_auto_typist.py
    ```

    The script will start running in the background and listen for hotkeys.

2.  **Global Hotkeys**:

    *   **`Alt+X`**: This hotkey acts as a toggle:
        *   **Start**: If no typing job is active, it will capture the question from Notepad, send it to Gemini, and start typing the solution.
        *   **Pause**: If typing is in progress, it will pause the typing.
        *   **Resume**: If typing is paused, it will resume from where it left off.

    *   **`Ctrl+Q`**: Press this hotkey to gracefully exit the script.

3.  **Running in Background (Windows)**:

    For a seamless experience, you can run the script silently in the background without a visible console window. A `launcher.vbs` file is provided for this purpose.

    *   Double-click `launcher.vbs` in your project directory.
    *   To make it run automatically on startup, create a shortcut to `launcher.vbs` and place it in your Windows Startup folder (`shell:startup`).

## Troubleshooting

*   **`Notepad not found`**: Ensure Notepad is open and active when you press `Alt+X`.
*   **`Gemini API call failed`**: Check your `GEMINI_API_KEY` in `notepad_auto_typist.py`. Ensure it's correct and you have an active internet connection. The model might also be temporarily overloaded; try again later.
*   **Syntax Errors**: If you encounter syntax errors after modifying the script, double-check your changes carefully.

