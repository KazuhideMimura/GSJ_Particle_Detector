from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..helper import settings
from ..helper.filesystem import abspath
from ..helper.qcontext import QContext
from ..widget.filesystem import FolderInputWidget
from .data import Paramset


class ParamsetWidget(QWidget):
    form_layout: QFormLayout = None

    dataset_dir: FolderInputWidget = None
    class0: QLineEdit = None
    class1: QLineEdit = None
    class2: QLineEdit = None
    class3: QLineEdit = None
    class4: QLineEdit = None
    class5: QLineEdit = None
    class6: QLineEdit = None
    class7: QLineEdit = None
    class8: QLineEdit = None
    class9: QLineEdit = None
    lr0: QLineEdit = None
    flipud: QLineEdit = None
    fliplr: QLineEdit = None

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        with QContext(QVBoxLayout()) as layout:
            layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
            layout.setContentsMargins(3, 3, 3, 3)
            layout.setSpacing(2)
            self.setLayout(layout)

        with QContext(QGroupBox(self.tr("Parameter set"), self)) as box:
            self.layout().addWidget(box)

            with QContext(QFormLayout()) as layout:
                layout.setContentsMargins(3, 3, 3, 3)
                layout.setSpacing(1)
                box.setLayout(layout)
                self.form_layout = layout

            with QContext(QLabel(parent=self), FolderInputWidget(parent=self)) as (label, dir):
                label.setText(self.tr("path to dataset"))
                label.setProperty("style", "property")
                dir.setObjectName("dataset_dir")
                dir.setExistRequired(True)
                box.layout().addRow(label, dir)
                self.dataset_dir = dir

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setText(self.tr("names"))
                label.setProperty("style", "property")
                edit.setObjectName("class0")
                box.layout().addRow(label, edit)
                self.class0 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setProperty("style", "property")
                edit.setObjectName("class1")
                box.layout().addRow(label, edit)
                self.class1 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setProperty("style", "property")
                edit.setObjectName("class2")
                box.layout().addRow(label, edit)
                self.class2 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setProperty("style", "property")
                edit.setObjectName("class3")
                box.layout().addRow(label, edit)
                self.class3 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setProperty("style", "property")
                edit.setObjectName("class4")
                box.layout().addRow(label, edit)
                self.class4 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setProperty("style", "property")
                edit.setObjectName("class5")
                box.layout().addRow(label, edit)
                self.class5 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setProperty("style", "property")
                edit.setObjectName("class6")
                box.layout().addRow(label, edit)
                self.class6 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setProperty("style", "property")
                edit.setObjectName("class7")
                box.layout().addRow(label, edit)
                self.class7 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setProperty("style", "property")
                edit.setObjectName("class8")
                box.layout().addRow(label, edit)
                self.class8 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setProperty("style", "property")
                edit.setObjectName("class9")
                box.layout().addRow(label, edit)
                self.class9 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setText(self.tr("lr0"))
                label.setProperty("style", "property")
                edit.setObjectName("lr0")
                box.layout().addRow(label, edit)
                self.lr0 = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setText(self.tr("flipud"))
                label.setProperty("style", "property")
                edit.setObjectName("flipud")
                box.layout().addRow(label, edit)
                self.flipud = edit

            with QContext(QLabel(parent=self), QLineEdit(parent=self)) as (label, edit):
                label.setText(self.tr("fliplr"))
                label.setProperty("style", "property")
                edit.setObjectName("fliplr")
                box.layout().addRow(label, edit)
                self.fliplr = edit

    def setValues(self, paramset: Paramset):
        if not paramset:
            self.dataset_dir.clear()
            self.class0.clear()
            self.class1.clear()
            self.class2.clear()
            self.class3.clear()
            self.class4.clear()
            self.class5.clear()
            self.class6.clear()
            self.class7.clear()
            self.class8.clear()
            self.class9.clear()
            self.lr0.clear()
            self.flipud.clear()
            self.fliplr.clear()
            return

        self.dataset_dir.setText(paramset.dataset_dir)
        self.class0.setText(paramset.classes.get(0, ""))
        self.class1.setText(paramset.classes.get(1, ""))
        self.class2.setText(paramset.classes.get(2, ""))
        self.class3.setText(paramset.classes.get(3, ""))
        self.class4.setText(paramset.classes.get(4, ""))
        self.class5.setText(paramset.classes.get(5, ""))
        self.class6.setText(paramset.classes.get(6, ""))
        self.class7.setText(paramset.classes.get(7, ""))
        self.class8.setText(paramset.classes.get(8, ""))
        self.class9.setText(paramset.classes.get(9, ""))
        self.lr0.setText(str(paramset.lr0))
        self.flipud.setText(str(paramset.flipud))
        self.fliplr.setText(str(paramset.fliplr))


