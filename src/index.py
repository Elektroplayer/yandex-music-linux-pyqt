# Импорт библиотек и файлов
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap, QFont, QImage, QCursor
from designs.MainWindow import Ui_MainWindow
from designs.LoginDialog import Ui_Dialog
from yandex_music import Client
from gi.repository import Gio
import datetime
import mpv
import locale
import sys
import requests

class LoginDialog(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.loginbutton.clicked.connect(self.login)

    def login(self):
        login = self.loginInput.text()
        password = self.passinput.text()

        print(login, len(login))
        print(password, len(password))

        if len(login) == 0 or len(password) == 0:
            self.label.setText('Поля не должны быть пустыми!')
            return

        link_post = "https://oauth.yandex.com/token"
        header = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
        }

        try:
            request_post = f"grant_type=password&client_id=23cabbbdc6cd418abb4b39c32c41195d&client_secret=53bc75238f0c4d08a118e51fe9203300&username={login}&password={password}"
            request_auth = requests.post(link_post, data=request_post, headers=header)
            if request_auth.status_code == 200:
                json_data = request_auth.json()
                self.token = json_data.get('access_token')

                if self.token != '':
                    self.close()
                else:
                    self.label.setText('Произошла ошибка, попробуйте снова')
            else:
                self.label.setText('Не верный логин или пароль')
        except requests.exceptions.ConnectionError:
            self.label.setText('Не удалось отправить запрос')

