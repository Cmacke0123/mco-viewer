
####################################
#          Connor MacKenzie        #
####################################

import os
import re
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.widgets import Button


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
                    print(f"Warning: Line {line_num + 1} has extra points, trimming to {nx}")
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
input_dir_1 = r"D:\cmackenzie\ITER LePIC Data\sim16\Macho\DATA_mco"
input_dir_2 = r"D:\cmackenzie\ITER LePIC Data\sim17\Macho\DATA_mco"
label_1 = "Sim 16 (Updated hydrogen cross sections)"
label_2 = "Sim 17 (Legacy hydrogen cross sections)"


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
# figure() env. set up
#
current_index = 0
cax1 = None
cax2 = None

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))
fig.subplots_adjust(bottom=0.10, top=0.90, left=0.05, right=0.95, wspace=0.35)


def draw_panel(ax, file_name, dir_path, dir_label, existing_cax):
    """Render one panel. Returns the new cax so the caller can track it."""
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

    im = ax.imshow(data, cmap='gist_heat', origin='lower', aspect='auto')
    ax.set_title(f"{dir_label}\n{file_name}", fontsize=13)
    ax.set_xlabel(units["xlabel"], fontsize=12)
    ax.set_ylabel(units["ylabel"], fontsize=12)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.tick_params(left=False, bottom=False)

    divider = make_axes_locatable(ax)
    new_cax = divider.append_axes("right", size="5%", pad=0.10)
    cbar = plt.colorbar(im, cax=new_cax)
    cbar.set_label(units["cbar_label"], fontsize=11)

    return new_cax


def update_plot(index):
    global cax1, cax2
    file_name = mco_files[index]

    # Left panel – dir 1
    d1 = dir_path_for(file_name, prefer=1)
    d2 = dir_path_for(file_name, prefer=2)

    cax1 = draw_panel(ax1, file_name, d1, label_1, cax1)
    cax2 = draw_panel(ax2, file_name, d2, label_2, cax2)

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

plt.show()