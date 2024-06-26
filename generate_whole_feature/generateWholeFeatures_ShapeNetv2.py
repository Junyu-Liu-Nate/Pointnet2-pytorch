import random
import numpy as np
import torch
import os
from tqdm import tqdm

from models.pointnet2_cls_ssg_original import get_model
from data_utils.ModelNetDataLoader import pc_normalize, farthest_point_sample
from train_test_custom.customized_inference import preProcessPC, inferenceBatch
from geometry import sampleFromMesh, fpsSample, is_inside_sphere, scale_to_unit_sphere
from fileIO import savePCAsObj, saveWholeFeature, read_obj_vertices, get_names_from_json, save_parameters

DATASET_PATH = "/Volumes/DataSSDLJY/Data/Research/dataset/"
PROJECT_PATH = "/Volumes/DataSSDLJY/Data/Research/project/BVC/ITSS/"

PARAMETERS = {
    "pc_folder": "ShapeNetCore_v2_PC",
    "category": "03001627",

    "name_select_filename": "shapenet_chairs_train.json",
    "output_name": "ShapeNetv2_Wholes_ellipsoid_200",
    
    "num_parts": 200,
    "min_radius": 0.08,
    "max_radius": 0.5,
    "is_save_pc": False
}

def is_inside_ellipsoid(point, center, radius_x, radius_y, radius_z):
    """
    Check if a point is inside the given ellipsoid.
    """
    x, y, z = point
    cx, cy, cz = center
    return ((x - cx)**2 / radius_x**2 + (y - cy)**2 / radius_y**2 + (z - cz)**2 / radius_z**2) <= 1

def computeWholeFeature(outputName, objectName, wholeIdx, model, wholeVertices, numParts, minPoints=1024):
    """
    Compute feature for 1 whole shape: composed of numParts part features (numParts, 1024)
    """
    partPCs = []

    min_radius = PARAMETERS["min_radius"]
    max_radius = PARAMETERS["max_radius"]

    centers = fpsSample(wholeVertices, numParts)

    for idx in range(numParts):
        # radius_x = radius_y = radius_z = random.uniform(min_radius, max_radius)
        radius_x = random.uniform(min_radius, max_radius)
        radius_y = random.uniform(min_radius, max_radius)
        radius_z = random.uniform(min_radius, max_radius)
        center = centers[idx]

        partVertices = []
        for i in range(len(wholeVertices)):
            if is_inside_ellipsoid(wholeVertices[i], center, radius_x, radius_y, radius_z):
                partVertices.append(wholeVertices[i])
        
        while len(partVertices) < minPoints:
            radius_x += 0.1
            radius_y += 0.1
            radius_z += 0.1
            partVertices = []
            for i in range(len(wholeVertices)):
                if is_inside_ellipsoid(wholeVertices[i], center, radius_x, radius_y, radius_z):
                    partVertices.append(wholeVertices[i])

        partVertices = np.array(partVertices)
        partProcessed = preProcessPC(1024, partVertices)
        partPCs.append(partProcessed)

        if PARAMETERS["is_save_pc"]:
            visualizeBaseFolder = os.path.join(PROJECT_PATH, "generated", "ShapeNet", outputName + "_PC", objectName)
            visualizeFolder = os.path.join(visualizeBaseFolder, str(wholeIdx))
            if not os.path.exists(visualizeFolder):
                os.makedirs(visualizeFolder)
            save_parameters(PARAMETERS, os.path.join(visualizeBaseFolder, "parameters.txt"))
            visualizePath = os.path.join(visualizeFolder, str(idx) + ".obj")
            savePCAsObj(partVertices, visualizePath) # This is non-normalized, which preserves the original PC positions

    partPCs = np.array(partPCs)

    featureArray = inferenceBatch(model, partPCs)

    return featureArray

# def computeWholeFeature(outputName, wholeIdx, model, wholeVertices, numParts, minPoints = 1024):
#     """
#         Compute feature for 1 whole shape: composed of numParts part features (numParts, 1024)
#     """
#     partPCs = []
    
#     min_radius = 0.05
#     max_radius = 0.25

#     centers = fpsSample(wholeVertices, numParts)

#     for idx in range(numParts):
#         radius = random.uniform(min_radius, max_radius)
#         center = centers[idx]

#         partVertices = []
#         for i in range(len(wholeVertices)):
#             if is_inside_sphere(wholeVertices[i], center, radius):
#                 partVertices.append(wholeVertices[i])
        
