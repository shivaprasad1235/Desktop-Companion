import sys
import os
from PIL import Image

def remove_background(img, threshold=240):
    img = img.convert("RGBA")
    datas = img.getdata()
    
    new_data = []
    for item in datas:
        r, g, b, a = item
        if r >= threshold and g >= threshold and b >= threshold:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append((r, g, b, 255))
            
    img.putdata(new_data)
    return img

def process_spider(src_path, output_path):
    print(f"Processing spider image: {src_path}")
    raw_img = Image.open(src_path)
    rgba = remove_background(raw_img)
    
    bbox = rgba.getbbox()
    if bbox:
        cropped = rgba.crop(bbox)
    else:
        cropped = rgba
        
    target_size = 64
    aspect = cropped.width / cropped.height
    if aspect > 1.0:
        w = target_size
        h = int(target_size / aspect)
    else:
        h = target_size
        w = int(target_size * aspect)
        
    resized = cropped.resize((w, h), Image.Resampling.LANCZOS)
    
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    canvas.paste(resized, ((64 - w) // 2, (64 - h) // 2), resized)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    canvas.save(output_path, "PNG")
    print(f"Saved processed spider to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_spider.py <src_path>")
    else:
        process_spider(sys.argv[1], "assets/characters/spider/spider.png")
