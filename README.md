# Desktop Buddy AI & Spider Mascot 🤖🕷️

A lightweight, premium Windows desktop companion that floats directly on top of your windows. It features a customizable chibi mascot (Robo Buddy) running on a deterministic state machine and a wobbly, elastic desktop spider toy with physics-based spring mechanics.

---

## ✨ Key Features

### 1. Transparent Floating Chibi Mascot (Robo Buddy)
*   **True Transparency**: Resizes exactly to the sprite box bounds. Clicking outside the mascot passes clicks to background applications, while clicking directly on the mascot triggers interaction.
*   **Cute Original Chibi Art**: Metallic red-and-gold futuristic robot body, glowing cyan visor eyes, and circular chest reactor.
*   **Blinking & Sleeping Visors**: Visor automatically closes during random blinks and dims by 80% during system idle sleep states.

### 2. Interaction Modes
*   **Normal Mode**: Mascot wanders freely across the entire desktop, floating above windows and periodically saying friendly comments.
*   **Catch Evasion Mode**: Moves away from the cursor when close. To keep him talkative, he displays cheeky comments (e.g. *"Too slow!"*, *"Hehe!"*, *"Nope! 😂"*) randomly every 2 to 3 seconds during chases.
*   **CTRL Capture Mode**: Holding the `CTRL` key disables his evasion. Moving your mouse over him captures him. He attaches to the cursor, swaying and bobbing playfully under your mouse as you carry him.
*   **Release & Recovery**: Releasing `CTRL` drops him. He plays a landing impact dust cloud and boing sound, locks in a squished `"surprised"` pose for 0.8 seconds, and then automatically returns to normal AI evasion.
*   **Move Mode**: Double-clicking him enables a full-screen click catcher. Click anywhere on the screen, and he runs/walks to the location and cancels early if he hits a boundary.

### 3. Desktop Spider Toy
*   **Wobbly Curving Web**: A cartoon spider hangs from a silk thread in the top-right corner. The web curves dynamically based on gravity and movement velocity.
*   **Tension Vibrations**: Pulling the spider adds high-frequency transverse vibrations (shaking waves) to the web.
*   **Squash & Stretch**: The spider body stretches along the pull direction (up to 1.28x) and squashes perpendicular to it under tension.
*   **Hooke's Law spring physics**: Stretches with progressive quadratic resistance up to a hard clamp of 330px. Releasing it launches it back, overshooting and oscillating before settling.
*   **99% Click-Through**: Window hit mask is restricted strictly to the spider body and thread, letting you click on background browser tabs or icons underneath the web.

---

## 🛠️ Architecture

*   **Deterministic State Machine**: Replaced the behavior tree with an explicit 7-State Engine (`Startup`, `Idle`, `Wander`, `Escape`, `Capture`, `Release`, `MoveMode`) ensuring exactly one behavior executes at any millisecond.
*   **2-Second Stuck Failsafe**: Monitors mascot velocity. If the mascot is trying to move but speed drops under 10px/s for > 2.0 seconds, the failsafe aborts targets, halts velocity, and resets to `Idle` (waiting 0.5s before choosing a new path).
*   **SQLite User Settings**: Stores settings like character size, opacity, mute state, and movement speed in a local database (`settings.db`).

---

## 🚀 Getting Started

### Prerequisites
*   Python 3.8+
*   Dependencies listed in `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Companion
To run the companion in the background without terminal windows, double-click the **`run.bat`** file in the project folder:
```batch
@echo off
start pythonw main.py
```
This launches the mascot directly into the Windows background. It stays active even after closing your IDE or terminal.

### Controlling the Companion
*   **Drag Mode**: Hold `CTRL` and double-click the buddy to make him draggable manually without mouse evasion.
*   **Context Menu**: Right-click the buddy (or tray icon) to open settings, mute sound effects, change active character packs, or **Exit** the application.

---

## 📂 File Structure

*   `main.py`: Launcher bootstrapper and window instantiations.
*   `run.bat`: Background silent launcher.
*   `engine/game_loop.py`: 60 FPS tick cycle and 7-State Machine logic.
*   `ui/buddy_window.py`: Mascot transparent widget canvas and mouse interactions.
*   `ui/spider_window.py`: Web spring physics calculations, masking, and paint renders.
*   `ui/speech_bubble.py`: Standalone transparent overlay speech bubbles.
*   `physics/physics_engine.py`: 2D gravity, drag, velocity easing, and boundary clamps.
