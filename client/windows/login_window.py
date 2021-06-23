from PyQt5 import uic
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow

SYS_IMG = 'src/images/sys_img'

LOGIN_FORM = 'forms/loginForm.ui'


class LoginWindow(QMainWindow):
    def __init__(self, fabric):
        super().__init__()
        uic.loadUi(LOGIN_FORM, self)
        self.fabric = fabric

        self.initUI()

    def initUI(self):
        self.setFixedSize(450, 600)
        self.setWindowIcon(QIcon(f'{SYS_IMG}/icon.ico'))

        self.loginBtn.clicked.connect(self.log_in)

        self.registerBtn.clicked.connect(self.show_registration_form)

    def show_registration_form(self):
        self.close()
        self.fabric.create_registration_window()

    def log_in(self):
        self.status.setText('')

        login = self.loginInput.text()
        password = self.passwordInput.text()

        if login and password:
            if self.fabric.connection.check_login(login):  # Если пользователя с логином login не существует -
                self.status.setText('Неверный логин.')     # возвращается True. Т.е. логин неверный.
            else:  # Пользователь с логином login существует.
                player_info = self.fabric.connection.check_password(login, password)
                if not player_info:  # В случае, если пароль неверный, возвращается False
                    self.status.setText('Неверный пароль.')
                else:  # Иначе кортеж из ника и изображения
                    self.fabric.set_player_info(*player_info)  # см. fabric.py: set_player_info
                    self.close()
                    self.fabric.create_game_window()
        else:
            self.status.setText('Заполнены не все поля.')
