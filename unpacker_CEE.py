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

"""
# Za spremanje događaja u datoteku; analogno i za eventsPhotonic.txt
with open('eventsPhotonic.txt', 'w') as f:
    for event in branches["event"]:
        f.write(f"{event}\n")
"""

def dict_CEE(layer, ts_u, ts_v, ts_en, endcap, sector=0): # Function that creates a dictionary with keys (layer,(u,v)) and energy values
    dict = {}
    for i in range(len(layer)):
        if i in endcap: # given side of the endcap
            # We need to convert (u,v) labels from CMSSW to (u,v) labels from Pedro's mapping that was used to define our mapping from MS/STC to Stage-1
            #if(layer[i]== 5):  print(f"Before function: u={ts_u[i]} v={ts_v[i]} layer={layer[i]} energy = {ts_en[i]}")
            new_ts_u,new_ts_v,sec = pkg.getuvsector(layer[i],ts_u[i],ts_v[i])
            #if(layer[i]== 5):  print(f"After function: u={ts_u[i]} v={ts_v[i]} sector={sec} energy = {ts_en[i]}")
            if(sec == sector):
                key = str((layer[i], (new_ts_u, new_ts_v)))
                dict[key] = str(ts_en[i])
    return dict

def extract_data_CEE(line): #function for finding keys from incoming txt files
    match = re.match(r'Board_(-?\d+),Channel_(-?\d+)=Layer_(-?\d+),\s*\((-?\d+),(-?\d+)\)\s*silicon', line)
    if match:
        key = str((int(match[3]), (int(match[4]), int(match[5])))) #Layer , (u,v)
        return key, int(match[1]) # Return key(layer,(u,v)) and board index
    return np.nan, np.nan #empty lines


def make_board_files_CEE(file, dict, directory, sector=0):
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(file, "r") as file:
        energies = np.array([])
        packed_energies = np.array([],dtype=np.int8) #For CE-E energies of Module Sums are in 5E3M format which is 8 bits
        write_file = 0 #number of the board that is currently written
        for line in file:
            line = line.replace(" ","").replace("\t", "")
            key,board = extract_data_CEE(line) #Get the key(layer,(u,v)) and board index from the mapping
            if key == key:
                if board == write_file:
                    try: #Check if dictionary has a key that we found in the mapping. If it does, store the energy value in 5E3M format
                        energies = np.append(energies,dict[key])
                        packed_energies = np.append(packed_energies,pkg.pack5E3M_FromInt(pkg.packInt_FromFloat(float(dict[key]))))
                    except KeyError: #If the key doesn't exist, simply store 0 energy.
                        energies = np.append(energies,0) #this key is missing in the dictionary
                        packed_energies = np.append(packed_energies,pkg.pack5E3M_FromInt(pkg.packInt_FromFloat(0.)))
                        continue
                else:
                    with open(f"{directory}/Sector_{sector}_Board_{write_file}.txt", "w") as file:
                        for energy in packed_energies:
                            # Convert each number to a 8-bit representation and write it in a file
                            file.write(f"{energy:08b}\n")
                    write_file = board # Check if it is time to move to the next board
                    energies = np.array([])
                    packed_energies = np.array([],dtype=np.int8)
                    try:
                        energies = np.append(energies,dict[key])
                        packed_energies = np.append(packed_energies,pkg.pack5E3M_FromInt(pkg.packInt_FromFloat(float(dict[key]))))
                    except KeyError:
                        energies = np.append(energies,0) #this key is missing in the dictionary
                        packed_energies = np.append(packed_energies,pkg.pack5E3M_FromInt(pkg.packInt_FromFloat(0.)))
                        continue

        with open(f"{directory}/Sector_{sector}_Board_{write_file}.txt", "w") as file: #Write everything for the last board
            for energy in packed_energies:
                # Convert each number to a 8-bit representation and write it in a file
                file.write(f"{energy:08b}\n")


event_index = pkg.get_index(branches["event"],event_id)[0]
u = np.asarray(branches["good_ts_waferu"][event_index]).flatten()
v = np.asarray(branches["good_ts_waferv"][event_index]).flatten()
energy = np.asarray(branches["good_ts_energy"][event_index]).flatten()
layer = np.asarray(branches["good_ts_layer"][event_index]).flatten()
index_endcap = pkg.get_endcap_index(branches["good_ts_z"][event_index], 1)

dict_energy_CEE_sector_0 = dict_CEE(layer,u,v,energy,index_endcap,0)
dict_energy_CEE_sector_1 = dict_CEE(layer,u,v,energy,index_endcap,1)
dict_energy_CEE_sector_2 = dict_CEE(layer,u,v,energy,index_endcap,2)

make_board_files_CEE("inputs/mapping/v2/Input_CEE_v2.txt",dict_energy_CEE_sector_0,"output/Stage1_Unpacker/CEE",0)
make_board_files_CEE("inputs/mapping/v2/Input_CEE_v2.txt",dict_energy_CEE_sector_1,"output/Stage1_Unpacker/CEE",1)
make_board_files_CEE("inputs/mapping/v2/Input_CEE_v2.txt",dict_energy_CEE_sector_2,"output/Stage1_Unpacker/CEE",2)
