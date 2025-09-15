import os
import glob
from PIL import Image
from apng import APNG
import numpy as np
import imageio
import json

IMAGE_DIR = "a"
SCALE_FACTOR = 1
FRAMES_PER_SECOND = 30
HOLD_DURATION = 1.0
CROSSFADE_DURATION = 0.22
FRAME_W = 16 * SCALE_FACTOR
FRAME_H = None 
MAX_SHEET_H = 600
SHEET_FILENAME = "output.png"
JSON_FILENAME = "output.json"
APNG_FILENAME = "smithing_anim.apng"

def lerp(a, b, t):
    return a + (b - a) * t

def scale_img(img, factor):
    w, h = img.size
    return img.resize((w*factor, h*factor), Image.NEAREST)

def apply_alpha(img, alpha):
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    arr = np.array(img)
    arr[...,3] = (arr[...,3].astype(np.float32) * alpha).astype(np.uint8)
    return Image.fromarray(arr)

def make_frame(img1, img2, alpha1, alpha2):
    base = Image.new("RGBA", img1.size, (0,0,0,0))
    if alpha1 > 0:
        base = Image.alpha_composite(base, apply_alpha(img1, alpha1))
    if alpha2 > 0:
        base = Image.alpha_composite(base, apply_alpha(img2, alpha2))
    return scale_img(base, SCALE_FACTOR)

def generate_apng():
    png_files = sorted(glob.glob(os.path.join(IMAGE_DIR, "*.png")), key=lambda p: int(os.path.splitext(os.path.basename(p))[0]))
    images = [Image.open(p) for p in png_files]
    frames = []
    delays = []
    frame_idx = 0
    num_imgs = len(images)

    for i in range(num_imgs):
        current_img = images[i]
        next_img = images[(i + 1) % num_imgs]

        for _ in range(int(HOLD_DURATION * FRAMES_PER_SECOND)):
            frame = make_frame(current_img, next_img, 1, 0)
            fname = f"apng_frame_{frame_idx}.png"
            frame.save(fname)
            frames.append(fname)
            delays.append(int(1000 / FRAMES_PER_SECOND))
            frame_idx += 1

        for f in range(int(CROSSFADE_DURATION * FRAMES_PER_SECOND)):
            t = f / (int(CROSSFADE_DURATION * FRAMES_PER_SECOND) - 1)
            alpha_current = lerp(1, 0, t)
            alpha_next = lerp(0, 1, t)
            frame = make_frame(current_img, next_img, alpha_current, alpha_next)
            fname = f"apng_frame_{frame_idx}.png"
            frame.save(fname)
            frames.append(fname)
            delays.append(int(1000 / FRAMES_PER_SECOND))
            frame_idx += 1

    apng = APNG()
    for fname, delay in zip(frames, delays):
        apng.append_file(fname, delay=delay)
    apng.save(APNG_FILENAME)
    return frames, delays

def extract_apng_frames(apng_filename):
    reader = imageio.get_reader(apng_filename, format='apng')
    frames = []
    durations = []
    for frame in reader:
        img = Image.fromarray(frame)
        frames.append(img)
        durations.append(int(1000 / FRAMES_PER_SECOND)) 
    FRAME_H = frames[0].height
    return frames, durations, FRAME_H

def compose_spritesheet(frames, frame_w, frame_h, max_sheet_h):
    columns = []
    current_col = []
    current_height = 0
    for idx, frame in enumerate(frames):
        if current_height + frame_h > max_sheet_h and current_col:
            columns.append(current_col)
            current_col = []
            current_height = 0
        current_col.append(frame)
        current_height += frame_h
    if current_col:
        columns.append(current_col)

    sheet_w = frame_w * len(columns)
    sheet_h = max_sheet_h
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0,0,0,0))
    frame_rects = []
    for col_idx, col in enumerate(columns):
        y = 0
        for row_idx, frame in enumerate(col):
            x = col_idx * frame_w
            sheet.paste(frame, (x, y))
            frame_rects.append((x, y, frame_w, frame_h))
            y += frame_h
    return sheet, frame_rects

def make_json(frame_rects, durations, frame_w, frame_h, sheet_w, sheet_h):
    frames_json = []
    for idx, ((x, y, w, h), dur) in enumerate(zip(frame_rects, durations)):
        frames_json.append({
            "filename": f"output.png {idx}.gif",
            "frame": {"x": x, "y": y, "w": w, "h": h},
            "rotated": False,
            "trimmed": False,
            "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h},
            "sourceSize": {"w": w, "h": h},
            "duration": dur
        })
    meta_json = {
        "app": "https://github.com/aseprite/aseprite/releases",
        "version": "1.3.0",
        "image": "output.png",
        "format": "RGBA8888",
        "size": {"w": sheet_w, "h": sheet_h},
        "scale": "1",
        "frameTags": [],
        "layers": [
            {"name": "Layer", "opacity": 255, "blendMode": "normal"}
        ],
        "slices": []
    }
    return {"frames": frames_json, "meta": meta_json}

def cleanup_temp_files(frames):
    for fname in frames:
        if os.path.exists(fname):
            os.remove(fname)

if __name__ == "__main__":
    temp_frame_files, delays = generate_apng()
    frames, durations, FRAME_H = extract_apng_frames(APNG_FILENAME)
    cleanup_temp_files(temp_frame_files)

    sheet, frame_rects = compose_spritesheet(frames, FRAME_W, FRAME_H, MAX_SHEET_H)
    sheet.save(SHEET_FILENAME)
    sheet_w, sheet_h = sheet.size

    ase_json = make_json(frame_rects, durations, FRAME_W, FRAME_H, sheet_w, sheet_h)
    with open(JSON_FILENAME, "w") as f:
        json.dump(ase_json, f, indent=2)

    print(f"Saved spritesheet to {SHEET_FILENAME} and JSON to {JSON_FILENAME}")