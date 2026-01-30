# **Algorithmic Indigo (LaserCyano)** - Project Overview

## **Project Summary**

**Algorithmic Indigo** is a sophisticated computational photography system that bridges digital imaging with traditional cyanotype printing using a UV laser engraver. The project implements a complete pipeline from digital image to physical cyanotype print through:

1. **Advanced image processing** with adaptive dithering algorithms
2. **Physical calibration** of laser-material interactions
3. **Realistic simulation** of cyanotype printing physics
4. **Hardware integration** with UV laser systems

The system compensates for the non-linear responses of both the cyanotype chemistry and the laser engraver, enabling high-fidelity photographic reproduction on a traditional alternative process medium.

---

## **Technical Architecture**

### **1. Core Computational Pipeline**

#### **A. Calibration System** (`dot_gain_calibration.py`)
- **Target Generation**: Creates multi-feature calibration patterns including:
  - Step wedges (0-80 power levels)
  - Frequency wedges (varying dot spacing)
  - Resolution test patterns
  - Fiducial markers for automatic alignment
  - White runout borders for laser positioning

- **Scan Analysis**:
  - Automated patch detection using adaptive thresholding
  - Perspective correction via fiducial markers
  - Edge bleed quantification (10-90% transition width)
  - Modulation Transfer Function (MTF) calculation
  - 2D Point Spread Function (PSF) kernel extraction

- **Lookup Table Creation**:
  - Measures actual density vs. commanded power
  - Applies spline smoothing (UnivariateSpline)
  - Generates compensation LUT for non-linear response
  - Exports CSV for dithering engine

#### **B. Dithering Engine** (`dither_experiment.py`)
- **Multi-level Adaptive Dithering**:
  - Blue noise masking with perceptual weighting (Rec. 601)
  - Adaptive spread based on LUT sensitivity analysis
  - Hysteresis application for dot connectivity
  - Non-monotonic region avoidance

- **Cyanotype-Specific Features**:
  - **Spread profiling**: Maps sensitivity to spread amount
    - Sensitive regions: Minimal spread (1 pixel)
    - Moderate regions: Medium spread (3 pixels)
    - Flat regions: Large spread (5-17 pixels)
  - **Stability factors**: Adjusts blue noise vs. adaptive threshold blending
  - **Edge bias control**: Optimizes thresholding for highlight/shadow regions

- **Physical Simulation**:
  - Dot gain modeling via measured PSF kernels
  - Spatial bleed simulation (Gaussian filtering)
  - Brightness loss calculation
  - Richardson-Lucy deconvolution for pre-compensation

#### **C. Image Preprocessing**
- **Perceptual conversion**: RGB to grayscale (0.299R + 0.587G + 0.114B)
- **Dynamic range management**:
  - Logarithmic compression for HDR handling
  - Gamma correction with robust clamping
  - Auto-contrast optimization
- **Spatial compensation**:
  - Unsharp masking for bleed pre-compensation
  - Size normalization to physical dimensions
  - White border addition for laser runout

---

### **2. Key Algorithms**

#### **Adaptive Threshold Dithering**
```python
# Core dithering logic
def cyanotype_adaptive_dither_with_hysteresis(img, noise, lut, spread_profile):
    # Calculate target density (inverted for cyanotype)
    target_density = 1.0 - img
    
    # Adaptive spread per pixel based on LUT sensitivity
    pixel_spreads = spread_profile[(target_density * spread_len).astype(int)]
    
    # Lattice-aligned lower/upper bounds
    lower_bound = (floor(idx_float / spread) * spread)
    upper_bound = lower_bound + spread
    
    # Hysteresis-enhanced threshold
    threshold = blend(blue_noise, adaptive_threshold, stability_factor)
    
    # Final laser power selection
    return lut[lower_bound + (fraction > threshold) * spread]
```

#### **Physical Modeling**
- **Edge Spread Function (ESF)**: Measured from calibration prints
- **Line Spread Function (LSF)**: Derivative of ESF (blur kernel)
- **Modulation Transfer Function (MTF)**: Frequency response via FFT
- **Effective DPI Calculation**: `effective_dpi = MTF10_frequency × 2 × scan_DPI`

#### **Kernel Processing**
- **2D PSF Creation**: Rotational symmetry from 1D LSF
- **DPI Scaling**: Bicubic interpolation for resolution matching
- **Deconvolution**: Richardson-Lucy iteration for pre-compensation

---

### **3. Hardware Integration**

#### **Laser System: TwoTrees TTS-55 Pro**
- **Laser Type**: UV Diode, 5.5W output
- **Spot Size**: 0.08×0.08mm (80μm)
- **Working Area**: 300×300mm
- **Positioning Accuracy**: ±0.05mm over 100mm
- **Focus Strategy**: -2mm defocus for chemical penetration vs. surface burning

#### **Physical Parameters**
- **Material**: Cyanotype-coated paper (hand-coated)
- **DPI Range**: 254-318 DPI (100-125 pixels/cm)
- **Power Steps**: 80 discrete levels (0-79)
- **Exposure Strategy**: Dot-area modulation (not pulse-width)