#         while len(partVertices) < minPoints:
#             radius += 0.1
#             partVertices = []
#             for i in range(len(wholeVertices)):
#                 if is_inside_sphere(wholeVertices[i], center, radius):
#                     partVertices.append(wholeVertices[i])

#         partVertices = np.array(partVertices)
#         partProcessed = preProcessPC(partVertices)
#         partPCs.append(partProcessed)

#         # visualizeBaseFolder = "/Users/liujunyu/Data/Research/BVC/ITSS/visualize/Pointnet_Whole_enlarged200/"
#         visualizeBaseFolder = os.path.join("/Users/liujunyu/Data/Research/BVC/ITSS/visualize/", outputName)
#         visualizeFolder = os.path.join(visualizeBaseFolder, str(wholeIdx))
#         if not os.path.exists(visualizeFolder):
#             os.makedirs(visualizeFolder)
#         visualizePath = os.path.join(visualizeFolder, str(idx) + ".obj")
#         savePCAsObj(partProcessed, visualizePath)

#     partPCs = np.array(partPCs)
#     # print(partPCs)

#     featureArray = inferenceBatch(model, partPCs)

#     return featureArray


def main():
    #%%
    # dataPath = '/Users/liujunyu/Data/Research/BVC/ITSS/dataset/ModelNet40/airplane/train/'
    # meshName = 'airplane_0001'
    # meshPath = os.path.join(dataPath, meshName + ".off")

    #%% Load model
    modelPath = 'log/classification/pointnet2_ssg_wo_normals/checkpoints/best_model.pth'
    print("Model loaded.")
    # Initialize the model and load the trained weights
    model = get_model(40, False)
    loaded_dict = torch.load(modelPath, map_location=torch.device('cpu'))
    model_state_dict = loaded_dict['model_state_dict']
    model.load_state_dict(model_state_dict)
    model.eval()

    #%% Note: read directly from pre-generated pc
    ### For ModelNet 40
    # pcDatasetPath = "/Users/liujunyu/Data/Research/BVC/ITSS/dataset/ModelNet40_PC/airplane/train/"
    # pcPaths = []
    # for pcName in range(1, 601):
    #     pcPath = os.path.join(pcDatasetPath, 'airplane_' + f"{pcName:04d}" + '.obj')
    #     pcPaths.append(pcPath)

    ### For ShapeNet
    pcDatasetPath = os.path.join(PROJECT_PATH, "generated", "ShapeNet", PARAMETERS["pc_folder"], PARAMETERS["category"])
    # pcNames = [f for f in os.listdir(pcDatasetPath) if os.path.isfile(os.path.join(pcDatasetPath, f))]
    spaghettiNamePath = os.path.join(PROJECT_PATH, "generated", "Spaghetti", PARAMETERS["name_select_filename"])
    pcNamesPure = get_names_from_json(spaghettiNamePath, PARAMETERS["category"])
    pcNames = []
    for pcNamePure in pcNamesPure:
        pcNames.append(pcNamePure + ".obj")
    print(len(pcNames))
    
    pcPaths = []
    for pcName in pcNames:
        pcPath = os.path.join(pcDatasetPath, pcName)
        pcPaths.append(pcPath)

    outputFolder = os.path.join(PROJECT_PATH, "generated", "ShapeNet")
    outputName = PARAMETERS["output_name"]
    objectName = "03001627"
    outputPath = os.path.join(outputFolder, outputName, objectName)
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    save_parameters(PARAMETERS, os.path.join(outputPath, "parameters.txt"))

    print(len(pcPaths))
    # for i in range(len(meshPaths)):
    for i in range(len(pcPaths)):
        savePath = os.path.join(outputPath, pcNames[i][:-4])
        if os.path.exists(savePath):
            continue
        
        wholeVertices = read_obj_vertices(pcPaths[i])

        numParts = PARAMETERS["num_parts"]
        wholeFeature = computeWholeFeature(outputName, objectName, pcNames[i][:-4], model, wholeVertices, numParts, 1024)

        # savePath = os.path.join(outputPath, pcNames[i][:-4])
        saveWholeFeature(wholeFeature, savePath)

        print(f"[{i}/{len(pcPaths)}] Finish generating whole feature for idx: {pcNames[i][:-4]}.")


if __name__ == '__main__':
    main()