class ParamsetView(ParamsetWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.dataset_dir.setEnabled(False)
        self.class0.setEnabled(False)
        self.class1.setEnabled(False)
        self.class2.setEnabled(False)
        self.class3.setEnabled(False)
        self.class4.setEnabled(False)
        self.class5.setEnabled(False)
        self.class6.setEnabled(False)
        self.class7.setEnabled(False)
        self.class8.setEnabled(False)
        self.class9.setEnabled(False)
        self.lr0.setEnabled(False)
        self.flipud.setEnabled(False)
        self.fliplr.setEnabled(False)

        self.updateRowVisible()

    def setValues(self, paramset: Paramset):
        super().setValues(paramset)
        self.updateRowVisible()

    def updateRowVisible(self):
        self.form_layout.setRowVisible(self.class0, True)  # 1st row is always visible
        self.form_layout.setRowVisible(self.class1, bool(self.class1.text()))
        self.form_layout.setRowVisible(self.class2, bool(self.class2.text()))
        self.form_layout.setRowVisible(self.class3, bool(self.class3.text()))
        self.form_layout.setRowVisible(self.class4, bool(self.class4.text()))
        self.form_layout.setRowVisible(self.class5, bool(self.class5.text()))
        self.form_layout.setRowVisible(self.class6, bool(self.class6.text()))
        self.form_layout.setRowVisible(self.class7, bool(self.class7.text()))
        self.form_layout.setRowVisible(self.class8, bool(self.class8.text()))
        self.form_layout.setRowVisible(self.class9, bool(self.class9.text()))


class ParamsetForm(ParamsetWidget):
    inputChanged = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)

        yolov9_dir = settings.value("yolov9_dir")
        dataset_dir = settings.value("dataset_dir", yolov9_dir)

        self.dataset_dir.setPlaceholderText("path to dataset folder")
        self.dataset_dir.setInitialDir(dataset_dir)
        self.dataset_dir.setStartDir(yolov9_dir)

        self.class0.setPlaceholderText("name of class 0")
        self.class1.setPlaceholderText("name of class 1")
        self.class2.setPlaceholderText("name of class 2")
        self.class3.setPlaceholderText("name of class 3")
        self.class4.setPlaceholderText("name of class 4")
        self.class5.setPlaceholderText("name of class 5")
        self.class6.setPlaceholderText("name of class 6")
        self.class7.setPlaceholderText("name of class 7")
        self.class8.setPlaceholderText("name of class 8")
        self.class9.setPlaceholderText("name of class 9")
        self.lr0.setPlaceholderText("initial learning rate")
        self.lr0.setValidator(QDoubleValidator(bottom=0.0, top=1.0))
        self.flipud.setPlaceholderText("randomly flip upside down")
        self.flipud.setValidator(QDoubleValidator(bottom=0.0, top=1.0))
        self.fliplr.setPlaceholderText("randomly flip left/right")
        self.fliplr.setValidator(QDoubleValidator(bottom=0.0, top=1.0))

        self.dataset_dir.textChanged.connect(self.onTextChanged)
        self.class0.textChanged.connect(self.onTextChanged)
        self.class1.textChanged.connect(self.onTextChanged)
        self.class2.textChanged.connect(self.onTextChanged)
        self.class3.textChanged.connect(self.onTextChanged)
        self.class4.textChanged.connect(self.onTextChanged)
        self.class5.textChanged.connect(self.onTextChanged)
        self.class6.textChanged.connect(self.onTextChanged)
        self.class7.textChanged.connect(self.onTextChanged)
        self.class8.textChanged.connect(self.onTextChanged)
        self.class9.textChanged.connect(self.onTextChanged)
        self.lr0.textChanged.connect(self.onTextChanged)
        self.flipud.textChanged.connect(self.onTextChanged)
        self.fliplr.textChanged.connect(self.onTextChanged)

    @Slot()
    def onTextChanged(self):
        sender = self.sender()
        if sender is None:
            return

        if isinstance(sender.validator(), QDoubleValidator):
            if sender.hasAcceptableInput():
                self.inputChanged.emit(sender.objectName(), float(sender.text()))
        else:
            self.inputChanged.emit(sender.objectName(), sender.text())

    def hasAcceptableInput(self):
        return (
            abspath(self.dataset_dir.path()).exists()
            and any(bool(getattr(self, f"class{i}").text()) for i in range(10))
            and self.lr0.hasAcceptableInput()
            and self.flipud.hasAcceptableInput()
            and self.fliplr.hasAcceptableInput()
        )
