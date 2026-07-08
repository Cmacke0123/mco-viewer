#
# plot_mco_comparison.py
#
# Generates journal-ready, side-by-side comparison plots of chosen .mco
# files from two PIC simulation output directories. Each requested file
# produces one figure (two panels, linear scale, shared color axis)
# saved as a vector PDF.
#
import os
import re
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable


input_dir_1 = r"e:\cmackenzie\ITERLePIC_DATA\sim7\Macho\DATA_mco"
input_dir_2 = r"e:\cmackenzie\ITERLePIC_DATA\sim8\Macho\DATA_mco"
label_1 = "Hydrogen Ion Flux Profile"
label_2 = "Deuterium Ion Flux Profile"

FILES_TO_PLOT = [
    "j3.mco",
]

output_dir = r"e:\cmackenzie\ITERLePIC_DATA\figures"

output_format = "pdf"

figsize = (10, 4.5)

cmap = "gist_heat"


plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "pdf.fonttype": 42,   # embed fonts as editable text, not paths
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})


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
                    line = line[:nx]
                elif len(line) < nx:
                    raise ValueError(
                        f"Line length {len(line)} does not match nx={nx} on line {line_num + 1}"
                    )

                data.append([float(point) for point in line])

            data = np.array(data)

            if data.shape != (ny, nx):
                raise ValueError(f"Data shape {data.shape} does not match (ny, nx)=({ny}, {nx})")

            return data
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None


def getUnitsFromFileName(fileName):
    file_units_patterns = [
        (r"bcnd\.mco",       {"xlabel": "X", "ylabel": "Z", "cbar_label": ""}),
        (r"dr\.mco",         {"xlabel": "X", "ylabel": "Z", "cbar_label": ""}),
        (r"Ex\.mco",         {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\vec{E}_x\ (V/m)$"}),
        (r"Ey\.mco",         {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\vec{E}_y\ (V/m)$"}),
        (r"j[1-5]\.mco",     {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\Gamma_i (A m^{-2})$"}),
        (r"n[1-5]\.mco",     {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$n_i (m^{-3})$"}),
        (r"phi\.mco",        {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\phi$"}),
        (r"sour[2-4]\.mco",  {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$(m^{-3}s^{-1})$"}),
        (r"T[1-5]\.mco",     {"xlabel": "X", "ylabel": "Z", "cbar_label": "T (eV)"}),
    ]
    for pattern, units in file_units_patterns:
        if re.match(pattern, fileName):
            return units
    return {"xlabel": "X", "ylabel": "Y", "cbar_label": ""}


def draw_panel(ax, data, units, panel_title, vmin, vmax):
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    im = ax.imshow(data, cmap=cmap, origin="lower", aspect="auto", norm=norm)

    ax.set_title(panel_title, fontsize=12)
    ax.set_xlabel(units["xlabel"])
    ax.set_ylabel(units["ylabel"])
    ax.set_xticks([])
    ax.set_yticks([])
    ax.tick_params(left=False, bottom=False)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.10)
    cbar = plt.colorbar(im, cax=cax)
    cbar.set_label(units["cbar_label"])
    return im

def make_comparison_figure(file_name):
    path_1 = os.path.join(input_dir_1, file_name)
    path_2 = os.path.join(input_dir_2, file_name)

    if not os.path.exists(path_1):
        print(f"Skipping {file_name}: not found in {input_dir_1}")
        return
    if not os.path.exists(path_2):
        print(f"Skipping {file_name}: not found in {input_dir_2}")
        return

    data1 = load_mco(path_1)
    data2 = load_mco(path_2)
    if data1 is None or data2 is None:
        print(f"Skipping {file_name}: load error")
        return

    units = getUnitsFromFileName(file_name)

    # Shared color scale across both panels
    vmin = min(np.min(data1), np.min(data2))
    vmax = max(np.max(data1), np.max(data2))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    draw_panel(ax1, data1, units, label_1, vmin, vmax)
    draw_panel(ax2, data2, units, label_2, vmin, vmax)

    fig.suptitle("Spatial Distribution of Ion Flux for Hydrogen and Deuterium Plasmas", fontsize=13, y=1.02)
    fig.tight_layout()

    os.makedirs(output_dir, exist_ok=True)
    out_name = f"{os.path.splitext(file_name)[0]}_comparison.{output_format}"
    out_path = os.path.join(output_dir, out_name)

    fig.savefig(out_path, format=output_format, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    for f in FILES_TO_PLOT:
        make_comparison_figure(f)