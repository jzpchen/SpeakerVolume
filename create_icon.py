from PIL import Image
import os

def create_icon(input_path, output_path, size=(512, 512)):  # Increased size for better quality
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
        
        # Resize original image with high quality
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Calculate position to center the image
        x = (size[0] - new_width) // 2
        y = (size[1] - new_height) // 2
        
        # Paste resized image onto transparent background
        new_img.paste(resized, (x, y), resized)
        
        # Create smaller versions for better scaling
        sizes = [(512, 512), (256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]
        
        # Save the main icon
        new_img.save(output_path, 'PNG', optimize=True)
        print(f"Created icon at {output_path} with size {size}")

if __name__ == '__main__':
    input_file = 'NeumannSpeaker.png'
    output_file = 'icon.png'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        exit(1)
        
    create_icon(input_file, output_file)
    print(f"Icon created successfully: {output_file}")
