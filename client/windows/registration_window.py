from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMainWindow, QFileDialog

from utils.image_functions import to_pixmap_from_file

SYS_IMG = 'src/images/sys_img'

REGISTRATION_FORM = 'forms/registrationForm.ui'


class RegistrationWindow(QMainWindow):
    def __init__(self, fabric):
        super().__init__()
        uic.loadUi(REGISTRATION_FORM, self)

        self.fabric = fabric

        self.image = None
        self.image_format = None

        self.initUI()

    def initUI(self):
        self.setFixedSize(450, 600)
        self.setWindowIcon(QIcon(f'{SYS_IMG}/icon.ico'))

        self.imagePlaceholder.resize(64, 64)

        icon = QPixmap(f'{SYS_IMG}/back_button.png')
        self.backBtn.setIcon(QIcon(icon))
        self.backBtn.clicked.connect(self.go_back)

        icon = QPixmap(f'{SYS_IMG}/load_image.png')
        self.addImageBtn.setIcon(QIcon(icon))
        self.addImageBtn.clicked.connect(self.add_image)

        self.registerBtn.clicked.connect(self.register)

    def go_back(self):
        self.close()
        self.fabric.create_login_window()

    def add_image(self):
        self.imagePlaceholder.clear()
        file_name = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '', 'Картинка (*.jpg *.png)')[0]
        if file_name:
            self.image = file_name
            self.image_format = file_name[file_name.rfind('.'):]

            self.imagePlaceholder.setPixmap(to_pixmap_from_file(file_name, 64))
        else:
            self.image = None
            self.image_format = None

    def register(self):
        self.status.setText('')
        login = self.loginInput.text()
        password = self.passwordInput.text()
        nickname = self.nicknameInput.text()

        if self.image and login and password and nickname:
            if not self.fabric.connection.check_login(login):
                self.status.setText('Этот логин уже занят.')
            elif not self.fabric.connection.check_nickname(nickname):
                self.status.setText('Этот ник уже занят.')
            else:
                self.fabric.connection.add_player(login, password, nickname, self.image, self.image_format)
                self.close()
                self.fabric.create_login_window()
        else:
            self.status.setText('Заполнены не все поля.')
