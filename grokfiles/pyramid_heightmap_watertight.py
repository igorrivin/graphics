import trimesh
import numpy as np
from PIL import Image

# Load grayscale image
image = Image.open("grayscale_image.png").convert("L")  # Ensure grayscale
img_array = np.array(image)  # Shape: (height, width)
img_height, img_width = img_array.shape

# Define block size and height parameters
block_size = 10  # e.g., 10x10 pixel blocks
max_height = 10.0  # Maximum height for intensity 255
min_height = 1e-4  # Minimum height for zero-intensity blocks

# Function to create a square-based pyramid
def create_pyramid(x, y, block_size, height):
    # Vertices: 4 base corners at Z=0, 1 apex at center
    vertices = np.array([
        [x, y, 0],                    # Bottom-left (0)
        [x + block_size, y, 0],       # Bottom-right (1)
        [x, y + block_size, 0],       # Top-left (2)
        [x + block_size, y + block_size, 0],  # Top-right (3)
        [x + block_size / 2, y + block_size / 2, height]  # Apex (4)
    ])
    
    # Faces: 4 side triangles + 2 base triangles
    faces = np.array([
        [0, 1, 4],  # Side 1: bottom-left to bottom-right to apex
        [1, 3, 4],  # Side 2: bottom-right to top-right to apex
        [3, 2, 4],  # Side 3: top-right to top-left to apex
        [2, 0, 4],  # Side 4: top-left to bottom-left to apex
        [0, 2, 1],  # Base triangle 1 (counterclockwise from below)
        [1, 2, 3]   # Base triangle 2
    ])
    
    return trimesh.Trimesh(vertices=vertices, faces=faces)

# Compute block intensities and create pyramids
block_meshes = []
for y in range(0, img_height, block_size):
    for x in range(0, img_width, block_size):
        # Extract block
        block = img_array[y:y+block_size, x:x+block_size]
        # Compute average intensity
        avg_intensity = np.mean(block)
        # Scale intensity to height, ensuring non-zero height
        height = max((avg_intensity / 255.0) * max_height, min_height)
        
        # Create pyramid for the block
        pyramid = create_pyramid(x, y, block_size, height)
        block_meshes.append(pyramid)

# Perform boolean union
mesh = trimesh.boolean.union(block_meshes, engine="cork", skip_empty=True)

# Verify watertightness
print("Is mesh watertight?", mesh.is_watertight)

# Export or visualize
mesh.export("pyramid_heightmap_watertight.stl")
mesh.show()