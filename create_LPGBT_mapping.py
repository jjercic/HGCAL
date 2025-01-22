import yaml
import os

# Function to calculate end_value based on version
def calculate_range(start_value, nElinks):
    return start_value + nElinks - 1

# Initialize the dictionary
data = {'lpgbt_pair': {}}

# Version settings for each econt (user-defined)
# 0 = BC, 1 = STC4, 2 = STC16
econt_algorithm = [0, 0, 1, 2, 2]
# Example: [4, 2, 4, 2, 2] means econt 0 and 2 have 4 elinks in lpgbt, econt 1,3,4 have 2 elinks.
econt_nElinks = [4,2,4,2,2]

# Populate the dictionary with the specified ranges
for lpgbt_pair in range(59):  # lpgbt_pair goes from 0 to 58 because we are connecting 59x2=118 lpgbts with this particular Stage_1 board (120 is max)
    econt_mapping = {}
    start_value = 0
    for econt in range(5):  # econt goes from 0 to 4
        end_value = calculate_range(start_value, econt_nElinks[econt])
        if end_value > 13:
            raise ValueError(f"Range exceeded 13 for lpgbt_pair {lpgbt_pair}, econt {econt}") #There is a maximum of 14 elinks in each lpgbt
        econt_mapping[econt] = [
            {'elink_start': start_value},
            {'elink_end': end_value},
            {'algo': econt_algorithm[econt]}
        ]
        start_value = end_value + 1  # Ensure the next start_value continues from the previous end_value + 1
    data['lpgbt_pair'][lpgbt_pair] = econt_mapping

# Write the data to a YAML file
file_name = 'Stage1_dummyLPGBTmapping.yaml'
directory_path = 'inputs/mapping/lpgbt_mapping/'

if not os.path.exists(directory_path):
    os.makedirs(directory_path)
file_path = os.path.join(directory_path, file_name)

with open(file_path, 'w') as file:
    yaml.dump(data, file, default_flow_style=False)

print(f"YAML file {file_path} created successfully!")
