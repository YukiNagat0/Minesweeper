from PyQt5.QtGui import QFontDatabase

from utils.image_functions import save_image_and_get_pixmap

from windows.login_window import LoginWindow
from windows.registration_window import RegistrationWindow
from windows.game_window import GameWindow
from windows.records_window import RecordsWindow


class Fabric:
    """Класс, отвечающий за создание окон."""

    def __init__(self, connection):
        QFontDatabase.addApplicationFont('src/fonts/Montserrat-Regular.ttf')  # Загрузка шрифта
        self.connection = connection

        self.player_id = None
        self.player_nickname = None
        self.player_pixmap = None
        self.current_window = None

    def create_login_window(self):
        self.current_window = LoginWindow(self)
        self.current_window.show()

    def create_registration_window(self):
        self.current_window = RegistrationWindow(self)
        self.current_window.show()

    def create_game_window(self):
        self.current_window = GameWindow(self)
        self.current_window.show()

    def create_records_window(self):
        self.current_window = RecordsWindow(self)
        self.current_window.show()

    def set_player_info(self, player_id, player_nickname, player_image_id, player_image_bytes, player_image_format):
        """Заполнение информации о пользователе. Плюс сохранение его фото в дамп-файл (см img_functions.py)."""
        self.player_id = player_id
        self.player_nickname = player_nickname
        self.player_pixmap = save_image_and_get_pixmap(player_image_id, player_image_bytes, player_image_format)

    def clear_player_info(self):
        self.player_id = None
        self.player_nickname = None
        self.player_pixmap = None
