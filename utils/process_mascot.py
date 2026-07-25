import sys
import os
import json
import math
from PIL import Image, ImageOps, ImageChops

def remove_background(img, threshold=240):
    """Converts near-white background to transparent."""
    img = img.convert("RGBA")
    datas = img.getdata()
    
    new_data = []
    for item in datas:
        r, g, b, a = item
        # If pixel is very close to white, make it transparent
        if r >= threshold and g >= threshold and b >= threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append((r, g, b, 255))
            
    img.putdata(new_data)
    return img

def find_cyan_pixels(img):
    """Finds bounding boxes of glowing cyan parts (eyes / reactor) for modifications."""
    datas = img.getdata()
    width, height = img.size
    
    cyan_points = []
    for y in range(height):
        for x in range(width):
            r, g, b, a = datas[y * width + x]
            if a > 0:
                # Cyan check: low red, high green/blue
                if r < 120 and g > 180 and b > 180:
                    cyan_points.append((x, y))
    return cyan_points

def dim_cyan_pixels(img, factor=0.25):
    """Dims glowing cyan pixels to simulate off/sleeping state."""
    img_copy = img.copy()
    datas = img_copy.getdata()
    width, height = img_copy.size
    
    new_data = []
    for item in datas:
        r, g, b, a = item
        if a > 0 and r < 120 and g > 180 and b > 180:
            # Dim the cyan color to dark blue-gray
            new_data.append((int(r * factor), int(g * factor * 1.5), int(b * factor * 2.0), a))
        else:
            new_data.append((r, g, b, a))
            
    img_copy.putdata(new_data)
    return img_copy

def draw_blink_eyes(img, cyan_points):
    """Draws metallic eyelids over cyan eyes for blinking."""
    img_copy = img.copy()
    if not cyan_points:
        return img_copy
        
    # Group points by Y position to find the eyes
    # (Typically eyes are in the upper half of the character bounding box)
    width, height = img_copy.size
    
    # We find the min/max X and Y of the cyan points in the upper half
    upper_cyan = [p for p in cyan_points if p[1] < height * 0.55]
    if not upper_cyan:
        return img_copy
        
    # We can just overwrite these upper cyan pixels with a dark red armor color
    # to simulate closed eyes!
    datas = list(img_copy.getdata())
    for x, y in upper_cyan:
        # Metallic dark red armor color
        datas[y * width + x] = (150, 20, 20, 255)
        
    img_copy.putdata(datas)
    return img_copy

