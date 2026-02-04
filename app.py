import gradio as gr
import numpy as np
import cv2
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image
import io
import pandas as pd
import lasercyano_defaults as defaults
from print_simulation import apply_print_simulation_alt
from dotgain_cal import analyze_geometric_grid_v2, generate_calchart_target, refine_calibration_curve
from dither_image import apply_cyanotype_correction, dither_image
from laser_settings import get_spot_size, get_optimal_interval, get_dpi, get_power_scaling, check_pwm_overlap


# ======================
# GRADIO APP LAYOUT
# ======================

def dot_gain_interface():
    """Create Gradio interface for dot gain calibration."""
    with gr.Tab("Dot Gain Calibration"):
        with gr.Row():
            image_input = gr.File(label="Input Image", type="filepath")
            kernel_input = gr.TextArea(label="Kernel File", type="text", value=defaults.kernel_file)
            lut_input = gr.TextArea(label="LUT CSV", type="text", value=defaults.lut_file) 
            
            with gr.Column():
                source_dpi = gr.Slider(600, 1200, value=defaults.kernel_source_dpi, label="Source DPI")
                target_dpi = gr.Slider(150, 600, value=defaults.target_image_dpi, label="Target DPI")
                target_gamma = gr.Slider(1.0, 3.0, value=defaults.pre_gamma, label="Target Gamma")
                strength = gr.Slider(0.0, 1.0, value=defaults.pre_adj_strength, label="Strength")
                
                process_btn = gr.Button("Process Image")
                output_image = gr.Image(label="Simulated Output")
                
                process_btn.click(
                    fn=lambda img_path, kernel_path, lut_path, source_dpi, target_dpi, target_gamma, strength: 
                        dither_image(
                            img_path, kernel_path, lut_path, source_dpi, target_dpi, target_gamma, strength
                        ),
                    inputs=[image_input, kernel_input, lut_input, source_dpi, target_dpi, target_gamma, strength],
                    outputs=output_image
                )
                
                # Additional Analyze Grid button
                analyze_btn = gr.Button("Analyze Grid")
                analyze_output = gr.Image(label="Analysis Output")
                
                analyze_btn.click(
                    fn=lambda img_path: refine_calibration_curve(img_path)[1],
                    inputs=image_input,
                    outputs=analyze_output
                )
                
                # Additional Generate Target button
                target_btn = gr.Button("Generate Calibration Target")
                target_output = gr.Image(label="Target Output")
                
                target_btn.click(
                    fn=lambda: generate_calchart_target(),
                    inputs=None,
                    outputs=target_output
                )
        return gr.Tab("Dot Gain Calibration")

def print_simulation_interface():
    """Create Gradio interface for image dither with print simulation."""
    with gr.Tab("Image Dither & Print Simulation"):
        with gr.Row():
            with gr.Column():
                source_dpi = gr.Slider(600, 1200, value=defaults.kernel_source_dpi, label="Source DPI")
                target_dpi = gr.Slider(150, 600, value=defaults.target_image_dpi, label="Target DPI")
                target_longest_edge = gr.Slider(50, 500, value=defaults.TARGET_LONGEST_EDGE_MM, label="Target Longest Edge (mm)")
                percentile = gr.Slider(1, 99, value=defaults.percentile, label="Percentile")
                pre_adj_strength = gr.Slider(0.0, 1.0, value=defaults.pre_adj_strength, label="Pre-Adjust Strength")
                pre_gamma = gr.Slider(1.0, 3.0, value=defaults.pre_gamma, label="Pre-Gamma")
                power_levels_input = gr.Textbox(lines=1, placeholder="Enter power levels as comma-separated values (e.g., 0.0,0,0,1.0)", value="0.0,0,0,1.0", label="Power Levels")
            with gr.Column():
                    output_image = gr.Image(label="Dithered Print")
            with gr.Column():
                process_dit_btn = gr.Button("Dither Image")
                
                process_sim_btn = gr.Button("Simulate Image")
                
                image_input = gr.File(label="Input Image", type="filepath")
                kernel_input = gr.TextArea(label="Kernel File", type="text", value=defaults.kernel_file)
                lut_input = gr.TextArea(label="LUT CSV", type="text", value=defaults.lut_file)
                blue_noise_input = gr.TextArea(label="Blue Noise Kernel", type="text", value=defaults.BLUE_NOISE_PATH)
                process_sim_btn.click(
                    fn=lambda img_path, kernel_path, lut_path, source_dpi, target_dpi, percentile, pre_adj_strength, pre_gamma, blue_noise_path, target_longest_edge:
                        print_simulation_process(img_path, kernel_path, lut_path, source_dpi, target_dpi, percentile, pre_adj_strength, pre_gamma, blue_noise_path, target_longest_edge),
                    inputs=[image_input, kernel_input, lut_input, source_dpi, target_dpi, 
                           percentile, pre_adj_strength, pre_gamma, blue_noise_input, target_longest_edge],
                    outputs=output_image
                )
                process_dit_btn.click(
                    fn=lambda img_path, kernel_path, lut_path, source_dpi, target_dpi, 
                           percentile, pre_adj_strength, pre_gamma, blue_noise_path, target_longest_edge: 
                        dither_image(
                            img_path, kernel_path, lut_path, source_dpi, target_dpi, 
                            percentile, pre_adj_strength, pre_gamma, blue_noise_path, target_longest_edge 
                        ),
                    inputs=[image_input, kernel_input, lut_input, source_dpi, target_dpi, 
                           percentile, pre_adj_strength, pre_gamma, blue_noise_input, target_longest_edge],
                    outputs=output_image
                )
    return gr.Tab("Image Dither & Print Simulation")
    
