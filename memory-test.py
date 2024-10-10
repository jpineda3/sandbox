import yaml
from nebula import network
import os
import glob

import pytest


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


configFile = '/home/analog/nebula/sdg-nuc-04.yaml'

# Open and read the YAML file
with open(configFile, 'r') as file:
    data = yaml.safe_load(file)

# Run fee command on every board
boards = (list(data.keys()))

#########################################
@pytest.mark.parametrize("board", boards)
def test_free_memory(board):
    clean_up()

    n = network(yamlfilename=configFile, board_name=board)
    n.run_ssh_command(command="dmesg | grep sysid ; free")
    
    log = read_log(board)

    mem = {}
    swap = {}
    keys = ['total', 'used', 'free', 'shared', 'buff/cache', 'available']
    memory_type = ['Mem:', 'Swap:']

    for line in log:
        for memory in memory_type:
            tmp_dict = memory.lower()[:-1]
            if memory in line:
                values = line.split()[1:]
                for index, value in enumerate(values):
                    eval(tmp_dict)[keys[index]] = int(value)

    
    assert mem['free'] > 10000
    assert swap['free'] > 10000

    clean_up(board)

