import torch
from pytorch_lightning import LightningModule
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.ops import box_iou


def _evaluate_iou(target, pred):
    """Evaluate intersection over union (IOU) for target from dataset and output prediction from model."""
    if pred["boxes"].shape[0] == 0:
        # no box detected, 0 IOU
        return torch.tensor(0.0, device=pred["boxes"].device)
    return box_iou(target["boxes"], pred["boxes"]).diag().mean()


class DetectionLightningModule(LightningModule):
    def __init__(
        self,
        model,
        losses,
        optimizer_cfg,
        scheduler_cfg=None,
        num_classes=2,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.model = model
        self.losses = losses
        self.num_classes = num_classes

        self.optimizer_cfg = optimizer_cfg
        self.scheduler_cfg = scheduler_cfg
        self.counter = 0  # todo: give a description

        # self.save_hyperparameters()  # todo:

    def model_load_checkpoint(self, path):
        self.model.load_state_dict(torch.load(path)["state_dict"])

    def forward(self, batch: torch.Tensor) -> torch.Tensor:
        """Make a prediction"""
        return self.model(batch)

    def predict_proba(self, batch: torch.Tensor) -> torch.Tensor:
        """Predict and output probabilities"""
        out = self.model(batch)
        return out

    def configure_optimizers(self):
        """Function to set up optimizers and schedulers"""

        # optim = hydra.utils.instantiate(self.optimizer_cfg, params=params)
        # instantiate scheduler from configurations
        # scheduler = hydra.utils.instantiate(self.scheduler_cfg, optim)
        # return optimizers and schedulers

        # get all trainable model parameters
        params = [x for x in self.model.parameters() if x.requires_grad]
        # instantiate models from configurations
        optim = self.optimizer_cfg(params=params)
        if self.scheduler_cfg:
            return [optim], [self.scheduler_cfg(optim)]
        return [optim]

    def training_step(self, batch, batch_idx):
        """Process a batch in a training loop"""
        images, targets, idx = batch
        targets = [{k: v for k, v in t.items()} for t in targets]
        images = torch.stack(images).float()
        losses_dict = self.model(images, targets)
        loss = sum(loss for loss in losses_dict.values())
        return {"loss": loss, "log": losses_dict}

    def validation_step(self, batch, batch_id):
        images, targets, idx = batch
        targets = [{k: v for k, v in t.items()} for t in targets]
        outs = self.model(images)
        iou = torch.stack([_evaluate_iou(t, o) for t, o in zip(targets, outs)]).mean()
        self.log("val_loss", 1 - iou, prog_bar=True)
        return {"val_iou": iou}
