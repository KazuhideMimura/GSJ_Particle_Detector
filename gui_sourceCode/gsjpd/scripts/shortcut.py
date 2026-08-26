#!python

import os
import sys
from importlib import resources
from pathlib import Path

from ..__metadata__ import APPLICATION_NAME, PACKAGE_NAME
from ..helper.filesystem import getDesktopDir


class ShortCut:
    shortcut_name = f"{APPLICATION_NAME}.lnk"
    app_exe = "gsj_pd.exe"

    def __init__(self, dir: os.PathLike = None):
        if dir is None:
            dir = getDesktopDir() or Path.cwd()

        self.shortcut_path = Path(dir, self.shortcut_name).resolve()

    def exists(self):
        return self.shortcut_path.exists()

    def unlink(self):
        return self.shortcut_path.unlink()

    def create(self):
        try:
            from win32com.client import Dispatch
        except ImportError:
            raise ImportError("pywin32 is required to create a shortcut.")

        if self.exists():
            self.unlink()

        def python_executable():
            python_exe = Path(sys.executable).resolve()
            pythonw_exe = python_exe.with_name("pythonw.exe")
            return pythonw_exe if pythonw_exe.exists() else python_exe

        app_executable = next(Path(sys.prefix).glob(f"**/{self.app_exe}"))
        if not app_executable:
            raise FileNotFoundError(f"{self.app_exe} not found.")

        shortcut_path = os.fspath(self.shortcut_path)
        python_executable = os.fspath(python_executable())
        app_executable = os.fspath(app_executable.resolve())

        with resources.as_file(resources.files(PACKAGE_NAME) / "application.ico") as ico_file:
            icon_location = Path(ico_file).resolve()

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = python_executable
        shortcut.Arguments = app_executable
        shortcut.WorkingDirectory = os.fspath(Path(os.curdir).resolve())
        shortcut.IconLocation = f"{icon_location}"
        shortcut.save()

        return shortcut_path


if __name__ == "__main__":
    try:
        shortcut = ShortCut().create()

        print(f"Shortcut created: {shortcut}")
    except Exception as e:
        print(f"Shortcut creation failed: {e}")
