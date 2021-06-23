import random

import time
from datetime import datetime

from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QUrl
from PyQt5.QtGui import QPixmap, QIcon, QColor, QPainter, QPalette, QBrush, QPen, QImage
from PyQt5.QtWidgets import QMainWindow, QWidget, QGridLayout, QMessageBox
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

SYS_IMG = 'src/images/sys_img'

ICON = f'{SYS_IMG}/icon.ico'

IMG_BOMB = QImage(f'{SYS_IMG}/bomb.png')
IMG_FLAG = QImage(f'{SYS_IMG}/flag.png')

NUM_COLORS = {
    1: QColor('#f44336'),
    2: QColor('#9C27B0'),
    3: QColor('#3F51B5'),
    4: QColor('#03A9F4'),
    5: QColor('#00BCD4'),
    6: QColor('#4CAF50'),
    7: QColor('#E91E63'),
    8: QColor('#FF9800')
}

STATUS_READY = 0
STATUS_PLAYING = 1
STATUS_FAILED = 2
STATUS_SUCCESS = 3

SOUNDS = 'src/sounds'

# У Qt очень плохой API для работы с аудио, поэтому ниже не очень красивый код.
CLICK = QMediaPlayer(flags=QMediaPlayer.LowLatency)
EXPLOSION = QMediaPlayer(flags=QMediaPlayer.LowLatency)
FLAG = QMediaPlayer(flags=QMediaPlayer.LowLatency)
GAME_OVER = QMediaPlayer(flags=QMediaPlayer.LowLatency)
GAME_WIN = QMediaPlayer(flags=QMediaPlayer.LowLatency)
MUSIC = QMediaPlayer(flags=QMediaPlayer.LowLatency)
UNFLAG = QMediaPlayer(flags=QMediaPlayer.LowLatency)

CLICK.setMedia(QMediaContent(QUrl.fromLocalFile(f'{SOUNDS}/click.wav')))
EXPLOSION.setMedia(QMediaContent(QUrl.fromLocalFile(f'{SOUNDS}/explosion.wav')))
FLAG.setMedia(QMediaContent(QUrl.fromLocalFile(f'{SOUNDS}/flag.wav')))
GAME_OVER.setMedia(QMediaContent(QUrl.fromLocalFile(f'{SOUNDS}/game_over.wav')))
GAME_WIN.setMedia(QMediaContent(QUrl.fromLocalFile(f'{SOUNDS}/game_win.wav')))
UNFLAG.setMedia(QMediaContent(QUrl.fromLocalFile(f'{SOUNDS}/unflag.wav')))

CLICK.setVolume(5)
EXPLOSION.setVolume(5)
FLAG.setVolume(5)
GAME_OVER.setVolume(5)
GAME_WIN.setVolume(5)
UNFLAG.setVolume(5)
# ---

GAME_FORM = 'forms/gameForm.ui'


