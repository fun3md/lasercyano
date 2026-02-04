import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import lasercyano_defaults

def generate_paper_texture(shape, scale=0.5, intensity=0.05):
    """Procedurally generates a watercolor paper texture (Aquarell)."""
    # Create random noise
    noise = np.random.normal(128, 20, (shape[0], shape[1])).astype(np.uint8)
    # Blur it to create "clumps" like paper pulp
    pulp = cv2.GaussianBlur(noise, (5, 5), 0)
    pulp = cv2.resize(pulp, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    pulp = pulp[:shape[0], :shape[1]]
    
    # Use Sobel to create a "bump map" effect (lighting from top-left)
    kernel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    kernel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])
    edge_x = cv2.filter2D(pulp, -1, kernel_x)
    edge_y = cv2.filter2D(pulp, -1, kernel_y)
    
    texture = (edge_x + edge_y).astype(np.float32) * intensity
    return texture

def apply_print_simulation_alt(image_path, kernel_path, lut_csv_path, source_dpi=1200, target_dpi=300):
     # 1. Load Image
    img_in = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img_in is None: raise FileNotFoundError("Input image not found.")

    scale_factor_in = source_dpi / target_dpi
    img_newx =  int(round(img_in.shape[1] * scale_factor_in))
    img_newy =  int(round(img_in.shape[0] * scale_factor_in))
    img = cv2.resize(img_in, (img_newx, img_newy), interpolation=cv2.INTER_CUBIC)

    # --- ADDED: STRETCH INPUT VALUES TO 0-255 ---
    # This ensures the darkest pixel becomes 0 and the lightest becomes 255
    # before the LUT is applied.
    img_min, img_max = img.min(), img.max()
    if img_max > img_min:
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
    # --------------------------------------------
    
    # 2. Fix the Inverted LUT Logic
    df_lut = pd.read_csv(lut_csv_path).sort_values(by='Input')
    all_inputs = np.arange(256)
    
    # We create the LUT from your CSV
    lut_raw = np.interp(all_inputs, df_lut['Input'], df_lut['Output'])
    
    # LOGIC CHECK: 
    # If the user sends a white pixel (255), we want 0 density.
    # If the user sends a black pixel (0), we want max density.
    # We force the LUT to be a "Digital-to-Ink" map where 255 digital = 0 ink.
    if lut_raw[255] > lut_raw[0]:
        # If 255 digital resulted in high output, we must flip it
        lut_map = 255 - lut_raw
    else:
        lut_map = lut_raw

    # Apply the mapping to get Ink Density (0.0 to 1.0)
    ink_density = cv2.LUT(img, lut_map.astype(np.uint8).reshape((1, 256))).astype(np.float32) / 255.0

    # 3. Handle Kernel (Spatial Spread)
    kernel_1200 = np.load(kernel_path).astype(np.float32)
    kernel_1200 /= (kernel_1200.sum() + 1e-8)
    
    # scale = target_dpi / source_dpi
    # k_size = int(round(kernel_1200.shape[0] * scale))
    # if k_size % 2 == 0: k_size += 1
    # kernel_scaled = cv2.resize(kernel_1200, (k_size, k_size), interpolation=cv2.INTER_AREA)
    # kernel_scaled /= (kernel_scaled.sum() + 1e-8)

    # Spread the ink
    spread_density = cv2.filter2D(ink_density, -1, kernel_1200)

    # 4. Subtractive Overlap (Capping)
    k_val = 2.5 
    saturated_density = 1.0 - np.exp(-k_val * spread_density)
    saturated_density = np.clip(saturated_density, 0, 1)

    # 5. Final RGB Color Mapping
    PAPER_WHITE = np.array([235, 241, 243]) # BGR (flipped from your original)
    # Indigo: Dark Blue
    INDIGO_DARK = np.array([25, 5, 1]) # BGR (flipped from your original)
    
    h, w = saturated_density.shape
    sim_rgb = np.zeros((h, w, 3), dtype=np.float32)
    
    for i in range(3):
        # 0.0 Density = Paper Color
        # 1.0 Density = Indigo Color
        sim_rgb[:,:,i] = (1.0 - saturated_density) * PAPER_WHITE[i] + (saturated_density) * INDIGO_DARK[i]

    # 6. Add Texture
    grain = np.random.normal(0, 1.2, (h, w))
    for i in range(3): sim_rgb[:,:,i] += grain

    # Debug: Confirm inversion is correct
    # Corner pixels in digital images are usually background (White/255)
    # They should have near-zero density.
    print(f"Top-Left Pixel Digital Value: {img[0,0]}")
    print(f"Top-Left Pixel Ink Density: {ink_density[0,0]:.4f}")

    sim_rgb = cv2.resize(sim_rgb, (int(round(img.shape[1])), int(round(img.shape[0]))), interpolation=cv2.INTER_AREA)
    sim_rgb = cv2.normalize(sim_rgb, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    sim_rgb = cv2.cvtColor(sim_rgb, cv2.COLOR_BGR2RGB)
    sim_out = Image.fromarray(sim_rgb.astype(np.uint8))
    return sim_out



