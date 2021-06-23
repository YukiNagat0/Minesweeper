import sys
from PyQt5.QtWidgets import QApplication

from fabric import Fabric
from connection import Connection

IP, PORT = 'localhost', 25665  # Если запускать сервер на другом ПК, нужно менять localhost на реальный ip.


def main():
    connection = Connection(IP, PORT)

    app = QApplication(sys.argv)
    fabric = Fabric(connection)
    fabric.create_login_window()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
