# make_ring_visualizer.py
# Visualizer: white "radiant ring" (radial bars) over a custom background image, exported as MP4 (H.264)
# Compatible with Python 3.13.x, moviepy 2.2.x — no librosa/scipy
# Update: TRUE Glow — wider lines in glow passes + alpha falloff

import sys
import math
import numpy as np
from PIL import Image, ImageDraw

# MoviePy 2.2.x import (with fallback)
try:
    from moviepy import VideoClip, AudioFileClip
except Exception:
    import moviepy.editor as _mpy
    VideoClip = _mpy.VideoClip
    AudioFileClip = _mpy.AudioFileClip

# ========= Configuration =========
W, H       = 3840, 2160     # Target resolution: 4K
FPS        = 60             # Frame rate: 60 fps
CENTER     = (W // 2, H // 2.5)

# Ring appearance
BASE_RADIUS   = 220         # Base radius (px) up to the start of the bars
SPOKES        = 360         # Number of radial bars (evenly distributed over 360°)
BAR_THICKNESS = 2           # Line thickness of bars (px)
BAR_MIN       = 4           # Minimum bar length (px) – ensures something is always visible
BAR_MAX_EXTRA = 70          # Additional length (px) depending on audio level
BASE_RING_ON  = True        # subtle base circle beneath bars
BASE_RING_W   = 1           # Line width of base circle
GLOW_ON       = False       # subtle "glow" (soft) around the bars
GLOW_STEPS    = 0           # number of soft overlay passes
GLOW_ALPHA    = 80          # initial alpha for glow (0..255)
GLOW_EXPAND   = 2           # how much wider per step (extra pixels added to line width)

# Audio analysis
WINDOW_SEC = 0.10           # time window per frame (seconds) for FFT
LOW_HZ     = 30
HIGH_HZ    = 12000
SR         = 44100          # analysis sample rate (ffmpeg resample)

# Output
OUT_MP4    = "ring_on_bg_spokes.mp4"

# ========= CLI =========
if len(sys.argv) < 3:
    print("Verwendung: python make_ring_visualizer.py <audiofile.mp3> <background_image> [cover|contain]")
    sys.exit(1)

AUDIO_PATH = sys.argv[1]
BG_PATH    = sys.argv[2]
FIT_MODE   = (sys.argv[3].lower() if len(sys.argv) >= 4 else "cover")  # "cover" or "contain"

# ========= Audio =========
audio = AudioFileClip(AUDIO_PATH)
duration = float(audio.duration or 0.0)
if duration <= 0.0:
    raise RuntimeError("Audio hat keine Länge.")

# ========= Background =========
def load_and_fit_background(path, w, h, mode="cover"):
    img = Image.open(path).convert("RGB")
    src_w, src_h = img.size
    target_ratio = w / h
    src_ratio = src_w / src_h
    if mode == "contain":
        if src_ratio > target_ratio:
            new_w = w
            new_h = int(round(w / src_ratio))
        else:
            new_h = h
            new_w = int(round(h * src_ratio))
        img_resized = img.resize((new_w, new_h), Image.LANCZOS)
        canvas = Image.new("RGB", (w, h), (0, 0, 0))
        x = (w - new_w) // 2
        y = (h - new_h) // 2
        canvas.paste(img_resized, (x, y))
        return canvas
    else:
        if src_ratio < target_ratio:
            new_h = h
            new_w = int(round(h * src_ratio))
        else:
            new_w = w
            new_h = int(round(w / src_ratio))
        img_resized = img.resize((new_w, new_h), Image.LANCZOS)
        x = (new_w - w) // 2
        y = (new_h - h) // 2
        return img_resized.crop((x, y, x + w, y + h))

BG_BASE = load_and_fit_background(BG_PATH, W, H, FIT_MODE).convert("RGBA")

# ========= Analysis Utils =========
def subclip_compat(clip, start, end):
    if hasattr(clip, "subclip"):
        return clip.subclip(start, end)
    if hasattr(clip, "subclipped"):
        return clip.subclipped(start, end)
    raise AttributeError("Clip hat weder subclip noch subclipped.")

def get_audio_window(t, win_sec=WINDOW_SEC, sr=SR):
    start = max(0.0, t - win_sec / 2)
    end   = min(duration, t + win_sec / 2)
    if end <= start:
        end = min(duration, start + max(1.0 / FPS, 0.01))
    sub = subclip_compat(audio, start, end)
    arr = sub.to_soundarray(fps=sr)
    if arr.ndim == 2:
        arr = arr.mean(axis=1)
    n = len(arr)
    if n == 0:
        return np.zeros(int(sr * win_sec), dtype=np.float32)
    win = np.hanning(n).astype(np.float32)
    return (arr.astype(np.float32) * win)

def fft_magnitude(sig, sr=SR):
    n = len(sig)
    if n <= 1:
        return np.array([0.0], dtype=np.float32), np.array([0.0], dtype=np.float32)
    spec = np.fft.rfft(sig)
    mags = np.abs(spec).astype(np.float32)
    freqs = np.fft.rfftfreq(n, d=1.0 / sr).astype(np.float32)
    return freqs, mags

def compute_band_edges(sr=SR, low=LOW_HZ, high=HIGH_HZ, bands=SPOKES):
    nyq = sr / 2.0
    hi  = float(min(high, nyq - 1.0))
    lo  = float(max(1.0, min(low, hi - 1.0)))
    if hi <= lo:
        hi = lo + 1.0
    return np.geomspace(lo, hi, bands + 1).astype(np.float32)

BAND_EDGES = compute_band_edges()

def spectrum_to_bands(freqs, mags, edges=BAND_EDGES):
    bands = len(edges) - 1
    out = np.zeros(bands, dtype=np.float32)
    mask = (freqs >= edges[0]) & (freqs <= edges[-1])
    if not np.any(mask):
        return out
    f = freqs[mask]; m = mags[mask]
    idx = np.searchsorted(edges, f, side="right") - 1
    idx = np.clip(idx, 0, bands - 1)
    np.add.at(out, idx, m)
    out = np.log1p(out)
    # Smoothing: slightly wider window to prevent "flickering" spokes
    if bands >= 9:
        k = 9
        pad = k // 2
        kernel = np.ones(k, dtype=np.float32) / k
        padded = np.pad(out, (pad, pad), mode="edge")
        out = np.convolve(padded, kernel, mode="same")[pad:-pad].astype(np.float32)
    mx = out.max()
    if mx > 1e-8:
        out /= mx
    return out

# ========= Render Logic (Spokes) =========
def draw_spokes(draw: ImageDraw.ImageDraw, levels: np.ndarray, color=(255,255,255,255), width: int = None):
    w = int(max(1, (BAR_THICKNESS if width is None else width)))
    cx, cy = CENTER
    thetas = np.linspace(0.0, 2.0 * math.pi, len(levels), endpoint=False, dtype=np.float32)
    heights = BAR_MIN + BAR_MAX_EXTRA * (np.clip(levels, 0, 1) ** 0.9)

    for theta, h in zip(thetas, heights):
        x0 = cx + BASE_RADIUS * math.cos(theta)
        y0 = cy + BASE_RADIUS * math.sin(theta)
        x1 = cx + (BASE_RADIUS + float(h)) * math.cos(theta)
        y1 = cy + (BASE_RADIUS + float(h)) * math.sin(theta)
        draw.line([(x0, y0), (x1, y1)], fill=color, width=w)

def make_frame_rgb(t):
    # Audio → FFT → bands
    sig = get_audio_window(t, WINDOW_SEC, SR)
    freqs, mags = fft_magnitude(sig, SR)
    levels = spectrum_to_bands(freqs, mags, BAND_EDGES)

    # Copy background (RGBA)
    frame = BG_BASE.copy()
    d = ImageDraw.Draw(frame, "RGBA")

    # Base circle (subtle)
    if BASE_RING_ON and BASE_RING_W > 0:
        d.ellipse(
            [CENTER[0] - BASE_RADIUS, CENTER[1] - BASE_RADIUS,
             CENTER[0] + BASE_RADIUS, CENTER[1] + BASE_RADIUS],
            outline=(255, 255, 255, 160), width=BASE_RING_W
        )

    # ---- Glow: true width + alpha falloff ----
    if GLOW_ON and GLOW_STEPS > 0:
        for i in range(1, GLOW_STEPS + 1):
            # From outside to inside: more width, less alpha
            width = BAR_THICKNESS + i * GLOW_EXPAND
            alpha = max(0, int(GLOW_ALPHA * (1.0 - (i - 1) / max(1, GLOW_STEPS))))
            draw_spokes(d, levels, color=(255, 255, 255, alpha), width=width)

    # Sharp, final spokes
    draw_spokes(d, levels, color=(255, 255, 255, 255), width=BAR_THICKNESS)

    return np.array(frame.convert("RGB"), dtype=np.uint8)

# ========= Clip & Export =========
video = VideoClip(make_frame_rgb, duration=duration).with_audio(audio)

video.write_videofile(
    OUT_MP4,
    fps=FPS,
    codec="libx264",
    audio_codec="aac",
    bitrate="12M",
    audio_bitrate="192k",
    preset="medium",
    threads=4
)

print(f"\nFinish: {OUT_MP4}\n")
