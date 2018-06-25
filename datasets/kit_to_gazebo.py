#!/usr/bin/python3

# Command line args
import sys, getopt
# CSV
import csv
# OS
import os
# Subprocess
import subprocess
# Copyfile
from shutil import copyfile, rmtree
# For file edit
import fileinput
# Regex
import re
# Triangular meshes
import numpy as np
import trimesh

# Usage
USAGE = 'options: -i <input mesh directory>\n' +   \
        '         -o <output model directory>\n' + \
        '         -t <template directory>\n' +     \
        '         -s <meshlab script> \n'

# Output mesh format
MESH_EXT = 'stl'

def parseArgs(argv):
    '''
    Parses command-line options.
    '''

    # Parameters
    in_dir = 'COLLADA'
    out_dir = 'output'
    template = 'template'
    script = 'script.mlx'
    
    usage = 'usage:   ' + argv[0] + ' [options]\n' + USAGE

    try:
        opts, args = getopt.getopt(argv[1:],
            "hi:o:t:s:",["in_dir=","out_dir=","template=","script="])
    except getopt.GetoptError:
        print (usage)
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print (usage)
            sys.exit()
        elif opt in ("-i", "--in_dir"):
            in_dir = arg
        elif opt in ("-o", "--out_dir"):
            out_dir = arg
        elif opt in ("-t", "--template"):
            template = arg
        elif opt in ("-s", "--script"):
            script = arg

    print ('Input mesh directory   ', in_dir)
    print ('Output model directory ', out_dir)
    print ('Template path          ', template)
    print ('Meshlab script         ', script)
    
    return [in_dir, out_dir, template, script]

def search_and_replace(filename, search, replace):
    with fileinput.FileInput(filename, inplace=True) as file:
        for line in file:
            print(line.replace(search, replace), end='')

def main(argv):

    # Obtain command-line arguments
    [in_dir, out_dir, template, script] = parseArgs(argv)

    meshes = [f for f in os.listdir(in_dir) \
        if os.path.isfile(os.path.join(in_dir, f))]

    print('\nGenerating Gazebo models:\n')

    meshes_num = len(meshes)
    for idx, mesh in enumerate(meshes):

    	# Preprocessing - dataset specific

        # Erase suffix and extension
        name = mesh.replace('_800_tex', '')
        name = name.replace('.obj', '')
        print("\x1b[2K{:10.4f}".format(idx * 100.0 / meshes_num) + ' % - ' + name, end="\r")
        
        out_name = out_dir + '/' + name + '/meshes/'
        os.makedirs(os.path.dirname(out_name), exist_ok=1)
        template_model = template + '/model.sdf'
        template_cfg = template + '/model.config'
        out_model = out_dir + '/' + name + '/model.sdf'
        out_cfg = out_dir + '/' + name + '/model.config'
        in_mesh = in_dir + '/' + mesh
        out_mesh = out_dir + '/' + name + '/meshes/' + name + '.' + MESH_EXT

        # Model mesh

        # Open null stream to surpress shell command output
        FNULL = open(os.devnull, 'w')

        try:
            subprocess.call(['meshlabserver -i ' + in_mesh
                + ' -o ' + out_mesh + ' -s ' + script], shell=1, \
                stdout=FNULL, stderr=subprocess.STDOUT)
        except:
            # Some models do not have poisson filtered meshes; discard them
            print(in_mesh + ' not found. Removing model.')
            rmtree(out_dir + '/' + name)

        # Model description files
        copyfile(template_model, out_model)
        copyfile(template_cfg, out_cfg)

        # Open mesh and compute inertia tensor estimation
        mesh = trimesh.load(out_mesh)
        properties = trimesh.triangles.mass_properties(mesh.triangles)
        inertia = properties['inertia']
        # TODO - Write inertia tensor to output

        search_and_replace(out_model, 'TEMPLATE', name)
        search_and_replace(out_model, 'MESH_EXT', 'stl')
        search_and_replace(out_model, 'SCALE', '1 1 1')
        search_and_replace(out_cfg, 'TEMPLATE', name)
        search_and_replace(out_cfg, 'DESCRIPTION', name)

    print("\r\n\nDone!")

if __name__ == "__main__":
    main(sys.argv)