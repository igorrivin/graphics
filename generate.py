from PIL import Image
import math
import numpy as np
from stl import Mesh
import argparse

def create_cylinder_mesh(image_path, cylinder_height, cylinder_radius, emboss_depth, fn, fh, roller_handle, spiked_mode, spike_downsample_factor=8, spike_base_scale=1.0, spike_base_aspect_ratio=0.52):
    """
    Generate a 3D cylinder mesh with embossing or spikes based on an input image.

    Args:
        image_path (str): Path to the input image.
        cylinder_height (float): Height of the cylinder in mm.
        cylinder_radius (float): Radius of the cylinder in mm.
        emboss_depth (float): Depth of embossing or spike height in mm.
        fn (int): Angular resolution (number of faces around the cylinder).
        fh (int): Vertical resolution (number of faces along the height).
        roller_handle (bool): If True, add stubs for a mini paint roller handle.
        spiked_mode (bool): If True, generate spikes instead of embossing.
        spike_downsample_factor (int): Downsampling factor for spike placement (higher = fewer spikes).
        spike_base_scale (float): Scale factor for spike base radius relative to spike height.
        spike_base_aspect_ratio (float): Aspect ratio for spike base (vertical/horizontal).

    Returns:
        str: Path to the generated STL file.

    Note:
        - The generated STL file should be watertight and render as a solid object in viewers like Cura.
        - Some viewers (e.g., Gradio, Xcode STL viewer) may render the model as transparent due to default material settings.
        - For accurate rendering, validate the model in Cura or another 3D printing slicer before printing.
    """
    # Load and process image
    image = Image.open(image_path)
    greyscale_image = image.convert("L")
    rescaled_image = greyscale_image.resize((fn, fh))
    
    points = []
    faces = []
    angle_step = 2 * math.pi / fn
    height_step = cylinder_height / fh
    
    # Handle roller stubs if enabled
    stub_length = 10.0 if roller_handle else 0.0  # 10mm stubs for roller handle
    stub_radius = 6.0  # Standard mini roller core diameter
    total_height = cylinder_height + 2 * stub_length
    height_offset = stub_length
    
    # Generate base cylinder surface points (same in both modes)
    base_indices = [[-1 for _ in range(fn)] for _ in range(fh)]
    for y in range(fh):
        for x in range(fn):
            angle = x * angle_step
            px = cylinder_radius * math.cos(angle)
            py = cylinder_radius * math.sin(angle)
            pz = y * height_step + height_offset
            base_idx = len(points)
            points.append((px, py, pz))
            base_indices[y][x] = base_idx
    
    # Generate faces for the base cylinder surface (ensure outward normals)
    for y in range(fh - 1):
        for x in range(fn):
            p1 = base_indices[y][x]
            p2 = base_indices[y][(x + 1) % fn]
            p3 = base_indices[y + 1][(x + 1) % fn]
            p4 = base_indices[y + 1][x]
            faces.append((p1, p2, p3))  # Counterclockwise (outward normal)
            faces.append((p4, p3, p1))  # Counterclockwise (outward normal)
    
    if spiked_mode:
        # Downsample the image for spike placement (user-settable factor, default 8)
        spike_fn = max(1, fn // spike_downsample_factor)
        spike_fh = max(1, fh // spike_downsample_factor)
        spike_image = greyscale_image.resize((spike_fn, spike_fh))
        
        # Number of points to form the base of each spike (for a conical shape)
        num_base_points = 6  # Hexagonal base for symmetry
        
        # Map downsampled coordinates back to full resolution for base points
        for y in range(spike_fh):
            for x in range(spike_fn):
                pixel_value = spike_image.getpixel((x, y))
                if pixel_value > 128:
                    # Map downsampled (x, y) to full-resolution (orig_x, orig_y)
                    orig_x = (x * fn) // spike_fn
                    orig_y = (y * fh) // spike_fh
                    # Ensure within bounds
                    orig_x = min(orig_x, fn - 1)
                    orig_y = min(orig_y, fh - 1)
                    # Use existing base point as the center
                    center_idx = base_indices[orig_y][orig_x]
                    center_point = points[center_idx]
                    center_x, center_y, center_z = center_point
                    
                    # Add spike tip (radially outward)
                    spike_height = emboss_depth
                    tip_x = center_x * (1 + spike_height/cylinder_radius)
                    tip_y = center_y * (1 + spike_height/cylinder_radius)
                    tip_z = center_z
                    tip_idx = len(points)
                    points.append((tip_x, tip_y, tip_z))
                    
                    # Create a small ring of points around the center to form the spike's base
                    base_radius = spike_height * spike_base_scale  # User-configurable base radius
                    base_point_indices = []
                    for i in range(num_base_points):
                        angle = (2 * math.pi * i) / num_base_points
                        # Offset in the xy-plane (perpendicular to the radial direction)
                        offset_x = base_radius * math.cos(angle)
                        offset_y = base_radius * math.sin(angle) * spike_base_aspect_ratio  # Apply aspect ratio
                        # Rotate the offset to be tangent to the cylinder surface
                        radial_magnitude = math.sqrt(center_x**2 + center_y**2)
                        if radial_magnitude > 0:
                            radial_x = center_x / radial_magnitude
                            radial_y = center_y / radial_magnitude
                            # Tangent direction is perpendicular to radial (rotate 90 degrees)
                            tangent_x = -radial_y
                            tangent_y = radial_x
                            # Apply offset in the tangent direction
                            px = center_x + offset_x * tangent_x - offset_y * radial_x
                            py = center_y + offset_x * tangent_y - offset_y * radial_y
                            pz = center_z
                            base_point_idx = len(points)
                            points.append((px, py, pz))
                            base_point_indices.append(base_point_idx)
                    
                    # Connect the center point to the base points to attach to the cylinder
                    for i in range(num_base_points):
                        j = (i + 1) % num_base_points
                        faces.append((center_idx, base_point_indices[i], base_point_indices[j]))
                    
                    # Connect the base points to the tip to form the spike
                    for i in range(num_base_points):
                        j = (i + 1) % num_base_points
                        faces.append((base_point_indices[i], base_point_indices[j], tip_idx))
    else:
        # Emboss the base surface
        for y in range(fh):
            for x in range(fn):
                pixel_value = rescaled_image.getpixel((x, y))
                distance_from_axis = cylinder_radius + (pixel_value / 255.0) * emboss_depth
                angle = x * angle_step
                idx = base_indices[y][x]
                points[idx] = (
                    distance_from_axis * math.cos(angle),
                    distance_from_axis * math.sin(angle),
                    points[idx][2]  # Keep z-coordinate
                )
    
    # Add roller handle stubs if enabled
    if roller_handle:
        stub_points_start = len(points)
        
        # Bottom stub
        for x in range(fn):
            angle = x * angle_step
            px = stub_radius * math.cos(angle)
            py = stub_radius * math.sin(angle)
            pz = 0.0
            points.append((px, py, pz))
        
        # Top stub
        for x in range(fn):
            angle = x * angle_step
            px = stub_radius * math.cos(angle)
            py = stub_radius * math.sin(angle)
            pz = total_height
            points.append((px, py, pz))
        
        # Stub faces
        for x in range(fn):
            # Bottom stub side faces
            p1 = stub_points_start + x
            p2 = stub_points_start + (x + 1) % fn
            p3 = base_indices[0][x]  # Connect to main cylinder bottom
            p4 = base_indices[0][(x + 1) % fn]
            faces.append((p1, p2, p3))
            faces.append((p2, p4, p3))
            
            # Top stub side faces
            p1 = stub_points_start + fn + x
            p2 = stub_points_start + fn + (x + 1) % fn
            p3 = base_indices[fh - 1][x]
            p4 = base_indices[fh - 1][(x + 1) % fn]
            faces.append((p1, p2, p3))
            faces.append((p2, p4, p3))
        
        # Stub end caps
        bottom_center = len(points)
        points.append((0, 0, 0))
        top_center = len(points)
        points.append((0, 0, total_height))
        
        for x in range(fn):
            # Bottom cap
            p1 = stub_points_start + x
            p2 = stub_points_start + (x + 1) % fn
            faces.append((bottom_center, p2, p1))
            # Top cap
            p1 = stub_points_start + fn + x
            p2 = stub_points_start + fn + (x + 1) % fn
            faces.append((top_center, p1, p2))
    else:
        # Normal end caps using base indices
        top_center_index = len(points)
        points.append((0, 0, cylinder_height + height_offset))
        for x in range(fn):
            p1 = base_indices[fh - 1][x]
            p2 = base_indices[fh - 1][(x + 1) % fn]
            faces.append((top_center_index, p1, p2))
        
        bottom_center_index = len(points)
        points.append((0, 0, height_offset))
        for x in range(fn):
            p1 = base_indices[0][x]
            p2 = base_indices[0][(x + 1) % fn]
            faces.append((bottom_center_index, p2, p1))
    
    # Create and save mesh
    points_array = np.array(points)
    faces_array = np.array(faces)
    cylinder_mesh = Mesh(np.zeros(faces_array.shape[0], dtype=Mesh.dtype))
    
    for i, face in enumerate(faces_array):
        for j in range(3):
            cylinder_mesh.vectors[i][j] = points_array[face[j], :]
    
    output_stl = image_path.rsplit('.', 1)[0] + ".stl"
    cylinder_mesh.save(output_stl)
    return output_stl

def main():
    parser = argparse.ArgumentParser(description="Generate a 3D embossed or spiked cylinder from an image.")
    parser.add_argument("image_path", help="Path to the input image")
    parser.add_argument("--height", type=float, default=20, help="Height of the cylinder (default: 20mm)")
    parser.add_argument("--radius", type=float, default=5, help="Radius of the cylinder (default: 5mm)")
    parser.add_argument("--emboss-depth", type=float, default=0.5, help="Depth of embossing or spike height (default: 0.5mm)")
    parser.add_argument("--fn", type=int, default=200, help="Angular resolution (number of faces around cylinder, default: 200)")
    parser.add_argument("--fh", type=int, default=200, help="Vertical resolution (number of faces along height, default: 200)")
    parser.add_argument("--roller-handle", action="store_true", help="Add stubs for mini paint roller handle")
    parser.add_argument("--spiked-mode", action="store_true", help="Generate spikes instead of embossing (for blocky designs)")
    parser.add_argument("--spike-downsample-factor", type=int, default=8, help="Downsampling factor for spikes in spiked mode (default: 8)")
    parser.add_argument("--spike-base-scale", type=float, default=1.0, help="Scale factor for spike base radius relative to spike height (default: 1.0)")
    parser.add_argument("--spike-base-aspect-ratio", type=float, default=0.52, help="Aspect ratio for spike base (vertical/horizontal, default: 0.52)")
    
    args = parser.parse_args()
    
    output = create_cylinder_mesh(
        args.image_path,
        args.height,
        args.radius,
        args.emboss_depth,
        args.fn,
        args.fh,
        args.roller_handle,
        args.spiked_mode,
        args.spike_downsample_factor,
        args.spike_base_scale,
        args.spike_base_aspect_ratio
    )
    print(f"Generated STL file: {output}")

if __name__ == "__main__":
    main()