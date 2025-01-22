import numpy as np
import packingHelper as pkg
import re
import os

def read_TowerSumsInput(directory_path):
    # Initialize a dictionary to store the numbers
    tower_sums = {}
    for s1_sector in range(3):
        for s1_board in range(14):
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

                        energy = line

                        key = (s1_board, region, phi, eta, s1_sector)

                        if key not in tower_sums:
                            tower_sums[key] = []
                        tower_sums[key].append(energy)

            with open(file_path_CEH, 'r') as file:
                region = 'CE-H'
                for phi in range(24):
                    for eta in range(20):
                        # Read the next line
                        line = file.readline().strip()

                        if not line:
                            raise ValueError("File does not contain the expected 480 lines")

                        energy = line

                        key = (s1_board, region, phi, eta, s1_sector)

                        if key not in tower_sums:
                            tower_sums[key] = []
                        tower_sums[key].append(energy)

    return tower_sums



def create_S1_S2_mapping_forS2Board(directory_path):
    """
    Create a dictionary that connects mapping of Sector number, S2_board number, Frame id, Link number,
    Word number, S1_board number, eta, phi, and type from a text file.
    """
    mapping = {}

    pattern = re.compile(r"S1_Sector=(\d+), S2_board=(\d+), Frame id = \"(\d+)\", Link=(\d+), Word=(\d+), pTT : S1_Board=(\d+), eta=(-?\d+), phi=(\d+), (\w+-\w+)")

    for s2_sector in range(3):
        file = os.path.join(directory_path, f"S2_Sector{s2_sector}_S2_Board0.txt")
        with open(file, 'r') as file:
            for line in file:
                match = pattern.match(line.strip())
                if match:
                    s1_sector = int(match.group(1)) #S1_sector is not the same as S2_sector
                    s2_board = int(match.group(2))
                    frame_id = int(match.group(3))
                    s1_link = int(match.group(4)) #s1_link is the link index looked at from the S1 point of view and it is not the same as s2_link index of the same link
                    word = int(match.group(5))
                    s1_board = int(match.group(6))
                    eta = int(match.group(7))
                    phi = int(match.group(8))
                    type = match.group(9)
                    s2_link = pkg.s1_link_to_s2_link(s1_board,s1_link) #Each link has an index when viewed from S1_board and also when viewed from S2_board

                    key = (s1_sector, s2_board, frame_id, s1_link, word, s1_board, eta, phi, type, s2_link, s2_sector)
                    if key not in mapping:
                        mapping[key] = []
                    mapping[key].append('0') #fill the mapping with 0 for energies that have to be extracted from the unpacker
                else:
                    print(f"Can't read mapping file {file} \n Please check formatting.")

    return mapping

def create_S1_S2_mapping_forS1Board(directory_path):
    """
    Create a dictionary that connects mapping of Sector number, S2_board number, Frame id, Link number,
    Word number, S1_board number, eta, phi, and type from a text file.
    """
    mapping = {}

    pattern = re.compile(r"S2_Sector=(\d+), S2_board=(\d+), Frame id = \"(\d+)\", Link=(\d+), Word=(\d+), pTT : S1_Board=(\d+), eta=(-?\d+), phi=(\d+), (\w+-\w+)")

    for s1_sector in range(3):
        file = os.path.join(directory_path, f"S1_Sector{s1_sector}_S1_Board0.txt")
        with open(file, 'r') as file:
            for line in file:
                match = pattern.match(line.strip())

                if match:
                    s2_sector = int(match.group(1)) #S2_sector is not the same as S1_sector
                    s2_board = int(match.group(2))
                    frame_id = int(match.group(3))
                    s1_link = int(match.group(4)) #s1_link is the link index looked at from the S1 point of view and it is not the same as s2_link index of the same link
                    word = int(match.group(5))
                    s1_board = int(match.group(6))
                    eta = int(match.group(7))
                    phi = int(match.group(8))
                    type = match.group(9)
                    s2_link = pkg.s1_link_to_s2_link(s1_board,s1_link) #Each link has an index when viewed from S1_board and also when viewed from S2_board

                    key = (s1_sector, s2_board, frame_id, s1_link, word, s1_board, eta, phi, type, s2_link, s2_sector)

                    if key not in mapping:
                        mapping[key] = []
                    mapping[key].append('0') #fill the mapping with 0 for energies that have to be extracted from the unpacker
                else:
                    print(f"Can't read mapping file in {str(directory_path)} \n Please check formatting.")

    print(f"Done reading mapping file in {str(directory_path)}")
    return mapping

