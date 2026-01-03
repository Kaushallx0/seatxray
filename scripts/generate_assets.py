from PIL import Image, ImageOps
import os

def create_box_art(input_path, output_path, size, bg_color="#16191d"):
    # Load input icon
    icon = Image.open(input_path).convert("RGBA")
    
    # Create background
    canvas = Image.new("RGBA", (size, size), bg_color)
    
    # Calculate icon size (e.g., 60% of canvas)
    target_icon_size = int(size * 0.7)
    icon.thumbnail((target_icon_size, target_icon_size), Image.Resampling.LANCZOS)
    
    # Center position
    offset = ((size - icon.width) // 2, (size - icon.height) // 2)
    
    # Paste icon
    canvas.paste(icon, offset, icon)
    
    # Save as PNG (converting to RGB for Store compatibility if needed, but RGBA is usually fine)
    # Store sometimes prefers JPEG/PNG without alpha for some slots, but PNG is safe.
    canvas.convert("RGB").save(output_path, "PNG")
    print(f"Created {output_path}")

input_icon = r"c:\Users\famil\Desktop\SeatXray\seatxray\src\assets\icon.png"
output_dir = r"c:\Users\famil\Desktop\SeatXray\seatxray\build"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

create_box_art(input_icon, os.path.join(output_dir, "Store_BoxArt_1080.png"), 1080)
create_box_art(input_icon, os.path.join(output_dir, "Store_BoxArt_2160.png"), 2160)
create_box_art(input_icon, os.path.join(output_dir, "Store_Logo_300.png"), 300)
