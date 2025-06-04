
import argparse
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
        vertices, faces = [], []

        # Top
        top_vertices, top_faces = make_grid_mesh(heightmap, scale, mode="flat")
        offset = len(vertices)
        vertices.extend(top_vertices.tolist())
        faces.extend((np.array(top_faces) + offset).tolist())

        # Bottom
        bottom_vertices = top_vertices.copy()
        bottom_vertices[:, 2] = 0
        offset = len(vertices)
        vertices.extend(bottom_vertices.tolist())
        faces.extend((np.array(top_faces)[:, ::-1] + offset).tolist())  # reversed

        # Walls
        M, N = heightmap.shape
        def wall_strip(a_idx, b_idx):
            v0, v1 = top_vertices[a_idx]
            v2, v3 = bottom_vertices[b_idx]
            return [[v0, v1, v2], [v0, v2, v3]]

        for i in range(M - 1):
            for j in [0, N - 2]:
                top0 = i * (N - 1) * 4 + j * 4
                top1 = top0 + 4
                bot0 = top0 + len(top_vertices)
                bot1 = top1 + len(top_vertices)
                faces += [[top0, top1, bot1], [top0, bot1, bot0]]

        for j in range(N - 1):
            for i in [0, M - 2]:
                top0 = i * (N - 1) * 4 + j * 4
                top1 = top0 + (N - 1) * 4
                bot0 = top0 + len(top_vertices)
                bot1 = top1 + len(top_vertices)
                faces += [[top0, top1, bot1], [top0, bot1, bot0]]

        return np.array(vertices), np.array(faces)

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

    if thickness is None:
        return np.array(verts_outer)

    # Hollow version: duplicate and offset inner surface
    verts_inner = []
    for v in vertices:
        i, j, z = v
        if roll_axis == "y":
            theta = 2 * np.pi * j / (N - 1)
            x = i * (length / (M - 1))
            y = (radius - thickness) * np.cos(theta)
            z_new = (radius - thickness) * np.sin(theta)
        else:
            theta = 2 * np.pi * i / (M - 1)
            x = (radius - thickness) * np.cos(theta)
            y = (radius - thickness) * np.sin(theta)
            z_new = j * (length / (N - 1))
        verts_inner.append([x, y, z_new])

    # Faces remain the same, we only output the vertices for now
    return np.vstack([verts_outer, verts_inner])

def save_mesh(vertices, faces, output_path):
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
        vertices = roll_surface_to_cylinder(
            vertices, heightmap.shape,
            radius=args.radius,
            length=args.length,
            roll_axis=args.roll_axis,
            thickness=args.thickness
        )

    save_mesh(vertices, faces, args.output)
    print(f"STL saved to {args.output}")

if __name__ == "__main__":
    main()
