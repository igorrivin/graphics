
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
                             thickness=None, roll_axis="x", subdivision=2, mode="embossed"):
    if mode == 'pyramidal':
        heightmap_sub = heightmap
    else:
        heightmap_sub = subdivide_heightmap(heightmap, subdivision)

    M, N = heightmap_sub.shape
    vertices, faces = [], []
    index_map = {}
    seam_map = {}

    def add_vertex(v):
        key = tuple(np.round(v, 6))
        if key not in index_map:
            index_map[key] = len(vertices)
            vertices.append(v)
        return index_map[key]

    for i in range(M):
        for j in range(N):
            u = i / (M - 1)
            v = j / (N - 1)
            if mode == "flat":
                z = 0.0
            el
    if mode == "embossed":
        # Add vertical side walls along the perimeter
        for i in range(M - 1):
            for j in [0, N - 1]:
                u0 = i / (M - 1)
                u1 = (i + 1) / (M - 1)
                v = j / (N - 1)
                z0 = heightmap_sub[i, j] * height_scale
                z1 = heightmap_sub[i + 1, j] * height_scale
                p0_top = cylindrical_coords(u0, v, radius + z0, length, roll_axis)
                p1_top = cylindrical_coords(u1, v, radius + z1, length, roll_axis)
                p0_bot = cylindrical_coords(u0, v, radius, length, roll_axis)
                p1_bot = cylindrical_coords(u1, v, radius, length, roll_axis)
                v0 = add_vertex(p0_top)
                v1 = add_vertex(p1_top)
                v2 = add_vertex(p1_bot)
                v3 = add_vertex(p0_bot)
                faces += [[v0, v1, v2], [v2, v3, v0]]
        for j in range(N - 1):
            for i in [0, M - 1]:
                u = i / (M - 1)
                v0_ = j / (N - 1)
                v1_ = (j + 1) / (N - 1)
                z0 = heightmap_sub[i, j] * height_scale
                z1 = heightmap_sub[i, j + 1] * height_scale
                p0_top = cylindrical_coords(u, v0_, radius + z0, length, roll_axis)
                p1_top = cylindrical_coords(u, v1_, radius + z1, length, roll_axis)
                p0_bot = cylindrical_coords(u, v0_, radius, length, roll_axis)
                p1_bot = cylindrical_coords(u, v1_, radius, length, roll_axis)
                v0 = add_vertex(p0_top)
                v1 = add_vertex(p1_top)
                v2 = add_vertex(p1_bot)
                v3 = add_vertex(p0_bot)
                faces += [[v0, v1, v2], [v2, v3, v0]]
        # Add vertical side walls along the perimeter
        for i in range(M - 1):
            for j in [0, N - 1]:
                u0 = i / (M - 1)
                u1 = (i + 1) / (M - 1)
                v = j / (N - 1)
                z0 = heightmap_sub[i, j] * height_scale
                z1 = heightmap_sub[i + 1, j] * height_scale
                p0_top = cylindrical_coords(u0, v, radius + z0, length, roll_axis)
                p1_top = cylindrical_coords(u1, v, radius + z1, length, roll_axis)
                p0_bot = cylindrical_coords(u0, v, radius, length, roll_axis)
                p1_bot = cylindrical_coords(u1, v, radius, length, roll_axis)
                v0 = add_vertex(p0_top)
                v1 = add_vertex(p1_top)
                v2 = add_vertex(p1_bot)
                v3 = add_vertex(p0_bot)
                faces += [[v0, v1, v2], [v2, v3, v0]]
        for j in range(N - 1):
            for i in [0, M - 1]:
                u = i / (M - 1)
                v0_ = j / (N - 1)
                v1_ = (j + 1) / (N - 1)
                z0 = heightmap_sub[i, j] * height_scale
                z1 = heightmap_sub[i, j + 1] * height_scale
                p0_top = cylindrical_coords(u, v0_, radius + z0, length, roll_axis)
                p1_top = cylindrical_coords(u, v1_, radius + z1, length, roll_axis)
                p0_bot = cylindrical_coords(u, v0_, radius, length, roll_axis)
                p1_bot = cylindrical_coords(u, v1_, radius, length, roll_axis)
                v0 = add_vertex(p0_top)
                v1 = add_vertex(p1_top)
                v2 = add_vertex(p1_bot)
                v3 = add_vertex(p0_bot)
                faces += [[v0, v1, v2], [v2, v3, v0]]

