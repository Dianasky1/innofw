import os
import pathlib
import shutil

import cv2
import torch
import albumentations as albu
import albumentations.pytorch as albu_pytorch

from innofw.constants import Frameworks, Stages

from innofw.core.datamodules.lightning_datamodules.base import (
    BaseLightningDataModule,
)
from innofw.core.datasets.image_infer import ImageFolderInferDataset
from innofw.core.datasets.segmentation import SegmentationDataset
from innofw.core.augmentations import Augmentation
from innofw.utils.data_utils.preprocessing.dicom_handler import (
    dicom_to_img,
    img_to_dicom,
)


class DirSegmentationLightningDataModule(BaseLightningDataModule):
    task = ["image-segmentation"]
    framework = [Frameworks.torch]

    def __init__(
        self,
        train,
        test,
        infer=None,
        augmentations=None,
        channels_num: int = 3,
        val_size: float = 0.2,
        batch_size: int = 32,
        num_workers: int = 1,
        random_seed: int = 42,
        stage=None,
        *args,
        **kwargs,
    ):
        super().__init__(
            train=train,
            test=test,
            batch_size=batch_size,
            num_workers=num_workers,
            infer=infer,
            stage=stage,
            *args,
            **kwargs,
        )

        # TODO: should object instantiation be here?
        self.aug = Augmentation(
            augmentations=augmentations
            or albu.Compose([albu_pytorch.transforms.ToTensorV2()])
        )
        self.channels_num = channels_num
        self.val_size = val_size
        self.random_seed = random_seed

    def setup_train_test_val(self, **kwargs):
        train_val = SegmentationDataset(
            os.path.join(self.train_dataset, "image"),
            os.path.join(self.train_dataset, "label"),
            self.aug,
        )
        val_size = int(len(train_val) * float(self.val_size))
        self.train_dataset, self.val_dataset = torch.utils.data.random_split(
            train_val, [len(train_val) - val_size, val_size]
        )
        self.test_dataset = SegmentationDataset(
            os.path.join(self.test_dataset, "image"),
            os.path.join(self.test_dataset, "label"),
            self.aug,
        )

    def setup_infer(self):
        pass

    def save_preds(self, preds, stage: Stages, dst_path: pathlib.Path):
        pass


class DicomDirSegmentationLightningDataModule(DirSegmentationLightningDataModule):
    dataset = ImageFolderInferDataset

    def setup_train_test_val(self, **kwargs):
        dicom_train_path = os.path.join(self.train_dataset, "images")
        png_train_path = os.path.join(self.train_dataset, "png")
        shutil.rmtree(png_train_path, ignore_errors=True)
        os.makedirs(png_train_path)
        for dicom in os.listdir(dicom_train_path):
            dicom_to_img(
                os.path.join(dicom_train_path, dicom),
                os.path.join(png_train_path, dicom.replace("dcm", "png")),
            )

        dicom_test_path = os.path.join(self.test_dataset, "images")
        png_test_path = os.path.join(self.test_dataset, "png")

        shutil.rmtree(png_test_path, ignore_errors=True)
        os.makedirs(png_test_path)
        for dicom in os.listdir(dicom_test_path):
            dicom_to_img(
                os.path.join(dicom_test_path, dicom),
                os.path.join(png_test_path, dicom.replace("dcm", "png")),
            )

        train_val = SegmentationDataset(
            png_train_path,
            os.path.join(self.train_dataset, "labels"),
            self.aug,
        )
        val_size = int(len(train_val) * float(self.val_size))
        self.train_dataset, self.val_dataset = torch.utils.data.random_split(
            train_val, [len(train_val) - val_size, val_size]
        )
        self.test_dataset = SegmentationDataset(
            png_test_path,
            os.path.join(self.test_dataset, "labels"),
            self.aug,
        )

    def save_preds(self, preds, stage: Stages, dst_path: pathlib.Path):
        dicoms = []
        shutil.rmtree(os.path.join(self.dicoms, "png"), ignore_errors=True)
        for i in os.listdir(self.dicoms):
            if i.endswith(".dcm"):
                dicoms.append(os.path.join(self.dicoms, i))
        pred = [p for pp in preds for p in pp]
        for i, m in enumerate(pred):
            mask = m.clone()
            mask = mask[0]
            mask[mask < 0.1] = 0
            mask[mask != 0] = 1
            img = dicom_to_img(dicoms[i])
            img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            img[mask != 0] = 255
            img_to_dicom(img, dicoms[i], dicoms[i][:-4] + "SC" + dicoms[i][-4:])

    def setup_infer(self):
        if isinstance(self.predict_dataset, self.dataset):
            return self.predict_dataset
        self.dicoms = str(self.predict_dataset)
        png_path = os.path.join(self.dicoms, "png")
        if not os.path.exists(png_path):
            os.makedirs(png_path)
        dicoms = [f for f in os.listdir(self.dicoms) if "dcm" in f]
        for dicom in dicoms:
            dicom_to_img(
                os.path.join(self.dicoms, dicom),
                os.path.join(png_path, dicom.replace("dcm", "png")),
            )
        self.predict_dataset = self.dataset(png_path, self.aug, True)
