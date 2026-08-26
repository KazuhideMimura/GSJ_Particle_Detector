import os
from io import IOBase
from pathlib import Path

import yaml
from pydantic import BaseModel
from send2trash import send2trash

from ..helper import settings
from ..helper.filesystem import abspath, relpath


def getDefaultName(basename: str) -> str:
    runs_train_dir = settings.value("runs_train_dir", "runs/train")
    runs_dir = Path(runs_train_dir)
    name = basename
    i = 2
    while True:
        if not Path(runs_dir, name).exists():
            break
        name = f"{basename} {i}"
        i += 1
    return name


class Metadata(BaseModel):
    name: str | None = None
    description: str | None = None
    timestamp: str | None = None

    def __init__(self, **data):
        with settings.group("Defaults") as group:
            default_name = getDefaultName(group.value("name", "New Model"))
            data.setdefault("name", default_name)

        super().__init__(**data)

    def write_as_yaml(self, stream: IOBase):
        yaml.safe_dump(
            self.model_dump(mode="json", exclude_none=True),
            stream,
            allow_unicode=True,
            sort_keys=False,
        )


class Paramset(BaseModel):
    dataset_dir: str = None
    classes: dict[int, str | None] = {}
    lr0: float = None
    flipud: float = None
    fliplr: float = None

    def __init__(self, **data):
        # set default values
        with settings.group("Defaults") as group:
            data.setdefault("dataset_dir", group.value("dataset_dir", ""))
            data.setdefault("lr0", group.value("lr0", 0.01))
            data.setdefault("flipud", group.value("flipud", 0.0))
            data.setdefault("fliplr", group.value("fliplr", 0.0))

        data.setdefault("classes", {i: None for i in range(10)})

        super().__init__(**data)

    def write_as_yaml(self, stream: IOBase):
        yaml.safe_dump(
            self.model_dump(mode="json", exclude_none=True),
            stream,
            allow_unicode=True,
            sort_keys=False,
        )

    def load_data_yaml(self, data_yaml: os.PathLike):
        data_yaml = abspath(data_yaml)

        if data_yaml.exists():
            with open(data_yaml, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            self.dataset_dir = relpath(data.get("path", self.dataset_dir), posix=True)
            self.classes = {i: data["names"].get(i, None) for i in range(10)}

    def load_hyp_yaml(self, hyp_yaml: os.PathLike):
        hyp_yaml = abspath(hyp_yaml)

        if hyp_yaml.exists():
            with open(hyp_yaml, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            self.lr0 = data.get("lr0", self.lr0)
            self.flipud = data.get("flipud", self.flipud)
            self.fliplr = data.get("fliplr", self.fliplr)

    def equals(self, other: "Paramset") -> bool:
        return (
            self.dataset_dir == other.dataset_dir
            and self.classes == other.classes
            and self.lr0 == other.lr0
            and self.flipud == other.flipud
            and self.fliplr == other.fliplr
        )


class Arguments(BaseModel):
    data_yaml: str = None
    hyp_yaml: str = None
    img_size: int = None
    weights: str = None
    cfg: str = None
    epochs: int = None

    def __init__(self, **data):
        # set default values
        with settings.group("Defaults") as group:
            data.setdefault("data_yaml", group.value("data_yaml", None))
            data.setdefault("hyp_yaml", group.value("hyp_yaml", None))
            data.setdefault("img_size", group.value("img_size", 640))
            data.setdefault("cfg", group.value("cfg", None))
            data.setdefault("epochs", group.value("epochs", 1))

        super().__init__(**data)

    def write_as_yaml(self, stream: IOBase):
        yaml.safe_dump(
            self.model_dump(mode="json", exclude_none=True),
            stream,
            allow_unicode=True,
            sort_keys=False,
        )


class Metrics(BaseModel):
    precision: float | None = None
    recall: float | None = None
    mAP50: float | None = None
    mAP: float | None = None
    timestamp: str | None = None

    def __init__(self, **data):
        super().__init__(**data)

    def write_as_yaml(self, stream: IOBase):
        yaml.safe_dump(
            self.model_dump(mode="json", exclude_none=True),
            stream,
            allow_unicode=True,
            sort_keys=False,
        )


class ModelInfo(BaseModel):
    runs_dir: str | None = None

    metadata: Metadata | None = None
    paramset: Paramset | None = None
    arguments: Arguments | None = None
    metrics: Metrics | None = None

    def __init__(self, **data):
        super().__init__(**data)

        self.metadata = Metadata(**data.get("metadata", {}))
        self.paramset = Paramset(**data.get("paramset", {}))
        self.arguments = Arguments(**data.get("arguments", {}))
        self.metrics = Metrics(**data.get("metrics", {}))

    def save(self, runs_dir: os.PathLike):
        runs_dir = abspath(runs_dir)

        filename = settings.value("model_yaml", "particle_detector.yaml")
        with open(Path(runs_dir, filename), "w", encoding="utf-8") as f:
            self.write_as_yaml(f)

    def write_as_yaml(self, stream: IOBase):
        yaml.safe_dump(
            self.model_dump(mode="json", exclude_none=True),
            stream,
            allow_unicode=True,
            sort_keys=False,
        )

    @staticmethod
    def from_yaml(stream: IOBase):
        data = yaml.safe_load(stream)
        return ModelInfo(**data)

    @staticmethod
    def from_dir(runs_dir: os.PathLike):
        runs_dir = relpath(runs_dir, posix=True)
        name = Path(runs_dir).name

        filename = settings.value("model_yaml", "particle_detector.yaml")
        path = abspath(Path(runs_dir, filename))
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            data = {"runs_dir": runs_dir}

        model = ModelInfo(**data)

        # 読み込んだ内容がディレクトリ名と異なる場合はディレクトリ名を優先
        if model.runs_dir != runs_dir:
            model.runs_dir = runs_dir
        if model.metadata.name != name:
            model.metadata.name = name

        data_yaml = Path(runs_dir, "data.yaml")
        if data_yaml.exists():
            model.paramset.load_data_yaml(data_yaml)

        hyp_yaml = Path(runs_dir, "hyp.yaml")
        if hyp_yaml.exists():
            model.paramset.load_hyp_yaml(hyp_yaml)

        return model

    def rename(self, name: str) -> str:
        try:
            src_dir = abspath(self.runs_dir)
            dst_dir = src_dir.rename(src_dir.with_name(name))
            self.runs_dir = relpath(dst_dir, posix=True)
            self.save(dst_dir)
        except PermissionError:
            raise PermissionError("Permission denied")
        except OSError:
            raise OSError("Error renaming folder")

    def delete(self):
        try:
            runs_dir = abspath(self.runs_dir, fspath=True)
            send2trash(runs_dir)
        except PermissionError:
            raise PermissionError("Permission denied")
        except OSError:
            raise OSError("Error deleting folder")
