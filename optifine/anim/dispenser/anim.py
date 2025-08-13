import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageSequence
import re
import os
import json

BG_DARK = "#1e1e1e"
BG_DARKER = "#181818"
PRIMARY = "#3aa0f3"
TEXT_MAIN = "#d4d4d4"
BORDER_COLOR = "#3a3d41"
FONT = ("JetBrains Mono", 11)

TICKS_PER_SECOND = 20
MS_PER_TICK = 1000 // TICKS_PER_SECOND
TRANSITION_SPEED = 0.5

class SpriteAnimator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sprite Animation Previewer")
        self.configure(bg=BG_DARK)
        self.geometry("950x650")
        self.resizable(False, False)

        self.title_lbl = tk.Label(self, text="Paste .properties data here:", fg=PRIMARY, bg=BG_DARK, font=(FONT[0], 14, "bold"))
        self.title_lbl.pack(pady=(15,5))

        self.textbox = tk.Text(self, font=FONT, bg=BG_DARKER, fg=TEXT_MAIN, insertbackground=TEXT_MAIN,
                              relief="solid", bd=1, highlightthickness=0, height=10)
        self.textbox.pack(fill="both", expand=False, padx=20, pady=(0,10), ipady=10)

        self.btn_frame = tk.Frame(self, bg=BG_DARK)
        self.btn_frame.pack(pady=(0,10))

        self.load_btn = tk.Button(self.btn_frame, text="Load & Play Animation", command=self.load_and_play,
                                  bg=PRIMARY, fg="#e1e9ff", relief="flat", activebackground="#0e639c",
                                  font=(FONT[0], 12, "bold"), cursor="hand2")
        self.load_btn.pack(ipadx=15, ipady=8)

        self.export_btn = tk.Button(self.btn_frame, text="Export Animation as GIF", command=self.export_gif,
                                    bg=PRIMARY, fg="#e1e9ff", relief="flat", activebackground="#0e639c",
                                    font=(FONT[0], 12, "bold"), cursor="hand2", state="disabled")
        self.export_btn.pack(padx=15, ipady=8, pady=(5,0))

        self.export_spritesheet_btn = tk.Button(self.btn_frame, text="Export as Spritesheet", command=self.export_spritesheet,
                                    bg=PRIMARY, fg="#e1e9ff", relief="flat", activebackground="#0e639c",
                                    font=(FONT[0], 12, "bold"), cursor="hand2", state="disabled")
        self.export_spritesheet_btn.pack(padx=15, ipady=8, pady=(5,0))

        self.convert_gif_btn = tk.Button(self.btn_frame, text="Convert GIF to Spritesheet", command=self.convert_gif_to_spritesheet,
                                       bg=PRIMARY, fg="#e1e9ff", relief="flat", activebackground="#0e639c",
                                       font=(FONT[0], 12, "bold"), cursor="hand2")
        self.convert_gif_btn.pack(padx=15, ipady=8, pady=(5,0))

        self.canvas = tk.Canvas(self, width=176, height=77, bg=BG_DARKER, highlightthickness=1, highlightbackground=BORDER_COLOR)
        self.canvas.pack(pady=(0,20))

        self.animating = False
        self.frames = []
        self.frame_sequence = []
        self.frame_durations = []
        self.interpolate = False
        self.current_frame_index = 0
        self.current_frame_start_time = 0
        self.after_id = None
        self.sprite_sheet = None
        self.w = 0
        self.h = 0
        self.canvas_image = None
        self.animation_time = 0

    def parse_properties(self, text):
        props = {}
        lines = text.strip().splitlines()
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if '=' in line:
                key, val = line.split('=',1)
                props[key.strip()] = val.strip()
        return props

    def load_and_play(self):
        if self.animating:
            self.animating = False
            if self.after_id:
                self.after_cancel(self.after_id)
                self.after_id = None
    
        props = self.parse_properties(self.textbox.get("1.0", "end"))
    
        required = ['from', 'x', 'y', 'w', 'h']
        for r in required:
            if r not in props:
                messagebox.showerror("Error", f"Missing required property: {r}")
                return
    
        from_path = props['from']
        if not os.path.isfile(from_path):
            messagebox.showerror("Error", f"File not found: {from_path}")
            return
    
        try:
            self.sprite_sheet = Image.open(from_path).convert("RGBA")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")
            return
    
        try:
            self.w = int(props['w'])
            self.h = int(props['h'])
            self.x = int(props.get('x',0))
            self.y = int(props.get('y',0))
        except ValueError:
            messagebox.showerror("Error", "w, h, x, y must be integers")
            return
    
        self.interpolate = props.get('interpolate', 'false').lower() == 'true'
    
        tile_entries = {}
        duration_entries = {}
        for k, v in props.items():
            if re.match(r'^tile\.\d+$', k):
                idx = int(k.split('.')[1])
                try:
                    tile_entries[idx] = int(v)
                except:
                    messagebox.showerror("Error", f"Invalid tile index value: {v}")
                    return
            elif re.match(r'^duration\.\d+$', k):
                idx = int(k.split('.')[1])
                try:
                    duration_entries[idx] = int(v)
                except:
                    messagebox.showerror("Error", f"Invalid duration value: {v}")
                    return
    
        if not tile_entries:
            total_height = self.sprite_sheet.height - self.y
            total_frames = total_height // self.h
            self.frame_sequence = list(range(total_frames))
            default_duration = int(props.get('duration', '1'))
            self.frame_durations = [default_duration]*len(self.frame_sequence)
        else:
            max_tick = max(tile_entries.keys())
            self.frame_sequence = []
            self.frame_durations = []
            default_duration = int(props.get('duration', '1'))
            for tick in range(max_tick+1):
                frame_num = tile_entries.get(tick)
                if frame_num is None:
                    messagebox.showerror("Error", f"Missing tile.{tick} definition")
                    return
                self.frame_sequence.append(frame_num)
                self.frame_durations.append(duration_entries.get(tick, default_duration))
    
        # Calculate maximum frame index needed
        max_frame_needed = max(self.frame_sequence)
        total_available_frames = (self.sprite_sheet.height - self.y) // self.h
        
        if max_frame_needed >= total_available_frames:
            messagebox.showerror("Error", 
                f"Animation requires frame {max_frame_needed} but only {total_available_frames} frames available\n"
                f"Check your y position ({self.y}) and frame height ({self.h})")
            return
    
        self.frames = []
        for i in range(max_frame_needed + 1):
            box = (self.x, self.y + i*self.h, self.x + self.w, self.y + (i+1)*self.h)
            frame = self.sprite_sheet.crop(box)
            self.frames.append(frame)
    
        self.canvas.config(width=self.w, height=self.h)
        self.current_frame_index = 0
        self.animation_time = 0
        self.animating = True
        self.export_btn.config(state="normal")
        self.export_spritesheet_btn.config(state="normal")
    
        self.animate()
        
            if self.animating:
                self.animating = False
                if self.after_id:
                    self.after_cancel(self.after_id)
                    self.after_id = None
    
            props = self.parse_properties(self.textbox.get("1.0", "end"))
    
            required = ['from', 'x', 'y', 'w', 'h']
            for r in required:
                if r not in props:
                    messagebox.showerror("Error", f"Missing required property: {r}")
                    return
    
            from_path = props['from']
            if not os.path.isfile(from_path):
                messagebox.showerror("Error", f"File not found: {from_path}")
                return
    
            try:
                self.sprite_sheet = Image.open(from_path).convert("RGBA")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load image:\n{e}")
                return
    
            try:
                self.w = int(props['w'])
                self.h = int(props['h'])
                self.x = int(props.get('x',0))
                self.y = int(props.get('y',0))
            except ValueError:
                messagebox.showerror("Error", "w, h, x, y must be integers")
                return
    
            self.interpolate = props.get('interpolate', 'false').lower() == 'true'
    
            tile_entries = {}
            duration_entries = {}
            for k, v in props.items():
                if re.match(r'^tile\.\d+$', k):
                    idx = int(k.split('.')[1])
                    try:
                        tile_entries[idx] = int(v)
                    except:
                        messagebox.showerror("Error", f"Invalid tile index value: {v}")
                        return
                elif re.match(r'^duration\.\d+$', k):
                   idx = int(k.split('.')[1])
                    try:
                        duration_entries[idx] = int(v)
                    except:
                        messagebox.showerror("Error", f"Invalid duration value: {v}")
                        return
    
            if not tile_entries:
                total_height = self.sprite_sheet.height - self.y
                total_frames = total_height // self.h
                self.frame_sequence = list(range(total_frames))
                default_duration = int(props.get('duration', '1'))
                self.frame_durations = [default_duration]*len(self.frame_sequence)
            else:
                max_tick = max(tile_entries.keys())
                self.frame_sequence = []
                self.frame_durations = []
                default_duration = int(props.get('duration', '1'))
                for tick in range(max_tick+1):
                    frame_num = tile_entries.get(tick)
                    if frame_num is None:
                        messagebox.showerror("Error", f"Missing tile.{tick} definition")
                        return
                    self.frame_sequence.append(frame_num)
                    self.frame_durations.append(duration_entries.get(tick, default_duration))
    
           max_frame_index = max(self.frame_sequence)
            self.frames = []
            for i in range(max_frame_index+1):
                box = (self.x, self.y + i*self.h, self.x + self.w, self.y + (i+1)*self.h)
                frame = self.sprite_sheet.crop(box)
                self.frames.append(frame)
    
            self.canvas.config(width=self.w, height=self.h)
            self.current_frame_index = 0
            self.animation_time = 0
            self.animating = True
            self.export_btn.config(state="normal")
            self.export_spritesheet_btn.config(state="normal")
    
            self.animate()
    
        def blend_frames(self, frame1, frame2, alpha):
            return Image.blend(frame1, frame2, alpha)
    
        def animate(self):
            if not self.animating or not self.frames:
                return
    
            total_duration = sum(d * MS_PER_TICK for d in self.frame_durations) / TRANSITION_SPEED
            self.animation_time = (self.animation_time + 15) % total_duration
            
            accumulated_time = 0
            current_frame_idx = 0
            next_frame_idx = 0
            frame_progress = 0
            
            for i, duration in enumerate(self.frame_durations):
                frame_duration_ms = (duration * MS_PER_TICK) / TRANSITION_SPEED
                if accumulated_time + frame_duration_ms > self.animation_time:
                    current_frame_idx = i
                    next_frame_idx = (i + 1) % len(self.frame_sequence)
                    frame_progress = (self.animation_time - accumulated_time) / frame_duration_ms
                    break
                accumulated_time += frame_duration_ms
            
            current_frame_num = self.frame_sequence[current_frame_idx]
            next_frame_num = self.frame_sequence[next_frame_idx]
        
            current_frame = self.frames[current_frame_num]
            next_frame = self.frames[next_frame_num]
        
            blended = self.blend_frames(current_frame, next_frame, frame_progress)
            img = ImageTk.PhotoImage(blended)
        
            self.canvas.image = img
            if self.canvas_image is None:
                self.canvas_image = self.canvas.create_image(0, 0, anchor="nw", image=img)
            else:
                self.canvas.itemconfig(self.canvas_image, image=img)
        
            self.after_id = self.after(15, self.animate)

    def export_gif(self):
        if not self.frames:
            messagebox.showerror("Error", "No animation loaded.")
            return

        filepath = filedialog.asksaveasfilename(defaultextension=".gif",
                                                filetypes=[("GIF files","*.gif")],
                                                title="Save Animation GIF")
        if not filepath:
            return

        export_frames = []
        export_durations = []
        
        total_duration = sum(d * MS_PER_TICK for d in self.frame_durations) / TRANSITION_SPEED
        gif_frame_count = min(100, max(30, int(total_duration // 30)))
        
        for i in range(gif_frame_count):
            progress = i / gif_frame_count
            
            accumulated_time = 0
            current_frame_idx = 0
            next_frame_idx = 0
            frame_progress = 0
            
            for j, duration in enumerate(self.frame_durations):
                frame_duration_ms = (duration * MS_PER_TICK) / TRANSITION_SPEED
                if accumulated_time + frame_duration_ms > progress * total_duration:
                    current_frame_idx = j
                    next_frame_idx = (j + 1) % len(self.frame_sequence)
                    frame_progress = (progress * total_duration - accumulated_time) / frame_duration_ms
                    break
                accumulated_time += frame_duration_ms
            
            current_frame_num = self.frame_sequence[current_frame_idx]
            next_frame_num = self.frame_sequence[next_frame_idx]
            
            current_frame = self.frames[current_frame_num]
            next_frame = self.frames[next_frame_num]
            
            blended = self.blend_frames(current_frame, next_frame, frame_progress)
            export_frames.append(blended.copy())
            export_durations.append(int(total_duration / gif_frame_count))

        try:
            export_frames[0].save(
                filepath,
                save_all=True,
                append_images=export_frames[1:],
                duration=export_durations,
                loop=0,
                disposal=2,
                transparency=0
            )
            messagebox.showinfo("Export Successful", f"GIF saved to:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save GIF:\n{e}")

    def export_spritesheet(self):
        if not self.frames:
            messagebox.showerror("Error", "No animation loaded.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
            title="Save Spritesheet As"
        )
        if not filepath:
            return

        sprite_width = self.w
        sprite_height = self.h
        num_frames = len(self.frames)
        spritesheet = Image.new(
            "RGBA",
            (sprite_width, sprite_height * num_frames)
        )

        for i, frame in enumerate(self.frames):
            spritesheet.paste(frame, (0, i * sprite_height))

        try:
            spritesheet.save(filepath)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save spritesheet:\n{e}")
            return

        base_filename = os.path.splitext(os.path.basename(filepath))[0]
        frames_metadata = []
        
        for i in range(num_frames):
            frames_metadata.append({
                "filename": f"{base_filename}_{i}.png",
                "frame": {
                    "x": 0,
                    "y": i * sprite_height,
                    "w": sprite_width,
                    "h": sprite_height
                },
                "rotated": False,
                "trimmed": False,
                "spriteSourceSize": {
                    "x": 0,
                    "y": 0,
                    "w": sprite_width,
                    "h": sprite_height
                },
                "sourceSize": {
                    "w": sprite_width,
                    "h": sprite_height
                },
                "duration": self.frame_durations[i % len(self.frame_durations)] * MS_PER_TICK
            })

        metadata = {
            "frames": frames_metadata,
            "meta": {
                "app": "Sprite Animation Previewer",
                "version": "1.0",
                "image": os.path.basename(filepath),
                "format": "RGBA8888",
                "size": {
                    "w": sprite_width,
                    "h": sprite_height * num_frames
                },
                "scale": "1",
                "frameTags": [],
                "layers": [
                    {
                        "name": "Layer",
                        "opacity": 255,
                        "blendMode": "normal"
                    }
                ],
                "slices": []
            }
        }

        json_path = os.path.splitext(filepath)[0] + ".json"
        try:
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            messagebox.showinfo(
                "Export Successful",
                f"Spritesheet saved to:\n{filepath}\n\n"
                f"Metadata saved to:\n{json_path}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save metadata:\n{e}")

    def convert_gif_to_spritesheet(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("GIF files", "*.gif")],
            title="Select GIF to Convert"
        )
        if not filepath:
            return

        try:
            gif = Image.open(filepath)
            frames = []
            durations = []
            
            for frame in ImageSequence.Iterator(gif):
                frames.append(frame.copy().convert("RGBA"))
                durations.append(frame.info.get('duration', 100))
            
            if not frames:
                messagebox.showerror("Error", "No frames found in GIF")
                return

            sprite_width = frames[0].width
            sprite_height = frames[0].height
            num_frames = len(frames)

            spritesheet_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")],
                title="Save Spritesheet As"
            )
            if not spritesheet_path:
                return

            spritesheet = Image.new(
                "RGBA",
                (sprite_width, sprite_height * num_frames)
            )

            for i, frame in enumerate(frames):
                spritesheet.paste(frame, (0, i * sprite_height))

            spritesheet.save(spritesheet_path)

            base_filename = os.path.splitext(os.path.basename(spritesheet_path))[0]
            frames_metadata = []
            
            for i in range(num_frames):
                frames_metadata.append({
                    "filename": f"{base_filename}_{i}.png",
                    "frame": {
                        "x": 0,
                        "y": i * sprite_height,
                        "w": sprite_width,
                        "h": sprite_height
                    },
                    "rotated": False,
                    "trimmed": False,
                    "spriteSourceSize": {
                        "x": 0,
                        "y": 0,
                        "w": sprite_width,
                        "h": sprite_height
                    },
                    "sourceSize": {
                        "w": sprite_width,
                        "h": sprite_height
                    },
                    "duration": durations[i]
                })

            metadata = {
                "frames": frames_metadata,
                "meta": {
                    "app": "Sprite Animation Previewer",
                    "version": "1.0",
                    "image": os.path.basename(spritesheet_path),
                    "format": "RGBA8888",
                    "size": {
                        "w": sprite_width,
                        "h": sprite_height * num_frames
                    },
                    "scale": "1",
                    "frameTags": [],
                    "layers": [
                        {
                            "name": "Layer",
                            "opacity": 255,
                            "blendMode": "normal"
                        }
                    ],
                    "slices": []
                }
            }

            json_path = os.path.splitext(spritesheet_path)[0] + ".json"
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            messagebox.showinfo(
                "Conversion Successful",
                f"Spritesheet saved to:\n{spritesheet_path}\n\n"
                f"Metadata saved to:\n{json_path}"
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert GIF:\n{e}")

if __name__ == "__main__":
    app = SpriteAnimator()
    app.mainloop()