
import argparse
import numpy as np
from PIL import Image
import trimesh
import os

def load_image(image_path, shape):
    image = Image.open(image_path).convert('L')
    if shape:
        shape = tuple(map(int, shape.split('x')))
        image = image.resize((shape[1], shape[0]), Image.Resampling.LANCZOS)
    return np.array(image, dtype=np.float32) / 255.0

def create_flat_surface(heightmap, scale):
    M, N = heightmap.shape
    vertices = []
    faces = []
    for i in range(M):
        for j in range(N):
            x = j * scale
            y = i * scale
            z = 0
            vertices.append([x, y, z])
    vertices = np.array(vertices)

    def idx(i, j): return i * N + j
    for i in range(M - 1):
        for j in range(N - 1):
            a, b, c, d = idx(i, j), idx(i, j+1), idx(i+1, j+1), idx(i+1, j)
            faces.append([a, b, c])
            faces.append([a, c, d])
    return vertices, np.array(faces)

def create_pyramidal_surface(heightmap, scale):
    M, N = heightmap.shape
    vertices = []
    faces = []

    def grid_idx(i, j): return i * N + j
    for i in range(M):
        for j in range(N):
            vertices.append([j * scale, i * scale, 0])

    for i in range(M - 1):
        for j in range(N - 1):
            x0 = j * scale + scale / 2
            y0 = i * scale + scale / 2
            z0 = heightmap[i, j] * scale
            center_index = len(vertices)
            vertices.append([x0, y0, z0])
            a, b, c, d = grid_idx(i, j), grid_idx(i, j+1), grid_idx(i+1, j+1), grid_idx(i+1, j)
            faces += [[a, center_index, b], [b, center_index, c],
                      [c, center_index, d], [d, center_index, a]]
    return np.array(vertices), np.array(faces)

def create_embossed_surface(heightmap, scale):
    M, N = heightmap.shape
    vertices = []
    faces = []

    def grid_idx(i, j): return i * N + j
    for i in range(M):
        for j in range(N):
            z = heightmap[i, j] * scale
            vertices.append([j * scale, i * scale, z])

    for i in range(M - 1):
        for j in range(N - 1):
            a, b, c, d = grid_idx(i, j), grid_idx(i, j+1), grid_idx(i+1, j+1), grid_idx(i+1, j)
            faces.append([a, b, c])
            faces.append([a, c, d])

    # Add base surface
    base_index = len(vertices)
    for i in range(M):
        for j in range(N):
            vertices.append([j * scale, i * scale, 0])

    for i in range(M - 1):
        for j in range(N - 1):
            a, b, c, d = base_index + grid_idx(i, j), base_index + grid_idx(i, j+1), base_index + grid_idx(i+1, j+1), base_index + grid_idx(i+1, j)
            faces.append([a, c, b])
            faces.append([a, d, c])

    return np.array(vertices), np.array(faces)

def roll_to_cylinder(vertices, M, N, scale, radius, length, roll_axis):
    V = vertices.copy()
    if roll_axis == 'x':
        for i in range(len(V)):
            y = V[i][1]
            theta = 2 * np.pi * y / length
            V[i][0] = radius * np.sin(theta)
            V[i][1] = radius * np.cos(theta)
    else:
        for i in range(len(V)):
            x = V[i][0]
            theta = 2 * np.pi * x / length
            V[i][0] = radius * np.sin(theta)
            V[i][1] = radius * np.cos(theta)
    return V

def save_mesh(vertices, faces, image_path):
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
    os.makedirs("output_stl", exist_ok=True)
    base = os.path.splitext(os.path.basename(image_path))[0]
    path = f"output_stl/{base}.stl"
    mesh.export(path)
    print(f"STL saved to: {path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--shape", default=None)
    parser.add_argument("--scale", type=float, default=5.0)
    parser.add_argument("--mode", choices=["flat", "pyramidal", "embossed"], default="embossed")
    parser.add_argument("--cylinder", action="store_true")
    parser.add_argument("--radius", type=float, default=25.0)
    parser.add_argument("--length", type=float, default=60.0)
    parser.add_argument("--roll_axis", choices=["x", "y"], default="x")
    args = parser.parse_args()

    heightmap = load_image(args.image, args.shape)
    shape = heightmap.shape

    if args.mode == "flat":
        vertices, faces = create_flat_surface(heightmap, args.scale)
    elif args.mode == "pyramidal":
        vertices, faces = create_pyramidal_surface(heightmap, args.scale)
    else:
        vertices, faces = create_embossed_surface(heightmap, args.scale)

    if args.cylinder:
        vertices = roll_to_cylinder(vertices, *shape, args.scale, args.radius, args.length, args.roll_axis)

    save_mesh(vertices, faces, args.image)

if __name__ == "__main__":
    main()
