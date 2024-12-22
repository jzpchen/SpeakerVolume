from PIL import Image
import os
import subprocess

def create_iconset():
    # Create iconset directory if it doesn't exist
    if not os.path.exists('Speaker.iconset'):
        os.makedirs('Speaker.iconset')

    # Open and convert the original image
    img = Image.open('icon.png')

    # Generate different sizes
    sizes = [
        (16, '16x16'),
        (32, '16x16@2x'),
        (32, '32x32'),
        (64, '32x32@2x'),
        (128, '128x128'),
        (256, '128x128@2x'),
        (256, '256x256'),
        (512, '256x256@2x'),
        (512, '512x512'),
        (1024, '512x512@2x')
    ]

    for size, name in sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f'Speaker.iconset/icon_{name}.png')

    # Convert iconset to icns using iconutil
    subprocess.run(['iconutil', '-c', 'icns', 'Speaker.iconset'])
    
    # Clean up iconset directory
    subprocess.run(['rm', '-rf', 'Speaker.iconset'])

if __name__ == '__main__':
    create_iconset()
