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

# Compute block intensities and create boxes
block_meshes = []
for y in range(0, img_height, block_size):
    for x in range(0, img_width, block_size):
        # Extract block
        block = img_array[y:y+block_size, x:x+block_size]
        # Compute average intensity
        avg_intensity = np.mean(block)
        # Scale intensity to height, ensuring non-zero height
        height = max((avg_intensity / 255.0) * max_height, min_height)
        
        # Create box for the block
        # Box dimensions: [block_size, block_size, height]
        # Box origin: (x, y, 0), centered at (x + block_size/2, y + block_size/2, height/2)
        box = trimesh.creation.box(
            extents=[block_size, block_size, height],
            transform=trimesh.transformations.translation_matrix([
                x + block_size / 2,
                y + block_size / 2,
                height / 2
            ])
        )
        block_meshes.append(box)

# Perform boolean union
mesh = trimesh.boolean.union(block_meshes, engine="cork", skip_empty=True)

# Verify watertightness
print("Is mesh watertight?", mesh.is_watertight)

# Export or visualize
mesh.export("boolean_heightmap_watertight.stl")
mesh.show()