import numpy as np
import os
import chardet
import json
import random

def load_mesh(mesh_path):
    """
        Input: Mesh file .off format
        Output: Dictionary for part {"vertices": [], "normals": []}
    """
    vertices = []
    faces = []

    with open(mesh_path, 'r') as file:
        # Read the header line
        header = file.readline().strip()
        if header != 'OFF':
            raise ValueError("Invalid OFF file format")

        # Read number of vertices, faces, and edges
        num_vertices, num_faces, _ = map(int, file.readline().split())
        # print(num_vertices, num_faces)

        # Read vertex coordinates
        for _ in range(num_vertices):
            vertex = list(map(float, file.readline().split()))
            vertices.append(np.array(vertex))

        # Read faces
        for _ in range(num_faces):
            face = list(map(int, file.readline().split()))
            num_vertices_per_face = face[0]
            if num_vertices_per_face != 3:
                raise ValueError("Only triangular faces are supported")
            faces.append(np.array(face[1:]))  # Store vertex indices

    return {
        'vertices': vertices,
        'faces': faces
    }

def savePCAsObj(vertices, file_path):
    with open(file_path, 'w') as f:
        for vertex in vertices:
            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")

def saveWholeFeature(feature, file_path):
    np.save(file_path, feature)

def read_obj_vertices(obj_path):
    vertices = []

    # with open(obj_path, 'rb') as f:
    #     result = chardet.detect(f.read())
    # encoding = result['encoding']
    
    with open(obj_path, 'r') as file:
        for line in file:
            # Check for a vertex line
            if line.startswith('v '):
                # Split the line, convert to float, and ignore the first element ('v')
                vertex = list(map(float, line.split()[1:]))
                vertices.append(vertex)

    return np.array(vertices)

# def read_obj_vertices(obj_path, sampling_rate=0.5):
#     vertices = []

#     with open(obj_path, 'r') as file:
#         for line in file:
#             # Check for a vertex line
#             if line.startswith('v '):
#                 # Split the line, convert to float, and ignore the first element ('v')
#                 vertex = list(map(float, line.split()[1:]))
#                 vertices.append(vertex)

#     # Convert to numpy array
#     vertices = np.array(vertices)

#     # Randomly sample points
#     num_points = len(vertices)
#     num_sample = int(num_points * sampling_rate)
#     indices = random.sample(range(num_points), num_sample)
#     sampled_vertices = vertices[indices]

#     return sampled_vertices

#%% For PointNet features on whole shape (no parts)
def read_features_from_txt(filename, selectedWholeNames):
    mesh_features = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            mesh_path = parts[0]
            feature = np.array([float(x) for x in parts[1:]])
            if mesh_path in selectedWholeNames:
                mesh_features.append((mesh_path, feature))
    return [feature for _, feature in mesh_features]

def read_features_from_txt_shapenet(filename, selectedWholeNames):
    mesh_features = {}
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            mesh_path = parts[0]
            feature = np.array([float(x) for x in parts[1:]])
            if mesh_path in selectedWholeNames:
               mesh_features[mesh_path] = feature
    return mesh_features

### For ComplementMe
def readSelectedMD5s_component(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    return [line.strip() for line in lines]

def readSelectedMD5s_part(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        md5s = [line.split(',')[0].strip() for line in lines[1:]]  # skip the header
        return list(set(md5s))  # remove duplicates
    
#%%
def get_names_from_json(file_path, category):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data.get('ShapeNetV2', {}).get(category, [])

#%% For generating pairs dataset
### txt
def write_pair_to_txt(file_path, pair):
    with open(file_path, 'a') as f:
        label = '1' if pair['label'] else '0'
        part = ','.join(map(str, pair['part']))
        whole = pair['whole']
        f.write(f"{label} {part} {whole}\n")

def create_initial_txt(file_path):
    # Simply creating or clearing an existing file
    with open(file_path, 'w') as f:
        pass
    print(f"Created dataset at {file_path}")

def add_pair_to_existing_txt(file_path, pair):
    write_pair_to_txt(file_path, pair)

#%% Save parameters
def save_parameters(params, save_path, format='txt'):
    if format == 'json':
        with open(save_path, 'w') as json_file:
            json.dump(params, json_file, indent=4)
    elif format == 'txt':
        with open(save_path, 'w') as txt_file:
            for key, value in params.items():
                txt_file.write(f'{key}: {value}\n')
    else:
        raise ValueError("Format not supported. Please choose 'txt' or 'json'.")
