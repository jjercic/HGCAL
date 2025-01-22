import matplotlib.pyplot as plt
import packingHelper as pkg
import os
import sys
import json
import uproot
import numpy as np
from shapely.geometry import shape # you need to run "python3 -m pip install shapely" to install shapely the first time
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import Normalize
from shapely.geometry import Polygon

event_id = int(float(sys.argv[1]))

# Read the outputs of 14 Stage_1 boards. Each one outputs eta(20)xphi(24) = 480 pTTs for CEE + 480 pTTs for CEH in 8-bit format. Store it in two arrays.
def sum_TowerSumsInput(directory_path):
    # Initialize arrays to store energies
    tower_sums_CEE = np.zeros((3, 20, 24))
    tower_sums_CEH = np.zeros((3, 20, 24))
    for s1_sector in range(3): #Loop over 3 sectors
        for s1_board in range(14): #Loop over 14 S1boards in each sector
            file_path_CEE = os.path.join(directory_path, f"TowerSums_Sector_{s1_sector}_Board_{s1_board}_CE_E.txt")
            file_path_CEH = os.path.join(directory_path, f"TowerSums_Sector_{s1_sector}_Board_{s1_board}_CE_H.txt")
            # Open and read the file
            with open(file_path_CEE, 'r') as file:
                region = 'CE-E'
                for phi in range(24):
                    for eta in range(20):
                        # Read the next line
                        line = file.readline().strip()
                        if not line:
                            raise ValueError("File does not contain the expected 480 lines")
                        energy = int(line, 16) #convert hex (base 16) to integer
                        energy_unpacked = pkg.unpack4E4M_ToInt(energy) #unpack from 4E4M format
                        energy_unpacked = pkg.undo_trimming(energy_unpacked, 19, 34)
                        energy_float = pkg.unpackFloat_FromInt(energy_unpacked) #unpack from int

                        tower_sums_CEE[s1_sector,eta,phi] += energy_float
                        #if(energy_float > 0.5): print(f"s1_sector = {s1_sector}, s1_board = {s1_board} eta = {eta}, phi = {phi}, energy = {tower_sums_CEE[s1_sector,eta,phi]}")


            with open(file_path_CEH, 'r') as file:
                region = 'CE-H'
                for phi in range(24):
                    for eta in range(20):
                        # Read the next line
                        line = file.readline().strip()

                        if not line:
                            raise ValueError("File does not contain the expected 480 lines")

                        energy = int(line, 16) #convert hex (base 16) to integer
                        energy_unpacked = pkg.unpack4E4M_ToInt(energy) #unpack from 4E4M format
                        energy_unpacked = pkg.undo_trimming(energy_unpacked, 19, 35)
                        energy_float = pkg.unpackFloat_FromInt(energy_unpacked) #unpack from int

                        tower_sums_CEH[s1_sector,eta,phi] += energy_float

    return tower_sums_CEE, tower_sums_CEH


def find_coord(eta, phi, z): # Determining the position of photon entry
    theta = 2 * np.arctan(np.exp(-eta))
    r = z * np.tan(theta)
    x = np.round(r * np.cos(phi), 2)
    y = np.round(r * np.sin(phi), 2)

    return x, y



