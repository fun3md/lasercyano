# Algorithmic Indigo (LaserCyano) - README

[Banner Image]

## Overview
Algorithmic Indigo is an open-source system that transforms digital images into cyanotype prints using a UV laser engraver. This repository includes a Gradio web interface for interactive control of the workflow.

## 📖 Documentation
- [System Overview](docs/project_overview.md)
- [Calibration & Workflow](docs/analysis_summary.md)
- [Dithering Pipeline](docs/dither_image_pipeline_summary.md)
- [Blue Noise & Spatial Deconvolution](docs/blue_noise_and_spatial_deconvolution_explanation.md)

## 🚀 Gradio Web Interface
The Gradio demo provides a point‑and‑click interface to generate laser maps from images.

## Setup

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate it:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

```bash
python app.py
```
open browser to http://localhost:7860  

### Interface Walkthrough
| Control | Description |
|---------|-------------|
| **Input Image** | Upload or drag‑drop a source image (JPG, PNG, etc.). |
| **Kernel File** | Path to the dot‑gain kernel file (e.g., `avg_deconvolution_kernel_1200dpi.npy`). |
| **LUT CSV** | Path to the calibrated LUT file (e.g., `cyanotype_lut.csv`). |
| **Blue Noise Kernel** | Path to the 128×128 blue‑noise dithering kernel file. |
| **Source DPI** | DPI of the scanned image; influences dot size calculation. |
| **Target DPI** | Desired print resolution; determines line interval (e.g., 0.065 mm). |
| **Target Longest Edge** | Physical length of the longest edge of the print (mm). |
| **Percentile** | White‑clamp percentile for contrast adjustment (e.g., 93 %). |
| **Pre‑Adjust Strength** | Strength parameter for pre‑adjustment in dithering (0‑1). |
| **Power Levels** | Comma‑separated list of power levels (e.g., `0.0,0,0,1.0`) mapping grayscale to laser power. |
| **Process Image** | Compute the optimized laser map using the current settings. |
| **Simulate Image** | Run a print‑simulation preview (`print_simulation_process`) and display `scratch/out_dithered.png`. |
| **Dither Image** | Generate the final dithered bitmap (`dither_image`). |
| **Output Image** | Real‑time preview of the dithered result; updates as you adjust parameters. |
| **Download Dithered Image** | Download the generated `scratch/out_dithered.png` file. |

For a comprehensive walkthrough, see the `lasercyano_howto_gradio.md` documentation.

### Advanced Options
- **Noise Level Slider** – Controls the amount of blue‑noise dithering; higher values produce finer grain but may increase processing time.
- **Spread Profile Dropdown** – Choose preset diffusion profiles (e.g., *Fine Art Paper*, *Coated Board*) or load a custom profile.
- **Live Preview Checkbox** – When enabled, the interface updates the simulated output in real time as you adjust parameters.

## 🛠️ Hardware Requirements
- UV laser engraver (e.g., TwoTrees TTS‑55 Pro)
- Flatbed scanner (≥1200 DPI)
- Heavy watercolor paper (300 gsm+)
- Cyanotype chemicals (potassium ferricyanide + ferric ammonium citrate)


## 📄 License
GNU GPL v3.0 – see [LICENSE](LICENSE) for details.

---

*Algorithmic Indigo – Where code meets chemistry, pixels become Prussian blue.*