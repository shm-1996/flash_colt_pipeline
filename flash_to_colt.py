#!/usr/bin/env python
# -*- coding: utf-8 -*-
#################################################################
#Convert FLASH AMR output to COLT format and modify yaml files
#Author: Shyam Menon (CCA/Rutgers, 2025)
#Email: smenon@flatironinstitute.org
#################################################################

import numpy as np
import h5py
import yt
import argparse
import os
import glob

Msun = 1.989e33 # Solar mass [g]
Year = 31557600.0
Zsun = 0.0134 # Solar metallicity (Asplund+2009)
d2g_sun = 0.0081 # Dust-to-gas ratio in the solar neighborhood (Weingartner & Draine 2001)


def convert_flash_to_colt(File, output_file='colt'):
    """
    Convert FLASH AMR output to COLT format
    
    Args:
        File (str): Path to the FLASH plt file
        output_file (str): Output HDF5 file path
    """

    #Get snapshot number of file
    snapshot_number_str = File.split('_')[-1]  # e.g., plt_cnt_0000 -> 0000
    output_dir = output_file+'_dir'
    #Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        print(f"Creating output directory for colt outputs: {output_dir}")
        os.makedirs(output_dir)

    output_file = output_file + f'_{snapshot_number_str}.hdf5'
    output_file = output_dir + '/' + output_file

    ds = yt.load(File)
    #Read in metallicities
    Zgas, dusttogasratio = ds.parameters['krome_metallicity'],ds.parameters['dusttogasratio']
    #Convert from solar-scaled to mass fractions
    Zgas = Zgas * Zsun
    dusttogasratio = dusttogasratio * d2g_sun

    #Check if inputFilename is chkFile (i.e. contains in it _hdf5_chk_)
    if '_hdf5_chk_' in File:
        print("Input file appears to be a checkpoint file (_hdf5_chk_ found in filename).")
        pf = ds
    else:
        # Derive particle file name from plt file name
        partFile = File.replace('plt_cnt', 'part')
        pf = yt.load(partFile)
    
    #Cartesian version
    #Get the maximum level (grid resolution)
    max_resolution = (2**ds.max_level) * ds.domain_dimensions
    cg = ds.covering_grid(level=ds.max_level,left_edge=ds.domain_left_edge, dims=max_resolution)
    mH = 1.6735575e-24 # Mass of hydrogen
    mH2 = 2.0*mH
    me = 9.10938356e-28 # Mass of electron

    with h5py.File(output_file,'w') as f:
        f.attrs['time'] = np.float64(ds.current_time.to('s'))  # Current simulation time
        f.attrs['nx'] = np.int32(max_resolution[0])
        f.attrs['ny'] = np.int32(max_resolution[1])
        f.attrs['nz'] = np.int32(max_resolution[2])
        f.attrs['n_cells'] = np.int32(max_resolution[0] * max_resolution[1] * max_resolution[2])
        f.create_dataset('bbox', data=np.array([ds.domain_left_edge.to('cm').d, ds.domain_right_edge.to('cm').d], dtype=np.float64)) # Bounding box [cm]
        f['bbox'].attrs['units'] = b'cm'

        f.create_dataset('v', data=np.vstack([cg["velx"].flatten(),cg["vely"].flatten(),cg["velz"].flatten()]).T, dtype=np.float64) # Velocities [cm/s]
        f['v'].attrs['units'] = b'cm/s'
        f.create_dataset('rho', data=cg["dens"].flatten(), dtype=np.float64) # Density [g/cm^3]
        f['rho'].attrs['units'] = b'g/cm^3'
        nHI = (cg["h   "] * cg["dens"]/mH).flatten()
        nH2 = (cg["h2  "] * cg["dens"]/mH2).flatten()
        nHp = (cg["hp  "] * cg["dens"]/mH).flatten()
        ne = (cg["elec"] * cg["dens"]/me).flatten()
        xHI = (nHI)/(2*nH2 + nHp + nHI)
        xH2 = (2*nH2)/(2*nH2 + nHp + nHI)
        tgas = cg["temp"].flatten()
        f.create_dataset('T', data=tgas, dtype=np.float64) # Temperature [K]
        f['T'].attrs['units'] = b'K'
        f.create_dataset('x_HI', data=xHI, dtype=np.float64) # Neutral fraction (n_HI/n_Htot)
        f.create_dataset('x_H2', data=xH2, dtype=np.float64) # Molecular fraction (2*n_H2/n_Htot)
        f.create_dataset('n_e', data=ne, dtype=np.float64) # Electron number density [cm^-3]

        f.attrs['n_stars'] = len(pf.all_data()['particle_mass']) #Number of stars
        f.create_dataset('r_star', data=np.vstack([pf.all_data()["particle_position_x"], pf.all_data()["particle_position_y"], 
                                                   pf.all_data()["particle_position_z"]]).T, dtype=np.float64) # Star positions [cm]
        f['r_star'].attrs['units'] = b'cm'
        f.create_dataset('v_star', data=np.vstack([pf.all_data()["particle_velocity_x"], pf.all_data()["particle_velocity_y"], 
                                                   pf.all_data()["particle_velocity_z"]]).T, dtype=np.float64) # Star velocities [cm/s]
        f['v_star'].attrs['units'] = b'cm/s'
        f.create_dataset('m_init_star', data=pf.all_data()["particle_mass"]/Msun, dtype=np.float64) # Star masses [g]
        f['m_init_star'].attrs['units'] = b'Msun'

        f.create_dataset('Z_star', data=np.ones(len(pf.all_data()['particle_mass']))*Zgas, dtype=np.float64) # stellar metallicites

        star_ages = (np.ones(len(pf.all_data()['particle_creation_time']))*pf.current_time.value - pf.all_data()['particle_creation_time'].value)/(1.e9*Year)
        f.create_dataset('age_star', data=star_ages, dtype=np.float64) # Star ages [Gyr]
        f['age_star'].attrs['units'] = b'Gyr'

    print(f"Successfully converted {File} to {output_file}")
    return output_file, dusttogasratio, Zgas

