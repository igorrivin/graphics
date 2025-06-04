import gradio as gr
from generate import create_cylinder_mesh  # Import from your modified script

def generate_cylinder(image, height, radius, emboss_depth, fn, fh, roller_handle, spiked_mode, spike_downsample_factor, spike_base_scale, spike_base_aspect_ratio):
    if image is None:
        return None, None, "Please upload an image."
    
    # Save the uploaded image temporarily
    image_path = "temp_image.png"
    image.save(image_path)
    
    # Call the cylinder mesh generator
    try:
        output_stl = create_cylinder_mesh(
            image_path,
            height,
            radius,
            emboss_depth,
            fn,
            fh,
            roller_handle,
            spiked_mode,
            spike_downsample_factor,
            spike_base_scale,
            spike_base_aspect_ratio
        )
        return output_stl, output_stl, ""
    except Exception as e:
        return None, None, f"Error: {str(e)}"

# Define the Gradio interface
with gr.Blocks(title="Cylinder Seal Generator") as demo:
    gr.Markdown("# Cylinder Seal Generator")
    gr.Markdown("Upload an image, set parameters, and preview the 3D cylinder seal before downloading the STL file.")
    
    with gr.Row():
        with gr.Column():
            image_input = gr.Image(type="pil", label="Upload Image")
            height = gr.Slider(10, 100, value=20, step=1, label="Cylinder Height (mm)")
            radius = gr.Slider(5, 50, value=5, step=0.5, label="Cylinder Radius (mm)")
            emboss_depth = gr.Slider(0.1, 5, value=0.5, step=0.1, label="Emboss/Spike Depth (mm)")
            fn = gr.Number(value=200, label="Angular Resolution (faces around cylinder)", precision=0)
            fh = gr.Number(value=200, label="Vertical Resolution (faces along height)", precision=0)
            roller_handle = gr.Checkbox(label="Add Roller Handle Stubs")
            spiked_mode = gr.Checkbox(label="Spiked Mode (for blocky designs)")
            spike_downsample_factor = gr.Slider(1, 32, value=8, step=1, label="Spike Downsample Factor (higher = fewer spikes)")
            spike_base_scale = gr.Slider(0.5, 2.0, value=1.0, step=0.1, label="Spike Base Scale (higher = wider spikes)")
            spike_base_aspect_ratio = gr.Slider(0.2, 2.0, value=0.52, step=0.1, label="Spike Base Aspect Ratio (vertical/horizontal)")
            generate_btn = gr.Button("Generate STL")
        
        with gr.Column():
            gr.Markdown("### Preview and Download")
            model_preview = gr.Model3D(label="3D Model Preview", clear_color=[0.9, 0.9, 0.9, 1.0])
            output_file = gr.File(label="Download STL File")
            error_message = gr.Markdown()
    
    generate_btn.click(
        fn=generate_cylinder,
        inputs=[image_input, height, radius, emboss_depth, fn, fh, roller_handle, spiked_mode, spike_downsample_factor, spike_base_scale, spike_base_aspect_ratio],
        outputs=[model_preview, output_file, error_message]
    )

# Launch the interface
demo.launch()