# Создание главного класса
class Window(QtWidgets.QMainWindow, Ui_MainWindow):

    # Инициализируем всё, что нужно
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # Это можно были сделать и в файле MainWindow.py, но тк он часто меняется, я это пожалуй оставлю пока что тут
        self.setGeometry(300, 220, 1220, 650)
        self.setMinimumSize(QtCore.QSize(580, 400))
        self.setWindowTitle('Yandex.Music')
        self.setWindowIcon(QIcon('./src/images/logo.svg'))

        # Скрываем правое меню
        self.rightMenu.hide() 

        # Подключаем к кнопкам их функции
        self.startStopButton.clicked.connect(self.startTrack)
        self.rightMenu_Hide.clicked.connect(self.hideRightMenu)

        # Запускаем функцию получения токена
        token = self.getToken()

        # Инициализируем YMClient с полученным токеном
        self.YMClient = Client(token).init() 

        # Создаём плэер mpv
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.mpvPlayer = mpv.MPV(ytdl=True)

        # Пока что бесполезные переменные
        self.track = "10994777:1193829"
        self.trackLink = ""
        self.playingStatus = False

        # Инициализируем плэйлисты пользователя. Пока что только сгененированные.
        self.playlistInit()

    def getToken(self):
        # Создаём схемы для сохранения токена
        schema_source = Gio.SettingsSchemaSource.new_from_directory('./src/', Gio.SettingsSchemaSource.get_default(), False)
        schema = schema_source.lookup('com.github.vitaly.yandex-music-pyqt', False)
        self.settings = Gio.Settings.new_full(schema, None, None)

        # Изымаем его
        token = self.settings.get_string('token')

        # Если токена нет
        if token == '':
            dlg = LoginDialog() # Запускаем диалог для его получения
            dlg.exec()

            self.settings.set_string('token', dlg.token) # Записываем в схему

            #token = dlg.token 
        
        return token or dlg.token # Возвращаем токен

    def playlistInit(self):
        playlists  = self.YMClient.feed().generated_playlists # Получаем плэйлисты
        month      = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'] # Массив с месяцами в нужном падеже

        for playlist in playlists:
            img = playlist.data.cover.uri.replace('%%', '200x200') # Получаем картинку
            title = playlist.data.title # Имя
            description = playlist.data.description # Описание
            time = playlist.data.modified # Время обновления 
            curTime = str(datetime.datetime.now())[:10] # Текущее время 

            # Получаем "хорошее" время
            if time[:10] == curTime:
                modTime = 'сегодня'
            elif int(curTime[8:10]) - int(time[8:10]) == 1:
                modTime = 'вчера'
            else:
                modTime = time[8:10] + ' ' + month[ int(time[5:7])-1 ]

            # Создаём виджет плэйлиста
            widget = QtWidgets.QWidget(self.scrollAreaWidgetContents)
            widget.setObjectName(playlist.type + "PlaylistWidget")
            widget.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
            widget.setStyleSheet("QWidget:hover { background-color: palette(window) }")
            widget.mouseReleaseEvent = self.playlistClickedDecorator(playlist) # self.printText1(self, playlist)

            # Далее layout в виджете
            layout = QtWidgets.QVBoxLayout(widget)
            layout.setObjectName(playlist.type + "PlaylistWidgetLayout")

            # Картинку загружаем по ссылке
            image = QImage()
            image.loadFromData(requests.get('http://'+img).content)

            # Создаём лэйбл с картинкой
            ImageLabel = QtWidgets.QLabel(self.scrollAreaWidgetContents)
            ImageLabel.setMinimumSize(QtCore.QSize(200, 200))
            ImageLabel.setMaximumSize(QtCore.QSize(200, 200))
            ImageLabel.setPixmap(QPixmap(image))
            ImageLabel.setObjectName(playlist.type+ "_PlaylistImage")
            layout.addWidget(ImageLabel) 

            # Лэйбл с именем
            LabelName = QtWidgets.QLabel(self.scrollAreaWidgetContents)
            LabelName.setMinimumSize(QtCore.QSize(200, 0))
            LabelName.setMaximumSize(QtCore.QSize(200, 25))
            font = QFont()
            font.setBold(True)
            font.setWeight(75)
            LabelName.setFont(font)
            LabelName.setIndent(5)
            LabelName.setObjectName(playlist.type + '_PlaylistName')
            LabelName.setText(title)
            layout.addWidget(LabelName)

            # Лэйбл с описанием
            LabelDescription = QtWidgets.QLabel(self.scrollAreaWidgetContents)
            sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(0)
            sizePolicy.setHeightForWidth(LabelDescription.sizePolicy().hasHeightForWidth())
            LabelDescription.setSizePolicy(sizePolicy)
            LabelDescription.setMaximumSize(QtCore.QSize(200, 16777215))
            LabelDescription.setTextFormat(QtCore.Qt.AutoText)
            LabelDescription.setWordWrap(True)
            LabelDescription.setIndent(5)
            LabelDescription.setObjectName(playlist.type + '_PlaylistDescription')
            LabelDescription.setText(description)
            layout.addWidget(LabelDescription)

            # Лэйбл "когда обновлён плэйлист"
            LabelReloaded = QtWidgets.QLabel(self.scrollAreaWidgetContents)
            LabelReloaded.setMaximumSize(QtCore.QSize(200, 25))
            LabelReloaded.setIndent(5)
            LabelReloaded.setObjectName(playlist.type + '_PlaylistReloaded')
            LabelReloaded.setText("Обновлён " + modTime)
            layout.addWidget(LabelReloaded)

            # Добавляем виджет к "главному" layout
            self.horizontalLayout_5.addWidget(widget)
            
            # И к нему добавляем небольшой спэйсер
            spacerItem2 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
            self.horizontalLayout_5.addItem(spacerItem2)
    
    # Докартор, цель которого только запомнить, с каким плэйлистом устанавливалась функция
    def playlistClickedDecorator(self, playlist):
        
        def outF(event):
            self.playlistClicked(playlist) #playlist
            
        return outF

    # Очистка layout
    def clearLayout(self,layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self.clearLayout(child.layout())

    # При клике на плейлист создаём правое меню и вставляет треки выбранного плейлиста
    def playlistClicked(self, playlist):
        # Устанавливаем имя плейлиста
        self.rightMenu_PlaylistName.setText(playlist.data.title)

        # Удаляем все элементы в меню
        self.clearLayout(self.rightMenu_PlaylistMusic)

        # Показываем левое меню
        self.showRightMenu()

        # Получаем ID треков
        tracksIDs = []
        for track in playlist.data.tracks:
            tracksIDs.append(track.id)

        # Получаем о них всю инфу
        tracks = self.YMClient.tracks(tracksIDs) 

        # Добавляем каждый трек в общий layout
        for track in tracks:
            name = track.title
            authors = track.artists[0].name

            layoutTrack = QtWidgets.QHBoxLayout()
            layoutTrack.setObjectName(str(track.id) + "_Track")
            layoutTrack_PlayButton = QtWidgets.QPushButton(self.scrollAreaWidgetContents_2)
            layoutTrack_PlayButton.setMaximumSize(QtCore.QSize(30, 30))
            layoutTrack_PlayButton.setObjectName(str(track.id) + "_PlayButton")
            layoutTrack_PlayButton.setText("Play")
            layoutTrack.addWidget(layoutTrack_PlayButton)
            layoutTrack_TrackAuthorName = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
            layoutTrack_TrackAuthorName.setTextFormat(QtCore.Qt.MarkdownText)
            layoutTrack_TrackAuthorName.setObjectName(str(track.id) + "_TrackAuthorName")
            layoutTrack_TrackAuthorName.setText("**" + authors + "** - " + name)
            layoutTrack.addWidget(layoutTrack_TrackAuthorName)
            layoutTrack_LikeButton = QtWidgets.QPushButton(self.scrollAreaWidgetContents_2)
            layoutTrack_LikeButton.setMaximumSize(QtCore.QSize(30, 30))
            layoutTrack_LikeButton.setObjectName(str(track.id) + "_LikeButton")
            layoutTrack_LikeButton.setText("like")
            layoutTrack.addWidget(layoutTrack_LikeButton)
            self.rightMenu_PlaylistMusic.addLayout(layoutTrack)

    def hideRightMenu(self):
        self.rightMenu.hide()

    def showRightMenu(self):
        self.rightMenu.show()

    # Если и работает, но весьма не очень
    def startTrack(self):

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
    app = QtWidgets.QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())