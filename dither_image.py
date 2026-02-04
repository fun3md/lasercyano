import cv2
import numpy as np
import pandas as pd
import lasercyano_defaults

def apply_dot_gain(image_path, kernel_path, source_dpi=1200, target_dpi=300):
    # 1. Load the target image and the kernel
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError("Target image not found.")
    
    scale_factor_in = source_dpi / target_dpi
    img_newx =  int(round(img.shape[1] * scale_factor_in))
    img_newy =  int(round(img.shape[0] * scale_factor_in))

    img_scaled = cv2.resize(img, (img_newx, img_newy), interpolation=cv2.INTER_CUBIC)
    
    # Load the 1200dpi kernel we saved earlier
    kernel_1200 = np.load(kernel_path)
        
    # 3. Apply the simulation
    # To simulate ink spreading (dot gain), we convolve the image.
    # filter2D handles multi-channel images (BGR) automatically.
    simulated_img = cv2.filter2D(img_scaled, -1, kernel_1200)

    simulated_img = cv2.resize(simulated_img,(int(round(img.shape[1])), int(round(img.shape[0]))), interpolation=cv2.INTER_AREA)
    return img, simulated_img, kernel_1200

def apply_cyanotype_correction(image_path, kernel_path, lut_csv_path, target_gamma=2.2, strength=1.0):
    # 1. Load Image
    img = cv2.imread(image_path)
    if img is None: raise FileNotFoundError("Image not found")
    img = img.astype(np.float32) / 255.0  # Work in 0.0-1.0 range for gamma

    # 2. Step 1: Gamma Pre-Compensation
    # If paper darkens with gamma 2.2, we lighten with 1/2.2
    gamma_corrected = np.power(img, 1.0 / target_gamma)

    # 3. Step 2: LUT Compensation (from your CSV)
    # We load the CSV and find the inverse mapping
    df = pd.read_csv(lut_csv_path).sort_values(by='Input')
    
    # Check if CSV is Density (0=White) or Brightness (255=White)
    # If the end of the curve is lower than the start, it's Density. Flip it.
    if df['Output'].iloc[-1] < df['Output'].iloc[0]:
        df['Output'] = 255 - df['Output']

    # Create the inverse LUT: "What digital value gives this paper output?"
    all_vals = np.linspace(0, 1, 256)
    # Interpolate using normalized 0-1 values
    xp = df['Output'].values / 255.0
    fp = df['Input'].values / 255.0
    
    # Generate the compensation curve
    inv_lut_vals = np.interp(all_vals, xp, fp)
    
    # Apply LUT to the gamma-corrected image
    # We use a simple interpolation to apply the curve to the float image
    final_toned = np.interp(gamma_corrected, all_vals, inv_lut_vals)

    # 4. Step 3: Spatial Deconvolution (Sharpening)
    # Use your 1200dpi kernel to counteract physical bleeding
    kernel_1200 = np.load(kernel_path)

    scale_factor = 1200 / lasercyano_defaults.target_image_dpi
    new_size = int(round(kernel_1200.shape[0] * scale_factor))
    if new_size % 2 == 0: new_size += 1
    
    kernel_small = cv2.resize(kernel_1200, (new_size, new_size), interpolation=cv2.INTER_AREA)
    kernel_small /= kernel_small.sum()

    # High-pass sharpening logic
    blurred = cv2.filter2D(final_toned, -1, kernel_small)
    sharpened = final_toned + (final_toned - blurred) * strength
    
    # 5. Final Output
    final_img = np.clip(sharpened * 255.0, 0, 255).astype(np.uint8)

    return final_img


import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageFilter, ImageOps
import os

# ==========================================
# 2. Helper Functions
# ==========================================

def load_and_normalize(img):
    """Loads an image, converts to float, normalizes to 0-1."""
    return np.array(img).astype(np.float32) / 255.0

def rgb_to_grayscale_perceptual(img_rgb):
    """
    Converts RGB to Grayscale using Rec. 601 Luma coefficients.
    L = 0.299*R + 0.587*G + 0.114*B
    """
    # img_rgb shape is (H, W, 3)
    r = img_rgb[:, :, 0]
    g = img_rgb[:, :, 1]
    b = img_rgb[:, :, 2]
    
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    return gray

