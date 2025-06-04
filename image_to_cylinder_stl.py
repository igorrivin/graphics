
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

def subdivide_heightmap(heightmap, subdivision_factor=2):
    M, N = heightmap.shape
    new_M = M * subdivision_factor
    new_N = N * subdivision_factor
    return resize(heightmap, (new_M, new_N), anti_aliasing=True)

def cylindrical_coords(u, v, radius, length, roll_axis):
    theta = 2 * np.pi * u
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    if roll_axis == "x":
        return np.array([v * length, x, y])
    else:
        return np.array([x, v * length, y])

def roll_surface_to_cylinder(heightmap, radius=30.0, length=40.0, height_scale=10.0,
                             thickness=None, roll_axis="x", subdivision=2):
    heightmap_sub = subdivide_heightmap(heightmap, subdivision)
    M, N = heightmap_sub.shape
    vertices, faces = [], []
    index_map = {}

    def add_vertex(v):
        key = tuple(np.round(v, 6))
        if key not in index_map:
            index_map[key] = len(vertices)
            vertices.append(v)
        return index_map[key]

    for i in range(M - 1):
        for j in range(N - 1):
            u0, u1 = i / (M - 1), (i + 1) / (M - 1)
            v0, v1 = j / (N - 1), (j + 1) / (N - 1)

            h00 = heightmap_sub[i, j] * height_scale
            h10 = heightmap_sub[i + 1, j] * height_scale
            h11 = heightmap_sub[i + 1, j + 1] * height_scale
            h01 = heightmap_sub[i, j + 1] * height_scale

            p0 = cylindrical_coords(u0, v0, radius + h00, length, roll_axis)
            p1 = cylindrical_coords(u1, v0, radius + h10, length, roll_axis)
            p2 = cylindrical_coords(u1, v1, radius + h11, length, roll_axis)
            p3 = cylindrical_coords(u0, v1, radius + h01, length, roll_axis)

            v0_idx = add_vertex(p0)
            v1_idx = add_vertex(p1)
            v2_idx = add_vertex(p2)
            v3_idx = add_vertex(p3)

            faces += [[v0_idx, v1_idx, v2_idx], [v2_idx, v3_idx, v0_idx]]

    if thickness is not None and thickness > 0:
        index_map_inner = {}
        inner_faces = []

        def add_inner_vertex(v):
            key = tuple(np.round(v, 6))
            if key not in index_map_inner:
                index_map_inner[key] = len(vertices)
                vertices.append(v)
            return index_map_inner[key]

        for i in range(M - 1):
            for j in range(N - 1):
                u0, u1 = i / (M - 1), (i + 1) / (M - 1)
                v0, v1 = j / (N - 1), (j + 1) / (N - 1)

                h00 = heightmap_sub[i, j] * height_scale
                h10 = heightmap_sub[i + 1, j] * height_scale
                h11 = heightmap_sub[i + 1, j + 1] * height_scale
                h01 = heightmap_sub[i, j + 1] * height_scale

                p0 = cylindrical_coords(u0, v0, radius + h00 - thickness, length, roll_axis)
                p1 = cylindrical_coords(u1, v0, radius + h10 - thickness, length, roll_axis)
                p2 = cylindrical_coords(u1, v1, radius + h11 - thickness, length, roll_axis)
                p3 = cylindrical_coords(u0, v1, radius + h01 - thickness, length, roll_axis)

                v0_idx = add_inner_vertex(p0)
                v1_idx = add_inner_vertex(p1)
                v2_idx = add_inner_vertex(p2)
                v3_idx = add_inner_vertex(p3)

                inner_faces += [[v2_idx, v1_idx, v0_idx], [v0_idx, v3_idx, v2_idx]]

        faces += inner_faces

    return trimesh.Trimesh(vertices=vertices, faces=faces, process=True)

def main():
    parser = argparse.ArgumentParser(description="Generate STL surfaces from images.")
    parser.add_argument("--image", "-i", required=True, help="Path to input image")
    parser.add_argument("--shape", "-s", default="40x40", help="Grid shape like '40x40'")
    parser.add_argument("--scale", "-z", type=float, default=10.0, help="Height scale")
    parser.add_argument("--output", "-o", default="output_stl", help="Output directory")

    parser.add_argument("--cylinder", action="store_true", help="Roll the surface into a cylinder")
    parser.add_argument("--radius", type=float, default=30.0, help="Cylinder base radius")
    parser.add_argument("--length", type=float, default=40.0, help="Cylinder height")
    parser.add_argument("--thickness", type=float, default=None, help="Wall thickness for hollow cylinders")
    parser.add_argument("--roll_axis", choices=["x", "y"], default="x", help="Axis along which to roll")
    parser.add_argument("--subdivision", type=int, default=2, help="Subdivisions for smooth surface")

    args = parser.parse_args()
    m, n = map(int, args.shape.lower().split('x'))
    os.makedirs(args.output, exist_ok=True)

    heightmap = process_image_to_heightmap(args.image, target_shape=(m, n))

    base_name = os.path.splitext(os.path.basename(args.image))[0]

    if args.cylinder:
        mesh = roll_surface_to_cylinder(
            heightmap,
            radius=args.radius,
            length=args.length,
            height_scale=args.scale,
            thickness=args.thickness,
            roll_axis=args.roll_axis,
            subdivision=args.subdivision
        )
        path = os.path.join(args.output, f"{base_name}_cylinder.stl")
        mesh.export(path)
        print("Cylinder STL saved to:", path)
    else:
        print("Add regular embossed/pyramidal generation here if needed.")

if __name__ == "__main__":
    main()
