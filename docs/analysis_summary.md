# Analysis Summary: Jupyter Notebooks in /old

## 1. Dot Gain Calibration with Kernel Generation

**Key Functions**
- `analyze_scan(image_path)` – Analyzes a scanned test target to derive kernel parameters.
- `measure_edge_bleed(image, box, scan_dpi)` – Measures bleed characteristics of printed edges.
- `apply_dot_gain(image_path, kernel_path, source_dpi=1200, target_dpi=300)` – Convolves image with a kernel to simulate dot gain.
- `KernelProcessor.create_2d_kernel()` – Generates a 2D convolution kernel from measured data.
- `KernelProcessor.rescale_kernel(source_dpi, target_dpi)` – Rescales kernel to match target image DPI while preserving normalization.
- `apply_cyanotype_correction(image_path, kernel_path, lut_csv_path, target_gamma=2.2, strength=1.0)` – Applies non‑linear correction for cyanotype prints.

**Required Parameters**
- `image_path`: Path to the target image or scan.
- `kernel_path`: Path to the kernel file (`.npy` or similar) that models ink spread.
- `source_dpi`, `target_dpi`: DPI of source scan and desired output DPI.
- `lut_csv_path`: CSV lookup table for tone correction.
- `target_gamma`, `strength`: Control non‑linear correction intensity.

**Typical Workflow**
1. Capture a high‑resolution scan of a calibrated test target (`source_dpi` ≈ 1200).
2. Extract kernel parameters via `analyze_scan` and save kernel (`*.npy`).
3. Load the kernel with `KernelProcessor` and optionally rescale using `rescale_kernel`.
4. Apply the kernel to the target image using `apply_dot_gain` to simulate dot gain.
5. Optionally correct colors/tone with `apply_cyanotype_correction`.
6. Save or visualize the simulated output.

---

## 2. Image Dither with Print Simulation

**Key Functions**
- `apply_print_simulation(image_path, kernel_path, lut_csv_path, source_dpi=1200, target_dpi=300)` – Full print simulation including dithering, tone mapping, and kernel convolution.
- `apply_print_simulation_alt(...)` – Alternative implementation with additional texture generation.
- `generate_paper_texture(shape, scale=0.5, intensity=0.05)` – Procedurally creates paper texture for realism.
- `apply_cyanotype_correction(...)` – Corrects color mapping for cyanotype prints.
- Helper functions (`load_and_normalize`, `resize_to_physical_dim`, `scale_to_percentile_global`) – Support image preprocessing and resizing.

**Required Parameters**
- `image_path`: Path to the source image.
- `kernel_path`: Convolution kernel modeling dot gain.
- `lut_csv_path`: Lookup table for tone reproduction.
- `source_dpi`, `target_dpi`: DPI values for scaling.
- `percentile`, `pre_adj_strength`, `pre_gamma`: Controls for contrast and gamma adjustments.
- `BLUE_NOISE_PATH`, `kernel_source_dpi`: Paths and DPI for blue‑noise dithering kernel.

**Typical Workflow**
1. Load the source image and associated metadata (DPI, target dimensions).
2. Optionally generate or load a blue‑noise dithering kernel.
3. Apply `apply_print_simulation` (or `apply_print_simulation_alt`) which:
   - Resizes image to physical dimensions.
   - Convolves with the kernel to simulate ink spread.
   - Adjusts tone using LUT and optional gamma correction.
   - Adds paper texture for realism.
4. Export the simulated print image.

---

## 3. Laser Settings Helper

**Key Functions**
- `get_spot_size(z_mm)` – Computes spot size for a given defocus distance.
- `get_optimal_interval(spot_size, overlap)` – Calculates the line spacing needed to achieve a target overlap percentage.
- `get_dpi(interval_mm)` – Converts line interval (mm) to DPI.
- `get_power_scaling(current_z)` – Determines power scaling factor based on current defocus.
- `check_pwm_overlap(speed_mm_min, freq_hz, spot_mm)` – Validates PWM settings against overlap requirements.

**Required Parameters**
- `z_mm`: Defocus distance (mm); positive for under‑focus, negative for over‑focus.
- `feedrate`: Speed of the laser (mm/min).
- `pwm_freq`: PWM frequency (Hz).
- `overlap_target`: Desired overlap ratio (e.g., 0.5 for 50%).
- `base_spot_0mm`, `base_spot_2mm`: Baseline spot sizes at focus and -2 mm defocus.
- `max_scale`: Maximum S‑value (1000 or 255) for PWM resolution.
- `ref_z`, `ref_power_min`, `ref_power_max`: Reference calibration points.

**Typical Workflow**
1. Define desired focus depth (`target_z`) and overlap target.
2. Compute spot size using `get_spot_size(target_z)`.
3. Determine optimal line interval with `get_optimal_interval`, then convert to DPI via `get_dpi`.
4. Calculate power scaling factor with `get_power_scaling(target_z)`.
5. Validate PWM configuration using `check_pwm_overlap`.
6. Use reference points (`ref_z`, `ref_power_min/max`) to set final power settings.
7. Adjust machine parameters accordingly.

---

**Overall Observations**
- All three processes heavily rely on kernel‑based convolution to model physical phenomena (dot gain, ink spread, laser spot behavior).
- DPI handling is critical; source scans are typically at 1200 DPI, while output prints or simulations target 260–300 DPI.
- Non‑linear corrections (gamma, LUT) are applied to mimic real‑world print behavior.
- The laser helper integrates geometric optics (spot size vs. defocus) with process parameters (feedrate, PWM) to produce reproducible printing settings.

*File saved: `analysis_summary.md` in the project root.*