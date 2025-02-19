# other
import pytest
from omegaconf import DictConfig
import torch.nn as nn

# local
from innofw.constants import Frameworks
from innofw.utils.framework import (
    get_obj,
    get_model,
    get_datamodule,
)
from innofw import InnoModel
from tests.fixtures.config.augmentations import resize_augmentation
from tests.fixtures.config.datasets import (
    faces_datamodule_cfg_w_target,
)
from tests.fixtures.config.models import (
    resnet_cfg_w_target,
)
from tests.fixtures.config import (
    losses as fixt_losses,
    optimizers as fixt_optimizers,
    trainers as fixt_trainers,
    models as fixt_models,
)


# todo: write a test where config specifies model inside a model and both should be instantiated
# todo: test if tensor get processed
# todo: test output is in valid range when tensor is passed

# todo: test for a full cycle(train, test, val)
# todo: measure metrics


@pytest.mark.parametrize(
    ["target"],
    [
        ["segmentation_models_pytorch.DeepLabV3Plus"],
        [
            "innofw.core.models.torch.architectures.detection.faster_rcnn.FasterRcnnModel"
        ],
        ["innofw.core.models.torch.architectures.classification.resnet.Resnet18"],
    ],
)
def test_model_creation(target):
    cfg = DictConfig(
        {
            "models": {
                "_target_": target,
                "name": "test",
                "description": "something",
            }
        }
    )
    model = get_model(cfg.models, fixt_trainers.base_trainer_on_cpu_cfg)
    assert isinstance(model, nn.Module)


@pytest.mark.parametrize(
    ["name"],
    [["unet"], ["FasterRcnnModel"], ["resnet18"]],
)
def test_model_creation_name_given(name):

    cfg = DictConfig(
        {
            "models": {
                "_target_": None,
                "name": name,
                "description": "something",
            }
        }
    )
    model = get_model(cfg.models, fixt_trainers.base_trainer_on_cpu_cfg)
    assert isinstance(model, nn.Module)


def test_model_creation_with_arguments():
    cfg = DictConfig(
        {
            "models": {
                "name": "deeplabv3plus",
                "description": "something",
                "_target_": "segmentation_models_pytorch.DeepLabV3Plus",
                "encoder_name": "dpn98",
                "encoder_weights": None,
                "classes": 1,
                "activation": "sigmoid",
                "in_channels": 4,
            }
        }
    )
    model = get_model(cfg.models, fixt_trainers.base_trainer_on_cpu_cfg)
    assert isinstance(model, nn.Module)


def test_model_n_optimizer_creation():
    cfg = DictConfig(
        {
            "models": fixt_models.deeplabv3_plus_w_target,
            "optimizers": fixt_optimizers.adam_optim_w_target,
        }
    )
    task = "image-segmentation"
    framework = Frameworks.torch
    model = get_model(cfg.models, fixt_trainers.base_trainer_on_cpu_cfg)
    optim = get_obj(cfg, "optimizers", task, framework, params=model.parameters())


def test_torch_wrapper_creation():
    cfg = DictConfig(
        {
            "models": fixt_models.deeplabv3_plus_w_target,
            "optimizers": fixt_optimizers.adam_optim_w_target,
            "losses": fixt_losses.jaccard_loss_w_target,
        }
    )
    task = "image-segmentation"
    framework = Frameworks.torch
    model = get_model(cfg.models, fixt_trainers.base_trainer_on_cpu_cfg)
    losses = get_obj(cfg, "losses", task, framework)
    wrapped_model = InnoModel(model, task=task, losses=losses, log_dir="./logs/test/")

    assert wrapped_model is not None


@pytest.mark.parametrize(
    ["model_cfg", "dm_cfg", "task", "aug"],
    [
        # [yolov5_cfg_w_target, lep_datamodule_cfg_w_target, "image-detection", None],
        # [faster_rcnn_cfg_w_target, wheat_datamodule_cfg_w_target, "image-detection", None],
        [
            resnet_cfg_w_target,
            faces_datamodule_cfg_w_target,
            "image-classification",
            resize_augmentation,
        ]
        # [model_cfg_wo_target, datamodule_cfg_w_target],
        # [model_cfg_w_empty_target, datamodule_cfg_w_target],
        # [model_cfg_w_missing_target, datamodule_cfg_w_target],
    ],
)
def test_model_training(model_cfg, dm_cfg, task, aug):
    model = get_model(model_cfg, fixt_trainers.base_trainer_on_cpu_cfg)
    framework = Frameworks.torch
    augmentations = None if not aug else get_obj(aug, "augmentations", task, framework)
    datamodule = get_datamodule(dm_cfg, framework, augmentations=augmentations)

    wrapped_model = InnoModel(
        model,
        task=task,
        trainer_cfg=fixt_trainers.base_trainer_on_cpu_cfg,
        log_dir="./logs/test/logs",
    )
    wrapped_model.train(datamodule)
