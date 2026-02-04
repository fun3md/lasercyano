import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image
import lasercyano_defaults
from scipy.interpolate import UnivariateSpline  # <--- Added for smoothing

def mm_to_px(mm, dpi):
    return int((mm / 25.4) * dpi)

def generate_calibration_target(PATCH_SIZE_MM=lasercyano_defaults.PATCH_SIZE_MM, GAP_MM=lasercyano_defaults.GAP_MM, COLUMNS=lasercyano_defaults.COLUMNS, MAX_STEPS=lasercyano_defaults.MAX_STEPS, DPI=lasercyano_defaults.DPI):
    patch_px = mm_to_px(PATCH_SIZE_MM, DPI)
    gap_px = mm_to_px(GAP_MM, DPI)

    # Calculate total canvas size
    grid_size = patch_px + gap_px
    canvas_w = grid_size * COLUMNS + gap_px
    canvas_h = grid_size * COLUMNS + gap_px

    # Create white canvas
    canvas = np.ones((canvas_h, canvas_w), dtype=np.uint8) * 255

    # Generate Patches
    for step in range(MAX_STEPS + 1):
        r = step // COLUMNS
        c = step % COLUMNS
        
        y = gap_px + r * grid_size
        x = gap_px + c * grid_size
        
        # Calculate the 0-255 value the laser software expects 
        # based on your dither script logic (final_steps * 255 / max_steps)
        val = int(round(step * (255.0 / MAX_STEPS)))
        
        # Fill patch
        canvas[y : y + patch_px, x : x + patch_px] = val
        
        # Add a tiny 1-pixel "isolated dot" in the gap to measure spread
        canvas[y - 1, x + (patch_px // 2)] = val

    
    return canvas


import cv2
import numpy as np
import matplotlib.pyplot as plt

# 1. Configuration
image_path = 'out_wash2detail.png'
kernel_size = 35         # Size of the kernel (odd number)
num_dots_to_average = 50 # Number of dots to find and average
kernel_filename = 'averaged_deconvolution_kernel.npy'

def extract_printing_kernel(image_path, kernel_size=35, num_dots_to_average=50):
    # 2. Load and Pre-process
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"Image not found at {image_path}")

    # Threshold to find dots (Inverted: dots become white, paper becomes black)
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 3. Find and Filter Contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter dots based on area (avoiding dust or large ink clumps)
    # We calculate the median area to identify "standard" dots
    areas = [cv2.contourArea(c) for c in contours if cv2.contourArea(c) > 5]
    median_area = np.median(areas)
    valid_contours = [c for c in contours if 0.7 * median_area < cv2.contourArea(c) < 1.3 * median_area]

    print(f"Found {len(valid_contours)} candidate dots. Averaging the top {num_dots_to_average}...")

    # 4. Extract and Average
    kernels = []
    half = kernel_size // 2

    for i, cnt in enumerate(valid_contours):
        # Calculate Center of Mass (Moments) for sub-pixel centering accuracy
        M = cv2.moments(cnt)
        if M["m00"] == 0: continue
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        # Ensure crop stays within image boundaries
        if cy-half < 0 or cy+half+1 > img.shape[0] or cx-half < 0 or cx+half+1 > img.shape[1]:
            continue

        # Extract crop from original image
        dot_crop = img[cy-half : cy+half+1, cx-half : cx+half+1].astype(np.float32)
        
        # Invert (so dot is signal/light and paper is background/dark)
        # Background subtraction: use the maximum value in the crop as the 'paper' value
        paper_level = np.percentile(dot_crop, 95) 
        dot_signal = paper_level - dot_crop
        dot_signal = np.maximum(dot_signal, 0) # Clip negative values
        
        kernels.append(dot_signal)

    if not kernels:
        raise ValueError("No valid dots were found. Check the thresholding or image quality.")

    # Average all extracted dots
    master_kernel = np.mean(kernels, axis=0)

    # 5. Final Normalization
    # Kernel must sum to 1.0 for deconvolution to maintain image brightness
    master_kernel /= master_kernel.sum()

    return master_kernel

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
DPI = 254           
RUN_OUT_MM = 3      # White area outside the black border for laser lead-in/out
PATCH_SIZE = 25     
GAP_SIZE = 10       
COLUMNS = 9         
MAX_POWER_STEPS = 85 
BORDER_THICKNESS = 4
WHITE_MARGIN = 40   
FIDUCIAL_SIZE = 15  

# Calculate Run-out in pixels
RUN_OUT_PX = int(round((RUN_OUT_MM / 25.4) * DPI))

def draw_fiducial(canvas, y, x, size, solid=False):
    canvas[y:y+size, x:x+size] = 0
    canvas[y+2:y+size-2, x+2:x+size-2] = 255
    if solid:
        canvas[y+4:y+size-4, x+4:x+size-4] = 0
    else:
        canvas[y+int(size/2), x+int(size/2)] = 0

def create_stepped_power_gap_line(width, gap_px, num_steps=9):
    line = np.ones(width, dtype=np.uint8) * 255
    step_width = width / num_steps
    dot_gap = 1 + gap_px
    indices = np.arange(0, width, dot_gap)
    for idx in indices:
        zone_idx = min(int(idx // step_width), num_steps - 1)
        hw_step = zone_idx * (MAX_POWER_STEPS // (num_steps - 1))
        gray_val = int(round(hw_step * (255.0 / MAX_POWER_STEPS)))
        line[idx] = gray_val
    return line

def create_res_block_v(h, w):
    block = np.ones((h, w), dtype=np.uint8) * 255
    segment_w = w // 4
    for i, spacing in enumerate([1, 2, 3, 4]):
        start_x = i * segment_w
        for x in range(0, segment_w, spacing * 2):
            block[:, start_x + x : start_x + x + spacing] = 0
    return block

def create_res_block_h(h, w):
    block = np.ones((h, w), dtype=np.uint8) * 255
    segment_h = h // 4
    for i, spacing in enumerate([1, 2, 3, 4]):
        start_y = i * segment_h
        for y in range(0, segment_h, spacing * 2):
            block[start_y + y : start_y + y + spacing, :] = 0
    return block

def generate_calchart_target(DPI=lasercyano_defaults.DPI, MAX_POWER_STEPS=lasercyano_defaults.MAX_STEPS, PATCH_SIZE=lasercyano_defaults.PATCH_SIZE_MM, GAP_SIZE=lasercyano_defaults.GAP_MM, COLUMNS=lasercyano_defaults.COLUMNS):
    # 1. CORE CONTENT GENERATION
    GRID_WIDTH = (COLUMNS * PATCH_SIZE) + ((COLUMNS - 1) * GAP_SIZE)

    # Top Frequency Wedge
    wedge_lines = []
    for gap in range(1, 15):
        for _ in range(1):
            wedge_lines.append(create_stepped_power_gap_line(GRID_WIDTH, gap))
    wedge_block = np.array(wedge_lines)

    # Top Frequency Wedge
    wedge_2p_block = []
    for gap in range(1, 15):
        for _ in range(1):
            wedge_2p_block.append(create_stepped_power_gap_line(GRID_WIDTH, gap))
    wedge_2p_block = np.array(wedge_2p_block)

    # Central Step Chart
    grid_canvas = np.ones((GRID_WIDTH, GRID_WIDTH), dtype=np.uint8) * 255
    for i in range(MAX_POWER_STEPS + 1):
        r, c = i // COLUMNS, i % COLUMNS
        y, x = r * (PATCH_SIZE + GAP_SIZE), c * (PATCH_SIZE + GAP_SIZE)
        val = int(round(i * (255.0 / MAX_POWER_STEPS)))
        grid_canvas[y:y+PATCH_SIZE, x:x+PATCH_SIZE] = val

    # Density Consistency Bar (0-75% max power, 4px steps)
    BAR_WIDTH = int(GRID_WIDTH * 0.6)
    BAR_MAX_POWER = int(MAX_POWER_STEPS * 0.75)
    NUM_DENSITY_STEPS = 16 
    STEP_HEIGHT = 4
    BAR_HEIGHT = NUM_DENSITY_STEPS * STEP_HEIGHT

    density_layers = []
    for i in range(NUM_DENSITY_STEPS):
        power_val = int((i / (NUM_DENSITY_STEPS - 1)) * BAR_MAX_POWER)
        gray_val = int(round(power_val * (255.0 / MAX_POWER_STEPS)))
        layer = np.ones((STEP_HEIGHT, BAR_WIDTH), dtype=np.uint8) * gray_val
        density_layers.append(layer)
    density_bar_block = np.vstack(density_layers)

    bottom_row = np.ones((BAR_HEIGHT, GRID_WIDTH), dtype=np.uint8) * 255
    margin_w = (GRID_WIDTH - BAR_WIDTH) // 2
    bottom_row[:, margin_w : margin_w + BAR_WIDTH] = density_bar_block
    res_w = margin_w - 10
    bottom_row[:, 5 : 5 + res_w] = create_res_block_v(BAR_HEIGHT, res_w)
    bottom_row[:, GRID_WIDTH - res_w - 5 : GRID_WIDTH - 5] = create_res_block_h(BAR_HEIGHT, res_w)

    spacer = np.ones((20, GRID_WIDTH), dtype=np.uint8) * 255
    content = np.vstack([wedge_block, wedge_2p_block, spacer, grid_canvas, spacer, bottom_row])

    # 2. FINAL ASSEMBLY WITH RUN-OUT
    h, w = content.shape

    # Padding layers: [Run Out] -> [Border] -> [White Margin]
    total_h = h + (2 * WHITE_MARGIN) + (2 * BORDER_THICKNESS) + (2 * RUN_OUT_PX)
    total_w = w + (2 * WHITE_MARGIN) + (2 * BORDER_THICKNESS) + (2 * RUN_OUT_PX)

    final_sheet = np.ones((total_h, total_w), dtype=np.uint8) * 255 # Start with White

    # Draw Black Border
    b_start = RUN_OUT_PX
    b_end_h = total_h - RUN_OUT_PX
    b_end_w = total_w - RUN_OUT_PX
    final_sheet[b_start:b_end_h, b_start:b_end_w] = 0

    # Draw White Inner Margin
    i_start = b_start + BORDER_THICKNESS
    i_end_h = b_end_h - BORDER_THICKNESS
    i_end_w = b_end_w - BORDER_THICKNESS
    final_sheet[i_start:i_end_h, i_start:i_end_w] = 255

    # Place Content
    c_offset = i_start + WHITE_MARGIN
    final_sheet[c_offset:c_offset+h, c_offset:c_offset+w] = content

    # 3. ADD ASYMMETRIC FIDUCIALS
    # Placed relative to the inner edge of the black border
    m_pad = b_start + BORDER_THICKNESS + 5
    draw_fiducial(final_sheet, m_pad, m_pad, FIDUCIAL_SIZE, solid=True)
    draw_fiducial(final_sheet, m_pad, total_w - m_pad - FIDUCIAL_SIZE, FIDUCIAL_SIZE, solid=False)
    draw_fiducial(final_sheet, total_h - m_pad - FIDUCIAL_SIZE, m_pad, FIDUCIAL_SIZE, solid=False)
    draw_fiducial(final_sheet, total_h - m_pad - FIDUCIAL_SIZE, total_w - m_pad - FIDUCIAL_SIZE, FIDUCIAL_SIZE, solid=False)

    return Image.fromarray(final_sheet)

def process_scan_v7(image_path, out_w=600, out_h=800):
    # 1. Load
    img = cv2.imread(image_path)
    if img is None: raise FileNotFoundError("Scan not found.")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Threshold - Clean up noise
    # We want the markers to be WHITE objects on a BLACK background
    _, thresh = cv2.threshold(gray, 120, 230, cv2.THRESH_BINARY_INV)
    
    # 3. Find ALL contours (not just external)
    contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    # Get image dimensions to find corner-most objects
    im_h, im_w = thresh.shape
    
    candidates = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # Filter: Markers are small, but not microscopic (adjust based on scan res)
        if 500 < area < 2000: 
            M = cv2.moments(cnt)
            if M["m00"] == 0: continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            candidates.append((cx, cy))

    if len(candidates) < 4:
        # Fallback debug view
        plt.imshow(thresh, cmap='gray')
        plt.title(f"Only found {len(candidates)} small objects. Need lower threshold?")
        return None

    # 4. Find the 4 Candidates closest to the 4 corners of the image
    # This ignores the density patches in the middle
    corners = [
        (0, 0),          # Top Left
        (im_w, 0),       # Top Right
        (im_w, im_h),    # Bottom Right
        (0, im_h)        # Bottom Left
    ]
    
    final_4 = []
    for corner in corners:
        # Find candidate with minimum distance to this corner
        best_cand = min(candidates, key=lambda p: (p[0]-corner[0])**2 + (p[1]-corner[1])**2)
        final_4.append(best_cand)
    
    # 5. Determine Orientation (North Star)
    # Sample the original gray image at the center of our 4 points.
    # The Top-Left marker center is SOLID (Dark), others are HOLLOW (Light).
    intensities = []
    for (cx, cy) in final_4:
        roi = gray[cy-2:cy+3, cx-2:cx+3]
        intensities.append(np.mean(roi))
    
    # The darkest center point is our true Top-Left
    tl_idx = np.argmin(intensities)
    
    # Re-order final_4 so it starts at Top-Left and goes Clockwise
    # We use a simple roll to align the detected TL with index 0
    src_pts = np.roll(np.array(final_4, dtype="float32"), -tl_idx, axis=0)

    # 6. Perspective Warp
    dst_pts = np.array([
        [0, 0],
        [out_w - 1, 0],
        [out_w - 1, out_h - 1],
        [0, out_h - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped = cv2.warpPerspective(gray, M, (out_w, out_h))

    # Optional: Draw markers on original for debug
    debug_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    for i, p in enumerate(src_pts):
        color = (0, 255, 0) if i == 0 else (255, 0, 0) # Green for TL
        cv2.circle(debug_img, (int(p[0]), int(p[1])), 10, color, 2)
    
    return warped, debug_img


# --- REFINED CONFIGURATION (PERCENTAGES) ---
GRID_X_START = 0.064 
GRID_X_END   = 0.938  
GRID_Y_START = 0.170 
GRID_Y_END   = 0.785 

SAMPLE_AREA_PCT = 0.30 
MAX_STEPS = 80
COLS, ROWS = 9, 9

# Controls how "stiff" the curve is. 
# 0 = fits every jagged point (noisy). 
# Higher (e.g., 500-1000) = very smooth line.
SMOOTHING_FACTOR = 5000

def analyze_geometric_grid_v2(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if img is None: raise FileNotFoundError("analysis_ready.png not found.")
    
    im_h, im_w = img.shape
    
    x1_grid = im_w * GRID_X_START
    x2_grid = im_w * GRID_X_END
    y1_grid = im_h * GRID_Y_START
    y2_grid = im_h * GRID_Y_END
    
    grid_w = x2_grid - x1_grid
    grid_h = y2_grid - y1_grid
    
    cell_w = grid_w / COLS
    cell_h = grid_h / ROWS
    
    side_mult = np.sqrt(SAMPLE_AREA_PCT)
    
    results = []
    viz = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            
            center_x = x1_grid + (c * cell_w) + (cell_w / 2)
            center_y = y1_grid + (r * cell_h) + (cell_h / 2)
            
            sw = (cell_w * side_mult) / 2
            sh = (cell_h * side_mult) / 2
            
            sx1, sx2 = int(center_x - sw), int(center_x + sw)
            sy1, sy2 = int(center_y - sh), int(center_y + sh)
            
            roi = img[sy1:sy2, sx1:sx2]
            if roi.size == 0: continue
            
            avg_val = np.mean(roi)
            
            results.append({
                "step": idx,
                # Rounding input to integer for cleaner CSV later
                "input_255": int(round((MAX_STEPS - idx) * (255.0 / MAX_STEPS))),
                "measured_raw": avg_val
            })
            
            cv2.rectangle(viz, (sx1, sy1), (sx2, sy2), (0, 0, 255), 1)

    return pd.DataFrame(results), viz

def refine_calibration_curve(image_path):
    # --- 1. LOAD AND PROCESS SCAN ---
    warped_img, debug_img = process_scan_v7(image_path, out_w=600, out_h=800)
    if warped_img is None:
        print("Failed to process scan for calibration.")
        return

    # --- EXECUTE ---
    df, viz_img = analyze_geometric_grid_v2(warped_img)
    # --- 1. EXTRACT STEP 0 ---
    df_step_0 = df[df['step'] == 0].copy()

    # --- 2. FILTER RANGE 55-80 ---
    df_range = df[(df['step'] >= 55) & (df['step'] <= 80)].copy()

    # --- 3. QUANTIZE THE RANGE (Pick 9 steps from the range) ---
    # We pick 9 steps here so that Step 0 + 9 steps = 10 steps total
    indices = np.linspace(0, len(df_range) - 1, 9).astype(int)
    df_sampled_range = df_range.iloc[indices]

    # --- 4. COMBINE ---
    df = pd.concat([df_step_0, df_sampled_range]).drop_duplicates().reset_index(drop=True)

    # Verify we have Step 0 and Step 80
    print("Final selected steps:", df['step'].tolist())

    # --- 3. NORMALIZATION (on the quantized data) ---
    r_min, r_max = df['measured_raw'].min(), df['measured_raw'].max()
    df['normalized'] = 255 * (df['measured_raw'] - r_min) / (r_max - r_min)

    # Use this df_quantized for the spline and CSV
    df = df.sort_values(by='input_255')


    # 2. Sorting (CRITICAL for Spline Interpolation)
    # We must sort by the X-axis (input power) or the math breaks
    df = df.sort_values(by='input_255')

    # 3. Smoothing / Interpolation
    x_data = df['input_255'].values
    y_data = df['normalized'].values

    # Create the spline function
    # s=SMOOTHING_FACTOR: Adjust this if the curve is too loose or too tight
    spline_func = UnivariateSpline(x_data, y_data, s=SMOOTHING_FACTOR)

    # Generate a clean 0-255 range (Lookup Table)
    x_lut = np.arange(0, 255)
    y_smooth = spline_func(x_lut)

    # Clip values to ensure they stay within 0-255 (splines can overshoot slightly)
    y_smooth = np.clip(y_smooth, 0, 255)

    # Create a new DataFrame for the smooth LUT
    df_lut = pd.DataFrame({
        'input_255': x_data,
        'normalized': y_data
    })

    # --- EXPORT ---
    # We now save the SMOOTHED full range (0-255) instead of the jagged points.
    # This makes dither_v2.py much more accurate.
    return df_lut

