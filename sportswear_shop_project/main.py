import sys
from PyQt6.QtWidgets import QApplication
from texshopProductShow import MyWin

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWin()
    window.show()
    sys.exit(app.exec())
