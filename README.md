# ✨ Glow Outline Maker

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?style=for-the-badge&logo=opencv)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-UI-darkviolet?style=for-the-badge)

**Glow Outline Maker** is a py desktop app that allows you to apply Glow, Outline, and Neon effects to transparent PNG images.

Dark-themed UI and multithreaded OpenCV rendering.

Vibe-Code Gemini 3.1 Pro

---

## 🚀 Key Features

* **Two Distinct Rendering Modes:**
    * **Classic Mode:** Standard outline and smooth Gaussian glow.
    * **Neon Mode:** Authentic neon tube effect using physical screen-blend calculations (solid core + layered light dispersion).
* **Intelligent Color Mapping:** Choose between custom colors or **Auto Edge** mode, which automatically extracts and diffuses the closest edge colors from your original image.

## 🛠️ Prerequisites

Before running the app, ensure you have Python 3.8 or higher installed. You will need to install the following dependencies:

```bash
pip install opencv-python numpy Pillow customtkinter
```

## 🎮 How to Use

1.  **Clone or download** this repository.
2.  **Run the script** from your terminal:
    ```bash
    python glow_studio.py
    ```
3.  **Workflow:**
    * Click **Load Image (PNG)** to import your image (must have a transparent background / Alpha channel).
    * Select your **Preview Quality** (50% is recommended for a balance of speed and fidelity).
    * Toggle between **Classic** and **Neon** tabs to choose your style.
    * Adjust the **Thickness** and **Glow/Spread** sliders. Changes will render in real-time.
    * Click **Export HD Image** to calculate and save the final image at 100% resolution.


## 📄 License

This project is open-source and available under the [MIT License](LICENSE). Feel free to fork, modify, and use it in your own projects!
