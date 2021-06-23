from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem

from utils.image_functions import get_id_and_filename

SYS_IMG = 'src/images/sys_img'

RECORDS_FORM = 'forms/recordsForm.ui'


class RecordsWindow(QMainWindow):
    def __init__(self, fabric):
        super().__init__()
        uic.loadUi(RECORDS_FORM, self)
        self.fabric = fabric

        self.initUI()

    def initUI(self):
        self.setFixedSize(800, 660)
        self.setWindowIcon(QIcon(f'{SYS_IMG}/icon.ico'))

        icon = QPixmap(f'{SYS_IMG}/back_button.png')
        self.backBtn.setIcon(QIcon(icon))
        self.backBtn.clicked.connect(self.go_back)

        self.imagePlaceholder.resize(64, 64)
        self.imagePlaceholder.setPixmap(self.fabric.player_pixmap)

        self.nickname.setText(self.fabric.player_nickname)

        modes = self.fabric.connection.get_modes()  # загрузка уровней сложности
        self.modesBox.addItem('Все')
        self.modesBox.addItem(modes[1][0])
        self.modesBox.addItem(modes[2][0])
        self.modesBox.addItem(modes[3][0])

        self.modesBox.setCurrentIndex(0)

        icon = QPixmap(f'{SYS_IMG}/reload.png')
        self.reloadBtn.setIcon(QIcon(icon))
        self.reloadBtn.clicked.connect(self.reload)

        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Сложность', 'Ник', 'Картинка', 'Время', 'Дата'])
        self.reload()

    def go_back(self):
        self.close()
        self.fabric.create_game_window()

    def reload(self):
        # Получение рекордов и сохранение еще не загруженных фото. (см. connection.py: get_records)
        records = self.fabric.connection.get_records(self.modesBox.currentIndex())

        id_and_filename = get_id_and_filename()

        self.table.setRowCount(0)
        for i, (mode_name, nickname, image_id, time, date) in enumerate(records):
            pixmap = QPixmap(id_and_filename[image_id])
            self.table.setRowCount(self.table.rowCount() + 1)

            mode_name_item = QTableWidgetItem(mode_name)
            mode_name_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 0, mode_name_item)

            nickname_item = QTableWidgetItem(nickname)
            nickname_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 1, nickname_item)

            image_item = QTableWidgetItem()
            image_item.setFlags(Qt.ItemIsEnabled)
            image_item.setData(Qt.DecorationRole, pixmap)
            self.table.setItem(i, 2, image_item)

            time_item = QTableWidgetItem(str(time))
            time_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 3, time_item)

            date_item = QTableWidgetItem(date[:date.rfind(':')])  # Отображение даты до минут. После : идут SS.mS
            date_item.setFlags(Qt.ItemIsEnabled)
            self.table.setItem(i, 4, date_item)

        self.table.resizeColumnToContents(4)
        self.table.resizeRowsToContents()
