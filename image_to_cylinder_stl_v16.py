
import argparse
import os
import numpy as np
from PIL import Image
import trimesh

def load_image_grayscale(path, shape=None):
    img = Image.open(path).convert("L")
    if shape:
        img = img.resize((shape[1], shape[0]), Image.LANCZOS)
    return np.array(img) / 255.0

def generate_heightmap(image_array, scale=1.0):
    return image_array * scale

def make_grid_mesh(heightmap, scale=1.0, mode="flat"):
    M, N = heightmap.shape
    vertices = []
    faces = []

    if mode == "pyramidal":
        for i in range(M - 1):
            for j in range(N - 1):
                v00 = [i, j, 0]
                v10 = [i + 1, j, 0]
                v11 = [i + 1, j + 1, 0]
                v01 = [i, j + 1, 0]
                vc = [i + 0.5, j + 0.5, heightmap[i, j] * scale]
                idx = len(vertices)
                vertices.extend([vc, v00, v10, v11, v01])
                faces += [
                    [idx, idx+1, idx+2],
                    [idx, idx+2, idx+3],
                    [idx, idx+3, idx+4],
                    [idx, idx+4, idx+1],
                ]
        # Base surface
        for i in range(M - 1):
            for j in range(N - 1):
                v0 = [i, j, 0]
                v1 = [i + 1, j, 0]
                v2 = [i + 1, j + 1, 0]
                v3 = [i, j + 1, 0]
                idx = len(vertices)
                vertices.extend([v0, v1, v2, v3])
                faces.append([idx, idx + 1, idx + 2])
                faces.append([idx, idx + 2, idx + 3])
        return np.array(vertices), np.array(faces)

    elif mode == "flat":
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

    elif mode == "embossed":
        top_vertices = np.zeros((M, N, 3))
        bottom_vertices = np.zeros((M, N, 3))
        for i in range(M):
            for j in range(N):
                top_vertices[i, j] = [i, j, heightmap[i, j] * scale]
                bottom_vertices[i, j] = [i, j, 0]

        vertices = np.concatenate((top_vertices.reshape(-1, 3), bottom_vertices.reshape(-1, 3)))
        faces = []

        def vidx(i, j, offset=0):
            return i * N + j + offset

        # Top surface
        for i in range(M - 1):
            for j in range(N - 1):
                a = vidx(i, j)
                b = vidx(i + 1, j)
                c = vidx(i + 1, j + 1)
                d = vidx(i, j + 1)
                faces.append([a, b, c])
                faces.append([a, c, d])

        # Bottom surface (flip order)
        for i in range(M - 1):
            for j in range(N - 1):
                a = vidx(i, j, offset=M*N)
                b = vidx(i + 1, j, offset=M*N)
                c = vidx(i + 1, j + 1, offset=M*N)
                d = vidx(i, j + 1, offset=M*N)
                faces.append([a, c, b])
                faces.append([a, d, c])

        # Side walls
        for i in range(M - 1):
            for top, bottom in [(vidx(i, 0), vidx(i, 0, M*N)), (vidx(i, N - 1), vidx(i, N - 1, M*N))]:
                a, b = top, top + 1
                c, d = bottom, bottom + 1
                faces.append([a, c, d])
                faces.append([a, d, b])
        for j in range(N - 1):
            for top, bottom in [(vidx(0, j), vidx(0, j, M*N)), (vidx(M - 1, j), vidx(M - 1, j, M*N))]:
                a, b = top, top + N
                c, d = bottom, bottom + N
                faces.append([a, c, d])
                faces.append([a, d, b])

        return vertices, np.array(faces)

def roll_surface_to_cylinder(vertices, heightmap_shape, radius, length, roll_axis="y", thickness=None):
    M, N = heightmap_shape
    verts_outer = []

    for v in vertices:
        i, j, z = v
        if roll_axis == "y":
            theta = 2 * np.pi * j / (N - 1)
            x = i * (length / (M - 1))
            y = (radius + z) * np.cos(theta)
            z_new = (radius + z) * np.sin(theta)
        else:
            theta = 2 * np.pi * i / (M - 1)
            x = (radius + z) * np.cos(theta)
            y = (radius + z) * np.sin(theta)
            z_new = j * (length / (N - 1))
        verts_outer.append([x, y, z_new])
    return np.array(verts_outer)

def save_mesh(vertices, faces, image_path, output_dir="output_stl"):
    os.makedirs(output_dir, exist_ok=True)
    name = os.path.splitext(os.path.basename(image_path))[0]
    path = os.path.join(output_dir, f"{name}.stl")
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    mesh.export(path)
    print(f"Saved to: {path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", default="output.stl")
    parser.add_argument("--shape", default="100x100")
    parser.add_argument("--scale", type=float, default=10.0)
    parser.add_argument("--mode", choices=["flat", "pyramidal", "embossed"], default="flat")
    parser.add_argument("--cylinder", action="store_true")
    parser.add_argument("--radius", type=float, default=25.0)
    parser.add_argument("--length", type=float, default=60.0)
    parser.add_argument("--roll_axis", choices=["x", "y"], default="y")
    parser.add_argument("--thickness", type=float, default=None)
    args = parser.parse_args()

    shape = tuple(map(int, args.shape.lower().split("x")))
    img_array = load_image_grayscale(args.image, shape)
    heightmap = generate_heightmap(img_array, scale=args.scale)
    vertices, faces = make_grid_mesh(heightmap, scale=args.scale, mode=args.mode)

    if args.cylinder:
        vertices = roll_surface_to_cylinder(vertices, heightmap.shape, radius=args.radius,
                                            length=args.length, roll_axis=args.roll_axis,
                                            thickness=args.thickness)

    save_mesh(vertices, faces, args.image)

if __name__ == "__main__":
    main()
