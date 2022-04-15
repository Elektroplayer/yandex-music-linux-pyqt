import datetime
import requests

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QObject, pyqtSignal  # , QThread # Это может понадобиться позже
from PyQt5.QtGui import QIcon, QPixmap, QFont, QImage, QCursor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
# from multiprocessing.dummy import Pool as ThreadPool  # Это может понадобиться позже
from gi.repository import Gio
from yandex_music import Client

from windows.LoginDialog import LoginDialog
from windows.models.MainWindowModel import Ui_MainWindow

month = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']  # Массив с месяцами в нужном падеже


# Переводит миллисекунды в минуты и секунды
def time_convert(ms):
    seconds = (ms / 1000) % 60
    minutes = (ms / (1000 * 60)) % 60

    return int(seconds), int(minutes)


class Playlist:
    def __init__(self, playlist, parent):
        self.playlist = playlist
        self.parent = parent
        self.qtplaylist = None

        # Получаем ID треков
        tracks_id = []
        for track in self.playlist.data.tracks:
            tracks_id.append(track.id)

        # Получаем о них всю информацию
        self.tracks = self.parent.YMClient.tracks(tracks_id)

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
        self.widget = QtWidgets.QWidget(parent.scrollAreaWidgetContents)
        self.widget.setObjectName(playlist.type + "PlaylistWidget")
        self.widget.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        self.widget.setStyleSheet("QWidget:hover { background-color: palette(window) }")
        self.widget.mouseReleaseEvent = self.playlist_clicked_decorator  # self.printText1(self, playlist)

        # Далее layout в widget
        layout = QtWidgets.QVBoxLayout(self.widget)
        layout.setObjectName(playlist.type + "PlaylistWidgetLayout")

        # Картинку загружаем по ссылке
        image = QImage()
        image.loadFromData(requests.get('http://' + img).content)

        # Создаём label с картинкой
        image_label = QtWidgets.QLabel(parent.scrollAreaWidgetContents)
        image_label.setMinimumSize(QtCore.QSize(200, 200))
        image_label.setMaximumSize(QtCore.QSize(200, 200))
        image_label.setPixmap(QPixmap(image))
        image_label.setObjectName(playlist.type + "_PlaylistImage")
        layout.addWidget(image_label)

        # Label с именем
        label_name = QtWidgets.QLabel(parent.scrollAreaWidgetContents)
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
        label_description = QtWidgets.QLabel(parent.scrollAreaWidgetContents)
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
        label_reloaded = QtWidgets.QLabel(parent.scrollAreaWidgetContents)
        label_reloaded.setMaximumSize(QtCore.QSize(200, 25))
        label_reloaded.setIndent(5)
        label_reloaded.setObjectName(playlist.type + '_PlaylistReloaded')
        label_reloaded.setText("Обновлён " + mod_time)
        layout.addWidget(label_reloaded)

    def playlist_clicked_decorator(self, event):
        # Устанавливаем имя плейлиста
        self.parent.rightMenu_PlaylistName.setText(self.playlist.data.title)

        # Удаляем все элементы в меню
        self.parent.clear_layout(self.parent.rightMenu_PlaylistMusic)

        # Показываем левое меню
        self.parent.show_right_menu()

        # Добавляем каждый трек в общий layout
        for track in self.tracks:
            name = track.title
            if len(track.artists) == 0:
                authors = ''
            else:
                authors = track.artists[0].name

            layout_track = QtWidgets.QHBoxLayout()
            layout_track.setObjectName(str(track.id) + "_Track")
            layout_track_play_button = QtWidgets.QPushButton(self.parent.scrollAreaWidgetContents_2)
            layout_track_play_button.setMaximumSize(QtCore.QSize(30, 30))
            layout_track_play_button.setObjectName(str(track.id) + "_PlayButton")
            layout_track_play_button.setIcon(self.parent.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
            layout_track_play_button.clicked.connect(self.music_in_playlist_clicked_decorator(track))
            layout_track.addWidget(layout_track_play_button)
            layout_track_track_author_name = QtWidgets.QLabel(self.parent.scrollAreaWidgetContents_2)
            layout_track_track_author_name.setTextFormat(QtCore.Qt.MarkdownText)
            layout_track_track_author_name.setObjectName(str(track.id) + "_TrackAuthorName")
            layout_track_track_author_name.setText("**" + authors + "** - " + name)
            layout_track.addWidget(layout_track_track_author_name)
            layout_track_like_button = QtWidgets.QPushButton(self.parent.scrollAreaWidgetContents_2)
            layout_track_like_button.setMaximumSize(QtCore.QSize(30, 30))
            layout_track_like_button.setObjectName(str(track.id) + "_LikeButton")
            layout_track_like_button.setText("like")
            layout_track.addWidget(layout_track_like_button)
            self.parent.rightMenu_PlaylistMusic.addLayout(layout_track)

    def generate_qtplaylist(self):
        self.qtplaylist = QMediaPlaylist(self.parent.player)

        for track in self.playlist.data.tracks:
            self.qtplaylist.addMedia(QMediaContent(QtCore.QUrl(self.parent.YMClient.tracks_download_info(track.id, True)[0].direct_link)))

    # Декоратор клика на музыку внутри плейлиста
    def music_in_playlist_clicked_decorator(self, track):
        #self.current_playlist = playlist

        def out_func(event):
            self.music_in_playlist_clicked(track)

        return out_func

    # Сама функция клика на музыку внутри плейлиста
    def music_in_playlist_clicked(self, track):

        # self.parent.play_audio_file(track.id)
        # self.play_playlist()

        index = 0
        for i in range(len(self.playlist.data.tracks)):
            if str(self.playlist.data.tracks[i].id) == str(track.id):
                index = i
                break

        if self.qtplaylist is None:
            self.generate_qtplaylist()

        self.parent.update_music_data(track, self.qtplaylist)

        self.parent.player.setPlaylist(self.qtplaylist)
        self.parent.player.playlist().setCurrentIndex(index)
        self.parent.player.play()

        self.parent.player.playlist().currentIndexChanged.connect(self.index_changed)

    def index_changed(self, position):
        self.parent.update_music_data(self.tracks[position], self.qtplaylist)


# class Worker(QObject):
#     finished = pyqtSignal()
#     progress = pyqtSignal(int)
#
#     def run_decorator(self):
#         pass
#         def run ():
#
#         """Long-running task."""
#         for i in range(5):
#             sleep(1)
#             self.progress.emit(i + 1)
#         self.finished.emit()

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
        self.nextButton.clicked.connect(self.next_music)
        self.prevButton.clicked.connect(self.prev_music)

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

        # Переменные текущих треков
        self.track = None
        self.qtplaylist = None

        # Инициализируем плейлисты пользователя. Пока что только сгенерированные.
        self.playlist_init()

    def next_music(self, event):
        """Запустить следующий трек"""

        if not (self.qtplaylist is None):
            self.qtplaylist.next()

            if self.qtplaylist.currentIndex() == -1:
                self.qtplaylist.setCurrentIndex(0)

    def prev_music(self, event):
        """Запустить предыдущий трек"""

        if not (self.qtplaylist is None):
            self.qtplaylist.previous()

            if self.qtplaylist.currentIndex() == -1:
                self.qtplaylist.setCurrentIndex(0)

    def play_pause(self):
        """Остановить или продолжить воспроизведение"""

        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def position_changed(self, position):
        """Сигнал изменения позиции на скролбаре"""

        seconds, minutes = time_convert(position)
        self.leastenMusic.setText(f'{minutes}:{seconds:02}')
        self.musicSlider.setValue(position)

    def position_change(self, position):
        """Изменение позиции на скролбаре пользователем"""

        self.player.setPosition(position)

    #
    def duration_changed(self, duration):
        """Сигнал изменения длительности.
        Когда начинается новый трек, длительность в специальном layout меняется."""

        seconds, minutes = time_convert(duration)
        self.durationMusic.setText(f'{minutes}:{seconds:02}')
        self.musicSlider.setRange(0, duration)

    def player_state_changed(self, state):
        """Сигнал изменения состояния плеера.
        Меняет иконку кнопки "старт-стоп" """

        if self.player.state() == QMediaPlayer.PlayingState:
            self.startStopButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        else:
            self.startStopButton.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

    def play_audio_file(self, track_id):
        """Проигрывает трек, указанный в аргументе"""

        url = QtCore.QUrl(self.YMClient.tracks_download_info(track_id, True)[0].direct_link)
        content = QMediaContent(url)

        self.player.setMedia(content)
        self.player.play()

    def update_music_data(self, track, playlist):
        """Обновляет информацию о треке в футере"""

        image = QImage()
        image.loadFromData(requests.get('http://' + track.og_image.replace('%%', '50x50')).content)

        self.MusicName.setText(track.title)
        self.MusicAuthor.setText(track.artists[0].name)
        self.ImageMusic.setPixmap(QPixmap(image))

        self.track = track.id
        self.qtplaylist = playlist

    def get_token(self):
        """Получение токена аккаунта яндекс.музыки"""

        # Изымаем его
        token = self.settings.get_string('token')

        # Если токена нет
        if token == '':
            dlg = LoginDialog()  # Запускаем диалог для его получения
            dlg.exec()

            self.settings.set_string('token', dlg.token)  # Записываем в схему

            # token = dlg.token

        return token or dlg.token  # Возвращаем токен

    def playlist_init(self):
        """Инициализация сгенерированных плейлистов"""

        playlists = self.YMClient.feed().generated_playlists  # Получаем плейлисты

        for playlist in playlists:

            # Создаём виджет из класса
            widget = Playlist(playlist, self)

            # Добавляем виджет к "главному" layout
            self.horizontalLayout_5.addWidget(widget.widget)

            # И к нему добавляем небольшой спэйсер
            spacer_item2 = QtWidgets.QSpacerItem(10, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
            self.horizontalLayout_5.addItem(spacer_item2)

    def clear_layout(self, layout):
        """Очищает указанный layout"""

        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self.clear_layout(child.layout())

    def hide_right_menu(self):
        """Скрыть правое меню"""

        self.rightMenu.hide()

    def show_right_menu(self):
        """Показать правое меню"""

        self.rightMenu.show()
