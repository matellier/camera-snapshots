import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    # Target the DSI touchscreen — smallest screen by area
    screens = app.screens()
    target = min(screens, key=lambda s: s.geometry().width() * s.geometry().height())
    window.setGeometry(target.geometry())
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
