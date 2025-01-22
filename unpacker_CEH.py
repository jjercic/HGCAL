import uproot
import numpy as np
import re
import os
import sys 
import packingHelper as pkg

root = uproot.open("/eos/user/t/tsculac/BigStuff/HGCAL/V16_data_ntuples_15June2024/SinglePhotonPU0V16.root")
#root = uproot.open("/eos/user/t/tsculac/BigStuff/HGCAL/V16_data_ntuples_15June2024/SinglePionPU0V16.root")
tree = root.get("l1tHGCalTriggerNtuplizer/HGCalTriggerNtuple")
#print(tree.keys())
selected_branches = ["good_tc_energy","good_tc_layer","event","good_tc_waferu","good_tc_waferv","good_tc_z","good_tc_cellu","good_tc_cellv"] #tc_* are values of STCs
branches = tree.arrays(selected_branches)

#event = 176869 #Event with nice photon in Sector0 in SinglePhoton Sample
#event = 19677 #Event with nice pion in Sector0 in SinglePion Sample

event_id = int(float(sys.argv[1]))

def dict_CEH(layer,tc_u,tc_v,tc_cellu,tc_cellv, ts_en,endcap, sector=0): #A function that creates a dictionary with keys (layer,(u,v)) and energy values
    dict = {}
    for i in range(len(layer)):
        if i in endcap: #the upper side of the detector
            # We need to convert (u,v) + (cellu, cellv) labels from CMSSW to (u,v,STC_idx) labels from Pedro's mapping that was used to define our mapping from MS/STC to Stage-1
            # print(tc_u[i],tc_v[i],tc_cellu[i],tc_cellv[i],i)
            new_tc_u,new_tc_v,STC_idx,sec = pkg.getuvSTCidxsector(layer[i],tc_u[i],tc_v[i],tc_cellu[i],tc_cellv[i])
            # print(tc_u[i],tc_v[i],STC_idx[i],sec)
            # print("\n")
            if(sec == sector):
                key = (layer[i], new_tc_u, new_tc_v, STC_idx) #Creating a key (layer,(u,v,STC,idx))
                energy = ts_en[i]

                if key not in dict:
                    dict[key] = []
                else: #This is complete nonsense until we have a correct function to assign (u,v,STC_idx). Don'T forget to remove it later!!!!
                    STC_idx = STC_idx + 1 # CHANGE IT LATER
                    key = (layer[i], new_tc_u, new_tc_v, STC_idx) # CHANGE IT LATER
                    dict[key] = [] # CHANGE IT LATER

                dict[key].append(energy)
    return dict


def extract_data_CEH(line): #function for finding keys from incoming txt files
    match = re.match(r'Board_(\d+),Channel_(\d+),Word_(\d+)=Layer_(\d+),\((\d+),(\d+),(\d+)\)silicon', line.strip())
    if match:
        key = str((int(match[4]), (int(match[5]), int(match[6]), int(match[7])))) #Layer , (u,v,STC_idx)
        board = int(match[1])
        word = int(match[3]) # CE-H sends 6 words per channel
        return key, board, word

    match = re.match(r'Board_(\d+),Channel_(\d+),Word_(\d+)=Layer_(\d+),\((\d+),(\d+),(\d+)\)scintillator', line.strip())
    if match:
        key = str((int(match[4]), (int(match[5]), int(match[6]), int(match[7])))) #Layer , (u,v,STC_idx)
        board = int(match[1])
        word = int(match[3]) # CE-H sends 6 words per channel
        return key, board, word

    return np.nan, np.nan, np.nan #empty lines

def produce_mapping_CEH(file_path, Stage1_board_Number):
    """
    Create a dictionary that connects mapping of S1 board number, Channel id,
    Word number, Layer number and (u,v,STC_idx) from a text file.
    """
    mapping = {}

    pattern_1 = re.compile(r'Board_(\d+), Channel_(\d+), Word_(\d+) =  Layer_(\d+), \((\d+),(\d+),(\d+)\) silicon')
    pattern_2 = re.compile(r'Board_(\d+), Channel_(\d+), Word_(\d+) =  Layer_(\d+), \((\d+),(\d+),(\d+)\) scintillator')

    with open(file_path, 'r') as file:
        for line in file:
            #Silicon part
            match = pattern_1.match(line.strip())
            if match:
                board = int(match.group(1))
                if(board != Stage1_board_Number):
                    continue
                channel = int(match.group(2))
                word = int(match.group(3))
                layer = int(match.group(4))
                u = int(match.group(5))
                v = int(match.group(6))
                STC_idx = int(match.group(7))

                key = (layer, u, v, STC_idx, board,channel, word)
                if key not in mapping:
                    mapping[key] = []
                mapping[key].append('0') #fill the mapping with 0 for energies that have to be extracted from the simulation
            #Scintillator part
            match = pattern_2.match(line.strip())
            if match:
                board = int(match.group(1))
                if(board != Stage1_board_Number):
                    continue
                channel = int(match.group(2))
                word = int(match.group(3))
                layer = int(match.group(4))
                u = int(match.group(5))
                v = int(match.group(6))
                STC_idx = int(match.group(7))

                key = (layer, u, v, STC_idx, board,channel, word)
                if key not in mapping:
                    mapping[key] = []
                mapping[key].append('0') #fill the mapping with 0 for energies that have to be extracted from the simulation
    return mapping