class Cell(QWidget):
    """Класс-клетка. Содержит кастомные сигналы, метод для отрисовки и другие методы, необходимые для работы."""
    expandable = pyqtSignal(int, int)
    expandable_safe = pyqtSignal(int, int)
    clicked = pyqtSignal()
    flagged = pyqtSignal(bool)
    bomb_activation = pyqtSignal()

    def __init__(self, x, y):
        super().__init__()

        self.setFixedSize(QSize(20, 20))

        self.x = x
        self.y = y

        self.is_interactive = True

        self.is_mine = False
        self.adjacent_n = 0

        self.is_revealed = False
        self.is_flagged = False
        self.is_end = False

        self.update()

    def reset(self):
        self.is_interactive = True

        self.is_mine = False
        self.adjacent_n = 0

        self.is_revealed = False
        self.is_flagged = False
        self.is_end = False

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        r = event.rect()

        if self.is_revealed:
            color = self.palette().color(QPalette.Background)
            outer, inner = color, color
            if self.is_end or (self.is_flagged and not self.is_mine):
                inner = NUM_COLORS[1]
        else:
            outer, inner = Qt.gray, Qt.lightGray

        p.fillRect(r, QBrush(inner))
        pen = QPen(outer)
        pen.setWidth(1)
        p.setPen(pen)
        p.drawRect(r)

        if self.is_revealed:
            if self.is_mine:
                p.drawPixmap(r, QPixmap(IMG_BOMB))

            elif self.adjacent_n > 0:
                pen = QPen(NUM_COLORS[self.adjacent_n])
                p.setPen(pen)
                f = p.font()
                f.setBold(True)
                p.setFont(f)
                p.drawText(r, Qt.AlignCenter, str(self.adjacent_n))

        elif self.is_flagged:
            p.drawPixmap(r, QPixmap(IMG_FLAG))

    def toggle_flag(self):
        self.is_flagged = not self.is_flagged
        self.update()
        self.flagged.emit(self.is_flagged)

    def reveal_self(self):
        self.is_revealed = True
        self.update()

    def reveal(self):
        if not self.is_revealed:
            self.reveal_self()
            if self.adjacent_n == 0:
                self.expandable.emit(self.x, self.y)

            if self.is_mine:
                EXPLOSION.play()

                self.is_end = True
                self.bomb_activation.emit()
            else:
                CLICK.play()

    def click(self):
        if not self.is_revealed and not self.is_flagged:
            self.reveal()

    def mouseReleaseEvent(self, e):
        if self.is_interactive:
            self.clicked.emit()
            if e.button() == Qt.RightButton:
                if not self.is_revealed:
                    self.toggle_flag()
                else:
                    self.expandable_safe.emit(self.x, self.y)

            elif e.button() == Qt.LeftButton:
                self.click()
            self.clicked.emit()


