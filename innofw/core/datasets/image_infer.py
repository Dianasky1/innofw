import os

import cv2
import numpy as np
from torch.utils.data import Dataset


class ImageFolderInferDataset(Dataset):
    def __init__(self, image_dir, transforms=None, gray=False):
        super().__init__()
        self.image_dir = image_dir
        self.transforms = transforms
        self.image_names = os.listdir(image_dir)
        self.gray = gray

    def __getitem__(self, index: int):
        image_name = self.image_names[index]
        image = cv2.imread(os.path.join(self.image_dir, image_name), cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        if self.gray:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        if self.transforms:
            image = self.transforms(image)

        return image

    def __len__(self) -> int:
        return len(self.image_names)