def merge_dictionaries(input, mapping):
        # Iterate through the first dictionary containing energy values of pTTs mapped by eta_phi coordinates
    for key1, value1 in input.items():
        # Check for matching entries from the mapping
        for key2, value2 in mapping.items():
            if (key1[0] == key2[5] and #match S1_boards
                key1[1] == key2[8] and #match regions CEE/CEH
                key1[3] == key2[6] and #match eta
                key1[2] == key2[7] and #match phi
                key1[4] == key2[0]     #match S1_sectors
                ):

                # Insert energies into mapping
                mapping[key2] = value1
    print("Dictionaries merged!")



def combine_words(word3bit, word8bit_0, word8bit_1, word15bit_0, word15bit_1, word15bit_2, ):
    # Combine the words by shifting and bitwise OR
    # print(word3bit, word8bit_1, word8bit_2, word15bit_1, word15bit_2, word15bit_3)
    word64bit = (word3bit << (15 + 15 + 15 + 8 + 8)) | \
                    (word8bit_1 << (15 + 15 + 15 + 8)) | \
                    (word8bit_0 << (15 + 15 + 15)) | \
                    (word15bit_2 << (15 + 15)) | \
                    (word15bit_1 << 15) | \
                    word15bit_0
    return word64bit

def create_S2input_emp_file(mapping, directory_path, s2_sector, N_s2_links, N_frames):
    # A function that takes data from all 3x14 stage 1 boards of endcap and sents them through 4(same sector)+2(duplicate) elinks to a single Stage_2 board
    # Open a text file for writing
    file_name = f"EMP_S2_sector_{s2_sector}_board_{0}.txt"
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    file_path = os.path.join(directory_path, file_name)

    #Writing the header of the EMP file
    with open(file_path, "w") as file:
        file.write(f"Link\t\t\t\t")
        for s2_link in range(N_s2_links):
            file.write(f"\t\t\t{s2_link:03d}\t\t\t\t")
        file.write("\n")

    with open(file_path, "a") as file:
        for frame in range(N_frames):
            file.write(f"Frame {frame:04d}\t")
            words = [0]*N_s2_links #Each board has N_s2_links incoming links from S1 boards from the same sector + from the neighbouring sector
            prefix_bit = [0]*N_s2_links #I was told that EMP files have a prefix bit.
            for s2_link in range(N_s2_links):
                match = False
                for key, value in mapping.items():
                    if(key[10]==s2_sector and key[2]==frame and key[9] == s2_link):
                        match = True #There was a match, meaning there is pTT data to be sent through that s2_link
                        # if(frame == 0):
                        #     print(f"frame={key[2]} s1_sector={key[0]} s1_board={key[1]} link={key[9]} eta={key[6]} phi={key[7]} word={key[4]} type={key[8]} pTT={format(int(mapping[key][0],16), '016x')}")

                        #A 64 bit word that is comprised of 3 bit header, 2x8 bit pTT information, and 3x15 bit of TC information
                        # Define the words that need to be combined
                        word_header = 0x7      # 3-bit header (binary 111)
                        # pTTs
                        if(key[4] == 0):
                            word_pTT_1 = int(mapping[key][0],16)    # 8-bit word for pTTs
                        if(key[4] == 1):
                            word_pTT_2 = int(mapping[key][0],16)    # 8-bit word for pTTs
                        # (S)TCs
                        word_TC_1 = 0x0000  # 15-bit word for TC (current placeholder)
                        word_TC_2 = 0x0000  # 15-bit word for TC (current placeholder)
                        word_TC_3 = 0x0000  # 15-bit word for TC (current placeholder)
                if(frame == 0):
                    prefix_bit[s2_link] = int('1101',2) # Prefix signaling start of data (first word)
                elif(frame == 107):
                    prefix_bit[s2_link] = int('0011',2) # Prefix signaling end of data (last word)
                else:
                    prefix_bit[s2_link] = int('0001',2) # Prefix signaling valid data

                if(match):
                    words[s2_link] = combine_words(word_header, word_pTT_1, word_pTT_2, word_TC_1, word_TC_2, word_TC_3)
                    # if(frame == 0): print(f"total word = {format(words[s2_link],'016x')}")
                else:
                    words[s2_link] = combine_words(0x7, int('0',16), int('0',16), 0x0000, 0x0000, 0x0000) # There are some links that currently carry no pTT data

            for word, prefix in zip(words,prefix_bit):
                file.write(f"{format(prefix,'04b')} {format(word, '016x')}\t")
            file.write("\n")

