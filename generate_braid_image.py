from PIL import Image, ImageDraw
import math

def create_braid_image(width=800, height=200, braid_width=40):
    # Create a new grayscale image
    image = Image.new("L", (width, height), 0)  # Black background
    draw = ImageDraw.Draw(image)
    
    # Parameters for the braid pattern
    num_braids = width // braid_width  # Number of braid segments
    step = braid_width // 2  # Half the braid width for overlap
    
    # Draw interwoven diagonal bands
    for i in range(-num_braids, num_braids + 1):
        # First set of diagonals (top-left to bottom-right)
        x0 = i * step
        y0 = 0
        x1 = x0 + height  # Diagonal across height
        y1 = height
        draw.line((x0, y0, x1, y1), fill=255, width=braid_width // 4)
        
        # Second set of diagonals (bottom-left to top-right)
        x0 = i * step
        y0 = height
        x1 = x0 + height
        y1 = 0
        draw.line((x0, y0, x1, y1), fill=255, width=braid_width // 4)
    
    # Save the image
    image.save("braid_tattoo.png")
    return "braid_tattoo.png"

if __name__ == "__main__":
    create_braid_image()