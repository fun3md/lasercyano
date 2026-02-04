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

### Launch the Interface
```bash
python gradio_demo.py --model cyanotype_lut.csv --dpi 318
```

### Interface Walkthrough
| Control | Description |
|---------|-------------|
| **Input Image** | Upload or drag‑drop a source image (JPG, PNG, etc.). |
| **LUT Selector** | Choose the calibrated LUT file (e.g., `cyanotype_lut.csv`). |
| **DPI Setting** | Enter your engraver’s resolution (e.g., `318`). |
| **Size Control** | Specify the physical dimensions of the print (e.g., `60mm`). |
| **Generate Laser Map** | Click to compute the optimized laser pattern. |
| **Export** | Download the resulting PNG for use in your laser engraver software. |
| **Noise Level** | Adjust blue‑noise intensity for dithering. |
| **Spread Profile** | Customize diffusion based on material tests. |
| **Real‑time Preview** | Toggle live visualization of the simulated output. |

### Example Workflow
1. **Upload** a portrait photograph.
2. **Select** the calibrated LUT (`cyanotype_lut.csv`).
3. **Set** DPI to `318` and **Size** to `60mm`.
4. **Click** *Generate Laser Map* – the system outputs `laser_map.png`.
5. **Download** the PNG and load it into your laser engraver software.
6. **Print** using the -2 mm focus offset for chemical penetration.

### Advanced Options
- **Noise Level Slider** – Controls the amount of blue‑noise dithering; higher values produce finer grain but may increase processing time.
- **Spread Profile Dropdown** – Choose preset diffusion profiles (e.g., *Fine Art Paper*, *Coated Board*) or load a custom profile.
- **Live Preview Checkbox** – When enabled, the interface updates the simulated output in real time as you adjust parameters.

## 📚 Links to Related Documentation
- [Calibration Summary](docs/analysis_summary.md) – Detailed steps for generating and applying LUTs.
- [Dithering Pipeline Overview](docs/dither_image_pipeline_summary.md) – Technical description of the adaptive dithering algorithm.
- [Blue Noise & Spatial Deconvolution](docs/blue_noise_and_spatial_deconvolution_explanation.md) – Explanation of the noise generation and deconvolution techniques.
- [Project Architecture](docs/project_overview.md) – High‑level diagram and component breakdown.

## 🛠️ Hardware Requirements
- UV laser engraver (e.g., TwoTrees TTS‑55 Pro)
- Flatbed scanner (≥1200 DPI)
- Heavy watercolor paper (300 gsm+)
- Cyanotype chemicals (potassium ferricyanide + ferric ammonium citrate)

## 📈 Performance Highlights
- **80 tonal levels** (vs. 10‑15 in traditional cyanotype)
- **<50 µm edge control**
- **±3 % repeatability**

## 📄 License
GNU GPL v3.0 – see [LICENSE](LICENSE) for details.

---

*Algorithmic Indigo – Where code meets chemistry, pixels become Prussian blue.*