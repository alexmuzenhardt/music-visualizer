# MP3 Visualizer – White Radial “Spokes” over Background

Renders a white radial bar (“spokes”) audio visualizer synced to an MP3, composited over your background image, and exports a standard H.264 MP4.  
Stack: Python 3.13, MoviePy 2.2.x, no librosa / scipy.

![An image with mountains in the background. In the foreground a white ring with spokes around it showing the music visualization.](./example.gif)

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Run (CMD/PowerShell/macOS/Linux)](#run-cmdpowershellmacoslinux)
- [Configurable Parameters](#configurable-parameters)
- [Tips & Performance](#tips--performance)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [License](#license)

## Requirements

- Python 3.13 (3.12 also fine)
- FFmpeg is handled via imageio-ffmpeg (no manual install needed)
- Modern CPU/GPU recommended — 4K/60fps is compute-heavy

## Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/alexmuzenhardt/music-visualizer.git
   cd music-visualizer
   ```

2. **Create & activate a virtual environment**

   **Windows (CMD/PowerShell):**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

   **macOS / Linux (bash/zsh):**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   python -m pip install --upgrade pip setuptools wheel
   python -m pip install moviepy numpy pillow imageio imageio-ffmpeg
   ```

## Run (CMD/PowerShell/macOS/Linux)

### Minimal usage
```bash
python music_visualizer.py <audiofile.mp3> <background_image> [cover|contain]
```

### Arguments

- `<audiofile.mp3>`: your audio track (MP3, WAV, etc.)
- `<background_image>`: background (JPG/PNG)
- `[cover|contain]` *(optional)*:
    - **cover (default)**: fills the frame, crops edges if needed
    - **contain**: shows the full image, letterboxes with black if needed

### Examples

**Windows**
```bash
python music_visualizer.py song.mp3 background.jpg cover
```

**macOS/Linux**
```bash
python music_visualizer.py song.mp3 background.jpg contain
```

### Output
`output_music_visualizer.mp4` in the repo folder

## Configurable Parameters

All settings live at the top of `music_visualizer.py`. Below are the key ones (current defaults shown).

### Output format
```python
W, H = 3840, 2160   # 4K (use 1920,1080 for Full HD)
FPS  = 60           # 60 fps (use 30 for lighter renders)
OUT_MP4 = "output_music_visualizer.mp4"
```

### Positioning
```python
CENTER = (W // 2, H // 1.5)  # ring center (x, y); y may be float
```

### Ring look (spokes)
```python
BASE_RADIUS   = 100   # radius where spokes start
SPOKES        = 180   # number of spokes (density)
BAR_THICKNESS = 1     # spoke thickness in px
BAR_MIN       = 4     # minimum spoke length
BAR_MAX_EXTRA = 70    # extra outward displacement
BASE_RING_ON  = False # draw a base circle?
BASE_RING_W   = 1     # base circle thickness (only if BASE_RING_ON=True)
```

### Glow (optional)
```python
GLOW_ON     = False  # enable/disable glow
GLOW_STEPS  = 0      # number of overpaint passes (more = wider/stronger)
GLOW_ALPHA  = 80     # starting alpha for glow (0..255)
GLOW_EXPAND = 2      # extra width per glow pass (px)
```

Glow uses wider, lower-alpha overdraw; final spokes render sharp.

### Audio analysis
```python
WINDOW_SEC = 0.10    # analysis window size per frame (seconds)
LOW_HZ     = 30
HIGH_HZ    = 12000
SR         = 44100   # resample rate for analysis
```

### Export settings
```python
video.write_videofile(
    OUT_MP4,
    fps=FPS,
    codec="libx264",
    audio_codec="aac",
    bitrate="35M",      # good for 4K@60; for 1080p@30 try 8–12M
    audio_bitrate="192k",
    preset="medium",
    threads=4
)
```
- **bitrate**: lower for smaller files (with quality tradeoff)
- **preset**: slow → better quality at same bitrate (slower encode)

## Tips & Performance

- For faster previews: 1080p/30, lower bitrate (e.g., 10M)
- Higher `SPOKES` → finer look but more draw calls
- Smoothing to reduce flicker is built-in; for even calmer motion try `WINDOW_SEC = 0.12–0.16`
- `cover` vs `contain`: *cover* is modern (no letterbox), *contain* preserves the full image

## Troubleshooting

### ModuleNotFoundError: No module named 'moviepy'
Virtual env not active or deps missing:
```bash
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
python -m pip install moviepy numpy pillow imageio imageio-ffmpeg
```

### “Requirement already satisfied” but still import errors
You might be using a different interpreter than your venv. Force-install with the active Python:
```bash
python -m pip install --upgrade moviepy
python -c "import sys; print(sys.executable)"
python -c "import moviepy, inspect; print(inspect.getfile(moviepy))"
```

### MoviePy API AttributeError (e.g., set_audio)
This code targets MoviePy 2.2.x and already uses the correct API (`with_audio`). Use the included script as-is.

### Stutters or dropouts
- Lower FPS to 30
- Reduce SPOKES (e.g., 180 → 120)
- Use `preset="slow"` for better compression at the same bitrate

## FAQ

**Why not transparent MP4?**  
H.264/MP4 has no standard alpha channel. For true transparency, export MOV (PNG or ProRes 4444). This project intentionally outputs a widely compatible H.264 MP4 over your chosen background.

**Will CapCut accept the output?**  
Yes. The file is a standard H.264 MP4 with AAC audio.

**Can I use a video background instead of an image?**  
Not in this version. It can be added by using `VideoFileClip` and compositing per frame.

## License

This project contains AI-generated code.  
The author does not claim copyright ownership and provides the code as-is, without any warranty or liability.  
You are free to use, modify, and distribute it at your own discretion and risk.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```