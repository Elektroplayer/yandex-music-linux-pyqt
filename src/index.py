# Импорт библиотек и файлов
import sys
from PyQt5 import QtWidgets
from windows.MainWindow import Window


# Запускаем класс и всё что к нему требуется
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