def tile_noise(noise_texture, target_shape):
    """
    Tiles the noise texture to cover the target image shape.
    target_shape: (Height, Width)
    """
    th, tw = target_shape
    nh, nw = noise_texture.shape
    
    # Calculate how many times to repeat in Y and X
    repeat_y = (th // nh) + 1
    repeat_x = (tw // nw) + 1
    
    # Tile and crop to exact size
    tiled = np.tile(noise_texture, (repeat_y, repeat_x))
    return tiled[:th, :tw]

def resize_to_physical_dim(pil_img, longest_edge_mm, dpi):
    target_pixels_max = int((longest_edge_mm / 25.4) * dpi)
    
    # FIX: Handle both PIL Images and NumPy Arrays
    if hasattr(pil_img, 'shape'):  # It's a NumPy array
        h, w = pil_img.shape[:2]   # shape is (Height, Width, Channels)
        is_numpy = True
    else:                          # It's a PIL Image
        w, h = pil_img.size        # size is (Width, Height)
        is_numpy = False
        
    # Calculate scale maintaining aspect ratio
    if w > h:
        scale = target_pixels_max / w
    else:
        scale = target_pixels_max / h
        
    new_w = int(w * scale)
    new_h = int(h * scale)

    # Perform resize
    if is_numpy:
        import cv2
        # OpenCV uses (width, height) for resize, but input was array
        return cv2.resize(pil_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        return pil_img.resize((new_w, new_h), resample=Image.LANCZOS)

def scale_to_percentile_global(img_rgb, percentile=95):
   
    # Calculate the percentile value of the entire image
    white_point = np.percentile(img_rgb, percentile)
    
    # Scale and clip
    # Any pixel above the white_point becomes 255 (white)
    rescaled = (img_rgb / white_point) * 255
    rescaled = np.clip(rescaled, 0, 255).astype(np.uint8)
    
    return rescaled

# ==========================================
# 3. Main Logic
# ==========================================
def dither_image(INPUT_IMAGE_PATH, kernel_path, lut_path, source_dpi, target_dpi, 
                            percentile, pre_adj_strength, pre_gamma, blue_noise_path, target_longest_edge
                        ):
    # A. Load Input Image
    print(f"Loading image: {INPUT_IMAGE_PATH}")
    img_rgb = apply_cyanotype_correction(
    image_path=INPUT_IMAGE_PATH,
    kernel_path=kernel_path,
    lut_csv_path=lut_path,
    target_gamma=pre_gamma, # Standard cyanotype contrast
    strength=pre_adj_strength      # Adjust sharpening strength (0.0 to 1.5)
)
    img_rgb = load_and_normalize(img_rgb)
    img_rgb = scale_to_percentile_global((img_rgb * 255).astype(np.uint8), percentile).astype(np.float32) / 255.0
    img_rgb = resize_to_physical_dim(img_rgb, target_longest_edge, target_dpi)
    
    # B. Convert to Grayscale Perceptually
    img_gray = rgb_to_grayscale_perceptual(img_rgb)
    print(f"Image Size: {img_gray.shape}")

    # C. Load Blue Noise Texture
    print(f"Loading noise: {blue_noise_path}")
    # Load noise, convert to grayscale (L), normalize 0-1
    noise_img = Image.open(blue_noise_path).convert('L')
    noise_arr = np.array(noise_img).astype(np.float32) / 255.0

    # D. Tile the Noise to match Image Size
    noise_tiled = tile_noise(noise_arr, img_gray.shape)

    # 2. Convert Image Brightness to Target Laser Power
    # Assuming img_gray: 1.0 = White (Paper), 0.0 = Black (Ink)
    # We invert this because for the laser: 0.0 = Off (Paper), 1.0 = On (Burn)
    target_power = img_gray

    # Ensure range is strictly 0-1
    target_power = np.clip(target_power, 0.0, 1.0)

    # 3. Find the Lower and Upper bounds for every pixel
    # We find which interval of power_levels the current pixel falls into.
    # np.searchsorted finds the insertion index to maintain order.
    # We subtract 1 to get the index of the "step below".
    idx = np.searchsorted(lasercyano_defaults.power_levels, target_power, side='right') - 1

    # Clamp indices to ensure we don't go out of bounds
    idx = np.clip(idx, 0, len(lasercyano_defaults.power_levels) - 2)

    lower_step = lasercyano_defaults.power_levels[idx]
    upper_step = lasercyano_defaults.power_levels[idx + 1]

    # 4. Normalize the pixel value within its specific step interval
    # Example: If pixel wants 0.7 power, it sits between 0.5 and 0.9.
    # The normalized value (0.0 to 1.0) represents how close it is to the upper step.
    step_range = upper_step - lower_step

    # Handle case where step_range is 0 to avoid division by zero
    step_range[step_range == 0] = 1.0 

    normalized_val = (target_power - lower_step) / step_range

    # 5. Apply the Blue Noise Threshold
    # If the normalized value is higher than the noise, bump up to the upper step.
    # Otherwise, stay at the lower step.
    step_up_mask = normalized_val > noise_tiled

    dithered_output = np.where(step_up_mask, upper_step, lower_step)

    runout_px = int((lasercyano_defaults.runout_mm / 25.4) * target_dpi)

    # Ensure the array is uint8 (0-255) or bool before converting
    if isinstance(dithered_output, np.ndarray):
        # If your dithered output is float (0.0-1.0), scale to 255
        if dithered_output.max() <= 1.0:
            dithered_output = (dithered_output * 255).astype(np.uint8)
        
        dithered_output = Image.fromarray(dithered_output.astype(np.uint8))

    dithered_output = ImageOps.expand(dithered_output, border=runout_px, fill='white')
   
    return dithered_output