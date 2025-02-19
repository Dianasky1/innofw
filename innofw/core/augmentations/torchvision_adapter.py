#
import numpy as np
import torchvision
import torch.nn as nn

#
from innofw.core.augmentations import register_augmentations_adapter
from innofw.core.augmentations.base import BaseAugmentationAdapter


@register_augmentations_adapter(name="torchvision_adapter")
class TorchvisionAdapter(BaseAugmentationAdapter):
    def __init__(self, transforms, *args, **kwargs):
        super().__init__(transforms)

    @staticmethod
    def is_suitable_input(transforms) -> bool:
        return isinstance(transforms, torchvision.transforms.Compose) or isinstance(
            transforms, nn.Module
        )

    def forward(self, x):
        return self.transforms(np.array(x))

    def __repr__(self):
        return f"Torchvision: {self.transforms}"  # todo: serialize
