# How‑to Guide: Using the LaserCyano Application with the Gradio Interface

*This guide explains the end‑to‑end workflow for preparing and printing cyanotype prints using the **LaserCyano** application. The process is orchestrated through the built‑in Gradio web interface (referenced as `app.py`). No JupyterBooks are used.*

---

## Table of Contents
1. [Prerequisites](#prerequisites)  
2. [Physical Calibration](#physical-calibration)  
3. [Digital Image Processing](#digital-image-processing)  
4. [Hardware Setup](#hardware-setup)  
5. [Printing via the Gradio App](#printing-via-the-gradio-app)  
6. [Development & Post‑Processing](#development--post-processing)  
7. [Troubleshooting](#troubleshooting)  
8. [References & Naming Conventions](#references--naming-conventions)  

---

## Prerequisites
- **LaserCyano** repository cloned and installed (`pip install -r requirements.txt`).
- A calibrated laser cutter running **LaserGRBL** firmware.
- Cyanotype paper, glass plate, and shims for bed leveling.
- Python 3.9+ environment with the following packages:
  - `gradio`, `numpy`, `scipy`, `opencv-python`, `matplotlib`
- Sufficient storage on the `scratch/` directory for intermediate files.

---

## Physical Calibration
1. **Z‑Offset**  
   - Set the laser focus to **-1.0 mm** using the LaserGRBL console.  
2. **Power Limits**  
   - Run a **Speed‑vs‑Power** test.  
   - Record the **White Point** step (e.g., `14`) and **Black Point** step (e.g., `65`).  
3. **Dot Gain Kernels**  
   - Print a calibration pattern.  
   - Scan at **1200 DPI**.  
   - Process with `dotgain_calibration.py` → generates a **Correction LUT** and an **Average Kernel**.  

> **Tip:** Store the resulting LUT and kernel under `cal_data/` for later use.

---

## Digital Image Processing
1. **Load Image**  
   - Open the target image in the Gradio UI (see *Image Input* component).  
2. **Target DPI & Dimensions**  
   - Set **Target DPI** to **390 DPI** (line interval ≈ **0.065 mm**).  
   - Ensure the longest edge (e.g., **270 mm**) matches the desired print size.  
3. **Contrast Adjustment**  
   - Apply a **White Clamp Percentile** of **93 %** to stretch the histogram.  
4. **Correction**  
   - Load the previously generated **LUT** and **kernel**.  
   - Run **Deconvolution** with:  
     - `Strength = 0.5`  
     - `Gamma = 1.0`  
5. **Dithering**  
   - Apply **Blue‑Noise Dithering** using the 128×128 matrix located in `bluenoise/128_128/`.  

---

## Hardware Setup
- **Mount** cyanotype paper on a glass plate using shims.  
- **Level** the bed to a tolerance of **0.2‑0.3 mm**.  
- **Re‑verify** the Z‑Offset at **-1.0 mm** before each print run.  

---

## Printing via the Gradio App
The Gradio interface (`app.py`) provides a unified UI for the entire pipeline.

| Component | Description |
|-----------|-------------|
| **Image Input** | Upload your processed image (PNG/JPEG). |
| **Print Simulation** | Checkbox to run `print_simulation_process`. |
| **Laser Mode** | Select **M3 (Static Power)** to avoid banding. |
| **Feed/Speed** | Set **3500 mm/min** and **Line Interval 0.065 mm**. |
| **Power Mapping** | Map grayscale to **S‑Min** (e.g., `14`) and **S‑Max** (e.g., `65`). |
| **Execute Print** | Click the **Print** button. |

### Pipeline Internals (referenced names)
- **`print_simulation_process`** – orchestrates dithering & simulation, writes the final bitmap to `scratch/out_dithered.png`.  
- **`dither_image`** – core function that produces the final bitmap after all corrections.  
- **`apply_print_simulation_alt`** – adds a visual print‑simulation overlay.  
- **`M3 (Static Power)`** – recommended laser mode for stable power delivery.  
- **`scratch/out_dithered.png`** – output file path used throughout the pipeline; the Gradio app displays this image after processing.

When the **Print** button is pressed, the backend calls `dither_image`, applies the LUT & kernel, runs deconvolution, adds dithering, and finally invokes `print_simulation_process` to generate `scratch/out_dithered.png`. The resulting image is returned to the UI for visual confirmation.

---

## Development & Post‑Processing
1. **Rinse** the printed plate in running water for 30 seconds.  
2. **Oxidize** in a dilute **H₂O₂** bath (≈ 1 % solution) for 2 minutes.  
3. **Dry** flat; avoid direct sunlight to prevent premature exposure.  

> **Note:** All intermediate files (e.g., `scratch/out_dithered.png`) are automatically cleaned by the Gradio app on session end.

---

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Banding in print | Laser mode not set to **M3** or power mapping incorrect | Switch to **M3 (Static Power)** and verify S‑Min/S‑Max values. |
| Image appears too dark | White Point step too low | Increase White Point step (e.g., from 14 → 16). |
| Dithering artifacts | Blue‑Noise matrix mismatch | Ensure the correct 128×128 matrix is loaded from `bluenoise/128_128/`. |
| Simulation preview not matching output | `print_simulation_process` not executed | Enable the *Print Simulation* checkbox in the Gradio UI. |

---

## References & Naming Conventions
- **`print_simulation_process`** – orchestrates the full pipeline and writes `scratch/out_dithered.png`.  
- **`dither_image`** – core function generating the final bitmap.  
- **`apply_print_simulation_alt`** – adds visual simulation overlay.  
- **`M3 (Static Power)`** – laser mode to prevent banding.  
- **`scratch/out_dithered.png`** – final output path used consistently across steps.  

For more detailed technical notes, see:
- `docs/dither_image_pipeline_summary.md`  
- `docs/blue_noise_and_spatial_deconvolution_explanation.md`  

---

*End of Guide*  
