import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import lasercyano_defaults

# ==========================================
# 2. CALCULATION FUNCTIONS
# ==========================================

def get_spot_size(z_mm):
    """
    Linearly interpolates beam expansion based on TTS-55 optics.
    0mm = 0.08mm, 2mm = 0.18mm. Expansion rate ~0.05mm per mm depth.
    """
    slope = (lasercyano_defaults.base_spot_2mm - lasercyano_defaults.base_spot_0mm) / 2.0
    return lasercyano_defaults.base_spot_0mm + (slope * abs(z_mm))

def get_optimal_interval(spot_size, overlap):
    """Calculates line interval to maintain overlap."""
    return spot_size * (1 - overlap)

def get_dpi(interval_mm):
    return 25.4 / interval_mm

def get_power_scaling(current_z):
    """
    Scales power based on the change in line interval.
    If lines are tighter (higher DPI), we need LESS power per line to avoid charring.
    If lines are wider (lower DPI), we need MORE power to maintain darkness.
    """
    ref_spot = get_spot_size(lasercyano_defaults.target_z)
    curr_spot = get_spot_size(current_z)
    
    # Calculate intervals
    ref_interval = get_optimal_interval(ref_spot, lasercyano_defaults.overlap_target)
    curr_interval = get_optimal_interval(curr_spot, lasercyano_defaults.overlap_target)
    
    # Power Scaling Factor: Ratio of intervals
    # Wider interval = Needs more power to cover the gap
    factor = curr_interval / ref_interval
    
    new_min = lasercyano_defaults.ref_power_min * factor
    new_max = lasercyano_defaults.ref_power_max * factor
    
    return min(new_min, lasercyano_defaults.max_scale), min(new_max, lasercyano_defaults.max_scale)

def check_pwm_overlap(speed_mm_min, freq_hz, spot_mm):
    speed_mm_sec = speed_mm_min / 60
    dist_per_pulse = speed_mm_sec / freq_hz
    overlaps = spot_mm / dist_per_pulse
    return overlaps

# ==========================================
# 3. GENERATE PLOTS
# ==========================================

# Create a range of Z-offsets from 0 to -4mm
z_values = np.linspace(0, -3, 50)
spots = [get_spot_size(z) for z in z_values]
dpis = [get_dpi(get_optimal_interval(s, lasercyano_defaults.overlap_target)) for s in spots]
intervals = [get_optimal_interval(s, lasercyano_defaults.overlap_target) for s in spots]
pwr_maxs = [get_power_scaling(z)[1] for z in z_values]


# ==========================================
# 4. PRINT CALCULATOR RESULTS
# ==========================================
overlaps = check_pwm_overlap(lasercyano_defaults.feedrate, lasercyano_defaults.pwm_freq, spot_mm=lasercyano_defaults.base_spot_0mm)
quality_status = "PERFECT" if overlaps > 3 else "WARNING: DOTS VISIBLE"

# ==========================================
# 1. SETUP PARAMETERS (Your Current Context)
# ==========================================
current_spot_size = lasercyano_defaults.base_spot_0mm

current_feedrate = lasercyano_defaults.feedrate
current_pwm = lasercyano_defaults.pwm_freq
current_dpi = lasercyano_defaults.DPI

# ==========================================
# 2. GENERATE DATA FOR MAPS
# ==========================================

# --- Map 1: PWM Stability (Speed vs Freq) ---
speed_range = np.linspace(1000, 8000, 100)
freq_range = np.linspace(500, 5000, 100)
X_pwm, Y_pwm = np.meshgrid(speed_range, freq_range)

# Calculate Pulses per Dot
# Formula: SpotSize / (Speed_mm_sec / Freq)
speed_mm_sec = X_pwm / 60
dist_per_pulse = speed_mm_sec / Y_pwm
Z_overlap_count = current_spot_size / dist_per_pulse

# --- Map 2: Power Requirements (Speed vs DPI) ---
# Assuming Z=-1mm (Spot 0.13) as baseline
dpi_range = np.linspace(100, 400, 100)
X_pwr, Y_pwr = np.meshgrid(speed_range, dpi_range)

# Base calibration: 4000mm/min @ 230 DPI = S-Value 290
base_speed = 4000
base_dpi = 230
base_power = 290

# Power Logic: 
# 1. Linear with speed (Faster = More Power)
# 2. Inverse with DPI (Lower DPI = Wider gaps = More Power needed per line to fill visual density)
Z_power = base_power * (X_pwr / base_speed) * (base_dpi / Y_pwr)
Z_power = np.clip(Z_power, 0, 1000) # Clamp to machine max

# --- Map 3: Focus Strategy (Z-Offset vs DPI) ---
z_range = np.linspace(0, -3.0, 100) # 0 to -3mm
dpi_range_z = np.linspace(100, 500, 100)
X_focus, Y_focus = np.meshgrid(z_range, dpi_range_z)

# Calculate Overlap %
# Spot size grows as we go deeper: 0.08 + (0.05 * abs(z))
spot_grid = 0.08 + (0.05 * np.abs(X_focus))
interval_grid = 25.4 / Y_focus
Z_overlap_pct = (spot_grid - interval_grid) / spot_grid
Z_overlap_pct = np.clip(Z_overlap_pct, -0.5, 1.0) # Clip for display

# --- PLOT 1: PWM STABILITY ---
# Custom colormap: Red (Bad) -> Yellow (Ok) -> Green (Good) -> Blue (Excellent)
colors_pwm = [(1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1)] 
cmap_pwm = mcolors.LinearSegmentedColormap.from_list("custom_pwm", colors_pwm, N=100)
# --- PLOT 3: FOCUS SWEET SPOT ---
# Custom Map: Blue(Gap) -> Green(Perfect) -> Red(Overlap/Trench)
colors_focus = [(0, 0, 1), (0, 1, 0), (1, 0, 0)]
nodes = [0.0, 0.5, 1.0] # Scale mapping assumes normalized 0-1 later? No, let's map manual values.
# Let's map values: <0 (Gap, Blue), 0.15-0.30 (Sweet, Green), >0.5 (Trench, Red)
cmap_focus = mcolors.LinearSegmentedColormap.from_list("custom_focus", ["blue", "cyan", "lime", "yellow", "red"], N=100)
# Normalize center around 0.2 (20% overlap)
divnorm = mcolors.TwoSlopeNorm(vmin=-0.2, vcenter=0.2, vmax=0.6)
