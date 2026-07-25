import json
import os
import math
from PIL import Image, ImageDraw

def create_shadow(draw, cx, cy, rx, ry):
    """Draws a soft drop shadow below the character."""
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(0, 0, 0, 45))

def draw_slime_body(draw, cx, cy, rx, ry, color, anim_name="idle"):
    """Draws a cute, shaded slime body."""
    # Base body
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color)
    
    # Bottom shading (darker blue)
    darker_color = (int(color[0] * 0.8), int(color[1] * 0.8), int(color[2] * 0.9))
    draw.chord([cx - rx + 2, cy - ry + 10, cx + rx - 2, cy + ry - 2], start=0, end=180, fill=darker_color)
    
    # Shiny gloss highlight at top-left
    highlight_color = (255, 255, 255, 130)
    draw.ellipse([cx - rx + rx * 0.3, cy - ry + ry * 0.2, cx - rx + rx * 0.7, cy - ry + ry * 0.5], fill=highlight_color)

def draw_cat_body(draw, cx, cy, rx, ry, color, anim_name="idle"):
    """Draws a cute cat body with ears and tail."""
    # Draw tail
    tail_pts = [
        (cx + rx - 10, cy + ry - 10),
        (cx + rx + 15, cy + ry - 25),
        (cx + rx + 20, cy - ry + 10)
    ]
    draw.line(tail_pts, fill=color, width=12, joint="round")
    
    # Draw ears (triangles)
    ear_color = color
    inner_ear_color = (255, 192, 203) # Pink
    
    # Left Ear
    draw.polygon([
        (cx - rx + 5, cy - ry + 15),
        (cx - rx + 25, cy - ry - 10),
        (cx - rx + 45, cy - ry + 15)
    ], fill=ear_color)
    draw.polygon([
        (cx - rx + 12, cy - ry + 12),
        (cx - rx + 25, cy - ry - 2),
        (cx - rx + 38, cy - ry + 12)
    ], fill=inner_ear_color)
    
    # Right Ear
    draw.polygon([
        (cx + rx - 45, cy - ry + 15),
        (cx + rx - 25, cy - ry - 10),
        (cx + rx - 5, cy - ry + 15)
    ], fill=ear_color)
    draw.polygon([
        (cx + rx - 38, cy - ry + 12),
        (cx + rx - 25, cy - ry - 2),
        (cx + rx - 12, cy - ry + 12)
    ], fill=inner_ear_color)
    
    # Main Body
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color)
    
    # Bottom Shading
    darker_color = (int(color[0] * 0.85), int(color[1] * 0.8), int(color[2] * 0.75))
    draw.chord([cx - rx + 2, cy - ry + 10, cx + rx - 2, cy + ry - 2], start=0, end=180, fill=darker_color)
    
    # Head highlight
    highlight_color = (255, 255, 255, 120)
    draw.ellipse([cx - rx + rx * 0.3, cy - ry + ry * 0.2, cx - rx + rx * 0.6, cy - ry + ry * 0.4], fill=highlight_color)

def draw_ironman_body(draw, cx, cy, rx, ry, color, anim_name="idle"):
    """Draws a cute, circular Iron Man chibi body with gold faceplate and glowing arc reactor."""
    # Draw booster fire if running, jumping, or happy
    if anim_name in ("run", "jump", "happy"):
        flame_y = cy + ry - 4
        # Draw outer orange flame
        draw.polygon([(cx - 10, flame_y), (cx + 10, flame_y), (cx, flame_y + 20)], fill=(255, 69, 0))
        # Draw inner yellow flame
        draw.polygon([(cx - 5, flame_y), (cx + 5, flame_y), (cx, flame_y + 12)], fill=(255, 215, 0))

    # Helmet ear plates (gold/red ear pieces)
    draw.polygon([(cx - rx - 2, cy - 6), (cx - rx + 4, cy - 15), (cx - rx + 4, cy + 6)], fill=(180, 10, 10))
    draw.polygon([(cx + rx + 2, cy - 6), (cx + rx - 4, cy - 15), (cx + rx - 4, cy + 6)], fill=(180, 10, 10))

    # Main red helmet
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color)
    
    # Helmet bottom shading
    darker_red = (int(color[0] * 0.75), int(color[1] * 0.75), int(color[2] * 0.75))
    draw.chord([cx - rx + 2, cy - ry + 12, cx + rx - 2, cy + ry - 2], start=0, end=180, fill=darker_red)

    # Gold faceplate shape
    fpx = cx
    fpy = cy - 2
    f_rx = rx * 0.65
    f_ry = ry * 0.6
    
    faceplate_pts = [
        (fpx - f_rx * 0.7, fpy - f_ry * 0.8),  # Top left
        (fpx + f_rx * 0.7, fpy - f_ry * 0.8),  # Top right
        (fpx + f_rx, fpy - f_ry * 0.2),        # Mid right
        (fpx + f_rx * 0.6, fpy + f_ry * 0.8),  # Bottom right
        (fpx - f_rx * 0.6, fpy + f_ry * 0.8),  # Bottom left
        (fpx - f_rx, fpy - f_ry * 0.2)         # Mid left
    ]
    draw.polygon(faceplate_pts, fill=(255, 215, 0), outline=(180, 130, 0), width=2)

    # Arc Reactor (on chest - bottom of head in chibi style)
    reactor_y = cy + ry * 0.45
    if anim_name == "sleep":
        reactor_fill = (80, 100, 120)
        reactor_outline = (60, 75, 90)
    else:
        reactor_fill = (224, 255, 255)
        reactor_outline = (0, 191, 255)
        
    draw.ellipse([cx - 7, reactor_y - 2, cx + 7, reactor_y + 12], fill=reactor_fill, outline=reactor_outline, width=2)