class GameWindow(QMainWindow):
    def __init__(self, fabric):
        super().__init__()
        uic.loadUi(GAME_FORM, self)
        self.fabric = fabric

        self.MODES = self.fabric.connection.get_modes()  # загрузка уровней сложности с сервера
        self.easyModeBtn.setText(self.MODES[1][0])
        self.mediumModeBtn.setText(self.MODES[2][0])
        self.hardModeBtn.setText(self.MODES[3][0])

        self.current_mode = 2
        self.field_width = self.MODES[self.current_mode][1]
        self.field_height = self.MODES[self.current_mode][2]
        self.n_mines = self.MODES[self.current_mode][3]

        self.initUI()

    def initUI(self):
        self.setFixedSize(800, 660)
        self.setWindowIcon(QIcon(ICON))

        icon = QPixmap(f'{SYS_IMG}/back_button.png')
        self.backBtn.setIcon(QIcon(icon))
        self.backBtn.clicked.connect(self.go_back)

        self.imagePlaceholder.resize(64, 64)
        self.imagePlaceholder.setPixmap(self.fabric.player_pixmap)

        self.nickname.setText(self.fabric.player_nickname)

        self.easyModeBtn.clicked.connect(self.change_mode)
        self.mediumModeBtn.clicked.connect(self.change_mode)
        self.hardModeBtn.clicked.connect(self.change_mode)

        self.recordsBtn.clicked.connect(self.go_to_records)

        self._timer = QTimer()                          # Создание таймера, который каждую секунду
        self._timer.timeout.connect(self.update_timer)  # вызывает метод update_timer, который
        self._timer.start(1000)                         # обновляет время игры, если она начата

        self.grid = QGridLayout()
        self.grid.setSpacing(5)

        self.gameField.setLayout(self.grid)

        self.rebuild_grid()

    def go_back(self):
        self.fabric.clear_player_info()
        self.close()
        self.fabric.create_login_window()

    def go_to_records(self):
        self.close()
        self.fabric.create_records_window()

    def change_mode(self):
        mode_name = self.sender().text()
        mode = None
        for elem in self.MODES:
            if mode_name in self.MODES[elem]:
                mode = elem
                break

        if self.current_mode != mode:
            self.current_mode = mode
            self.field_width = self.MODES[self.current_mode][1]
            self.field_height = self.MODES[self.current_mode][2]
            self.n_mines = self.MODES[self.current_mode][3]

            self.rebuild_grid()
        else:
            self.button_pressed()

    def rebuild_grid(self):
        """Перестройка игрового поля."""
        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)

        self.init_map()
        self.update_status(STATUS_READY)

        self.n_mines = self.MODES[self.current_mode][3]
        self.flagsLeftCnt.display(self.n_mines)
        self.timeCnt.display(0)

    def init_map(self):
        """Создание игрового поля."""
        for x in range(0, self.field_width):
            for y in range(0, self.field_height):
                w = Cell(x, y)
                self.grid.addWidget(w, y, x)

                # связывание кастомных сигналов с методами
                w.clicked.connect(self.trigger_start)
                w.expandable.connect(self.expand_reveal)
                w.expandable_safe.connect(self.expand_reveal_if_looks_safe)
                w.flagged.connect(self.flag_toggled)
                w.bomb_activation.connect(self.game_over)

    def reset_map(self, start_x: int, start_y: int):
        """Очищение игрового поля и заполнение минами.
        Args:
            start_x: координата первого клика по иксу
            start_y: координата первого клика по игреку
        """
        def get_adjacency_n(x, y):
            """Получение соседей-мин"""
            positions = [w for _, _, w in self.get_surrounding(x, y)]
            n_mines = sum(1 if w.is_mine else 0 for w in positions)

            return n_mines

        self.n_mines = self.MODES[self.current_mode][3]
        self.flagsLeftCnt.display(self.n_mines)
        self.timeCnt.display(0)

        # Очистка клеток
        for _, _, w in self.get_all():
            w.reset()

        # список с позициями клеток с минами
        positions = []
        while len(positions) < self.n_mines:
            x, y = random.randint(0, self.field_width - 1), random.randint(0, self.field_height - 1)
            if (x, y) not in positions and not (x == start_x and y == start_y):
                w = self.grid.itemAtPosition(y, x).widget()
                w.is_mine = True
                positions.append((x, y))

        # заполнение клеток количеством соседей-мин
        for x, y, w in self.get_all():
            w.adjacent_n = get_adjacency_n(x, y)

        # Первая клетка не может быть миной.
        no_adjacent = [(x, y, w) for x, y, w in self.get_all() if not w.adjacent_n and not w.is_mine]
        idx = random.randint(0, len(no_adjacent) - 1)
        x, y, w = no_adjacent[idx]

        for _, _, w in self.get_surrounding(start_x, start_y):
            if not w.is_mine:
                w.click()

    def get_all(self):
        for x in range(0, self.field_width):
            for y in range(0, self.field_height):
                yield x, y, self.grid.itemAtPosition(y, x).widget()

    def get_surrounding(self, x, y):
        positions = []

        for xi in range(max(0, x - 1), min(x + 2, self.field_width)):
            for yi in range(max(0, y - 1), min(y + 2, self.field_height)):
                positions.append((xi, yi, self.grid.itemAtPosition(yi, xi).widget()))

        return positions

    def button_pressed(self):
        if self.status == STATUS_PLAYING:
            self.update_status(STATUS_FAILED)
            self.reveal_map()

        elif self.status in (STATUS_FAILED, STATUS_SUCCESS):
            self.update_status(STATUS_READY)
            self.rebuild_grid()

    def reveal_map(self):
        for _, _, w in self.get_all():
            # Не открывать корректные флаги
            if not (w.is_flagged and w.is_mine):
                w.reveal_self()

    def get_revealable_around(self, x, y, force=False):
        for xi, yi, w in self.get_surrounding(x, y):
            if (force or not w.is_mine) and not w.is_flagged and not w.is_revealed:
                yield xi, yi, w

    def expand_reveal(self, x, y, force=False):
        for _, _, w in self.get_revealable_around(x, y, force):
            w.reveal()

    def determine_revealable_around_looks_safe(self, x, y, existing):
        flagged_count = 0
        for _, _, w in self.get_surrounding(x, y):
            if w.is_flagged:
                flagged_count += 1
        w = self.grid.itemAtPosition(y, x).widget()
        if flagged_count == w.adjacent_n:
            for xi, yi, w in self.get_revealable_around(x, y, True):
                if (xi, yi) not in ((xq, yq) for xq, yq, _ in existing):
                    existing.append((xi, yi, w))
                    self.determine_revealable_around_looks_safe(xi, yi, existing)

    def expand_reveal_if_looks_safe(self, x, y):
        reveal = []
        self.determine_revealable_around_looks_safe(x, y, reveal)
        for _, _, w in reveal:
            w.reveal()

    def trigger_start(self, *args):
        if self.status == STATUS_READY:
            # Первый клик
            sender = self.sender()
            x, y = sender.x, sender.y
            self.reset_map(x, y)
            self.update_status(STATUS_PLAYING)
            # Запуск отсчета таймера
            self._timer_start_nsecs = int(time.time())
        elif self.status == STATUS_PLAYING:
            self.check_win_condition()

    def update_status(self, status):
        self.status = status
        if self.status == STATUS_SUCCESS:
            self.fabric.connection.add_record(self.current_mode, self.fabric.player_id,
                                              int(self.timeCnt.value()), datetime.now())  # Добавление рекорда
            for _, _, w in self.get_all():
                w.is_interactive = False

            GAME_WIN.play()

            msg_box = QMessageBox()
            msg_box.setText(f'Поздравляем! Вы справились за {int(self.timeCnt.value())} секунд.')
            msg_box.setInformativeText('Хотите начать новую игру?')
            msg_box.setWindowTitle('Minesweeper')
            msg_box.setWindowIcon(QIcon(ICON))
            msg_box.setStyleSheet('background: #3b404e; font-family: Montserrat; color: #ffffff; font-size: 14px')

            yes_button = msg_box.addButton('Да!', QMessageBox.YesRole)
            no_button = msg_box.addButton('Нет.', QMessageBox.NoRole)

            msg_box.exec()

            if msg_box.clickedButton() == yes_button:
                self.button_pressed()
        elif self.status == STATUS_FAILED:
            GAME_OVER.play()

    def update_timer(self):
        if self.status == STATUS_PLAYING:
            n_secs = int(time.time()) - self._timer_start_nsecs
            self.timeCnt.display(n_secs)

    def game_over(self):
        self.reveal_map()
        self.update_status(STATUS_FAILED)

    def flag_toggled(self, flagged):
        adjustment = -1 if flagged else 1
        if self.n_mines + adjustment < 0:  # Чтобы не уходило в минус.
            cell: Cell = self.sender()
            cell.is_flagged = False
            cell.update()
        else:
            if adjustment < 0:
                FLAG.play()
            else:
                UNFLAG.play()

            self.n_mines += adjustment
            self.flagsLeftCnt.display(self.n_mines)
            # self.check_win_condition()

    def check_win_condition(self):
        if self.n_mines == 0:
            if all(w.is_revealed or w.is_flagged for _, _, w in self.get_all()):
                self.update_status(STATUS_SUCCESS)
        else:
            unrevealed = []
            for _, _, w in self.get_all():
                if not w.is_revealed and not w.is_flagged:
                    unrevealed.append(w)
                    if len(unrevealed) > self.n_mines or not w.is_mine:
                        return
            if len(unrevealed) == self.n_mines:
                if all(w.is_flagged == w.is_mine or w in unrevealed for _, _, w in self.get_all()):
                    for w in unrevealed:
                        w.toggle_flag()
                    self.update_status(STATUS_SUCCESS)
