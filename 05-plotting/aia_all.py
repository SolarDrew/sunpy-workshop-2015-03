"""
This example plot a nice image showing data from all AIA wavelengths and the
LOS magnetic field from HMI.
"""
# Imports
import os
import datetime

import astropy.units as u
import matplotlib.pyplot as plt

import sunpy.map
from sunpy.net import vso
from sunpy.time import parse_time

# Parameters
# Directory to store the data in
data_dir = '/home/nabobalis/'

# Start time and end time for the AIA search
start = parse_time('2014/12/09T10:01:30')
stop = start + datetime.timedelta(seconds=12)
stop_hmi = start + datetime.timedelta(seconds=30)

# Set up the submap box for the edge images in arcseconds
# Bottom X, Bottom Y , Width, Height
bx, by, w, h = -300, -150, 600, 300
# Padding for the labels, from the bottom right corner in arcseconds
label_padx, label_pady = 50, 20

#==============================================================================
# Comment this block out after first run
#==============================================================================
# Define two VSO Searches for the AIA data and the HMI data
search_aia = vso.attrs.Time(start, stop) & vso.attrs.Instrument('AIA')
search_hmi = vso.attrs.Time(start, stop_hmi) & vso.attrs.Instrument('HMI') & vso.attrs.Physobs('LOS_magnetic_field')

# Create the VSO Client
vsoClient = vso.VSOClient()

# Query VSO for both searches using the or operator `|`
results = vsoClient.query(search_aia | search_hmi)
# Download the data to the data directory
files = vsoClient.get(results, path="{base_dir}/{{file}}".format(base_dir=data_dir))
# Wait for the download to finish and show a progress bar.
files.wait(progress=True)

#==============================================================================

# Create the SunPy Maps for all the files
maps = sunpy.map.Map(os.path.join(data_dir, 'aia_lev1_*'))
hmimap = sunpy.map.Map(os.path.join(data_dir, 'hmi_*')).rotate(order=3)

# Create a dictionary where the keys are the wavelengths and the values are the maps
mapw = {map.wavelength:map.rotate(order=3) for map in maps}
mapw.update({6173.0:hmimap})


# We have a sorted list for the locations of the wavelengths in the figure,
# This goes from bottom left to top left then bottom right to top right,
# with the centre image last. This order is by temperature.
sorted_wavelengths = [335, 211, 171, 304, 6173.0, 193, 131, 94, 1700] #  u.AA

# Create a new dictionary but with the cropped maps rather than the whole disk.
maps = {map.wavelength:map.submap((bx, bx+w), (by, by+h)) for map in [mapw[key] for key in sorted_wavelengths[:-1]]}
maps.update({1700:mapw[1700].submap((-1000,1000), (-1000,1000))})


# Matplotlib Plotting
# Create a figure with correct width:height ratio
fig = plt.figure(figsize=(10,5))

# Add the axes to the figure.
height = 0.25
edge_width = 0.25
left_axes = [fig.add_axes([0, i*height, edge_width, height]) for i in range(4)]
right_axes = [fig.add_axes([1.-edge_width, i*height, edge_width, height]) for i in range(4)]
centre_axes = [fig.add_axes([edge_width, 0, 1.0-2*edge_width, 1])]

# Create a dictionary mapping wavelength to the correct axis, this is where the
# ordering of the sorted_wavelengths list has to match the axes generation.
axes = {wave:ax for wave, ax in zip(sorted_wavelengths, left_axes+right_axes+centre_axes)}

def mapwplot(key):
    """
    A function to plot the map and write the wavelength in the bottom left corner
    """
    # We do this manually because of a bug in map.plot()
    axes[key].imshow(maps[key].data, cmap=maps[key].cmap, norm=maps[key].mpl_color_normalizer, extent=maps[key].xrange + maps[key].yrange)
    if key not in (6173.0, sorted_wavelengths[-1]): # Not the main frame or HMI
        axes[key].text(bx+label_padx, by+label_pady, (key*u.AA).to(u.nm)._repr_latex_(),
                       color='w', fontdict={'fontsize':16})

# Run the above function on every key in the maps dictionary.
map(mapwplot, maps.keys())

# Remove all tick labels from all axes.
[ax.axes.get_xaxis().set_ticks([]) for ax in axes.values()]
[ax.axes.get_yaxis().set_ticks([]) for ax in axes.values()]

# Manually write on the text for the main image and the HMI image.
axes[6173.].text(bx+label_padx, by+label_padx, r"LOS Magnetic Field", color='w',
                 fontdict={'fontsize':16})
axes[sorted_wavelengths[-1]].text(-950, -990, (1700*u.AA).to(u.nm)._repr_latex_(),
                                  color='w', fontdict={'fontsize':16})

# Add a rectangle to the main image showing the crop box for the satellite images.
re = plt.Rectangle((bx,by), w, h, fc='none')
axes[sorted_wavelengths[-1]].add_patch(re)

# Display the Figure.
plt.show()
