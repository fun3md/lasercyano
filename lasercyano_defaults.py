import numpy as np
import os

# Dither Image Defaults
input_img_path = 'E:\projects\cyanosources\select\IMG_9022.jpg' # The "clean" image
# Set stable power levels for UV laser on Cyanotype with valid response data in LUT
power_levels = np.array([0.0, 0, 0, 1.0], dtype=np.float32)

target_image_dpi = 390 # Set this to the DPI of your input_img_path
TARGET_LONGEST_EDGE_MM = 270  # Set the desired length of the longest side in mm
runout_mm = 2.0

percentile = 93
pre_adj_strength = 0.5
pre_gamma = 1.0
lut_file = 'cal_data/uv_laser_response.csv'


BLUE_NOISE_PATH = os.path.join('.', 'bluenoise', '128_128', 'LDR_LLL1_0.png')
kernel_file = 'cal_data/avg_deconvolution_kernel_1200dpi.npy'
kernel_source_dpi = 1200

# --- Dither ---
# Adjust these paths as needed
INPUT_IMAGE_PATH = "scratch/corrected_pre_dither.png"
post_img_path = 'scratch/post_dither.png'


# --- CalChart CONFIGURATION ---
DPI = 318
MAX_STEPS = 80  # Your hardware max power steps
PATCH_SIZE_MM = 10
GAP_MM = 2
COLUMNS = 9 
# 81 steps total (0 to 80), perfect for a 9x9 grid

# ==========================================
# Laser Setting Helper Default Parameters
# ==========================================
target_z = -1.0        # Desired Focus Depth (mm) e.g., -1.0, -2.0
feedrate = 3500        # Speed (mm/min)
pwm_freq = 1800        # PWM Frequency (Hz)
overlap_target = 0.50  # Desired Overlap (20% is standard for smooth floors)

# Machine Baseline (TTS-55 Pro Data based on our conversation)
base_spot_0mm = 0.08   # Spot size at perfect focus
base_spot_2mm = 0.18   # Spot size at -2mm defocus
max_scale = 4000      # S-Value Scale (1000 or 255)

# Known "Good" calibration point (from our findings at -2mm)
ref_z = -2.0
ref_power_min = 20
ref_power_max = 90