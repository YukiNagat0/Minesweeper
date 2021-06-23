import sys

import socket
import pickle

from utils.hashing_password import hash_password, pepper_password

from utils.image_functions import to_blob, get_existing_images_ids, save_image


# Статус коды:
# 0  - Проверка на наличие соединения с сервером
# 10 - Есть ли пользователь с логином login в БД
# 11 - Есть ли пользователь с никнеймом nickname в БД
# 12 - Регистрация пользователя
# 13 - Проверка пароля пользователя
# 14 - Получить все уровни сложности
# 15 - Добавление рекорда
# 16 - Получение списка рекордов


class Connection:
    """Класс, отвечающий за общение с сервером по сокету."""

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

        self.check_server_availability()

    def send_message_and_get_response(self, message):
        """Отправка запроса на сервер и получение ответа. Если соединение разорвалось - выход из программы."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.ip, self.port))
        except ConnectionError as e:
            print(f'Отсутствует подключение к серверу ({e}).')
            sys.exit(1)
        else:
            sock.sendall(message)
            response = sock.recv(40480)
            sock.close()
            return response

    def check_server_availability(self):
        """Проверка на наличие соединения с сервером."""
        request = {'status_code': 0}
        message = pickle.dumps(request)
        response = pickle.loads(self.send_message_and_get_response(message))

    def check_login(self, login):
        """Проверка на существование логина в базе данных."""
        request = {'status_code': 10, 'login': login}
        message = pickle.dumps(request)
        response = pickle.loads(self.send_message_and_get_response(message))
        return response

    def check_nickname(self, nickname):
        """Проверка на существование ника в базе данных."""
        request = {'status_code': 11, 'nickname': nickname}
        message = pickle.dumps(request)
        response = pickle.loads(self.send_message_and_get_response(message))
        return response

    def add_player(self, login, password, nickname, image, image_format):
        """Регистрация пользователя."""
        hashed_password, salt = hash_password(password)

        image_bytes = to_blob(image, 64)

        request = {'status_code': 12, 'login': login, 'hash': hashed_password, 'salt': salt,
                   'nickname': nickname, 'image': image_bytes, 'image_format': image_format}

        message = pickle.dumps(request)
        response = self.send_message_and_get_response(message)

    def check_password(self, login, password):
        """Возврат ника, хеша и соли пользователя."""
        peppered_password = pepper_password(password)
        request = {'status_code': 13, 'login': login, 'peppered_password': peppered_password}
        message = pickle.dumps(request)
        response = pickle.loads(self.send_message_and_get_response(message))
        return response

    def get_modes(self):
        """Получение списка сложностей."""
        request = {'status_code': 14}
        message = pickle.dumps(request)
        response = pickle.loads(self.send_message_and_get_response(message))
        modes = {mode_id: info for mode_id, *info in response}
        return modes

    def add_record(self, mode_id, player_id, time, date_time):
        """"Добавление рекорда"""
        request = {'status_code': 15, 'mode_id': mode_id, 'player_id': player_id, 'time': time, 'date_time': date_time}
        message = pickle.dumps(request)
        response = pickle.loads(self.send_message_and_get_response(message))

    def get_records(self, mode_id):
        """Получение списка рекордов. Загружаются только еще незагруженные фото (см. get_existing_images_ids).
        Много pickle.dumps(True) для синхронизации сокетов. Иначе, может оборваться соединение."""
        request = {'status_code': 16, 'mode_id': mode_id, 'existing_images_ids': get_existing_images_ids()}
        message = pickle.dumps(request)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.ip, self.port))
        sock.sendall(message)

        n_records = pickle.loads(sock.recv(1024))
        sock.sendall(pickle.dumps(True))  # Юзер отправил сообщение, что получил n_records

        records = list()
        for _ in range(n_records):
            record = pickle.loads(sock.recv(4096))
            records.append(record)

            sock.sendall(pickle.dumps(True))  # Юзер отправил сообщение, что получил рекорд
        sock.sendall(pickle.dumps(True))  # Юзер отправил сообщение, что получил все рекорды

        n_images = pickle.loads(sock.recv(1024))
        sock.sendall(pickle.dumps(True))  # Юзер отправил сообщение, что получил n_images еще не загруженных фото

        for _ in range(n_images):
            image_info = pickle.loads(sock.recv(51200))
            save_image(*image_info)  # см. image_functions.py: save_image.
            sock.sendall(pickle.dumps(True))  # Юзер отправил сообщение, что получил фото

        return records