def draw_face(draw, cx, cy, rx, ry, expression, blink=False, look_dir="center", is_ironman=False):
    """Draws facial expressions based on state flags."""
    if is_ironman:
        # Draw Iron Man face elements
        eye_y = cy - ry * 0.15
        eye_spacing = rx * 0.38
        left_eye_x = cx - eye_spacing
        right_eye_x = cx + eye_spacing
        
        # Eyes glow color
        if expression == "sleep" or blink:
            eye_fill = (90, 80, 0)
            eye_outline = (120, 100, 0)
        else:
            eye_fill = (224, 255, 255)
            eye_outline = (0, 191, 255)
            
        # Draw Left Eye (glowing capsule/trapezoid)
        draw.polygon([
            (left_eye_x - 7, eye_y - 2),
            (left_eye_x + 5, eye_y - 2),
            (left_eye_x + 7, eye_y + 1),
            (left_eye_x - 5, eye_y + 1)
        ], fill=eye_fill, outline=eye_outline)
        
        # Draw Right Eye (mirrored)
        draw.polygon([
            (right_eye_x - 5, eye_y - 2),
            (right_eye_x + 7, eye_y - 2),
            (right_eye_x + 5, eye_y + 1),
            (right_eye_x - 7, eye_y + 1)
        ], fill=eye_fill, outline=eye_outline)
        
        # Draw mouth line (seam on gold faceplate)
        draw.line([(cx - 8, cy + ry * 0.28), (cx + 8, cy + ry * 0.28)], fill=(180, 130, 0), width=2)
        return

    # Eyes position
    eye_y = cy - ry * 0.1
    eye_spacing = rx * 0.45
    left_eye_x = cx - eye_spacing
    right_eye_x = cx + eye_spacing
    
    eye_r = 6
    if expression == "surprised":
        eye_r = 8
    
    # Eye direction offsets
    ox, oy = 0, 0
    if look_dir == "left":
        ox, oy = -4, 0
    elif look_dir == "right":
        ox, oy = 4, 0
    elif look_dir == "up":
        ox, oy = 0, -4
        
    # Draw Eyes
    if blink or expression == "sleep":
        # Closed eyes (lines or arcs)
        draw.arc([left_eye_x - 6, eye_y - 2, left_eye_x + 6, eye_y + 4], start=0, end=180, fill=(40, 40, 40), width=3)
        draw.arc([right_eye_x - 6, eye_y - 2, right_eye_x + 6, eye_y + 4], start=0, end=180, fill=(40, 40, 40), width=3)
    elif expression == "happy":
        # Happy arcs (^ ^)
        draw.arc([left_eye_x - 6, eye_y - 4, left_eye_x + 6, eye_y + 4], start=180, end=360, fill=(40, 40, 40), width=3)
        draw.arc([right_eye_x - 6, eye_y - 4, right_eye_x + 6, eye_y + 4], start=180, end=360, fill=(40, 40, 40), width=3)
    elif expression == "laugh":
        # Closed tight (> <)
        # Left eye >
        draw.line([(left_eye_x - 5, eye_y - 4), (left_eye_x + 2, eye_y), (left_eye_x - 5, eye_y + 4)], fill=(40, 40, 40), width=3)
        # Right eye <
        draw.line([(right_eye_x + 5, eye_y - 4), (right_eye_x - 2, eye_y), (right_eye_x + 5, eye_y + 4)], fill=(40, 40, 40), width=3)
    else:
        # Normal open eyes
        draw.ellipse([left_eye_x - eye_r + ox, eye_y - eye_r + oy, left_eye_x + eye_r + ox, eye_y + eye_r + oy], fill=(40, 40, 40))
        draw.ellipse([right_eye_x - eye_r + ox, eye_y - eye_r + oy, right_eye_x + eye_r + ox, eye_y + eye_r + oy], fill=(40, 40, 40))
        # Pupils reflection
        if expression != "surprised":
            draw.ellipse([left_eye_x - 2 + ox, eye_y - 3 + oy, left_eye_x + ox, eye_y - 1 + oy], fill=(255, 255, 255))
            draw.ellipse([right_eye_x - 2 + ox, eye_y - 3 + oy, right_eye_x + ox, eye_y - 1 + oy], fill=(255, 255, 255))

    # Rosy Cheeks
    cheek_w = 7
    cheek_h = 4
    cheek_y = eye_y + 6
    draw.ellipse([left_eye_x - cheek_w - 4, cheek_y - cheek_h, left_eye_x - 4, cheek_y + cheek_h], fill=(255, 160, 160, 180))
    draw.ellipse([right_eye_x + 4, cheek_y - cheek_h, right_eye_x + cheek_w + 4, cheek_y + cheek_h], fill=(255, 160, 160, 180))

    # Mouth
    mouth_y = cy + ry * 0.15
    if expression == "happy" or expression == "laugh":
        # Big open smile (semi-circle)
        draw.chord([cx - 8, mouth_y - 2, cx + 8, mouth_y + 10], start=0, end=180, fill=(180, 50, 50))
    elif expression == "surprised" or expression == "caught":
        # Small 'O' shape
        draw.ellipse([cx - 4, mouth_y - 2, cx + 4, mouth_y + 6], fill=(50, 30, 30))
    elif expression == "sleep":
        # Silent tiny line or curved smile
        draw.arc([cx - 4, mouth_y - 2, cx + 4, mouth_y + 2], start=0, end=180, fill=(40, 40, 40), width=2)
    elif expression == "thinking":
        # Flat line representing thinking
        draw.line([(cx - 5, mouth_y + 2), (cx + 5, mouth_y + 2)], fill=(40, 40, 40), width=2)
    else:
        # Cute curved line smile
        draw.arc([cx - 6, mouth_y - 4, cx + 6, mouth_y + 4], start=0, end=180, fill=(40, 40, 40), width=2)

