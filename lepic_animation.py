

import os
import re
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.axes_grid1 import make_axes_locatable


#
# Path(s) config
#

seq_dir    = r"E:\cmackenzie\ITERLePIC_DATA\sim23\Macho\DATA_seq"
output_dir = ".\Animations"
SAVE_FORMAT = 'gif'

FPS = 5      # frames per second
FIXED_CLIM = True   # True = colour scale locked across all timesteps for a variable


#
# *.mco file loader
#

def load_mco(filename):
    try:
        with open(filename, 'r') as f:
            nx, ny = map(int, f.readline().strip().split())
            data = []
            for i in range(ny):
                row = f.readline().strip().split()
                if len(row) > nx:
                    row = row[:nx]
                elif len(row) < nx:
                    raise ValueError(f"Row {i+1}: expected {nx} values, got {len(row)}")
                data.append(list(map(float, row)))
        data = np.array(data)
        return data
    except Exception as e:
        print(f"  ✗ {os.path.basename(filename)}: {e}")
        return None


def get_units(var_prefix):
    """Return cbar label for a variable prefix like 'j1', 'n3', 'phi', 'Ex'."""
    patterns = [
        (r"bcnd", ""),
        (r"dr",   ""),
        (r"Ex",   r"$\vec{E}_x\ (V/m)$"),
        (r"Ey",   r"$\vec{E}_y\ (V/m)$"),
        (r"j[1-5]", r"$\Gamma_i\ (m^{-2}s^{-1})$"),
        (r"n[1-5]", r"$n_i\ (m^{-3})$"),
        (r"phi",    r"$\phi\ (V)$"),
        (r"sour[2-4]", r"$(m^{-3}s^{-1})$"),
        (r"T[1-5]", r"$T\ (eV)$"),
    ]
    for pat, label in patterns:
        if re.fullmatch(pat, var_prefix):
            return label
    return ""


def natural_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


#
# Group variable files for animation
#
os.makedirs(output_dir, exist_ok=True)

all_files = sorted(
    [f for f in os.listdir(seq_dir) if f.endswith('.mco')],
    key=natural_sort_key
)

print(f"Found {len(all_files)} .mco files in {seq_dir}\n")

groups = defaultdict(list)
for fname in all_files:
    # strip extension, split on last underscore-number block
    stem = fname[:-4]                       # e.g. "j1_007"
    m = re.match(r'^(.+?)_(\d+)$', stem)   # prefix = "j1", step = "007"
    if m:
        prefix = m.group(1)
    else:
        prefix = stem                       # fallback: whole name is prefix
    groups[prefix].append(fname)

print(f"Variables found ({len(groups)}): {sorted(groups.keys())}\n")


#
# Main for loop to make animation
#

for var, fnames in sorted(groups.items()):
    fnames = sorted(fnames, key=natural_sort_key)
    print(f"  {var}: {len(fnames)} timesteps … ", end='', flush=True)

    # Load all frames
    frames = []
    for fname in fnames:
        data = load_mco(os.path.join(seq_dir, fname))
        if data is not None:
            frames.append(data)

    if len(frames) < 2:
        print("skipped (< 2 valid frames)")
        continue

    stack     = np.stack(frames)
    vmin      = stack.min() if FIXED_CLIM else None
    vmax      = stack.max() if FIXED_CLIM else None
    cbar_label = get_units(var)

    # Build figure
    fig, ax = plt.subplots(figsize=(4, 5))
    fig.patch.set_facecolor('#0d0d0d')
    ax.set_facecolor('#0d0d0d')

    im = ax.imshow(frames[0], cmap='inferno', origin='lower',
                   aspect='auto', vmin=vmin, vmax=vmax)

    divider = make_axes_locatable(ax)
    cax     = divider.append_axes("right", size="5%", pad=0.1)
    cbar    = fig.colorbar(im, cax=cax)
    cbar.set_label(cbar_label, fontsize=12, color='white')
    cbar.ax.yaxis.set_tick_params(color='white')
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white')

    title_obj  = ax.set_title(f"{var}  –  step 1 / {len(frames)}",
                               fontsize=13, color='white', pad=8)
    ax.set_xlabel("X", fontsize=12, color='white')
    ax.set_ylabel("Z", fontsize=12, color='white')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.tick_params(left=False, bottom=False)
    plt.tight_layout()

    def make_update(im_, title_, frames_, fixed):
        def update(i):
            im_.set_data(frames_[i])
            if not fixed:
                im_.set_clim(frames_[i].min(), frames_[i].max())
            title_.set_text(f"{var}  –  step {i+1} / {len(frames_)}")
            return im_, title_
        return update

    ani = animation.FuncAnimation(
        fig,
        make_update(im, title_obj, frames, FIXED_CLIM),
        frames=len(frames),
        interval=1000 // FPS,
        blit=True,
        repeat=True,
    )

    # Save
    out_path = os.path.join(output_dir, f"{var}.{SAVE_FORMAT}")
    if SAVE_FORMAT == 'mp4':
        ani.save(out_path, writer=animation.FFMpegWriter(fps=FPS, bitrate=1800))
    else:
        ani.save(out_path, writer='pillow', fps=FPS)

    plt.close(fig)
    print(f"saved → {out_path}")

print("\nDone.")