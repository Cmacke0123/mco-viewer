import os
import re
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.widgets import Button


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
    (r"j[1-5]\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\Gamma_i$"}),  
    (r"n[1-5]\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$n_i$"}),  
    (r"phi\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": r"$\phi$"}),  
    (r"sour[2-4]\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": r"($m^{-3}s^{-1}$)"}),
    (r"T[1-5]\.mco", {"xlabel": "X", "ylabel": "Z", "cbar_label": "T(eV)"})
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
    ax = plt.gca()  
    im = ax.imshow(data, cmap='inferno', origin='lower', aspect='auto')
    
    # Create a color bar closer to the plot
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)  
    cbar = plt.colorbar(im, cax=cax)
    cbar.set_label(cbar_label, fontsize=14)  
    
    
    # Set title and axis labels
    ax.set_title(title, fontsize=16)    
    ax.set_xlabel(xlabel, fontsize=14)  
    ax.set_ylabel(ylabel, fontsize=14)  
    ax.set_xticks([])
    ax.set_yticks([])
    ax.tick_params(left=False, bottom=False) 


# Setting input directory
input_dir = "D:\cmackenzie\ITER LePIC Data\sim17\Macho\DATA_mco"
mco_files = [f for f in os.listdir(input_dir) if f.endswith('.mco')]

# Initialize global variables for interactive navigation
current_index = 0
fig, ax = plt.subplots(figsize=(6, 6))

def update_plot(index):
    """Update the plot based on the current index."""
    global cax  
    ax.clear()  
    mco_file = mco_files[index]
    file_path = os.path.join(input_dir, mco_file)
    data, _ = load_mco(file_path)
    units = getUnitsFromFileName(mco_file)
    
    # Plot the data
    im = ax.imshow(data, cmap='gist_heat', origin='lower', aspect='auto')
    ax.set_title(f"Visualization of {mco_file}", fontsize=16)
    ax.set_xlabel(units["xlabel"], fontsize=14)
    ax.set_ylabel(units["ylabel"], fontsize=14)
    
    # Remove the previous color bar if it exists
    if 'cax' in globals() and cax is not None:
        cax.remove()
    
    # Add a new color bar
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    cbar = plt.colorbar(im, cax=cax)
    cbar.set_label(units["cbar_label"], fontsize=14)
    
    fig.canvas.draw_idle()  

def next_file(event):
    """Go to the next file."""
    global current_index
    if current_index < len(mco_files) - 1:
        current_index += 1
        update_plot(current_index)

def prev_file(event):
    """Go to the previous file."""
    global current_index
    if current_index > 0:
        current_index -= 1
        update_plot(current_index)

# Initial plot
update_plot(current_index)

# Add navigation buttons
axprev = plt.axes([0.7, 0.01, 0.1, 0.03])  
axnext = plt.axes([0.81, 0.01, 0.1, 0.03]) 
bnext = Button(axnext, 'Next')
bprev = Button(axprev, 'Previous')
bnext.on_clicked(next_file)
bprev.on_clicked(prev_file)

plt.show()