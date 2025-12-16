import sys
from PyQt6.QtWidgets import QApplication
from ui.widget import FloatingWidget

def main():
    app = QApplication(sys.argv)

    # App-level metadata
    app.setApplicationName("HoverX")
    app.setOrganizationName("HoverX")

    widget = FloatingWidget()
    widget.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()