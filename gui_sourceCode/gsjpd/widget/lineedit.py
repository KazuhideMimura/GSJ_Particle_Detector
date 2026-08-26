from PySide6.QtWidgets import QLineEdit


class RequiredLineEdit(QLineEdit):
    required: bool = False

    def __init__(self, *args, **kwargs):
        self.required = kwargs.pop("required", True)

        super().__init__(*args, **kwargs)
        self.textChanged.connect(self.validate)

    def validate(self):
        if not self.isEnabled() or not self.isVisible() or not self.required:
            self.setProperty("state", "accepted")
            return

        if not self.hasAcceptableInput():
            self.setProperty("state", "required")
        else:
            self.setProperty("state", "accepted")

    def setRequired(self, required: bool):
        self.required = required
        self.validate()
