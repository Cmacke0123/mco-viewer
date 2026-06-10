
#
# Import python libraries
#
import os
import re
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.widgets import Button
from matplotlib.colors import SymLogNorm, LogNorm


#
# *.mco loader
#
def load_mco(filename):
    try:
        with open(filename, 'r') as file:
            first_line = file.readline().strip().split()
            nx = int(first_line[0])
            ny = int(first_line[1])

            data = []
            for line_num in range(ny):
                line = file.readline().strip().split()

                if len(line) > nx:
                    #print(f"Warning: Line {line_num + 1} has extra points, trimming to {nx}")
                    line = line[:nx]
                elif len(line) < nx:
                    raise ValueError(f"Line length {len(line)} does not match nx={nx} on line {line_num + 1}")

                data.append([float(point) for point in line])

            data = np.array(data)

            if data.shape != (ny, nx):
                raise ValueError(f"Data shape {data.shape} does not match (ny, nx)=({ny}, {nx})")

            max_value = np.max(data)
            return data, max_value
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None, None


#
# Unit parser
#
def getUnitsFromFileName(fileName):
    file_units_patterns = [
        (r"bcnd\.mco",    {"xlabel": "X", "ylabel": "Z", "cbar_label": ""}),
        (r"dr\.mco",      {"xlabel": "X", "ylabel": "Z", "cbar_label": ""}),
        (r"Ex\.mco",      {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\vec{E}_x\ (V/m)$"}),
        (r"Ey\.mco",      {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\vec{E}_y\ (V/m)$"}),
        (r"j[1-5]\.mco",  {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\Gamma_i$"}),
        (r"n[1-5]\.mco",  {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$n_i$"}),
        (r"phi\.mco",     {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\phi$"}),
        (r"sour[2-4]\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$(m^{-3}s^{-1})$"}),
        (r"T[1-5]\.mco",  {"xlabel": "X", "ylabel": "Z", "cbar_label": "T (eV)"}),
    ]
    for pattern, units in file_units_patterns:
        if re.match(pattern, fileName):
            return units
    return {"xlabel": "X", "ylabel": "Z", "cbar_label": ""}



#
# Paths to simulations you would like to compare
#
input_dir_1 = r"D:\cmackenzie\ITER LePIC Data\sim19\Macho\DATA_mco"
input_dir_2 = r"D:\cmackenzie\ITER LePIC Data\sim20\sim20\Macho\DATA_mco"
label_1 = "Sim 19 (2026/05 Hydrogen Run (hydrogen2.dat))"
label_2 = "Sim 20 (2026/06 Hydrogen Run (Shydrogen.dat))"


# Build the union of .mco filenames present in both directories
files_1 = set(f for f in os.listdir(input_dir_1) if f.endswith('.mco'))
files_2 = set(f for f in os.listdir(input_dir_2) if f.endswith('.mco'))

# Files that exist in both directories (for matched comparison)
common_files = sorted(files_1 & files_2)
only_in_1    = sorted(files_1 - files_2)
only_in_2    = sorted(files_2 - files_1)

# Full ordered list: common first, then exclusives
mco_files = common_files + only_in_1 + only_in_2

if not mco_files:
    raise RuntimeError("No .mco files found in either directory.")

print(f"Found {len(common_files)} files in both directories, "
      f"{len(only_in_1)} only in dir1, {len(only_in_2)} only in dir2.")

#
# Calculate max values for all files
#
print("\n" + "="*80)
print("MAX VALUES FOR ALL FILES")
print("="*80)

max_values_dir1 = {}
max_values_dir2 = {}

for file_name in mco_files:
    print(f"\n{file_name}:")
    
    # Check dir1
    if file_name in files_1:
        file_path_1 = os.path.join(input_dir_1, file_name)
        data1, max1 = load_mco(file_path_1)
        if data1 is not None:
            max_values_dir1[file_name] = max1
            print(f"  {label_1}: {max1:.6e}")
    
    # Check dir2
    if file_name in files_2:
        file_path_2 = os.path.join(input_dir_2, file_name)
        data2, max2 = load_mco(file_path_2)
        if data2 is not None:
            max_values_dir2[file_name] = max2
            print(f"  {label_2}: {max2:.6e}")

print("\n" + "="*80)

#
# figure() env. set up
#
current_index = 0
cax1 = None
cax2 = None
cax3 = None
cax4 = None

fig, ((ax1_lin, ax1_log), (ax2_lin, ax2_log)) = plt.subplots(2, 2, figsize=(14, 10))
fig.subplots_adjust(bottom=0.10, top=0.90, left=0.05, right=0.95, hspace=0.35, wspace=0.35)


def draw_panel(ax, file_name, dir_path, dir_label, normalize_type, existing_cax, vmin=None, vmax=None):
    """
    Render one panel with specified normalization.
    normalize_type: 'linear' or 'log'
    Returns the new cax so the caller can track it.
    """
    ax.clear()
    if existing_cax is not None:
        try:
            existing_cax.remove()
        except Exception:
            pass

    file_path = os.path.join(dir_path, file_name)
    if not os.path.exists(file_path):
        ax.set_visible(False)
        return None

    ax.set_visible(True)
    data, _ = load_mco(file_path)
    if data is None:
        ax.text(0.5, 0.5, "Error loading file", ha='center', va='center',
                transform=ax.transAxes)
        return None

    units = getUnitsFromFileName(file_name)

    # Set up normalization
    if vmin is None or vmax is None:
        vmin = np.min(data)
        vmax = np.max(data)

    if normalize_type == 'log':
        # For log scale, check if data is positive
        if vmin > 0:
            # All positive: use standard LogNorm
            norm = LogNorm(vmin=vmin, vmax=vmax)
        else:
            # Has zero or negative values: use SymLogNorm
            # linthresh must be positive
            linthresh = max(abs(vmin), abs(vmax)) * 0.01
            if linthresh <= 0:
                linthresh = 1.0
            norm = SymLogNorm(linthresh=linthresh, vmin=vmin, vmax=vmax)
        norm_label = "Log Scale"
    else:
        # Linear normalization
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        norm_label = "Linear Scale"

    im = ax.imshow(data, cmap='gist_heat', origin='lower', aspect='auto', norm=norm)
    ax.set_title(f"{dir_label} — {norm_label}\n{file_name}", fontsize=12)
    ax.set_xlabel(units["xlabel"], fontsize=11)
    ax.set_ylabel(units["ylabel"], fontsize=11)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.tick_params(left=False, bottom=False)

    divider = make_axes_locatable(ax)
    new_cax = divider.append_axes("right", size="5%", pad=0.10)
    cbar = plt.colorbar(im, cax=new_cax)
    cbar.set_label(units["cbar_label"], fontsize=10)

    return new_cax



def update_plot(index):
    global cax1, cax2, cax3, cax4
    file_name = mco_files[index]

    # Get directories for both simulations
    d1 = dir_path_for(file_name, prefer=1)
    d2 = dir_path_for(file_name, prefer=2)

    # Load data for both simulations
    data1, _ = load_mco(os.path.join(d1, file_name))
    data2, _ = load_mco(os.path.join(d2, file_name))

    # Calculate combined vmin/vmax from both simulations
    if data1 is not None and data2 is not None:
        vmin = min(np.min(data1), np.min(data2))
        vmax = max(np.max(data1), np.max(data2))
    else:
        vmin, vmax = 0, 1

    # Both linear plots use the same scale
    cax1 = draw_panel(ax1_lin, file_name, d1, label_1 + " (Linear)", 
                      'linear', cax1, vmin=vmin, vmax=vmax)
    cax3 = draw_panel(ax2_lin, file_name, d2, label_2 + " (Linear)", 
                      'linear', cax3, vmin=vmin, vmax=vmax)

    # Both log plots use the same scale
    cax2 = draw_panel(ax1_log, file_name, d1, label_1 + " (Log)", 
                      'log', cax2, vmin=vmin, vmax=vmax)
    cax4 = draw_panel(ax2_log, file_name, d2, label_2 + " (Log)", 
                      'log', cax4, vmin=vmin, vmax=vmax)

    total = len(mco_files)
    fig.suptitle(f"File {index + 1} / {total}  —  {file_name}", fontsize=14, y=0.97)
    fig.canvas.draw_idle()


#
# Navigation
#
def dir_path_for(file_name, prefer):
    """Return the appropriate directory for a given filename."""
    if prefer == 1:
        return input_dir_1 if file_name in files_1 else input_dir_2
    else:
        return input_dir_2 if file_name in files_2 else input_dir_1


def next_file(event):
    global current_index
    if current_index < len(mco_files) - 1:
        current_index += 1
        update_plot(current_index)


def prev_file(event):
    global current_index
    if current_index > 0:
        current_index -= 1
        update_plot(current_index)


#
# Initial Render
#
update_plot(current_index)

#
# Plot Updater
#
ax_prev = plt.axes([0.40, 0.01, 0.09, 0.04])
ax_next = plt.axes([0.51, 0.01, 0.09, 0.04])
btn_prev = Button(ax_prev, '◀  Prev')
btn_next = Button(ax_next, 'Next  ▶')
btn_prev.on_clicked(prev_file)
btn_next.on_clicked(next_file)

#plt.show()