def process_image(src_path, output_dir):
    """Loads, cleans, and animates the generated character into output_dir."""
    print(f"Loading generated mascot image: {src_path}")
    if not os.path.exists(src_path):
        print("Error: Source image not found.")
        return False
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Load and remove background
    raw_img = Image.open(src_path)
    rgba_img = remove_background(raw_img, threshold=240)
    
    # Crop to bounding box of content
    bbox = rgba_img.getbbox()
    if bbox:
        cropped = rgba_img.crop(bbox)
    else:
        cropped = rgba_img
        
    # Resize to fit in a centered 128x128 frame (max size ~84px to prevent clip during animations)
    target_h = 84
    aspect = cropped.width / cropped.height
    target_w = int(target_h * aspect)
    
    base_character = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    # Create final 128x128 centered canvas
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    offset_x = (128 - target_w) // 2
    offset_y = (128 - target_h) // 2 + 10 # lower slightly
    canvas.paste(base_character, (offset_x, offset_y), base_character)
    
    # Find cyan parts
    cyan_points = find_cyan_pixels(canvas)
    
    # Write character.json
    char_config = {
        "name": "Robo Buddy",
        "scale": 1.0,
        "speed": 1.25,
        "greeting": "Systems Online! 🤖 Hello Shiva, ready to code? ⚡",
        "cursorFear": 160,
        "jumpHeight": 130,
        "idleChance": 0.20,
        "voice": True
    }
    with open(os.path.join(output_dir, "character.json"), "w") as f:
        json.dump(char_config, f, indent=2)
        
    # Animations frames definitions
    animations = {
        "idle": 4,
        "walk": 6,
        "run": 6,
        "jump": 6,
        "sleep": 4,
        "wave": 4,
        "happy": 4,
        "thinking": 4,
        "laugh": 4,
        "surprised": 2,
        "caught": 2
    }
    
    for anim_name, num_frames in animations.items():
        anim_dir = os.path.join(output_dir, anim_name)
        os.makedirs(anim_dir, exist_ok=True)
        
        for frame_idx in range(num_frames):
            # Start with base centered character
            frame_img = canvas.copy()
            
            # Setup deformations
            cx, cy = 64, 68
            w, h = 128, 128
            
            if anim_name == "idle":
                # Breathing stretch
                if frame_idx == 1:
                    frame_img = frame_img.resize((128 + 2, 128 - 2), Image.Resampling.BILINEAR).crop((1, -1, 129, 127))
                elif frame_idx == 3:
                    frame_img = frame_img.resize((128 - 2, 128 + 2), Image.Resampling.BILINEAR).crop((-1, 1, 127, 129))
                # Blink
                if frame_idx == 2:
                    frame_img = draw_blink_eyes(frame_img, cyan_points)
                    
            elif anim_name == "walk":
                # Walking bobbing and sway rotation
                bob = -3 if frame_idx % 2 == 1 else 0
                frame_img = ImageChops.offset(frame_img, 0, bob)
                
            elif anim_name == "run":
                # Running faster bob and tilt
                bob = -5 if frame_idx % 2 == 1 else 0
                # Offset Y
                frame_img = ImageChops.offset(frame_img, 0, bob)
                # Skew/rotate slightly forward
                angle = -4 if frame_idx % 2 == 0 else -2
                frame_img = frame_img.rotate(angle, Image.Resampling.BICUBIC, center=(64, 90))
                
            elif anim_name == "jump":
                # Jump stages
                if frame_idx == 0:   # Squish down
                    frame_img = frame_img.resize((128 + 6, 128 - 6), Image.Resampling.BILINEAR).crop((3, -3, 131, 125))
                elif frame_idx == 1: # Stretch launch
                    frame_img = frame_img.resize((128 - 4, 128 + 6), Image.Resampling.BILINEAR).crop((-2, 3, 126, 131))
                    frame_img = ImageChops.offset(frame_img, 0, -8)
                elif frame_idx == 2: # Apex float
                    frame_img = ImageChops.offset(frame_img, 0, -18)
                elif frame_idx == 3: # Fall stretch
                    frame_img = frame_img.resize((128 - 3, 128 + 4), Image.Resampling.BILINEAR).crop((-1, 2, 127, 130))
                    frame_img = ImageChops.offset(frame_img, 0, -6)
                elif frame_idx == 4: # Impact squish
                    frame_img = frame_img.resize((128 + 8, 128 - 8), Image.Resampling.BILINEAR).crop((4, -4, 132, 120))
                elif frame_idx == 5: # Recovery
                    frame_img = frame_img.resize((128 + 2, 128 - 2), Image.Resampling.BILINEAR).crop((1, -1, 129, 127))

            elif anim_name == "sleep":
                # Dim glowing parts and slow breathing
                frame_img = dim_cyan_pixels(frame_img, factor=0.20)
                frame_img = draw_blink_eyes(frame_img, cyan_points)
                # Slow breathing scale
                cycle = int(math.sin((frame_idx / num_frames) * math.pi * 2) * 2)
                frame_img = frame_img.resize((128 + cycle, 128 - cycle), Image.Resampling.BILINEAR).crop((cycle//2, -cycle//2, 128+cycle//2, 128-cycle//2))
                
            elif anim_name == "wave":
                # Sway side-to-side
                angle = 3 if frame_idx % 2 == 1 else -3
                frame_img = frame_img.rotate(angle, Image.Resampling.BICUBIC, center=(64, 90))
                
            elif anim_name == "happy":
                # Bounce bounce
                bob = -6 if frame_idx % 2 == 1 else 0
                frame_img = ImageChops.offset(frame_img, 0, bob)
                
            elif anim_name == "thinking":
                # Tilt head up/side
                frame_img = frame_img.rotate(3, Image.Resampling.BICUBIC, center=(64, 64))
                
            elif anim_name == "laugh":
                # Rapid shake
                dx = 3 if frame_idx % 2 == 1 else -3
                dy = 2 if (frame_idx // 2) % 2 == 1 else -2
                frame_img = ImageChops.offset(frame_img, dx, dy)
                
            elif anim_name == "surprised":
                # Stretch head
                frame_img = frame_img.resize((128 - 2, 128 + 4), Image.Resampling.BILINEAR).crop((-1, 2, 127, 130))
                
            elif anim_name == "caught":
                # Shake and squish
                frame_img = frame_img.resize((128 + 4, 128 - 4), Image.Resampling.BILINEAR).crop((2, -2, 130, 126))
                dx = 2 if frame_idx % 2 == 1 else -2
                frame_img = ImageChops.offset(frame_img, dx, 0)
                
            # Save frame
            frame_img.save(os.path.join(anim_dir, f"{frame_idx}.png"), "PNG")
            
    print("Robo Buddy character pack frames processed successfully!")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_mascot.py <path_to_jpg>")
    else:
        src = sys.argv[1]
        process_image(src, "assets/characters/robobuddy")
