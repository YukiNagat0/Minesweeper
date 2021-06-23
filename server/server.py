from loguru import logger

import threading
import socketserver

import pickle
from time import sleep

import sqlite3

import bcrypt

IP, PORT = '0.0.0.0', 25665
DATABASE = 'db/Minesweeper.sqlite'

# Конфигурация logger'а. Rotation каждую неделю, сжатие в zip.
logger.add('logs/log.log', format='{time} | {level} | {message}', rotation='1 week',
           compression='zip', encoding='UTF-8')


def hash_password_on_server(peppered_password, salt):
    """Функция для проверки совпадения пароля. (см. request['status_code'] == 13)."""
    hashed_password = bcrypt.hashpw(peppered_password, salt)
    return hashed_password


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    """Класс-handler, который принимает и отправляет сообщения."""

    @logger.catch  # Перехват всех ошибок в logger
    def handle(self):
        is_big = False
        message = None  # Message для logger'а

        con = sqlite3.connect(DATABASE)
        cur = con.cursor()

        request = self.request.recv(40480)

        request = pickle.loads(request)
        if request['status_code'] == 0:  # Проверка на наличие соединения с сервером
            message = 'New connection.'
            response = True

        elif request['status_code'] == 10:  # Проверка логина
            login = request['login']

            res = cur.execute(f"""
            SELECT 1 FROM Player
            WHERE PlayerLogin = '{login}'
            """).fetchone()

            if not res:
                response = True
            else:
                response = False

        elif request['status_code'] == 11:  # Проверка ника
            nickname = request['nickname']

            res = cur.execute(f"""
            SELECT 1 FROM Player
            WHERE PlayerNickname = '{nickname}'
            """).fetchone()

            if not res:
                response = True
            else:
                response = False

        elif request['status_code'] == 12:  # Регистрация игрока
            login = request['login']
            hashed_password = sqlite3.Binary(request['hash'])
            salt = sqlite3.Binary(request['salt'])
            nickname = request['nickname']
            image = request['image']
            image_format = request['image_format']

            message = f'New player [{login}] registered.'

            image = sqlite3.Binary(image)

            cur.execute(f"""
            INSERT INTO Avatar(AvatarImage, AvatarImageFormat) VALUES(?, '{image_format}')
            """, (image,))

            (avatar_id,) = cur.execute("""
            SELECT MAX(AvatarId) FROM Avatar
            """).fetchone()

            cur.execute(f"""
            INSERT INTO Player(PlayerLogin, PlayerHash, PlayerSalt, PlayerNickname, PlayerAvatarId)
            VALUES('{login}', ?, ?, '{nickname}', {avatar_id})
            """, (hashed_password, salt))

            con.commit()
            response = True

        elif request['status_code'] == 13:  # Проверка пароля
            login = request['login']
            peppered_password = request['peppered_password']
            player_id, salt, player_hash = cur.execute(f"""
            SELECT PlayerId, PlayerSalt, PlayerHash FROM Player
            WHERE PlayerLogin = '{login}'
            """).fetchone()

            password_hash = hash_password_on_server(peppered_password, salt)
            if password_hash != player_hash:
                response = False
            else:
                nickname, image_id = cur.execute(f"""
                SELECT PlayerNickname, PlayerAvatarId FROM Player
                WHERE PlayerId = {player_id}
                """).fetchone()
                image_bytes, image_format = cur.execute(f"""
                SELECT AvatarImage, AvatarImageFormat FROM Avatar
                WHERE AvatarId = {image_id}
                """).fetchone()

                message = f'Player [{login}] logged in.'
                response = (player_id, nickname, image_id, image_bytes, image_format)

        elif request['status_code'] == 14:  # Получение списка сложностей
            modes = cur.execute("""SELECT * FROM Mode""").fetchall()
            response = modes

        elif request['status_code'] == 15:  # Добавление рекорда
            mode_id = request['mode_id']
            player_id = request['player_id']
            time = request['time']
            date_time = request['date_time']

            message = f'New record [{player_id}]: mode [{mode_id}] time [{time}] date_time [{date_time}].'

            cur.execute("""
            INSERT INTO Game(GameModeId, GamePlayerId, GameTime, GameDateTime)
            VALUES(?, ?, ?, ?)""", (mode_id, player_id, time, date_time))

            con.commit()
            response = True

        elif request['status_code'] == 16:  # Получение списка рекордов
            mode_id = request['mode_id']
            existing_images_ids = request['existing_images_ids']

            if not mode_id:  # Все рекорды. Отсортированы по дате в обратном порядке (сначала новые рекорды).
                records = cur.execute("""
                SELECT M.ModeName, P.PlayerId, P.PlayerNickname, A.AvatarId, G.GameTime, G.GameDateTime
                FROM Game G
                JOIN Mode M ON G.GameModeId = M.ModeId
                JOIN Player P ON G.GamePlayerId = P.PlayerId
                JOIN Avatar A ON P.PlayerAvatarId = A.AvatarId
                ORDER BY G.GameDateTime DESC""").fetchall()
            else:  # Рекорды выбранной сложности. Отсортированы по игровому времени (самые быстрые).
                records = cur.execute("""
                SELECT M.ModeName, P.PlayerId, P.PlayerNickname, A.AvatarId, G.GameTime, G.GameDateTime
                FROM Game G
                JOIN Mode M ON (G.GameModeId = ? AND G.GameModeId = M.ModeId)
                JOIN Player P ON G.GamePlayerId = P.PlayerId
                JOIN Avatar A ON P.PlayerAvatarId = A.AvatarId
                ORDER BY G.GameTime""", (mode_id,)).fetchall()

            not_loaded_images = set()  # Добавление еще не загруженных фото по id.
            for elem in records:
                if elem[3] not in existing_images_ids:  # если AvatarId не в existing_images_ids
                    not_loaded_images.add(elem[3])

            # Список из AvatarId, AvatarImage, AvatarImageFormat. В нем только еще не загруженные фото.
            image_ids_images_and_formats = cur.execute(f"""
            SELECT A.AvatarId , A.AvatarImage, A.AvatarImageFormat FROM Avatar A
            JOIN Player P ON (P.PlayerAvatarId = A.AvatarId AND A.AvatarId IN 
            ({', '.join(str(elem) for elem in not_loaded_images)}))
            """).fetchall()

            records = list(map(lambda x: (x[0], x[2], x[3], x[4], x[5]), records))  # Удаляем из records id игроков.

            is_big = True
            message = f'Player downloaded {len(not_loaded_images)} images.'

        con.close()
        if not is_big:
            response = pickle.dumps(response)
            self.request.sendall(response)
        else:
            # Много self.request.recv(32) для синхронизации с юзером. Иначе, может разорваться соединение
            # (см. connection.py: get_records)
            n_records = len(records)
            self.request.sendall(pickle.dumps(n_records))
            self.request.recv(32)  # Юзер принял n_records

            for i in range(n_records):
                self.request.sendall(pickle.dumps(records[i]))
                self.request.recv(32)  # Юзер принял рекорд
            self.request.recv(32)  # Юзер принял все рекорды

            n_images = len(not_loaded_images)

            self.request.sendall(pickle.dumps(n_images))
            self.request.recv(32)  # Юзер принял n_images еще не загруженных фото

            for i in range(n_images):
                self.request.sendall(pickle.dumps(image_ids_images_and_formats[i]))
                self.request.recv(32)  # Юзер принял фото

        if message:
            logger.info(message)


class Queue:
    """Класс, отвечающий за общение с юзером."""

    def __init__(self, ip, port):
        self.server = ThreadedTCPServer((ip, port), ThreadedTCPRequestHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True

    def start_server(self):
        self.server_thread.start()

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()


if __name__ == '__main__':
    logger.info('START SERVER')
    server = Queue(IP, PORT)
    server.start_server()
    while True:
        try:
            sleep(0.05)
        except KeyboardInterrupt:       # В PyCharm не работает ctrl-C. Поэтому лучше запускать server.py не в PyCharm.
            logger.info('STOP SERVER')  # Т.е. Просто из проводника.
            sleep(1)
            break
    server.stop_server()
