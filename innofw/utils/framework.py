import inspect
from pathlib import Path

# third party libraries
from urllib.parse import urlparse

import hydra

# local modules
from innofw.constants import Frameworks
from innofw.core.integrations.base_integration_models import BaseIntegrationModel
from innofw.core.models import BaseModelAdapter
from innofw.utils import get_abs_path

from innofw.zoo.downloader import download_model
from innofw.constants import DefaultFolders


def map_model_to_framework(model):
    import sklearn
    import torch
    import xgboost
    import catboost

    if isinstance(model, xgboost.XGBModel):
        return Frameworks.xgboost
    elif isinstance(model, torch.nn.Module):
        return Frameworks.torch
    elif isinstance(model, sklearn.base.BaseEstimator):
        return Frameworks.sklearn
    elif isinstance(model, BaseIntegrationModel):
        return model.framework
    elif isinstance(model, catboost.CatBoost):
        return Frameworks.catboost
    else:
        raise NotImplementedError(f"Framework is not supported. {model}")


def is_suitable_for_framework(_cfg, fw):
    if fw == "adapter":
        return True
    else:
        for key in _cfg.implementations.keys():
            if Frameworks(key) is fw:
                return True
        return False


def is_suitable_for_task(_cfg, _task):
    return _cfg.task == ["all"] or _task in _cfg.task


TABLE_FRAMEWORKS = ["xgboost", "sklearn", "catboost"]


def get_obj(
    config,
    name,
    task,
    framework: Frameworks,
    search_func=None,
    _recursive_=True,
    *args,
    **kwargs,
):
    obj = None
    if (
        name in config
        and config[name] is not None
        # and "implementations" in config[name]
    ):  # framework not in TABLE_FRAMEWORKS and
        if "task" not in config[name]:
            return None

        if is_suitable_for_task(config[name], task) and is_suitable_for_framework(
            config[name], framework
        ):
            items = []
            for key, value in config[name].implementations[framework.value].items():
                if key == "meta":
                    continue
                if "function" in value:
                    v = value.copy()
                    item = lambda *args_, **kwargs_: hydra.utils.instantiate(
                        v["function"], *args_, **kwargs_
                    )
                else:
                    try:
                        item = hydra.utils.instantiate(
                            value["object"], _recursive_=_recursive_, *args, **kwargs
                        )
                    except Exception as e:
                        item = hydra.utils.instantiate(value["object"])
                items.append(item)
        else:
            raise ValueError(
                f"These {name} are not applicable with selected model and/or task"
            )

        obj = items[0] if len(items) == 1 else items
    elif search_func is not None:
        obj = search_func(task, framework, config[name], *args, **kwargs)
    # else:
    #     raise ValueError("Unable to instantiate the object")

    return obj


def get_losses(cfg, task, framework):
    losses = None
    if "losses" in cfg and cfg.losses is not None:
        if "task" not in cfg["losses"]:
            return None
        if is_suitable_for_task(cfg.losses, task) and is_suitable_for_framework(
            cfg.losses, framework
        ):
            losses = []
            for key, value in cfg.losses.implementations[framework.value].items():
                if key == "meta":
                    continue

                items = [key, value["weight"]]
                if "function" in value:
                    items.append(
                        lambda *args, **kwargs: hydra.utils.instantiate(
                            value["function"], *args, **kwargs
                        )
                    )
                else:
                    items.append(hydra.utils.instantiate(value["object"]))
                losses.append(items)
        else:
            raise ValueError(
                "This loss is not applicable with selected model and/or task"
            )
    return losses


def get_callbacks(cfg, task, framework, *args, **kwargs):
    # todo: make it compliant for other frameworks other than pytorch lightning
    # =*=*=*=*= Callbacks =*=*=*=*=
    callbacks = []
    if "callbacks" in cfg and cfg.callbacks is not None:
        if "task" not in cfg["callbacks"]:
            return None
        if is_suitable_for_task(cfg.callbacks, task) and is_suitable_for_framework(
            cfg.callbacks, framework
        ):
            for _, cb_conf in cfg.callbacks.implementations[framework.value].items():
                if "_target_" in cb_conf:
                    if inspect.isclass(cb_conf["_target_"]):
                        try:
                            callbacks.append(
                                hydra.utils.instantiate(
                                    cb_conf, *args, **kwargs, _recursive_=False
                                )
                            )
                        except:
                            callbacks.append(
                                hydra.utils.instantiate(cb_conf, _recursive_=False)
                            )
                    else:
                        callbacks.append(cb_conf)
    return callbacks


from innofw.schema.model import ModelConfig
from innofw.schema.dataset import DatasetConfig
from innofw.schema.experiment import ExperimentConfig


def get_model(cfg, trainer_cfg):
    model_datacls = ModelConfig(**cfg, trainer_cfg=trainer_cfg)
    return hydra.utils.instantiate(
        model_datacls.models
    )  # todo: make model_datacls.models call more configurable


def get_datamodule(cfg, framework: Frameworks, *args, **kwargs):
    dataset_datacls = DatasetConfig(**cfg, framework=framework)
    datamodule = hydra.utils.instantiate(dataset_datacls.datasets, *args, **kwargs)
    if framework not in datamodule.framework:
        raise ValueError("Wrong framework provided")
    return datamodule


def get_experiment(cfg):
    experiment_datacls = ExperimentConfig(**cfg)
    return experiment_datacls


def get_ckpt_path(cfg):
    ckpt_path = cfg.get("ckpt_path")
    if ckpt_path is None:
        return ckpt_path

    # download the file if remote path specified
    if urlparse(ckpt_path).netloc:
        default_save_folder: Path = get_abs_path(
            DefaultFolders.remote_model_weights_save_dir.value
        )
        default_save_folder.mkdir(exist_ok=True, parents=True)

        ckpt_path = download_model(
            file_url=ckpt_path,
            dst_path=default_save_folder,
        )

    ckpt_path = Path(ckpt_path)

    if not ckpt_path.is_absolute():
        ckpt_path = get_abs_path(ckpt_path)
    return ckpt_path
