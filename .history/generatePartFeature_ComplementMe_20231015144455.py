import random
import numpy as np
import torch
import os

from models.pointnet2_cls_ssg import get_model
from customized_inference import preProcessPC, inferenceBatch
from fileIO import read_obj_vertices

BASE_DATA_PATH = "/Users/liujunyu/Data/Research/BVC/ITSS/"

def computePartFeatures(model, pcDataPath, instanceName, partNames):
    partPCs = []
    for partName in partNames:
        partPath = os.path.join(pcDataPath, instanceName, partName)
        partVertices = read_obj_vertices(partPath)
        partVertices = np.array(partVertices)
        partProcessed = preProcessPC(partVertices)
        partPCs.append(partProcessed)
    partPCs = np.array(partPCs)

    featureArray = inferenceBatch(model, partPCs)

    saveFolderName = "component_all_centered_features"
    for partIdx in range(len(featureArray)):
        savePath = os.path.join(BASE_DATA_PATH, "components", "Airplane", saveFolderName, instanceName, str(partIdx + 1) + ".npy")
        np.save(savePath, featureArray[])


def main():
    #%% Load PointNet model
    modelPath = 'log/classification/pointnet2_ssg_wo_normals/checkpoints/best_model.pth'
    print("Model loaded.")
    # Initialize the model and load the trained weights
    model = get_model(40, False)
    loaded_dict = torch.load(modelPath, map_location=torch.device('cpu'))
    model_state_dict = loaded_dict['model_state_dict']
    model.load_state_dict(model_state_dict)
    model.eval()

    #%% ComplementMe Dataset
    dataset = os.path.join(BASE_DATA_PATH, "dataset", "ComplementMe")
    datasetType = "components"
    category = "Airplane"
    dataType = "component_all_centered_point_clouds"
    pcDataPath = os.path.join(dataset, datasetType, category, dataType)

    instanceNames = [d for d in os.listdir(pcDataPath) if os.path.isdir(os.path.join(pcDataPath, d))]
    for instanceName in instanceNames:
        instanceFolder = os.path.join(pcDataPath, instanceName)
        partNames = [f for f in os.listdir(instanceFolder) if os.path.isfile(os.path.join(instanceFolder, f))]