if mode == "embossed":
                z = heightmap_sub[min(i, M - 2), min(j, N - 2)] * height_scale
            elif mode == "pyramidal":
                z = 0.0
            r = radius + z
            if i == M - 1:
                key = (0, j)
                if key in seam_map:
                    add_vertex(seam_map[key])
                    continue
            else:
                key = (i, j)
            seam_map[key] = cylindrical_coords(u, v, r, length, roll_axis)
            pos = seam_map[key]
            add_vertex(pos)

    def get_idx(i, j):
        return i * N + j

    for i in range(M - 1):
        for j in range(N - 1):
            v0 = get_idx(i, j)
            v1 = get_idx(i + 1, j)
            v2 = get_idx(i + 1, j + 1)
            v3 = get_idx(i, j + 1)

            if mode == "pyramidal":
                u_mid = (i + 0.5) / (M - 1)
                v_mid = (j + 0.5) / (N - 1)
                z_center = heightmap_sub[i, j] * height_scale
                r_center = radius + z_center
                c = cylindrical_coords(u_mid, v_mid, r_center, length, roll_axis)
                c_idx = add_vertex(c)
                faces += [[v0, c_idx, v1], [v1, c_idx, v2], [v2, c_idx, v3], [v3, c_idx, v0]]
            else:
                faces += [[v0, v1, v2], [v2, v3, v0]]

    for j in range(N - 1):
        i0, i1 = 0, M - 1
        v0 = get_idx(i0, j)
        v1 = get_idx(i0, j + 1)
        v2 = get_idx(i1, j + 1)
        v3 = get_idx(i1, j)

        if mode == "pyramidal":
            u_mid = 0.0
            v_mid = (j + 0.5) / (N - 1)
            z_center = heightmap_sub[i, j] * height_scale
            r_center = radius + z_center
            c = cylindrical_coords(u_mid, v_mid, r_center, length, roll_axis)
            c_idx = add_vertex(c)
            faces += [[v0, c_idx, v3], [v3, c_idx, v2], [v2, c_idx, v1], [v1, c_idx, v0]]
        else:
            faces += [[v0, v3, v2], [v2, v1, v0]]


    if mode == "embossed":
        # Add vertical side walls along the perimeter
        for i in range(M - 1):
            for j in [0, N - 1]:
                u0 = i / (M - 1)
                u1 = (i + 1) / (M - 1)
                v = j / (N - 1)
                z0 = heightmap_sub[i, j] * height_scale
                z1 = heightmap_sub[i + 1, j] * height_scale
                p0_top = cylindrical_coords(u0, v, radius + z0, length, roll_axis)
                p1_top = cylindrical_coords(u1, v, radius + z1, length, roll_axis)
                p0_bot = cylindrical_coords(u0, v, radius, length, roll_axis)
                p1_bot = cylindrical_coords(u1, v, radius, length, roll_axis)
                v0 = add_vertex(p0_top)
                v1 = add_vertex(p1_top)
                v2 = add_vertex(p1_bot)
                v3 = add_vertex(p0_bot)
                faces += [[v0, v1, v2], [v2, v3, v0]]
        for j in range(N - 1):
            for i in [0, M - 1]:
                u = i / (M - 1)
                v0_ = j / (N - 1)
                v1_ = (j + 1) / (N - 1)
                z0 = heightmap_sub[i, j] * height_scale
                z1 = heightmap_sub[i, j + 1] * height_scale
                p0_top = cylindrical_coords(u, v0_, radius + z0, length, roll_axis)
                p1_top = cylindrical_coords(u, v1_, radius + z1, length, roll_axis)
                p0_bot = cylindrical_coords(u, v0_, radius, length, roll_axis)
                p1_bot = cylindrical_coords(u, v1_, radius, length, roll_axis)
                v0 = add_vertex(p0_top)
                v1 = add_vertex(p1_top)
                v2 = add_vertex(p1_bot)
                v3 = add_vertex(p0_bot)
                faces += [[v0, v1, v2], [v2, v3, v0]]

if mode == "embossed":
        for i in range(M - 1):
            for j in range(N - 1):
                u0 = i / (M - 1)
                u1 = (i + 1) / (M - 1)
                v0 = j / (N - 1)
                v1 = (j + 1) / (N - 1)
                p0 = cylindrical_coords(u0, v0, radius, length, roll_axis)
                p1 = cylindrical_coords(u1, v0, radius, length, roll_axis)
                p2 = cylindrical_coords(u1, v1, radius, length, roll_axis)
                p3 = cylindrical_coords(u0, v1, radius, length, roll_axis)
                v0_idx = add_vertex(p0)
                v1_idx = add_vertex(p1)
                v2_idx = add_vertex(p2)
                v3_idx = add_vertex(p3)
                faces += [[v2_idx, v1_idx, v0_idx], [v0_idx, v3_idx, v2_idx]]

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
    parser.add_argument("--mode", choices=["embossed", "pyramidal", "flat"], default="embossed",
                        help="Surface mode to apply")

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
            subdivision=args.subdivision,
            mode=args.mode
        )
        path = os.path.join(args.output, f"{base_name}_cylinder_{args.mode}.stl")
        mesh.export(path)
        print("Cylinder STL saved to:", path)
    else:
        print("Add flat/embossed/pyramidal planar modes here if desired.")

if __name__ == "__main__":
    main()