def prep_yaml_files(output_hdf5_file, yaml_config_file='config-ionpre.yaml', output_yaml_file=None,dusttogasratio=None, Zgas=None):
    """
    Prepare the yaml files used by COLT to reflect input file and output file names
    Uses text-based replacement to preserve COLT-specific YAML pragmas.
    
    Args:
        output_hdf5_file (str): Path to the generated HDF5 file
        yaml_config_file (str): Path to the input YAML configuration file
        output_yaml_file (str): Path for the modified YAML file (if None, overwrites input file)
    """
    import re

    if(dusttogasratio is None):
        dusttogasratio = d2g_sun
    if(Zgas is None):
        Zgas = Zsun
    
    # If no output file specified, overwrite the input file
    if output_yaml_file is None:
        output_yaml_file = os.getcwd() + '/' + os.path.basename(yaml_config_file)
        print(f"Creating YAML config file: {output_yaml_file}")
    
    try:
        # Read the existing YAML file as text
        with open(yaml_config_file, 'r') as f:
            content = f.read()

        #Update metallicity and dust-to-gas ratio fields
        d2g_pattern = r'^(\s*dust_to_gas:\s*).*(\s*#.*)?$'
        new_d2g_line = f'dust_to_gas: {dusttogasratio}     # Dust-to-gas ratio (default: 0.0081; solar neighborhood)'
        content = re.sub(d2g_pattern, new_d2g_line, content, flags=re.MULTILINE)

        Z_pattern = r'^(\s*metallicity:\s*).*(\s*#.*)?$'
        new_Z_line = f'metallicity: {Zgas}     # Gas metallicity (default: 0.0134; solar)'
        content = re.sub(Z_pattern, new_Z_line, content, flags=re.MULTILINE)

        output_hdf5_dir = os.path.relpath(os.path.dirname(output_hdf5_file)) # Directory of the HDF5 file

        init_dir_pattern = r'^(\s*init_dir:\s*).*(\s*#.*)?$'
        new_init_dir_line = f'init_dir: {output_hdf5_dir}     # Directory containing initial conditions file'
        content = re.sub(init_dir_pattern, new_init_dir_line, content, flags=re.MULTILINE)
        
        output_dir_pattern = r'^(\s*output_dir:\s*).*(\s*#.*)?$'
        new_output_dir_line = f'output_dir: {output_hdf5_dir}            # Output directory name'
        content = re.sub(output_dir_pattern, new_output_dir_line, content, flags=re.MULTILINE)
        
        # Write the modified content back to file
        with open(output_yaml_file, 'w') as f:
            f.write(content)
        
        print(f"Updated YAML configuration: {output_yaml_file}")
        print(f"  - dust_to_gas: {dusttogasratio}")
        print(f"  - metallicity: {Zgas}")
        print(f"  - output_dir: {output_hdf5_dir}")
        
    except FileNotFoundError:
        print(f"Warning: YAML config file '{yaml_config_file}' not found. Skipping YAML preparation.")
    except Exception as e:
        print(f"Error updating YAML file: {e}")



def main():
    """Main function to handle command line arguments and execute conversion"""
    parser = argparse.ArgumentParser(description='Convert FLASH AMR output to COLT format')
    parser.add_argument('File', help='Path to the FLASH plt file of format *_hdf5_plt_cnt_{snapshot}')
    parser.add_argument('-o', '--output', default='colt', help='Output HDF5 file path (default: colt_{snapshot})')
    parser.add_argument('-overwrite', action='store_true', help='Overwrite existing output files if they exist')

    args = parser.parse_args()

    #Get snapshot number of file
    snapshot_number_str = args.File.split('_')[-1]  # e.g., plt_cnt_0000 -> 0000

    output_file_name = args.output+'_dir' + '/' + args.output + f'_{snapshot_number_str}.hdf5'
    if os.path.exists(output_file_name) and not args.overwrite:
        print(f"Output file {output_file_name} already exists. Use -overwrite to overwrite existing files.")
        return
    
    # Convert FLASH to COLT format
    output_hdf5_file, dusttogasratio, Zgas = convert_flash_to_colt(args.File, args.output)

    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.realpath(__file__))

    yaml_files = glob.glob(os.path.join(script_dir, "config-*.yaml"))
    
    for file in yaml_files:
        print(f"Preparing YAML file: {file}")
        prep_yaml_files(output_hdf5_file=output_hdf5_file,yaml_config_file=file,dusttogasratio=dusttogasratio, Zgas=Zgas)


if __name__ == "__main__":
    main()

