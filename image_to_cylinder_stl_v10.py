
import argparse
import numpy as np
from PIL import Image
import trimesh


def load_image_grayscale(path, shape=None):
    image = Image.open(path).convert("L")
    if shape:
        image = image.resize((shape[1], shape[0]), Image.LANCZOS)
    return np.array(image) / 255.0


def generate_heightmap(image_array, scale=1.0):
    return image_array * scale


def make_embossed_mesh(heightmap, scale):
    M, N = heightmap.shape
    vertices = []
    faces = []

    # Top surface
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

    # Base surface (flat at z=0)
    base_offset = len(vertices)
    for i in range(M - 1):
        for j in range(N - 1):
            v00 = [i, j, 0]
            v10 = [i + 1, j, 0]
            v11 = [i + 1, j + 1, 0]
            v01 = [i, j + 1, 0]

            idx = len(vertices)
            vertices.extend([v00, v10, v11, v01])
            faces.append([idx, idx + 2, idx + 1])  # Flip winding for bottom
            faces.append([idx, idx + 3, idx + 2])

    return np.array(vertices), np.array(faces)


def make_grid_mesh(heightmap, scale, mode="flat"):
    if mode == "embossed":
        return make_embossed_mesh(heightmap, scale)

    M, N = heightmap.shape
    vertices = []
    faces = []

    if mode == "flat":
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

    elif mode == "pyramidal":
        for i in range(M - 1):
            for j in range(N - 1):
                v00 = [i, j, 0]
                v10 = [i + 1, j, 0]
                v11 = [i + 1, j + 1, 0]
                v01 = [i, j + 1, 0]

                zc = heightmap[i, j] * scale
                vc = [i + 0.5, j + 0.5, zc]

                idx = len(vertices)
                vertices.extend([vc, v00, v10, v11, v01])
                faces += [
                    [idx, idx + 1, idx + 2],
                    [idx, idx + 2, idx + 3],
                    [idx, idx + 3, idx + 4],
                    [idx, idx + 4, idx + 1],
                ]

    return np.array(vertices), np.array(faces)


def to_cylinder(vertices, heightmap_shape, radius, length, roll_axis):
    M, N = heightmap_shape
    cylindrical = []
    for v in vertices:
        i, j, z = v
        if roll_axis == "x":
            angle = 2 * np.pi * i / (M - 1)
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            z = j * (length / (N - 1))
        else:
            angle = 2 * np.pi * j / (N - 1)
            x = i * (length / (M - 1))
            y = radius * np.cos(angle)
            z = radius * np.sin(angle)
        if roll_axis == "x":
            z += v[2]
        else:
            x += v[2]
        cylindrical.append([x, y, z])
    return np.array(cylindrical)


def save_as_stl(vertices, faces, output_path):
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    mesh.export(output_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", default="output.stl")
    parser.add_argument("--shape", default="100x100")
    parser.add_argument("--scale", type=float, default=10.0)
    parser.add_argument("--mode", choices=["flat", "pyramidal", "embossed"], default="flat")
    parser.add_argument("--cylinder", action="store_true")
    parser.add_argument("--radius", type=float, default=20.0)
    parser.add_argument("--length", type=float, default=60.0)
    parser.add_argument("--roll_axis", choices=["x", "y"], default="y")
    parser.add_argument("--thickness", type=float, default=1.5)
    args = parser.parse_args()

    shape = tuple(map(int, args.shape.lower().split("x")))
    image_array = load_image_grayscale(args.image, shape=shape)
    heightmap = generate_heightmap(image_array)

    vertices, faces = make_grid_mesh(heightmap, args.scale, mode=args.mode)

    if args.cylinder:
        vertices = to_cylinder(vertices, heightmap.shape, args.radius, args.length, args.roll_axis)

    save_as_stl(vertices, faces, args.output)
    print(f"Saved STL to {args.output}")


if __name__ == "__main__":
    main()