def print_simulation_process(img_path, kernel_path, lut_path, source_dpi, target_dpi, percentile, pre_adj_strength, pre_gamma, blue_noise_path, target_longest_edge):
    output_image = dither_image(img_path, kernel_path, lut_path, source_dpi, target_dpi, percentile, pre_adj_strength, pre_gamma, blue_noise_path, target_longest_edge)
    output_image.save("scratch/out_dithered.png")
    out_img_path = "scratch/out_dithered.png"
    sim_rgb = apply_print_simulation_alt(out_img_path, kernel_path, lut_path, source_dpi, target_dpi),
    return sim_rgb[0]

def laser_settings_interface():
    """Create Gradio interface for laser settings helper."""
    with gr.Tab("Laser Settings Helper"):
        with gr.Row():
            with gr.Column():
                z_input = gr.Slider(-5, 5, value=defaults.target_z, label="Defocus Distance (z_mm)")
                feedrate_input = gr.Slider(10, 8000, value=defaults.feedrate, label="Feedrate (mm/min)")
                pwm_freq_input = gr.Slider(1, 10000, value=defaults.pwm_freq, label="PWM Frequency (Hz)")
                overlap_input = gr.Slider(0.1, 0.9, value=defaults.overlap_target, label="Overlap Target")
            
        with gr.Column():
            base_spot_0mm = gr.Slider(0.05, 0.5, value=defaults.base_spot_0mm, label="Base Spot at 0mm")
            base_spot_2mm = gr.Slider(0.05, 0.5, value=defaults.base_spot_2mm, label="Base Spot at -2mm")
            max_scale = gr.Slider(0, 4000, value=defaults.max_scale, label="Max Scale (1000 or 255)")
            ref_z = gr.Slider(-5, 5, value=defaults.ref_z, label="Reference Z (mm)")
            ref_power_min = gr.Slider(1, 100, value=defaults.ref_power_min, label="Ref Power Min")
            ref_power_max = gr.Slider(20, 4000, value=defaults.ref_power_max, label="Ref Power Max")
            
            process_btn = gr.Button("Calculate Settings")
            output_text = gr.Textbox(label="Calculated Settings")
            
            process_btn.click(
                fn=lambda z, feedrate, pwm_freq, overlap_target, 
                        base_spot_0mm, base_spot_2mm, max_scale, ref_z, 
                        ref_power_min, ref_power_max: 
                    _calculate_laser_settings(
                        z, feedrate, pwm_freq, overlap_target, 
                        base_spot_0mm, base_spot_2mm, max_scale, ref_z, 
                        ref_power_min, ref_power_max
                    ),
                inputs=[z_input, feedrate_input, pwm_freq_input, overlap_input,
                        base_spot_0mm, base_spot_2mm, max_scale, ref_z, 
                        ref_power_min, ref_power_max],
                outputs=output_text
            )
        return gr.Tab("Laser Settings Helper")

def _calculate_laser_settings(z, feedrate, pwm_freq, overlap_target, 
                              base_spot_0mm, base_spot_2mm, max_scale, ref_z, 
                              ref_power_min, ref_power_max):
    """Internal function to calculate laser settings."""
    spot_size = get_spot_size(z, base_spot_0mm, base_spot_2mm)
    interval_mm = get_optimal_interval(spot_size, overlap_target)
    dpi = get_dpi(interval_mm)
    power_scaling_min, power_scaling_max = get_power_scaling(z, ref_z, ref_power_min, ref_power_max, max_scale, overlap_target)
    
    # Validate PWM overlap
    overlaps = check_pwm_overlap(feedrate, pwm_freq, spot_size)
    
    quality_status = "PERFECT" if overlaps > 3 else "WARNING: DOTS VISIBLE"
    
    # Prepare output similar to notebook printout
    output = (
        "--- OPTIMIZED SETTINGS CALCULATOR ---\n"
        f"Target Z-Offset:     {z} mm\n"
        f"Target Feedrate:     {feedrate} mm/min\n"
        f"Target PWM Freq:     {pwm_freq} Hz\n"
        "-" * 35 + "\n"
        f"1. Calculated Spot:  {spot_size:.3f} mm\n"
        f"2. Line Interval:    {interval_mm:.3f} mm\n"
        f"3. Recommended DPI:  {int(dpi)} DPI\n"
        "-" * 35 + "\n"
        f"4. Min Power (S):    {int(power_scaling_min)}  (Start of burn)\n"
        f"5. Max Power (S):    {int(power_scaling_max)}  (Solid Black)\n"
        "-" * 35 + "\n"
        f"6. PWM Stability:    {overlaps:.1f} pulses per dot\n"
        f"   Status:           {quality_status}"
    )
    
    return output

# ======================
# MAIN APP LAYOUT
# ======================

def create_gradio_app():
    """Create and return the Gradio app."""
    with gr.Blocks() as demo:
        gr.Markdown("# UV Laser Cyano Print Dither & Simulation App")
        gr.Markdown("Interactive tool for dot gain calibration, dither generation, print simulation and laser settings")
        
        # Create tabs for each process
        tab1 = print_simulation_interface()
        tab2 = dot_gain_interface()
        tab3 = laser_settings_interface()
        
        # Combine all tabs
        with gr.Tab("All Tools"):
            with gr.Row():
                gr.Markdown("Use the individual tabs to access specific tools for print simulation, dot gain calibration, and laser settings optimization.")
                gr.Markdown("This combined tab is a placeholder to guide users to the individual tools.")
                gr.Markdown("Please select the desired tool from the tabs above to get started.")
    
    return demo

if __name__ == "__main__":
    app = create_gradio_app()
    app.launch(server_name="0.0.0.0", server_port=7860)