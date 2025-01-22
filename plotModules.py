import uproot
import numpy as np
import matplotlib.pyplot as plt
import os
import packingHelper as pkg


root = uproot.open("/eos/user/t/tsculac/BigStuff/HGCAL/V16_data_ntuples_15June2024/SinglePhotonPU0V16.root")
# root = uproot.open("/eos/user/t/tsculac/BigStuff/HGCAL/V16_data_ntuples_15June2024/SinglePionPU200V16.root")
tree = root.get("l1tHGCalTriggerNtuplizer/HGCalTriggerNtuple")
#print(tree.keys())
selected_branches = ["good_ts_x", "good_ts_y", "good_ts_energy","good_ts_layer","event","good_genpart_exeta","good_genpart_exphi","good_genpart_energy","good_genpart_pt",'good_ts_z']
branches = tree.arrays(selected_branches)

def delete_files_from_directory(directory_path):
    for file in os.listdir(directory_path):
        file_path = os.path.join(directory_path, file)
        os.remove(file_path)

def add_to_lists(list_x, list_y, list_e, x, y, e): # Function to sum energies of all layers
    overlap = False
    for i in range(len(list_x)):
        if abs(list_x[i] - x) <= 10.5 and abs(list_y[i] - y) <= 10.5: # Checking for overlap
            list_e[i] += e
            overlap = True
            break
    if not overlap: # If there was no overlap, simply add the coordinates to the lists
        list_x.append(x)
        list_y.append(y)
        list_e.append(e)

    return list_x, list_y, list_e

def plot_hexagon(list_x, list_y, list_e, i):
    # Creating hexagonal plot
    if len(list_e) > 1:
        ht = plt.hexbin(list_x, list_y, C=list_e, cmap='plasma', gridsize=23, vmax=(np.max(list_e)), vmin=np.min(list_e),extent=[-125,125,-125,125])
    else:
        ht = plt.hexbin(list_x, list_y, C=list_e, cmap='plasma', gridsize=23, vmax=(np.max(list_e)), vmin=np.min(list_e) - 0.05,extent=[-125,125,-125,125])
    #print(f"{i}. : {list_x},{list_y}")
    plt.plot(x, y, 'rx')  # 'rx' specifies red color ('r') and 'x' marker
    cb = plt.colorbar(ht)
    cb.set_label("Energy value")
    plt.xlabel("ts_x")
    plt.ylabel("ts_y")
    plt.title(f"ts_x:ts_y:ts_energy   |   ts_layer == {i}, event == {event} \n gen_energy = {gen_energy:.4f}    |    gen_pt = {gen_pt:.4f} \n Coordinates of photon entry (mm): ({x},{y})", fontsize=9)
    if not os.path.exists("plots/ModuleSums/"):
        os.makedirs("plots/ModuleSums/")
    plt.savefig(f"plots/ModuleSums/Event_{event}_layer_{i}.png")
    plt.clf()

def find_coord(eta, phi, z): # Determining the position of photon entry
    theta = 2 * np.arctan(np.exp(-eta))
    r = z * np.tan(theta)
    x = np.round(r * np.cos(phi), 2)
    y = np.round(r * np.sin(phi), 2)

    return x, y

def find_distance(old_distance, layer):
    is_even = True  # Check if the layer is even or odd
    if layer % 2 != 0:
        is_even = False
    current_cassette = round(layer / 2)
    # All distances are in cm
    cassettes = []
    cassettes.extend([0.387] * 2)      # Distance in cassettes CEE-part
    cassettes.extend([0.672] * 8)
    cassettes.extend([0.932] * 4)
    even_distance = 1.02
    odd_distance = 1.43
    ceh_si_distance = 1.785  # Cover included
    ceh_scin_distance = 1.785
    if layer < 27:  # CEE part
        if is_even:
            new_distance = old_distance + even_distance
        else:
            new_distance = old_distance + odd_distance + cassettes[current_cassette]  # Only odd layers have cassettes
    elif layer > 26 and layer < 35:  # CEH si part
        if layer == 27:
            new_distance = old_distance + 0.78 + 0.77
        else:
            new_distance = old_distance + ceh_si_distance
    else:  # CEH scintillator part
        if layer == 35:
            new_distance = old_distance + 0.925 + 0.971
        else:
            new_distance = old_distance + ceh_scin_distance

    return new_distance


event = 101858 #Event with nice photon in Sector0 in SinglePhoton Sample
# event = 10741 #Event with nice pion in Sector0 in SinglePion Sample
z_0 = 321.947 # Distance of the 1st layer from the origin of the HGCal detector

event_index = pkg.get_index(branches["event"], event)[0] # Getting the layer index, which is unique in the layers branch
ts_layer = np.asarray(branches["good_ts_layer"][event_index]) # Converting to numpy array

# Finding photon energy value for a specific event
gen_eta_index = pkg.eta_index(branches["good_genpart_exeta"][event_index])
gen_energy = branches["good_genpart_energy"][event_index][gen_eta_index]
gen_pt = branches["good_genpart_pt"][event_index][gen_eta_index]

# Calculating coordinates of photon entry
eta = branches["good_genpart_exeta"][event_index][gen_eta_index]
phi = branches["good_genpart_exphi"][event_index][gen_eta_index]

# Calculating minimum and maximum
min_layer = np.min(ts_layer)
max_layer = np.max(ts_layer)

sum_list_x = []
sum_list_y = []
sum_list_e = []

# Finding eta to be greater than 0
index_endcap = pkg.get_endcap_index(branches["good_ts_z"][event_index], 1)

# Iterating through layers
z = z_0
for i in range(min_layer, max_layer+1):
    layer_index = pkg.get_index(branches["good_ts_layer"][event_index], i) # Getting all indices where a specific layer is located
    layer_index_endcap = []
    for j in layer_index:
        if j in index_endcap:
            layer_index_endcap.append(j)
    list_x = np.array([])
    list_y = np.array([])
    list_e = np.array([])

    if len(layer_index_endcap) != 0 : # Checking if the indices are empty, expected for even layers
        for j in layer_index_endcap: # Creating lists of coordinates and energies for a specific layer
            list_x = np.append(list_x, [branches["good_ts_x"][event_index][j]])
            list_y = np.append(list_y, [branches["good_ts_y"][event_index][j]])
            list_e = np.append(list_e, [branches["good_ts_energy"][event_index][j]])
            sum_list_x, sum_list_y, sum_list_e = add_to_lists(sum_list_x, sum_list_y, sum_list_e, branches["good_ts_x"][event_index][j],
                                                                branches["good_ts_y"][event_index][j], branches["good_ts_energy"][event_index][j])
        x, y = find_coord(eta, phi, z)
        z = find_distance(z,i+1) #increse of z distance beetween layers
        plot_hexagon(list_x, list_y, list_e, i)

x, y = find_coord(eta, phi, z_0)
plot_hexagon(sum_list_x, sum_list_y, sum_list_e, "sum of all")
