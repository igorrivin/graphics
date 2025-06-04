
import argparse
import numpy as np
from PIL import Image
import trimesh


def load_image_grayscale(path, shape=None):
    image = Image.open(path).convert("L")
    if shape:
        image = image.resize(shape[::-1], Image.LANCZOS)
    return np.array(image) / 255.0


def generate_heightmap(image_array, scale=1.0):
    return image_array * scale


def create_vertices_and_faces_flat(heightmap, scale):
    M, N = heightmap.shape
    vertices = []
    faces = []

    for i in range(M - 1):
        for j in range(N - 1):
            z00 = heightmap[i, j] * scale
            z10 = heightmap[i + 1, j] * scale
            z11 = heightmap[i + 1, j + 1] * scale
            z01 = heightmap[i, j + 1] * scale

            v00 = [i, j, z00]
            v10 = [i + 1, j, z10]
            v11 = [i + 1, j + 1, z11]
            v01 = [i, j + 1, z01]

            idx = len(vertices)
            vertices.extend([v00, v10, v11, v01])
            faces.append([idx, idx + 1, idx + 2])
            faces.append([idx, idx + 2, idx + 3])

    return np.array(vertices), np.array(faces)


def create_vertices_and_faces_pyramidal(heightmap, scale):
    M, N = heightmap.shape
    vertices = []
    faces = []

    for i in range(M - 1):
        for j in range(N - 1):
            v00 = [i, j, 0]
            v10 = [i + 1, j, 0]
            v11 = [i + 1, j + 1, 0]
            v01 = [i, j + 1, 0]

            zc = heightmap[i, j] * scale
            vc = [(i + 0.5), (j + 0.5), zc]

            idx = len(vertices)
            vertices.extend([vc, v00, v10, v11, v01])
            faces += [
                [idx, idx + 1, idx + 2],
                [idx, idx + 2, idx + 3],
                [idx, idx + 3, idx + 4],
                [idx, idx + 4, idx + 1],
            ]

    return np.array(vertices), np.array(faces)


def save_as_stl(vertices, faces, output_path):
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    mesh.export(output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", default="output.stl")
    parser.add_argument("--shape", default="100x100")
    parser.add_argument("--scale", type=float, default=10.0)
    parser.add_argument("--mode", choices=["flat", "pyramidal"], default="flat")
    args = parser.parse_args()

    shape = tuple(map(int, args.shape.lower().split("x")))
    image_array = load_image_grayscale(args.image, shape=shape)
    heightmap = generate_heightmap(image_array, scale=1.0)

    if args.mode == "flat":
        vertices, faces = create_vertices_and_faces_flat(heightmap, args.scale)
    elif args.mode == "pyramidal":
        vertices, faces = create_vertices_and_faces_pyramidal(heightmap, args.scale)
    else:
        raise ValueError("Unknown mode")

    save_as_stl(vertices, faces, args.output)
    print(f"STL saved to {args.output}")


if __name__ == "__main__":
    main()
