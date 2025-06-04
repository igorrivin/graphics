import argparse
import numpy as np
from PIL import Image
from skimage.transform import resize
import trimesh
import os

def process_image_to_heightmap(image_path, target_shape=(40, 40), invert=False):
    img = Image.open(image_path).convert("L")
    arr = np.array(img, dtype=np.float32)
    if invert:
        arr = 255 - arr
    arr /= 255.0
    resized = resize(arr, target_shape, anti_aliasing=True)
    return resized

def generate_surface_from_heightmap(heightmap, mode="embossed", height_scale=10.0):
    M, N = heightmap.shape
    vertices, faces = [], []
    index_map = {}

    def add_vertex(v):
        key = tuple(v)
        if key not in index_map:
            index_map[key] = len(vertices)
            vertices.append(v)
        return index_map[key]

    for i in range(M - 1):
        for j in range(N - 1):
            p0 = np.array([i, j, 0])
            p1 = np.array([i + 1, j, 0])
            p2 = np.array([i + 1, j + 1, 0])
            p3 = np.array([i, j + 1, 0])

            z_vals = [
                heightmap[i, j],
                heightmap[i + 1, j],
                heightmap[i + 1, j + 1],
                heightmap[i, j + 1],
            ]

            if mode == "embossed":
                z = np.mean(z_vals) * height_scale
                q0, q1, q2, q3 = [p + [0, 0, z] for p in [p0, p1, p2, p3]]
                c = (q0 + q1 + q2 + q3) / 4
            elif mode == "pyramid":
                q0, q1, q2, q3 = p0, p1, p2, p3
                z = np.mean(z_vals) * height_scale
                c = (p0 + p1 + p2 + p3) / 4 + [0, 0, z]
            else:
                raise ValueError("Invalid mode")

            v0 = add_vertex(q0)
            v1 = add_vertex(q1)
            v2 = add_vertex(q2)
            v3 = add_vertex(q3)
            vc = add_vertex(c)

            faces.extend([
                [v0, vc, v1],
                [v1, vc, v2],
                [v2, vc, v3],
                [v3, vc, v0]
            ])

            if mode == "embossed":
                base_pts = [p0, p1, p2, p3]
                raised_pts = [q0, q1, q2, q3]
                for k in range(4):
                    a = add_vertex(base_pts[k])
                    b = add_vertex(base_pts[(k + 1) % 4])
                    A = add_vertex(raised_pts[k])
                    B = add_vertex(raised_pts[(k + 1) % 4])
                    faces += [
                        [a, b, B],
                        [B, A, a]
                    ]

    return trimesh.Trimesh(vertices=vertices, faces=faces, process=True)

def image_to_stl(image_path, output_dir, shape=(40, 40), scale=10.0):
    os.makedirs(output_dir, exist_ok=True)
    heightmap = process_image_to_heightmap(image_path, shape)

    mesh_embossed = generate_surface_from_heightmap(heightmap, mode="embossed", height_scale=scale)
    mesh_pyramid = generate_surface_from_heightmap(heightmap, mode="pyramid", height_scale=scale)

    base_name = os.path.splitext(os.path.basename(image_path))[0]
    embossed_path = os.path.join(output_dir, f"{base_name}_embossed.stl")
    pyramid_path = os.path.join(output_dir, f"{base_name}_pyramid.stl")

    mesh_embossed.export(embossed_path)
    mesh_pyramid.export(pyramid_path)

    return embossed_path, pyramid_path

def parse_shape(s):
    try:
        m, n = map(int, s.lower().split('x'))
        return (m, n)
    except:
        raise argparse.ArgumentTypeError("Shape must be like '40x40'")

def main():
    parser = argparse.ArgumentParser(description="Convert image to embossed and pyramidal STL surfaces.")
    parser.add_argument("--image", "-i", required=True, help="Path to input image")
    parser.add_argument("--shape", "-s", type=parse_shape, default=(40, 40), help="Grid shape like '40x40'")
    parser.add_argument("--scale", "-z", type=float, default=10.0, help="Height scaling factor")
    parser.add_argument("--output", "-o", default="output_stl", help="Output directory")

    args = parser.parse_args()

    embossed, pyramid = image_to_stl(args.image, args.output, shape=args.shape, scale=args.scale)
    print(f"Embossed STL saved to: {embossed}")
    print(f"Pyramidal STL saved to: {pyramid}")

if __name__ == "__main__":
    main()