def plot_bins_from_geojson(tower_sums,geojson_file, output_dir, type, simulation, event):
    # Read GeoJSON file and dictionary to store bins grouped by layer
    with open(geojson_file, 'r') as f:
        single_layer_bins = json.load(f)['Bins']
    bins = []
    #choose the S1 sector
    for bin_idx in range(len(single_layer_bins)):
        S1_Sector = single_layer_bins[bin_idx]["S1_Sectors"][0]
        eta = single_layer_bins[bin_idx]["S1_Sector"+str(S1_Sector)]['eta_index']
        phi = single_layer_bins[bin_idx]["S1_Sector"+str(S1_Sector)]['phi_index']
        Xvertices = single_layer_bins[bin_idx]['verticesX']
        Yvertices = single_layer_bins[bin_idx]['verticesY']
        polygon = pointtopolygon([Xvertices,Yvertices])
        bins.append({"S1_Sector":S1_Sector,"eta":eta,"phi":phi,"polygon":polygon,})

    # Plot bins
    if bins:
        cmap = plt.cm.viridis
        norm = plt.Normalize(vmin=0, vmax=max(tower_sums.flatten()))
        colorbar = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
        colorbar.set_array([])
        fig = plt.figure(figsize=(12, 10))
        total_energy = 0.

        for bin_index in range(len(bins)):
            eta = bins[bin_index]['eta']
            phi = bins[bin_index]['phi']
            bin_geometry =bins[bin_index]['polygon']
            S1_Sector =  bins[bin_index]['S1_Sector']
            total_energy += tower_sums[S1_Sector,eta,phi]
            plt.fill(*bin_geometry.exterior.xy, color=colorbar.to_rgba(tower_sums[S1_Sector,eta,phi]))
            plt.plot(*bin_geometry.exterior.xy, color='black', linewidth=0.2)
            plt.gca().set_aspect('equal', adjustable='datalim')

        plt.title(f"Trigger Towers - {type}")
        plt.xlabel('x [a.u.]')
        plt.ylabel('y [a.u.]')
        plt.grid(True)

        #Draw gen_photon info
        root = uproot.open(simulation)
        tree = root.get("l1tHGCalTriggerNtuplizer/HGCalTriggerNtuple")
        #print(tree.keys())
        selected_branches = ["event","good_genpart_exeta","good_genpart_exphi","good_genpart_energy"]
        branches = tree.arrays(selected_branches)

        event_index = pkg.get_index(branches["event"],event)[0]

        # Finding photon energy value for a specific event
        gen_eta_index = pkg.eta_index(branches["good_genpart_exeta"][event_index])
        gen_energy = branches["good_genpart_energy"][event_index][gen_eta_index]
        gen_eta = branches["good_genpart_exeta"][event_index][gen_eta_index]
        gen_phi = branches["good_genpart_exphi"][event_index][gen_eta_index]
        z_0 = 1 # Distance of the 1st layer from the origin of the HGCal detector

        x, y = find_coord(gen_eta, gen_phi, z_0)
        plt.plot(x, y, 'rx')  # 'rx' specifies red color ('r') and 'x' marker

        plt.figtext(0.15, 0.83, f'Gen energy = {gen_energy:.1f} GeV \n TT energy = {total_energy:.1f} GeV')

        # Save the plot as a PNG file
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = os.path.join(output_dir, f'sum_output_stage1_{type}_event_{event}.png')
        print(output_file)
        plt.savefig(output_file)
        plt.close()
        add_colorbar(output_dir, max(tower_sums.flatten()))  # add a colorbar to all images in the "out" folder


def add_colorbar(path, color_max):
    # Iteration through images in folder "out"
    for filename in os.listdir(path):
        if filename.endswith(".png") and "_colorbar" not in filename:  # Check the image extension and if it does not already have a colorbar
            # Load image from folder "out"
            img = plt.imread(os.path.join(path, filename))
            fig, ax = plt.subplots(figsize=(15, 10))
            ax.imshow(img)
            ax.axis('off')  # Turn off axis labels
            # Create colorbar on the right side
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.04)
            norm = Normalize(vmin=0, vmax=color_max)  # colorbar range

            cbar = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap='viridis'), cax=cax, fraction=0.046, aspect=1)
            cbar.set_label('Energy [GeV]')
            filename_new = filename.replace(".png", "")
            plt.savefig(os.path.join(path, filename_new + '_colorbar.png'), bbox_inches='tight')

            plt.close()
            os.remove(os.path.join(path,filename))

def is_within_bounds(array, x, y):
    rows, cols = array.shape
    return 0 <= x < rows and 0 <= y < cols

def pointtopolygon(vertices):
    points = []
    for i in range(len(vertices[0])):
        if vertices[0][i]!= 0 or vertices[1][i] != 0:
            points.append((vertices[0][i],vertices[1][i]))
    return(Polygon(points))


tower_sums_CEE, tower_sums_CEH = sum_TowerSumsInput('output/Stage1_TowerSums/')
plot_bins_from_geojson(tower_sums_CEE,"inputs/geometry/v16/tower_bins_24phi.geojson", "plots/TriggerTowers/", "CEE", "/eos/user/t/tsculac/BigStuff/HGCAL/V16_data_ntuples_15June2024/SinglePhotonPU0V16.root", event_id)
plot_bins_from_geojson(tower_sums_CEH,"inputs/geometry/v16/tower_bins_24phi.geojson", "plots/TriggerTowers/", "CEH", "/eos/user/t/tsculac/BigStuff/HGCAL/V16_data_ntuples_15June2024/SinglePhotonPU0V16.root", event_id)

#plot_bins_from_geojson(tower_sums_CEE,"inputs/geometry/v16/tower_bins_24phi.geojson", "plots/TriggerTowers/", "CEE", "/eos/user/t/tsculac/BigStuff/HGCAL/V16_data_ntuples_15June2024/SinglePionPU0V16.root", event_id)
#plot_bins_from_geojson(tower_sums_CEH,"inputs/geometry/v16/tower_bins_24phi.geojson", "plots/TriggerTowers/", "CEH", "/eos/user/t/tsculac/BigStuff/HGCAL/V16_data_ntuples_15June2024/SinglePionPU0V16.root", event_id)

