import sys
from PyQt6.QtWidgets import QApplication
from hoverx.ui.widget import FloatingWidget
from hoverx.controller.dummy import DummyController

def main():
    app = QApplication(sys.argv)

    # App-level metadata
    app.setApplicationName("HoverX")
    app.setOrganizationName("HoverX")

    controller = DummyController()
    widget = FloatingWidget(controller)
    widget.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()