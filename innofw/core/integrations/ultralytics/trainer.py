from omegaconf import DictConfig

from ..base_adapter import BaseAdapter


# todo: test this function
def get_device(trainer_cfg):
    if "accelerator" in trainer_cfg and trainer_cfg.accelerator == "cpu":
        result = "cpu"
    else:
        if "gpus" in trainer_cfg and trainer_cfg.gpus:
            if isinstance(trainer_cfg.gpus, int):
                result = f"{trainer_cfg.devices}"
            else:
                devices = ",".join(map(str, trainer_cfg.gpus))
                result = f"{devices}"
        else:
            # get all available devices
            if "devices" not in trainer_cfg or trainer_cfg.devices is None:
                import torch

                n_devices = torch.cuda.device_count()
            else:
                n_devices = trainer_cfg.devices

            if n_devices is None or n_devices == 0:
                return "cpu"
            else:
                devices = ",".join(map(str, range(n_devices)))

                result = f"{devices}"

    return result


class YOLOV5TrainerBaseAdapter(BaseAdapter):
    def __init__(self):
        pass

    # todo: test its correctness
    def adapt(self, trainer) -> dict:
        if isinstance(trainer, DictConfig):
            device: str = get_device(trainer)
            try:
                epochs: int = trainer.max_epochs
            except:
                epochs = 1
        else:
            raise NotImplementedError
        return {"epochs": epochs, "device": device}

    def from_cfg(self, cfg):
        return {}

    def from_obj(self, obj):
        return {}
