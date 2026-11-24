import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from DB_Units.database import init_database
from DB_Units.product_repository import ProductRepository
from Data_Processing.excel_processor import ensure_sample_excel
from Data_Processing.data_loader import import_products
from UI_Windows.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PyQt6 Shop Example")
    try:
        init_database()
        excel_file = ensure_sample_excel()
        if ProductRepository.count() == 0:
            import_products(excel_file)
        window = MainWindow()
        window.show()
    except Exception as error:
        QMessageBox.critical(None, "Ошибка запуска", str(error))
        return 1
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