def merge_dictionaries(input, mapping):
        # Iterate through the first dictionary containing energy values of pTTs mapped by eta_phi coordinates
    for key1, value1 in input.items():
        # Check for matching entries from the mapping
        for key2, value2 in mapping.items():
            if (key1[0] == key2[0] and #match layers
                key1[1] == key2[1] and #match u
                key1[2] == key2[2] and #match v
                key1[3] == key2[3]): #match STC_ifx

                # Insert energies into mapping
                mapping[key2] = value1
                #print(key2,value1)

def make_board_files_CEH(input_file, mapping, directory_path, sector=0, N_s1_boards=14):

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    for S1_board in range(N_s1_boards):
        current_mapping = produce_mapping_CEH(input_file, S1_board) # Store mapping of different STCs to S1_board channels and words in a dictionary
        merge_dictionaries(mapping,current_mapping) # Use a dictionary from simulation to extract energy values of STCs

        file_name = f"Sector_{sector}_Board_{S1_board}.txt"
        file_path = os.path.join(directory_path, file_name)
        #print(f"S1_board_{S1_board}")

        N_channels = max(key[5] for key in current_mapping.keys()) # Figure out how many channels there are for current S1 board of interest
        with open(file_path, "w") as file:
            for channel in range(N_channels):
                temp_channel = {key: value for key, value in current_mapping.items() if key[5] == channel} # Figure out how many words there are for a given channel
                N_words = max(key[6] for key in temp_channel.keys()) + 1
                for current_word in range(N_words):
                    for key,values in current_mapping.items():
                        if(key[5] == channel and key[6] == current_word):
                            energy = float(current_mapping[key][0])
                            energy_int = pkg.packInt_FromFloat(energy)
                            #if(energy > 0): print(f"Energy in GeV = {energy}   Packed in int = {energy_int} Packed in 5E4M = {pkg.pack5E4M_FromInt(energy_int)}  Unpacked int = {pkg.unpack5E4M_ToInt(pkg.pack5E4M_FromInt(energy_int))} Unpacked GeV = {pkg.unpackFloat_FromInt(pkg.unpack5E4M_ToInt(pkg.pack5E4M_FromInt(energy_int)))}")
                            compressed_energy = pkg.pack5E4M_FromInt(energy_int)
                            file.write(f"{compressed_energy:09b} ") # Write down channel N in N'th row and word M in M'th column
                for extra_word in range(N_words, 6):
                        file.write(f"{111111111} ") # If there are less than 6 words in a given channel fill the rest with 111111111
                file.write("\n")


event_index = pkg.get_index(branches["event"],event_id)[0]
u = np.asarray(branches["good_tc_waferu"][event_index]).flatten()
v = np.asarray(branches["good_tc_waferv"][event_index]).flatten()
cellu = np.asarray(branches["good_tc_cellu"][event_index]).flatten()
cellv = np.asarray(branches["good_tc_cellv"][event_index]).flatten()
energy = np.asarray(branches["good_tc_energy"][event_index]).flatten()
layer = np.asarray(branches["good_tc_layer"][event_index]).flatten()
index_endcap = pkg.get_endcap_index(branches["good_tc_z"][event_index], 1)

dict_energy_CEH_sector_0 = dict_CEH(layer,u,v,cellu,cellv,energy,index_endcap, sector = 0) # First we create a dictionary that stores energies from Simulation for each STC
dict_energy_CEH_sector_1 = dict_CEH(layer,u,v,cellu,cellv,energy,index_endcap, sector = 1)
dict_energy_CEH_sector_2 = dict_CEH(layer,u,v,cellu,cellv,energy,index_endcap, sector = 2)

make_board_files_CEH("inputs/mapping/v2/Input_CEH_v2.txt",dict_energy_CEH_sector_0,"output/Stage1_Unpacker/CEH", sector = 0)
make_board_files_CEH("inputs/mapping/v2/Input_CEH_v2.txt",dict_energy_CEH_sector_1,"output/Stage1_Unpacker/CEH", sector = 1)
make_board_files_CEH("inputs/mapping/v2/Input_CEH_v2.txt",dict_energy_CEH_sector_2,"output/Stage1_Unpacker/CEH", sector = 2)
