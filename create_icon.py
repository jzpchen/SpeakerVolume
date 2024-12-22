from PIL import Image
import os

def create_icon(input_path, output_path, size=(256, 256)):
    # Open the image
    with Image.open(input_path) as img:
        # Convert to RGBA if not already
        img = img.convert('RGBA')
        
        # Calculate aspect ratio
        aspect = img.width / img.height
        
        # Calculate new dimensions maintaining aspect ratio
        if aspect > 1:
            # Width is larger
            new_width = size[0]
            new_height = int(size[1] / aspect)
        else:
            # Height is larger
            new_height = size[1]
            new_width = int(size[0] * aspect)
            
        # Create a new image with transparency
        new_img = Image.new('RGBA', size, (0, 0, 0, 0))
        
        # Resize original image
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Calculate position to center the image
        x = (size[0] - new_width) // 2
        y = (size[1] - new_height) // 2
        
        # Paste resized image onto transparent background
        new_img.paste(resized, (x, y), resized)
        
        # Save as PNG
        new_img.save(output_path, 'PNG')

if __name__ == '__main__':
    input_file = 'NeumannSpeaker.png'
    output_file = 'icon.png'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        exit(1)
        
    create_icon(input_file, output_file)
    print(f"Icon created successfully: {output_file}")
