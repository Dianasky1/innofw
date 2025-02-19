import logging
import os.path
import pathlib

#
import pandas as pd
from torch.utils.data import random_split
from torchvision.datasets import ImageFolder
import albumentations as albu
import albumentations.pytorch as albu_pytorch

#
from innofw.constants import Frameworks, Stages
from innofw.core.augmentations import Augmentation
from innofw.core.datamodules.lightning_datamodules.base import (
    BaseLightningDataModule,
)


class ImageLightningDataModule(BaseLightningDataModule):
    task = ["image-classification"]
    framework = [Frameworks.torch]

    def __init__(
        # todo: add types to train and test parameters
        # todo: add type to the aug parameter
        self,
        train,
        test,
        batch_size: int = 16,
        val_size: float = 0.2,
        num_workers: int = 1,
        augmentations=None,
        infer=None,
        stage=None,
        *args,
        **kwargs,
    ):
        super().__init__(train, test, infer, batch_size, num_workers, stage=stage)
        self.aug = augmentations
        self.val_size = val_size

    def setup_train_test_val(self, **kwargs):
        if self.aug:
            train_dataset = ImageFolder(
                str(self.train_dataset), transform=Augmentation(self.aug)
            )
            self.test_dataset = ImageFolder(
                str(self.test_dataset), transform=Augmentation(self.aug)
            )
        else:
            train_dataset = ImageFolder(
                str(self.train_dataset),
                transform=Augmentation(
                    albu.Compose([albu_pytorch.transforms.ToTensorV2()])
                ),
            )
            self.test_dataset = ImageFolder(
                str(self.test_dataset),
                transform=Augmentation(
                    albu.Compose([albu_pytorch.transforms.ToTensorV2()])
                ),
            )
        # divide into train, val, test
        n = len(train_dataset)
        train_size = int(n * (1 - self.val_size))
        self.train_dataset, self.val_dataset = random_split(
            train_dataset, [train_size, n - train_size]
        )

    def save_preds(self, preds, stage: Stages, dst_path: pathlib.Path):
        out = []
        for sublist in preds:
            out.extend(sublist.tolist())
        images = self.predict_dataset.image_names
        df = pd.DataFrame(list(zip(images, out)), columns=["Image name", "Class"])
        dst_filepath = os.path.join(dst_path, "classification.csv")
        df.to_csv(dst_filepath)
        logging.info(f"Saved results to: {dst_filepath}")
