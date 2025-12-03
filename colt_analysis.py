#!/usr/bin/env python
# -*- coding: utf-8 -*-
# written by Shyam Menon, 2025
"""
COLT analysis/plotting scripts
"""
import numpy as np
import h5py
import matplotlib.pyplot as plt
import PhysicalConstantsCGS as const
import yt
import cmasher as cm
import os
import argparse

def emission_maps(file,teq=False):
    from matplotlib.colors import LogNorm

    fig,axs = plt.subplots(2,3,figsize=(16.2,9.6),tight_layout=True)
    lines = ["Halpha","Hbeta","NII-6585","OIII-5008","OIII-4364","NIV-1486"]
    labels = [r"${\rm H}\alpha$",r"${\rm H}\beta$",r"[NII] 6585\AA",r"[OIII] 5008\AA",r"[OIII] 4364\AA",r"[NIV] 1486\AA"]
    colorbars = [cm.lavender_r, cm.amber,cm.flamingo_r, cm.dusk, cm.toxic, cm.ghostlight]

    baseDirectory = os.path.dirname(os.path.abspath(file))
    fileNo = int(os.path.basename(file).split('_')[-1].split('.')[0])

    basefile = f'{baseDirectory}/colt_dir/colt_{fileNo:04d}.hdf5'
    bf = h5py.File(basefile, 'r')
    extent = [bf['bbox'][0][0]/const.Parsec, bf['bbox'][1][0]/const.Parsec, bf['bbox'][0][1]/const.Parsec, bf['bbox'][1][1]/const.Parsec]

    for i,line in enumerate(lines):
        file = baseDirectory + f'/colt_dir/{line}_{fileNo:04d}.hdf5'
        f = h5py.File(file, 'r')
        data = f['images'][:]
        ax = axs[i//3,i%3]

        image_data = data[0]
        
        # Use LogNorm for log scaling instead of manually taking log10
        im = ax.imshow(image_data, norm=LogNorm(vmin=image_data.max()/1.e5,vmax=image_data.max()),cmap=colorbars[i],origin='lower',extent=extent)
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label(labels[i] + r'$\, (\rm erg s ^{-1})$')

    axs[1,0].set_xlabel(r'$x \, (\rm pc)$')
    axs[1,1].set_xlabel(r'$x \, (\rm pc)$')
    axs[1,2].set_xlabel(r'$x \, (\rm pc)$')
    axs[0,0].set_ylabel(r'$y \, (\rm pc)$')
    axs[1,0].set_ylabel(r'$y \, (\rm pc)$')

    fig.savefig(baseDirectory + f'/colt_emission_maps_{fileNo:04d}.pdf',bbox_inches='tight')

def ionization_state_maps(file,teq=False):

    baseDirectory = os.path.dirname(os.path.abspath(file))
    fileNo = int(os.path.basename(file).split('_')[-1].split('.')[0])

    if(teq is True):
        states_file = f'{baseDirectory}/colt_dir/states-teq_{fileNo:04d}.hdf5'
    else:
        states_file = f'{baseDirectory}/colt_dir/states_{fileNo:04d}.hdf5'
    f = h5py.File(states_file, 'r')
    basefile = f'{baseDirectory}/colt_dir/colt_{fileNo:04d}.hdf5'
    bf = h5py.File(basefile, 'r')
    extent = [bf['bbox'][0][0]/const.Parsec, bf['bbox'][1][0]/const.Parsec, bf['bbox'][0][1]/const.Parsec, bf['bbox'][1][1]/const.Parsec]

    # Memory-efficient approach: define species list to read one at a time
    species_list = [
        ('x_OI', 'OI', 'k'),
        ('x_OII', 'OII', 'w'),
        ('x_OIII', 'OIII', 'w'),
        ('x_CII', 'CII', 'k'),
        ('x_CIII', 'CIII', 'w'),
        ('x_CIV', 'CIV', 'w'),
        ('x_NII', 'NII', 'k'),
        ('x_NIII', 'NIII', 'w'),
        ('x_NIV', 'NIV', 'w')
    ]

    from matplotlib.colors import LogNorm
    fig,axs = plt.subplots(3,3,figsize=(16.2,14.4),tight_layout=False)

    # Single container for image data - gets overwritten for each species
    image_container = None

    # Loop through species and plot each one immediately after reading
    for idx, (species_key, species_name, text_color) in enumerate(species_list):
        # Calculate subplot position
        row = idx // 3
        col = idx % 3
        ax = axs[row, col]
        
        # Read data into container (overwrites previous data to save memory)
        image_container = f[species_key][:].reshape((512,512,512))[:,:,256]
        
        # Plot immediately
        im = ax.imshow(image_container, origin='lower', vmin=0.0, vmax=1.0, extent=extent)
        ax.text(0.7, 0.1, species_name, color=text_color, transform=ax.transAxes, fontsize=16)
        
        # Clear the container to free memory (optional but helpful)
        del image_container

    axs[-1,0].set_xlabel(r'$x \, (\rm pc)$')
    axs[-1,1].set_xlabel(r'$x \, (\rm pc)$')
    axs[-1,2].set_xlabel(r'$x \, (\rm pc)$')
    axs[0,0].set_ylabel(r'$y \, (\rm pc)$')
    axs[1,0].set_ylabel(r'$y \, (\rm pc)$')
    axs[2,0].set_ylabel(r'$y \, (\rm pc)$')

    [[x00,y00],[x01,y01]] = axs[0,2].get_position().get_points()
    [[x10,y10],[x11,y11]] = axs[2,2].get_position().get_points()
    pad = 0.1; width = 0.03
    cbar_ax = fig.add_axes([x11+pad, y10, width, y01-y10])
    cbar = fig.colorbar(im,cax = cbar_ax)
    label_plot = r'$x_{\rm i}$'
    cbar.ax.set_ylabel(label_plot,rotation=90,
                labelpad=-10,fontsize=24)
    
    if(teq is True):
        outFilename = baseDirectory + f'/colt_ion_states-teq_{fileNo:04d}.pdf'
    else:
        outFilename = baseDirectory + f'/colt_ion_states_{fileNo:04d}.pdf'

    fig.savefig(outFilename,bbox_inches='tight')

def ionization_phase_diagrams(file,teq=False):

    baseDirectory = os.path.dirname(os.path.abspath(file))
    fileNo = int(os.path.basename(file).split('_')[-1].split('.')[0])
    if(teq is True):
        states_file = f'{baseDirectory}/colt_dir/states-teq_{fileNo:04d}.hdf5'
    else:
        states_file = f'{baseDirectory}/colt_dir/states_{fileNo:04d}.hdf5'
    f = h5py.File(states_file, 'r')

    # Load Flash simulation data for density and temperature
    flashFile = file
    ds = yt.load(flashFile)
    ad = ds.all_data()

    max_resolution = (2**ds.max_level) * ds.domain_dimensions
    cg = ds.covering_grid(level=ds.max_level,left_edge=ds.domain_left_edge, dims=max_resolution)
    number_density = cg["number_density"].flatten()
    temperature = cg["temp"].flatten()

    # Create 2D phase diagram
    from matplotlib.colors import LogNorm
    import matplotlib.pyplot as plt

    fig, axs = plt.subplots(3, 3, figsize=(16.2, 14.4), tight_layout=False)

    # Define phase space bins
    number_density_bins = np.logspace(0, 7, 100)  # Adjust range as needed
    temp_bins = np.logspace(1, 6, 100)  # 100K to 1MK

    # Function to create 2D histogram weighted by ionization fraction
    def create_phase_diagram(density, temperature, ionization_fraction, bins_x, bins_y):
        # Create 2D histogram
        H, xedges, yedges = np.histogram2d(density, temperature, bins=[bins_x, bins_y])
        H_weighted, _, _ = np.histogram2d(density, temperature, bins=[bins_x, bins_y], 
                                        weights=ionization_fraction)
        
        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            avg_ionization = H_weighted / H
            avg_ionization[H == 0] = np.nan
        
        return avg_ionization.T, xedges, yedges

    # Memory-efficient species list (dataset_key, display_name, text_color)
    species_keys = [
        ('x_OI', 'OI', 'k'), ('x_OII', 'OII', 'k'), ('x_OIII', 'OIII', 'k'),
        ('x_CII', 'CII', 'k'), ('x_CIII', 'CIII', 'k'), ('x_CIV', 'CIV', 'k'),
        ('x_NII', 'NII', 'k'), ('x_NIII', 'NIII', 'k'), ('x_NIV', 'NIV', 'k')
    ]

    # Single container for ionization data - gets overwritten for each species
    ion_frac_container = None

    # Create phase diagrams for each species
    for idx, (species_key, species_name, text_color) in enumerate(species_keys):
        row = idx // 3
        col = idx % 3
        ax = axs[row, col]
        
        # Read ionization fraction data into container (overwrites previous data to save memory)
        ion_frac_container = f[species_key][:]
        
        # Create 2D phase diagram
        phase_data, x_edges, y_edges = create_phase_diagram(number_density, temperature, 
                                                        ion_frac_container, number_density_bins, temp_bins)
        
        # Plot phase diagram
        # mask non-positive / invalid entries (LogNorm cannot handle zeros or negatives)
        masked_phase = np.ma.array(phase_data)
        masked_phase = np.ma.masked_invalid(masked_phase)
        masked_phase = np.ma.masked_where(masked_phase <= 0, masked_phase)

        # pick a sensible vmin (smallest positive value) or fallback
        pos = phase_data[np.isfinite(phase_data) & (phase_data > 0)]
        vmin = 1e-4

        # plot with logarithmic color scale
        im = ax.imshow(masked_phase, origin='lower', aspect='auto',
                    extent=[np.log10(number_density_bins[0]), np.log10(number_density_bins[-1]),
                            np.log10(temp_bins[0]), np.log10(temp_bins[-1])],
                    norm=LogNorm(vmin=vmin, vmax=1.0), cmap='viridis')
        
        # Add species label
        ax.text(0.7, 0.1, species_name, color=text_color, 
                transform=ax.transAxes, fontsize=16, weight='bold')
        
        # Set axis labels for bottom row
        if row == 2:
            ax.set_xlabel(r'$\log_{10}(n \, [\rm cm^{-3}])$')
        
        # Set axis labels for left column
        if col == 0:
            ax.set_ylabel(r'$\log_{10}(T \, [\rm K])$')
        
        # Clear the container to free memory (optional but helpful)
        del ion_frac_container

    # Add colorbar
    [[x00,y00],[x01,y01]] = axs[0,2].get_position().get_points()
    [[x10,y10],[x11,y11]] = axs[2,2].get_position().get_points()
    pad = 0.1; width = 0.03
    cbar_ax = fig.add_axes([x11+pad, y10, width, y01-y10])
    cbar = fig.colorbar(im, cax=cbar_ax)
    label_plot = r'$x_{\rm i}$'
    cbar.ax.set_ylabel(label_plot, rotation=90, labelpad=-10, fontsize=24)

    if(teq is True):
        outFilename = baseDirectory + f'/colt_ionphase-teq_{fileNo:04d}.pdf'
    else:
        outFilename = baseDirectory + f'/colt_ionphase_{fileNo:04d}.pdf'
    fig.savefig(outFilename,bbox_inches='tight')

    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plots/analysis for COLT outputs.')
    parser.add_argument("-file", type=str, nargs="*", help='Path to the FLASH pltfile for which COLT has produced outputs.')
    parser.add_argument("-teq",action='store_true', help='If set, uses the temperature equilibrium version files.')
    args = parser.parse_args()
    files = args.file
    for file in files:
        emission_maps(file,teq=args.teq)
        ionization_state_maps(file,teq=args.teq)
        ionization_phase_diagrams(file,teq=args.teq)