def find_suitable_model(name):
    # todo: search among models module
    # search within the special config file

    config_file_contents = {  # todo: make a yaml file with mappings between names and classes
        "knn": "sklearn.neighbors.KNeighborsClassifier",
        "knn-regressor": "sklearn.neighbors.KNeighborsRegressor",
        "linear_regression": "sklearn.linear_model.LinearRegression",
        "xgboost_classifier": "xgboost.XGBClassifier",
        "xgboost_regressor": "xgboost.XGBRegressor",
        "unet": "segmentation_models_pytorch.Unet",
        "unet++": "segmentation_models_pytorch.UnetPlusPlus",
        "deeplabv3": "segmentation_models_pytorch.DeepLabV3",
        "deeplabv3+": "segmentation_models_pytorch.DeepLabV3Plus",
        "yolov5": "innofw.core.integrations.YOLOv5",
        "yolov3": None,
        "FasterRcnnModel": "innofw.core.models.torch.architectures.detection.faster_rcnn.FasterRcnnModel",
        "resnet18": "innofw.core.models.torch.architectures.classification.resnet.Resnet18",
        "kmeans": "sklearn.cluster.KMeans",
    }

    return config_file_contents[name]
