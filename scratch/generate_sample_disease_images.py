import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def generate_sample_disease_images():
    base_dir = os.path.join("Dataset", "Fish_Disease", "images")
    train_dir = os.path.join(base_dir, "train")
    val_dir = os.path.join(base_dir, "val")

    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(val_dir, exist_ok=True)

    classes = [
        ("0_healthy_shrimp", (30, 140, 180), "Healthy Shrimp Specimen"),
        ("1_wssv_white_spot", (180, 50, 50), "WSSV White Spot Lesions"),
        ("2_ehp_stunted", (160, 120, 40), "EHP Stunted Shrimp Specimen"),
        ("3_vibrio_lesion", (140, 30, 140), "Vibrio Bacterial Lesion"),
        ("4_gill_rot_carps", (80, 80, 80), "Gill Rot Disease Specimen")
    ]

    for idx, (cls_name, color, label_text) in enumerate(classes):
        # Generate 3 training images per class
        for img_num in range(1, 4):
            img = Image.new("RGB", (640, 640), color=color)
            draw = ImageDraw.Draw(img)

            # Add texture noise
            np.random.seed(idx * 10 + img_num)
            noise = np.random.randint(-20, 20, (640, 640, 3), dtype=np.int16)
            img_arr = np.clip(np.array(img, dtype=np.int16) + noise, 0, 255).astype(np.uint8)
            img = Image.fromarray(img_arr)
            draw = ImageDraw.Draw(img)

            # Draw specimen outline / bounding box markers
            draw.rectangle([100, 150, 540, 490], outline=(255, 255, 255), width=3)

            # Add lesion dots for infected classes
            if "wssv" in cls_name:
                for _ in range(15):
                    cx, cy = np.random.randint(120, 520), np.random.randint(170, 470)
                    draw.ellipse([cx-8, cy-8, cx+8, cy+8], fill=(255, 255, 255), outline=(200, 200, 200))
            elif "vibrio" in cls_name:
                for _ in range(8):
                    cx, cy = np.random.randint(150, 480), np.random.randint(200, 440)
                    draw.ellipse([cx-15, cy-15, cx+15, cy+15], fill=(220, 20, 20), outline=(100, 0, 0))

            # Add label text
            draw.rectangle([100, 110, 540, 150], fill=(0, 0, 0))
            draw.text((110, 120), f"AIS VISION AI: {label_text} #{img_num}", fill=(255, 255, 255))

            # Save to train or val
            target_path = os.path.join(train_dir, f"{cls_name}_sample_{img_num}.jpg") if img_num <= 2 else os.path.join(val_dir, f"{cls_name}_val_{img_num}.jpg")
            img.save(target_path, quality=90)
            print(f"Generated sample image: {target_path}")

if __name__ == "__main__":
    generate_sample_disease_images()
    print("ALL SAMPLE DISEASE IMAGES GENERATED SUCCESSFULLY.")
