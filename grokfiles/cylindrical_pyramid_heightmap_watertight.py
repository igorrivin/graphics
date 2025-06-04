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
cylinder_radius = img_width / (2 * np.pi)  # Radius so X=img_width maps to 2pi

# Function to create a square-based pyramid
def create_pyramid(x, y, block_size, height):
    vertices = np.array([
        [x, y, 0],                    # Bottom-left (0)
        [x + block_size, y, 0],       # Bottom-right (1)
        [x, y + block_size, 0],       # Top-left (2)
        [x + block_size, y + block_size, 0],  # Top-right (3)
        [x + block_size / 2, y + block_size / 2, height]  # Apex (4)
    ])
    faces = np.array([
        [0, 1, 4],  # Side 1
        [1, 3, 4],  # Side 2
        [3, 2, 4],  # Side 3
        [2, 0, 4],  # Side 4
        [0, 2, 1],  # Base triangle 1
        [1, 2, 3]   # Base triangle 2
    ])
    return trimesh.Trimesh(vertices=vertices, faces=faces)

# Create pyramid meshes
block_meshes = []
for y in range(0, img_height, block_size):
    for x in range(0, img_width, block_size):
        block = img_array[y:y+block_size, x:x+block_size]
        avg_intensity = np.mean(block)
        height = max((avg_intensity / 255.0) * max_height, min_height)
        pyramid = create_pyramid(x, y, block_size, height)
        block_meshes.append(pyramid)

# Perform boolean union
mesh = trimesh.boolean.union(block_meshes, engine="cork", skip_empty=True)

# Subdivide mesh for smoothness
mesh = mesh.subdivide()  # Simple subdivision; repeat or use subdivide_to_size for more control

# Apply cylindrical transformation
vertices = mesh.vertices.copy()
new_vertices = np.zeros_like(vertices)
for i, (x, y, z) in enumerate(vertices):
    # Map X to theta (angle), Y to cylinder Z, Z to radial offset
    theta = (x / img_width) * 2 * np.pi  # X from 0 to img_width -> theta from 0 to 2pi
    cyl_z = y  # Y becomes cylinder's Z (height along cylinder)
    radius = cylinder_radius + z  # Z (height) becomes radial offset from cylinder
    new_vertices[i] = [
        radius * np.cos(theta),  # X' = r * cos(theta)
        radius * np.sin(theta),  # Y' = r * sin(theta)
        cyl_z                    # Z' = y
    ]
mesh.vertices = new_vertices

# Fix normals after transformation
mesh.fix_normals()

# Verify watertightness
print("Is mesh watertight?", mesh.is_watertight)

# Export or visualize
mesh.export("cylindrical_pyramid_heightmap_watertight.stl")
mesh.show()