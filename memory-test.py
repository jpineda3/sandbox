import yaml
from nebula import network
import os
import glob
import re

import pytest

def concatenate_yaml_files(output_config, *input_config):
    combined_data = {}
    # Load and combine the YAML files
    for file in input_config:
        with open(file, 'r') as f:
            try:
                contents = yaml.safe_load(f)  # Load YAML file
                if contents is not None:
                    combined_data.update(contents)  # Append data
            except yaml.YAMLError as e:
                print(f"Error reading {file}: {e}")

    # Write the combined data to the output YAML file
    with open(output_config, 'w') as out_file:
        yaml.dump(combined_data, out_file, default_flow_style=False)

def read_log(board_name):
    pattern = os.getcwd() + '/'+ board_name +'_*.log'
    lines = list()
    for file_path in glob.glob(pattern):
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()
        except Exception as e:
            print(f"Error occurred: {e}")
    return lines

def clean_up(board_name=None):
    # Delete existing or created .log files
    if board_name is None:
        pattern = os.getcwd() + '/_*.log'
    else:
        pattern = os.getcwd() + '/'+ board_name +'_*.log'
    for file_path in glob.glob(pattern):
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except PermissionError:
            print(f"Permission denied: {file_path}")
        except Exception as e:
            print(f"Error occurred: {e}")

# Read all nebula-config yaml files from ~/config
pattern = os.getcwd() + '/config/*.yaml'
input_config_filenames = list()
for file_path in glob.glob(pattern):
    input_config_filenames.append(file_path)
concatenate_yaml_files('config/combined_config.yaml', *input_config_filenames)

# Open and read the YAML file
configFile = os.getcwd() + '/config/combined_config.yaml'
with open(configFile, 'r') as file:
    data = yaml.safe_load(file)
# Get all board names
boards = (list(data.keys()))

#########################################
@pytest.mark.parametrize("board", boards)
def test_free_memory(board):
    clean_up()

    n = network(yamlfilename=configFile, board_name=board)
    n.run_ssh_command(command="dmesg | grep -iE 'sysid|mem' ; free")
    
    log = read_log(board)

    sha = ''
    mem = {}
    swap = {}
    keys = ['total', 'used', 'free', 'shared', 'buff/cache', 'available']
    memory_type = ['Mem:', 'Swap:']

    for line in log:
        if 'git' in line:
            matches = re.findall(r'<(.*?)>', line)
            sha =  ' '.join(matches)
        for memory in memory_type:
            tmp_dict = memory.lower()[:-1]
            if memory in line:
                values = line.split()[1:]
                for index, value in enumerate(values):
                    eval(tmp_dict)[keys[index]] = int(value)

    assert mem['free'] > 0.05 * mem['total']
    if board != 'pluto':
        assert swap['free'] > 0.05 * swap['total']

    clean_up(board)

