import datetime
import requests
import threading

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap, QFont, QImage, QCursor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from gi.repository import Gio
from yandex_music import Client

from windows.LoginDialog import LoginDialog
from windows.models.MainWindowModel import Ui_MainWindow


# Переводит миллисекунды в минуты и секунды
def time_convert(ms):
    seconds = (ms / 1000) % 60
    minutes = (ms / (1000 * 60)) % 60

    return int(seconds), int(minutes)


# Создание главного класса
class Window(QtWidgets.QMainWindow, Ui_MainWindow):

    # Инициализируем всё, что нужно
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # Это можно были сделать и в файле MainWindowModel.py, но тк он часто меняется, я это пожалуй оставлю пока что тут
        self.setGeometry(300, 220, 1220, 650)
        self.setMinimumSize(QtCore.QSize(580, 400))
        self.setWindowTitle('Yandex.Music')
        self.setWindowIcon(QIcon('./src/images/logo.svg'))

        # Устанавливаем иконки
        self.startStopButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.prevButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipBackward))
        self.nextButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaSkipForward))

        # Скрываем правое меню
        self.rightMenu.hide()

        # Подключаем к кнопкам их функции
        self.startStopButton.clicked.connect(self.play_pause)
        self.rightMenu_Hide.clicked.connect(self.hide_right_menu)
        self.musicSlider.sliderMoved.connect(self.position_change)

        # Создаём схемы для сохранения токена
        schema_source = Gio.SettingsSchemaSource.new_from_directory('./src/', Gio.SettingsSchemaSource.get_default(), False)
        schema = schema_source.lookup('com.github.vitaly.yandex-music-pyqt', False)
        self.settings = Gio.Settings.new_full(schema, None, None)

        # Запускаем функцию получения токена
        token = self.get_token()

        # Инициализируем YMClient с полученным токеном
        self.YMClient = Client(token).init()

        # Настраиваем проигрыватель
        self.player = QMediaPlayer()
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.stateChanged.connect(self.player_state_changed)

        # Настройка плейлиста
        self.playlist = None  # QMediaPlaylist(self.player)
        # self.player.setPlaylist(self.playlist)

        # Пока что бесполезные переменные
        self.track = "10994777:1193829"

        # self.trackLink = ""
        # self.playingStatus = False

        # Инициализируем плейлисты пользователя. Пока что только сгенерированные.
        self.playlist_init()

    # Остановить или продолжить
    def play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    # Если позиция на скроллбаре изменилась
    def position_changed(self, position):
        seconds, minutes = time_convert(position)
        self.leastenMusic.setText(f'{minutes}:{seconds:02}')
        self.musicSlider.setValue(position)

    # Если позицию на скроллбаре изменили
    def position_change(self, position):
        self.player.setPosition(position)

    # Если длительности изменилась
    def duration_changed(self, duration):
        seconds, minutes = time_convert(duration)
        self.durationMusic.setText(f'{minutes}:{seconds:02}')
        self.musicSlider.setRange(0, duration)

    # Активируется, когда изменяется состояние плеера (типа воспроизводит или нет)
    # Меняет иконку кнопки
    def player_state_changed(self, state):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.startStopButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        else:
            self.startStopButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

    # Проигрывает трек, указанный в аргументе
    def play_audio_file(self, track_id=None):
        url = QtCore.QUrl(self.YMClient.tracks_download_info(track_id, True)[0].direct_link)
        content = QMediaContent(url)

        self.player.setMedia(content)
        self.player.play()

    def play_playlist(self, playlist, index=0):
        # playlist.data.tracks[0].id

        # qtplaylist = QMediaPlaylist(self.player)
        # url =
        # self.playlist.addMedia(QMediaContent(QtCore.QUrl(self.YMClient.tracks_download_info(playlist.data.tracks[0].id, True)[0].direct_link)))
        # self.playlist.addMedia(QMediaContent(QtCore.QUrl(self.YMClient.tracks_download_info(playlist.data.tracks[1].id, True)[0].direct_link)))

        # self.player.setPlaylist(qtplaylist)
        # self.player.playlist().setCurrentIndex(0)

        self.playlist = QMediaPlaylist(self.player)

        # thread = threading.Thread(target=self.add_track_to_qtplaylist, args=(playlist))
        # thread.start()

        for track in playlist.data.tracks:
            self.playlist.addMedia(QMediaContent(QtCore.QUrl(self.YMClient.tracks_download_info(track.id, True)[0].direct_link)))

        self.playlist.setCurrentIndex(index)
        self.player.play()

    # def add_track_to_qtplaylist(self, playlist):
    #     print(1)


    # Получает токен
    def get_token(self):
        # Изымаем его
        token = self.settings.get_string('token')

        # Если токена нет
        if token == '':
            dlg = LoginDialog()  # Запускаем диалог для его получения
            dlg.exec()

            self.settings.set_string('token', dlg.token)  # Записываем в схему

            # token = dlg.token

        return token or dlg.token  # Возвращаем токен

    # Инициализация сгенерированных плейлистов
    def playlist_init(self):
        playlists = self.YMClient.feed().generated_playlists  # Получаем плейлисты
        month = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября',
                 'ноября', 'декабря']  # Массив с месяцами в нужном падеже

        for playlist in playlists:
            img = playlist.data.cover.uri.replace('%%', '200x200')  # Получаем картинку
            title = playlist.data.title  # Имя
            description = playlist.data.description  # Описание
            time = playlist.data.modified  # Время обновления
            cur_time = str(datetime.datetime.now())[:10]  # Текущее время

            # Получаем "хорошее" время
            if time[:10] == cur_time:
                mod_time = 'сегодня'
            elif int(cur_time[8:10]) - int(time[8:10]) == 1:
                mod_time = 'вчера'
            else:
                mod_time = time[8:10] + ' ' + month[int(time[5:7]) - 1]

            # Создаём виджет плейлиста
            widget = QtWidgets.QWidget(self.scrollAreaWidgetContents)
            widget.setObjectName(playlist.type + "PlaylistWidget")
            widget.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
            widget.setStyleSheet("QWidget:hover { background-color: palette(window) }")
            widget.mouseReleaseEvent = self.playlist_clicked_decorator(playlist)  # self.printText1(self, playlist)

            # Далее layout в widget
            layout = QtWidgets.QVBoxLayout(widget)
            layout.setObjectName(playlist.type + "PlaylistWidgetLayout")

            # Картинку загружаем по ссылке
            image = QImage()
            image.loadFromData(requests.get('http://' + img).content)

            # Создаём label с картинкой
            image_label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
            image_label.setMinimumSize(QtCore.QSize(200, 200))
            image_label.setMaximumSize(QtCore.QSize(200, 200))
            image_label.setPixmap(QPixmap(image))
            image_label.setObjectName(playlist.type + "_PlaylistImage")
            layout.addWidget(image_label)

            # Label с именем
            label_name = QtWidgets.QLabel(self.scrollAreaWidgetContents)
            label_name.setMinimumSize(QtCore.QSize(200, 0))
            label_name.setMaximumSize(QtCore.QSize(200, 25))
            font = QFont()
            font.setBold(True)
            font.setWeight(75)
            label_name.setFont(font)
            label_name.setIndent(5)
            label_name.setObjectName(playlist.type + '_PlaylistName')
            label_name.setText(title)
            layout.addWidget(label_name)

            # Label с описанием
            label_description = QtWidgets.QLabel(self.scrollAreaWidgetContents)
            size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
            size_policy.setHorizontalStretch(0)
            size_policy.setVerticalStretch(0)
            size_policy.setHeightForWidth(label_description.sizePolicy().hasHeightForWidth())
            label_description.setSizePolicy(size_policy)
            label_description.setMaximumSize(QtCore.QSize(200, 16777215))
            label_description.setTextFormat(QtCore.Qt.AutoText)
            label_description.setWordWrap(True)
            label_description.setIndent(5)
            label_description.setObjectName(playlist.type + '_PlaylistDescription')
            label_description.setText(description)
            layout.addWidget(label_description)

            # Label "когда обновлён плейлист"
            label_reloaded = QtWidgets.QLabel(self.scrollAreaWidgetContents)
            label_reloaded.setMaximumSize(QtCore.QSize(200, 25))
            label_reloaded.setIndent(5)
            label_reloaded.setObjectName(playlist.type + '_PlaylistReloaded')
            label_reloaded.setText("Обновлён " + mod_time)
            layout.addWidget(label_reloaded)

            # Добавляем виджет к "главному" layout
            self.horizontalLayout_5.addWidget(widget)

            # И к нему добавляем небольшой спэйсер
            spacer_item2 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
            self.horizontalLayout_5.addItem(spacer_item2)

    # Очистка layout
    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self.clear_layout(child.layout())

    # Декоратор клика на музыку внутри плейлиста
    def music_in_playlist_clicked_decorator(self, track, playlist):
        #self.current_playlist = playlist

        def out_func():
            self.music_in_playlist_clicked(track, playlist)

        return out_func

    # Сама функция клика на музыку внутри плейлиста
    def music_in_playlist_clicked(self, track, playlist):
        image = QImage()
        image.loadFromData(requests.get('http://' + track.og_image.replace('%%', '50x50')).content)

        self.MusicName.setText(track.title)
        self.MusicAuthor.setText(track.artists[0].name)
        self.ImageMusic.setPixmap(QPixmap(image))
        #self.play_audio_file(track.id)
        self.play_playlist(playlist)

    # Декоратор, цель которого только запомнить, с каким плейлистом устанавливалась функция
    def playlist_clicked_decorator(self, playlist):

        def out_func(event):

            self.playlist_clicked(playlist)  # playlist

        return out_func

    # При клике на плейлист создаём правое меню и вставляет треки выбранного плейлиста
    def playlist_clicked(self, playlist):
        # Устанавливаем имя плейлиста
        self.rightMenu_PlaylistName.setText(playlist.data.title)

        # Удаляем все элементы в меню
        self.clear_layout(self.rightMenu_PlaylistMusic)

        # Показываем левое меню
        self.show_right_menu()

        # Получаем ID треков
        tracks_id = []
        for track in playlist.data.tracks:
            tracks_id.append(track.id)

        # Получаем о них всю информацию
        tracks = self.YMClient.tracks(tracks_id)

        # Добавляем каждый трек в общий layout
        for track in tracks:
            name = track.title
            authors = track.artists[0].name

            layout_track = QtWidgets.QHBoxLayout()
            layout_track.setObjectName(str(track.id) + "_Track")
            layout_track_play_button = QtWidgets.QPushButton(self.scrollAreaWidgetContents_2)
            layout_track_play_button.setMaximumSize(QtCore.QSize(30, 30))
            layout_track_play_button.setObjectName(str(track.id) + "_PlayButton")
            layout_track_play_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
            layout_track_play_button.clicked.connect(self.music_in_playlist_clicked_decorator(track, playlist))
            layout_track.addWidget(layout_track_play_button)
            layout_track_track_author_name = QtWidgets.QLabel(self.scrollAreaWidgetContents_2)
            layout_track_track_author_name.setTextFormat(QtCore.Qt.MarkdownText)
            layout_track_track_author_name.setObjectName(str(track.id) + "_TrackAuthorName")
            layout_track_track_author_name.setText("**" + authors + "** - " + name)
            layout_track.addWidget(layout_track_track_author_name)
            layout_track_like_button = QtWidgets.QPushButton(self.scrollAreaWidgetContents_2)
            layout_track_like_button.setMaximumSize(QtCore.QSize(30, 30))
            layout_track_like_button.setObjectName(str(track.id) + "_LikeButton")
            layout_track_like_button.setText("like")
            layout_track.addWidget(layout_track_like_button)
            self.rightMenu_PlaylistMusic.addLayout(layout_track)

    # Скрыть правое меню
    def hide_right_menu(self):
        self.rightMenu.hide()

    # Показать правое меню
    def show_right_menu(self):
        self.rightMenu.show()

