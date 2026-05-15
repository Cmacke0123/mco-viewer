#
#  Python Library Loading 
# 

import os
import re
import numpy as np
import matplotlib.pyplot as plt 
from mpl_toolkits.axes_grid1 import make_axes_locatable

#
# Converting *.mco files into numpy arrays
#
def load_mco(filename):
    
    try:
        with open(filename, 'r') as file:
            # Parse nx and ny from the first line
            first_line = file.readline().strip().split()
            nx = int(first_line[0])
            ny = int(first_line[1])
            
            # Read and parse the rest of the file
            data = []
            for line_num in range(ny):
                line = file.readline().strip().split()
                
                # Handle mismatched line lengths
                if len(line) > nx:
                    print(f"Warning: Line {line_num + 1} has extra points, trimming to {nx}")
                    line = line[:nx]
                elif len(line) < nx:
                    raise ValueError(f"Line length {len(line)} does not match nx={nx} on line {line_num + 1}")
                
                data.append([float(point) for point in line])
            
            # Convert to NumPy array
            data = np.array(data)
            
            # Verify dimensions
            if data.shape != (ny, nx):
                raise ValueError(f"Data shape {data.shape} does not match (ny, nx)=({ny}, {nx})")
            
            # Normalize the data
            max_value = np.max(data)
            #if max_value > 0:
            #    data /= max_value
            
            return data, max_value
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None, None
    

#
# File unit directory for proper axes labelling
#

def getUnitsFromFileName(fileName):

    file_units_patterns = [
    (r"bcnd\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": ""}),
    (r"dr\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": ""}),
    (r"Ex\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$ \vec{E}_x (V/m) $"}),
    (r"Ey\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\vec{E}_y (V/m)$"}),
    (r"j[1-5]\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\Gamma_i$"}),  # Gamma/Gamma_max
    (r"n[1-5]\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$n_i$"}),  # Particle Density n/n_max
    (r"phi\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\phi$"}),  # Electric Potential phi/phi_max
    (r"sour[2-4]\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": "(m⁻³s⁻¹)"}),
    (r"T[1-5]\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\frac{T_i}{T_{\text{max}}}$"})
]

    for pattern in file_units_patterns:
        if(re.match(pattern[0], fileName)):
            return(pattern[1])
        
    return({"xlabel": "X", "ylabel": "Z", "cbar_label": ""})

#
# Plotting function for mco files
#
def plot_mco(data, title="Averaged Plasma Plots", xlabel="X-axis", ylabel="Y-axis", cbar_label="Colorbar"):
    """Plots the MCO data without showing it interactively (for saving purposes)."""
    plt.figure(figsize=(4, 5))
    ax = plt.gca()  # Get the current axes
    im = ax.imshow(data, cmap='magma', origin='lower', aspect='auto')
    
    # Create a color bar closer to the plot
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)  # Adjust pad to move closer
    cbar = plt.colorbar(im, cax=cax)
    cbar.set_label(cbar_label, fontsize=14)  # Adjust color bar label font size
    
    # Set title and axis labels
    ax.set_title(title, fontsize=16)  # Adjust title font size
    ax.set_xlabel(xlabel, fontsize=14)  # Adjust x-axis label font size
    ax.set_ylabel(ylabel, fontsize=14)  # Adjust y-axis label font size
    ax.set_xticks([])
    ax.set_yticks([])
    ax.tick_params(left=False, bottom=False)  # Remove tick marks

#
# Setting input and output directory
#

input_dir = "D:\cmackenzie\ITER LePIC Data\sim15\Macho\DATA_mco"
output_dir = "/"

mco_files = [f for f in os.listdir(input_dir) if f.endswith('.mco')]

# Process and save plots for each .mco file
for mco_file in mco_files:
    file_path = os.path.join(input_dir, mco_file)
    print(f"Loading and plotting {mco_file}")
    
    try:
        # Load the data
        data, max_value = load_mco(file_path)  
        if data is None:
            print(f"Skipping {mco_file} due to load error.")
            continue
        
        # Retrieve unit labels based on filename pattern
        units = getUnitsFromFileName(mco_file)  
        
        # Plot the data
        plot_mco(
            data,
            title=f"Visualization of {mco_file}",
            xlabel=units["xlabel"],
            ylabel=units["ylabel"],
            cbar_label=units["cbar_label"]
        )
        
        
    except Exception as e:
        print(f"Error processing {mco_file}: {e}")

       
plt.show()