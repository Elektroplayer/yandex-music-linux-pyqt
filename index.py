# Импорт библиотек и файлов
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QPixmap
from designs.MainWindow import Ui_MainWindow
from yandex_music import Client
from config import token
import mpv
import locale
import sys

# Создание главного класса
class Window(QMainWindow, Ui_MainWindow):

    # Инициализируем всё, что нужно
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # Это можно были сделать и в файле MainWindow.py, но тк он часто меняется, я это пожалуй оставлю пока что тут
        self.setGeometry(300, 220, 1220, 650)
        self.setMinimumSize(QtCore.QSize(580, 400))
        self.setWindowTitle('Yandex.Music')
        self.setWindowIcon(QIcon('images/logo.svg'))

        self.Everyday_PlaylistImage.setPixmap(QPixmap('./images/EverydayPlaylistImage.gif'))

        # Подключаем к кнопке старта музыки её функцию
        self.startStopButton.clicked.connect(self.startTrack)

        self.YMClient = Client(token).init() # Инициализируем YMClient

        self.track = "10994777:1193829"
        self.trackLink = ""
        self.playingStatus = False

        # Создаём плэер mpv
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.mpvPlayer = mpv.MPV(ytdl=True)

    #def resizeEvent(self, event):
        #width  = self.size().width()
        #height = self.size().height()

        # print(width, height)

        #self.footerFrame.setGeometry(QtCore.QRect(0, height-90, width, 90))
        #self.verticalLayoutWidget.setGeometry(QtCore.QRect(5, 5, width-10, 80))

        #self.headFrame.setGeometry(QtCore.QRect(0, 0, width, 46))
        #self.horizontalLayoutWidget.setGeometry(QtCore.QRect(5, 3, width-10, 41))

        #self.mainFrame.setGeometry(QtCore.QRect(0, 49, width, height-49-93))

        #player.wait_for_playback()
        

    def startTrack(self):
        # Если и работает, но весьма не очень

        if self.playingStatus == True:
            self.playingStatus = False
            print('Выключить')
            self.mpvPlayer.cycle("pause")
        else:
            if self.trackLink == '':
                self.trackLink = "https://music.yandex.ru/album/1193829/track/10994777"
                #print(self.trackLink)
                self.mpvPlayer.play(self.trackLink)
                #self.mpvPlayer.play("https://music.yandex.ru/album/1193829/track/10994777")
            else:
                self.mpvPlayer.cycle("pause")
            self.playingStatus = True

# Запускаем класс и всё что к нему требуется
if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())