#### **Workflow Integration**
1. Generate compensated image via Python pipeline
2. Export as 8-bit grayscale PNG (0-79 values)
3. Load into laser engraver software (LightBurn compatible)
4. Set physical dimensions and DPI matching
5. Execute print with focus offset

---

### **4. Cyanotype Physics Compensation**

The system models three key physical phenomena:

#### **A. Chemical Response**
- **Non-linear sensitivity**: Measured via step wedge prints
- **Threshold behavior**: Minimum exposure for reaction
- **Saturation limits**: Maximum density achievable

#### **B. Spatial Effects**
- **Dot gain**: Chemical diffusion beyond exposed area
- **Edge bleed**: Typically 50-150μm depending on power
- **Bleed-power relationship**: Non-linear, measured per system

#### **C. Laser Characteristics**
- **Gaussian beam profile**: Natural intensity distribution
- **Defocus effects**: -2mm creates larger, softer spot
- **Power non-linearity**: Driver response vs. commanded value

---

## **File Structure & Workflow**

### **Primary Workflow**
```
1. CALIBRATION PHASE
   dot_gain_calibration.py → Generate target → Print → Scan → Analyze → cyanotype_lut.csv
   
2. PROCESSING PHASE
   dither_experiment.py → Load image → Apply LUT → Adaptive dither → Export laser map
   
3. PRINTING PHASE
   Load laser_map.png into engraver software → Set focus offset → Print
```

### **Key Outputs**
- `cyanotype_lut.csv`: Compensation lookup table
- `laser_map.png`: 8-bit grayscale for laser (0-79 values)
- `simulated_on_paper.png`: Physical result prediction
- `my_kernel.npy`: 2D PSF for spatial compensation

---

## **Scientific Contributions**

### **1. Novel Algorithms**
- **Cyanotype-optimized dithering**: First published adaptive dithering specifically for cyanotype
- **Stability-factor blending**: Dynamic blue noise vs. adaptive threshold mixing
- **Hysteresis for cyanotype**: Dot connectivity optimization for chemical continuity

### **2. Measurement Techniques**
- **Automated calibration analysis**: Full pipeline from print to LUT
- **Edge transition profiling**: Quantitative bleed measurement
- **Effective DPI calculation**: Objective resolution quantification

### **3. Physical Modeling**
- **Complete PSF extraction**: From print measurements to 2D kernel
- **Brightness loss prediction**: Quantitative dot gain modeling
- **Pre-compensation deconvolution**: Inverse filtering for bleed correction

---

## **Usage Scenarios**

### **A. Fine Art Reproduction**
- High-detail photographic cyanotypes
- Controlled tonal reproduction
- Consistent edition printing

### **B. Experimental Photography**
- Algorithmic image transformations
- Multi-exposure techniques
- Hybrid digital-analog workflows

### **C. Research & Education**
- Alternative process optimization
- Physical computing demonstrations
- Computational photography teaching

---

## **Technical Requirements**

### **Software**
- Python 3.8+ with NumPy, SciPy, OpenCV, scikit-image
- Jupyter environment for experimentation
- Laser engraver control software (LightBurn)

### **Hardware**
- UV laser engraver (5W+ recommended)
- Flatbed scanner (1200+ DPI for calibration)
- Cyanotype chemistry and appropriate paper
- Dust-free coating environment

### **Calibration Materials**
- Consistent paper stock
- Fresh chemistry batches
- Controlled drying conditions

---

## **Future Development Directions**

### **Short-term**
1. **Web interface** for image upload and processing
2. **Real-time preview** with adjustable parameters
3. **Batch processing** for edition printing

### **Medium-term**
1. **Multi-material support** (van dyke brown, platinum/palladium)
2. **Color separation** for tri-color cyanotype
3. **3D relief mapping** for textured exposures

### **Long-term**
1. **AI-based optimization** of dither patterns
2. **Closed-loop control** with in-process monitoring
3. **Multi-laser systems** for larger formats or faster printing

---

## **Academic Context**

This project sits at the intersection of:
- **Computational Photography**: Algorithmic image manipulation
- **Digital Fabrication**: CNC control of material processes
- **Alternative Process Photography**: Historical technique modernization
- **Materials Science**: Chemical response characterization

The system demonstrates how computational methods can enhance traditional craft processes, enabling new expressive possibilities while maintaining the aesthetic qualities of historical photographic techniques.

---

## **Repository Structure**
```
lasercyano/
├── dither_experiment.py          # Main processing pipeline
├── dot_gain_calibration.py       # Calibration system
├── cyanotype_lut.csv            # Compensation table (generated)
├── kernels/                     # PSF kernels for different papers
├── calibration_scans/           # Example calibration data
├── examples/                    # Sample inputs and outputs
└── docs/                       # Documentation and schematics
```

This project represents a significant advancement in computational cyanotype printing, providing both practical tools for artists and a research platform for exploring digital-physical hybrid image-making systems.