def create_S1output_emp_file(mapping, directory_path, s1_sector, N_s1_links, N_frames):
    # A function that takes data from defined stage 1 board and produces EMP output file of that board
    # Open a text file for writing
    file_name = f"EMP_S1_sector_{s1_sector}_board_{0}.txt"
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    file_path = os.path.join(directory_path, file_name)

    #Writing the header of the EMP file
    with open(file_path, "w") as file:
        file.write(f"Link\t\t\t\t")
        for s1_link in range(N_s1_links):
            file.write(f"\t{s1_link:03d}\t\t")
        file.write("\n")

    with open(file_path, "a") as file:
        for frame in range(N_frames):
            file.write(f"Frame {frame:04d}\t")
            words = [0]*N_s1_links #Each board has N_s1_links outgoing links to S2 boards from the same sector + from the neighbouring sector
            prefix_bit = [0]*N_s1_links #I was told that EMP files have a prefix bit.
            for s1_link in range(N_s1_links):
                match = False
                for key, value in mapping.items():
                    if(key[0]==s1_sector and key[2]==frame and key[3] == s1_link):
                        match = True #There was a match, meaning there is pTT data to be sent through that s2_link
                        # if(frame == 0):
                        #     print(f"frame={key[2]} s1_sector={key[0]} s1_board={key[1]} link={key[9]} eta={key[6]} phi={key[7]} word={key[4]} type={key[8]} pTT={format(int(mapping[key][0],16), '016x')}")

                        #A 64 bit word that is comprised of 3 bit header, 2x8 bit pTT information, and 3x15 bit of TC information
                        # Define the words that need to be combined
                        word_header = 0x7      # 3-bit header (binary 111)
                        # pTTs
                        if(key[4] == 0):
                            word_pTT_1 = int(mapping[key][0],16)    # 8-bit word for pTTs
                        if(key[4] == 1):
                            word_pTT_2 = int(mapping[key][0],16)    # 8-bit word for pTTs
                        # (S)TCs
                        word_TC_1 = 0x0000  # 15-bit word for TC (current placeholder)
                        word_TC_2 = 0x0000  # 15-bit word for TC (current placeholder)
                        word_TC_3 = 0x0000  # 15-bit word for TC (current placeholder)
                if(frame == 0):
                    prefix_bit[s1_link] = int('1101',2) # Prefix signaling start of data (first word)
                elif(frame == 107):
                    prefix_bit[s1_link] = int('0011',2) # Prefix signaling end of data (last word)
                else:
                    prefix_bit[s1_link] = int('0001',2) # Prefix signaling valid data

                if(match):
                    words[s1_link] = combine_words(word_header, word_pTT_1, word_pTT_2, word_TC_1, word_TC_2, word_TC_3)
                    # if(frame == 0): print(f"total word = {format(words[s2_link],'016x')}")
                else:
                    words[s1_link] = combine_words(0x7, int('0',16), int('0',16), 0x0000, 0x0000, 0x0000) # There are some links that currently carry no pTT data

            for word, prefix in zip(words,prefix_bit):
                file.write(f"{format(prefix,'04b')} {format(word, '016x')}\t")
                #file.write(f"{format(word, '016x')}\t")
            file.write("\n")
    print(f"Created EMP file {file_name}!")    

# Read the outputs of 14 Stage_1 boards. Each one outputs eta(20)xphi(24) = 480 pTTs for CEE + 480 pTTs for CEH in 8-bit format. Store it in a dictionary.
tower_sums = read_TowerSumsInput('output/Stage1_TowerSums/')

## Create EMP files that are input to Stage_2 boards 0 from all 3 sectors
# Read the mapping from Stage_1 to Stage_2 that defines how each pTT is mapped to a frame/link/word. Store it in a dictionary
# mapping_s2board = create_S1_S2_mapping_forS2Board('inputs/mapping/S1S2_Mapping/')
# merge_dictionaries(tower_sums,mapping_s2board)
#
# create_S2input_emp_file(mapping_s2board,"output/Stage1_Packer/", 0, 14*6, 108)
# create_S2input_emp_file(mapping_s2board,"output/Stage1_Packer/", 1, 14*6, 108)
# create_S2input_emp_file(mapping_s2board,"output/Stage1_Packer/", 2, 14*6, 108)

## Create EMP files that are ouptut to Stage_1 boards 0 from all 3 sectors
mapping_s1board = create_S1_S2_mapping_forS1Board('inputs/mapping/S1S2_Mapping/')
merge_dictionaries(tower_sums,mapping_s1board)
create_S1output_emp_file(mapping_s1board,"output/Stage1_Packer/", 0, 18*6, 108)
create_S1output_emp_file(mapping_s1board,"output/Stage1_Packer/", 1, 18*6, 108)
create_S1output_emp_file(mapping_s1board,"output/Stage1_Packer/", 2, 18*6, 108)
