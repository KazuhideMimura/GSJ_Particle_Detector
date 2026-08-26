import sys
from argparse import ArgumentParser
from pathlib import Path

from PySide6.QtCore import QDir, QFile, QLocale, QSettings, QTranslator, Slot
from PySide6.QtWidgets import QApplication

from . import application_rc  # noqa: F401
from .__metadata__ import APPLICATION_NAME, ORGANIZATION_NAME, __version__
from .main_window import MainWindow


class Application(QApplication):
    translations: dict = {}

    settings: QSettings = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setOrganizationName(ORGANIZATION_NAME)
        self.setApplicationName(APPLICATION_NAME)
        self.setApplicationVersion(__version__)

        # load settings
        self.settings = QSettings(
            QSettings.IniFormat,
            QSettings.UserScope,
            self.organizationName(),
            self.applicationName(),
        )
        self.loadDefaultSettings()

        # change current directory
        yolov9_dir = self.settings.value("yolov9_dir")
        if yolov9_dir and Path(yolov9_dir).exists():
            QDir.setCurrent(yolov9_dir)

        # load translations
        self.initTranslations()

        # load stylesheets
        self.initStyle()

        # connect signals
        self.styleHints().colorSchemeChanged.connect(self.onColorSchemeChanged)

    def loadDefaultSettings(self):
        """
        デフォルト設定ファイルを読み込んで、self.settingsとマージする
        self.settingsに設定されている値は上書きしない
        """

        def mergeSettings(settings: QSettings):
            for key in settings.allKeys():
                if not self.settings.contains(key):
                    self.settings.setValue(key, settings.value(key))

        # リソースとしてバンドルされた設定ファイルを読み込む
        entries = QDir(":/settings").entryInfoList(["*.ini"], QDir.Files)
        for fileInfo in entries:
            settings = QSettings(fileInfo.filePath(), QSettings.IniFormat)
            mergeSettings(settings)

        self.upgradeSettings()

    def initTranslations(self):
        locale = QLocale.system()

        self.translations = {
            "ja_JP": QTranslator(),
            "en_US": QTranslator(),
        }
        for lang, translator in self.translations.items():
            translator.load(QLocale(lang), "translations", ".", ":/translations")

            if lang == locale.name():
                self.installTranslator(translator)

    def initStyle(self):
        entries = QDir(":/stylesheets").entryInfoList(["*.qss"], QDir.Files)

        styleSheet = ""

        for fileInfo in entries:
            qssFile = QFile(fileInfo.filePath())
            if qssFile.open(QFile.ReadOnly):
                styleSheet += qssFile.readAll().toStdString()

        self.setStyleSheet(styleSheet)

    @Slot()
    def onColorSchemeChanged(self):
        self.initStyle()
        for window in self.topLevelWidgets():
            if window.isVisible():
                window.update()

    def upgradeSettings(self):
        setting_version = self.settings.value("app_version", "1.0.0")
        match setting_version:
            case "1.0.0" | "1.0.1" | "1.0.2":
                pass

        self.settings.setValue("app_version", __version__)
        self.settings.sync()


application: Application = None


def main():
    parser = ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--shortcut", action="store_true")
    parser.add_argument("--yolov9-dir", type=str)
    args, *_ = parser.parse_known_args()

    if args.init:
        settings = QSettings(
            QSettings.IniFormat, QSettings.UserScope, ORGANIZATION_NAME, APPLICATION_NAME
        )
        settings.clear()

    if args.shortcut:
        try:
            from .scripts import ShortCut

            ShortCut().create()
        except Exception as e:
            print(e)

    global application
    application = Application(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(application.exec())


if __name__ == "__main__":
    main()