def generate_frames(character_name, base_color, char_type="slime"):
    """Generates all animation sequences for a character pack."""
    output_dir = f"assets/characters/{character_name}"
    os.makedirs(output_dir, exist_ok=True)
    
    is_cat = (char_type == "cat")
    is_ironman = (char_type == "ironman")
    
    # Custom configuration adjustments
    greeting = f"Hello Shiva! 👋 Ready to suit up? 🤖" if is_ironman else (f"Hello Shiva! 🐾 Meow!" if is_cat else f"Hello Shiva! 👋 Squish!")
    fear = 170 if is_ironman else (160 if is_cat else 140)
    jump = 135 if is_ironman else (140 if is_cat else 120)
    speed = 1.25 if is_ironman else (1.2 if is_cat else 1.0)
    
    # 1. character.json Config
    char_config = {
        "name": character_name.capitalize() + " Buddy",
        "scale": 1.0,
        "speed": speed,
        "greeting": greeting,
        "cursorFear": fear,
        "jumpHeight": jump,
        "idleChance": 0.15 if is_cat else 0.2,
        "voice": True
    }
    with open(os.path.join(output_dir, "character.json"), "w") as f:
        json.dump(char_config, f, indent=2)

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

    body_drawer = draw_ironman_body if is_ironman else (draw_cat_body if is_cat else draw_slime_body)

    for anim_name, num_frames in animations.items():
        anim_dir = os.path.join(output_dir, anim_name)
        os.makedirs(anim_dir, exist_ok=True)
        
        for frame_idx in range(num_frames):
            img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Physics/Geometry modifiers for animations
            cx, cy = 64, 68
            rx, ry = 30, 26
            look_dir = "center"
            expression = "normal"
            blink = False
            
            # Setup specific frame parameters
            if anim_name == "idle":
                # Breathing and Blinking
                if frame_idx == 1:
                    ry -= 2; rx += 2  # Squished
                elif frame_idx == 3:
                    ry += 2; rx -= 1  # Stretched
                if frame_idx == 2:
                    blink = True
                    
            elif anim_name == "walk":
                # Walking bobbing
                bob = -4 if frame_idx % 2 == 1 else 0
                cy += bob
                rx += (frame_idx % 2 * 2 - 1)
                look_dir = "right" if (frame_idx % 4 < 2) else "left"
                
            elif anim_name == "run":
                # Leaning forward running bobbing
                bob = -6 if frame_idx % 2 == 1 else 0
                cy += bob
                rx += 2; ry -= 1
                look_dir = "right"
                expression = "happy"
                
            elif anim_name == "jump":
                # Sequence of jumping
                if frame_idx == 0:   # Squish prep
                    ry -= 10; rx += 8; cy += 6
                elif frame_idx == 1: # Launch stretch
                    ry += 10; rx -= 6; cy -= 10
                elif frame_idx == 2: # Apex float
                    ry += 2; rx += 2; cy -= 20; expression = "happy"
                elif frame_idx == 3: # Falling stretch
                    ry += 8; rx -= 4; cy -= 5
                elif frame_idx == 4: # Landing squish
                    ry -= 12; rx += 10; cy += 8; expression = "surprised"
                elif frame_idx == 5: # Recovery
                    ry -= 2; rx += 2; cy += 2

            elif anim_name == "sleep":
                expression = "sleep"
                cycle = math.sin((frame_idx / num_frames) * math.pi * 2) * 3
                ry += int(cycle)
                rx -= int(cycle * 0.5)
                
            elif anim_name == "wave":
                expression = "normal"
                if frame_idx % 2 == 1:
                    rx -= 1; ry += 1
                look_dir = "left" if frame_idx % 2 == 0 else "center"
                
            elif anim_name == "happy":
                expression = "happy"
                bob = -8 if frame_idx % 2 == 1 else 0
                cy += bob
                
            elif anim_name == "thinking":
                expression = "thinking"
                look_dir = "up"
                if frame_idx % 2 == 1:
                    cy += 2
                    
            elif anim_name == "laugh":
                expression = "laugh"
                cy += (frame_idx % 2 * 4 - 2)
                
            elif anim_name == "surprised":
                expression = "surprised"
                ry += 4; rx -= 2; cy -= 4
                
            elif anim_name == "caught":
                expression = "caught"
                ry -= 6; rx += 6; cy += 4
            
            # 1. Draw Drop Shadow (does not bob/stretch with body)
            shadow_y = 110
            shadow_rx = rx * 0.9
            if anim_name == "jump":
                if frame_idx == 2: # Apex
                    shadow_rx = rx * 0.6
                elif frame_idx == 4: # Impact
                    shadow_rx = rx * 1.1
            create_shadow(draw, cx, shadow_y, shadow_rx, 7)
            
            # 2. Draw Body
            body_drawer(draw, cx, cy, rx, ry, base_color, anim_name)
            
            # 3. Draw Cat Whiskers if needed
            if is_cat:
                whisker_y = cy + 2
                draw.line([(cx - rx - 2, whisker_y - 2), (cx - rx + 8, whisker_y)], fill=(40, 40, 40), width=2)
                draw.line([(cx - rx - 3, whisker_y + 3), (cx - rx + 8, whisker_y + 1)], fill=(40, 40, 40), width=2)
                draw.line([(cx + rx + 2, whisker_y - 2), (cx + rx - 8, whisker_y)], fill=(40, 40, 40), width=2)
                draw.line([(cx + rx + 3, whisker_y + 3), (cx + rx - 8, whisker_y + 1)], fill=(40, 40, 40), width=2)
                
            # 4. Draw Face
            draw_face(draw, cx, cy, rx, ry, expression, blink, look_dir, is_ironman=is_ironman)
            
            # Save frame
            img.save(os.path.join(anim_dir, f"{frame_idx}.png"), "PNG")

def generate_all_characters():
    # Pastel blue slime
    generate_frames("slime", (135, 206, 250), char_type="slime")
    # Pastel peach cat
    generate_frames("cat", (255, 203, 164), char_type="cat")
    # Chibi Iron Man (Crimson red)
    generate_frames("ironman", (200, 30, 30), char_type="ironman")

if __name__ == "__main__":
    generate_all_characters()
    print("Default characters generated successfully.")
