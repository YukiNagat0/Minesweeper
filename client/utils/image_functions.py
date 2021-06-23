from os.path import exists

import pickle

from PIL import Image, ImageQt
from PyQt5.QtGui import QPixmap

PLAYERS_IMG = 'src/images/players_img'


def crop_and_resize_image(file_name, size):
    original_image = Image.open(file_name)

    width, height = original_image.size
    min_side = min(width, height)

    cropped_and_resized_image = original_image.crop(((width - min_side) // 2,
                                                     (height - min_side) // 2,
                                                     (width + min_side) // 2,
                                                     (height + min_side) // 2)).resize((size, size))
    return cropped_and_resized_image


def to_pixmap_from_file(file_name, size):
    image = crop_and_resize_image(file_name, size)
    return QPixmap.fromImage(ImageQt.ImageQt(image))


def to_blob(file_name, size):
    """Сериализация Image."""
    image = crop_and_resize_image(file_name, size)

    image_bytes = pickle.dumps(image)
    return image_bytes


def save_image(image_id: int, image_bytes: bytes, image_format: str) -> str:
    """Десериализация объекта PIL.Image из image_bytes, сохранение фото, добавление его в дамп-файл, возврат отн пути"""

    if exists(f'{PLAYERS_IMG}/id_and_filename.dumb'):  # Сериализованный dict с ids и путями к изображениям
        with open(f'{PLAYERS_IMG}/id_and_filename.dumb', 'rb') as f:
            id_and_filename = pickle.load(f)
    else:
        id_and_filename = dict()

    if image_id not in id_and_filename:
        image = pickle.loads(image_bytes)  # Объект класса Image из байтов image_bytes.

        image.save(f'{PLAYERS_IMG}/{image_id}{image_format}')

        id_and_filename[image_id] = f'{PLAYERS_IMG}/{image_id}{image_format}'  # Добавление id и имени файла в дамп-файл

    with open(f'{PLAYERS_IMG}/id_and_filename.dumb', 'wb') as f:  # Перезапись дамп-файла
        pickle.dump(id_and_filename, f)

    return id_and_filename[image_id]  # Относительный путь


def get_pixmap(image_id: int) -> QPixmap:
    """Возвращает QPixmap по image_id."""
    if exists(f'{PLAYERS_IMG}/id_and_filename.dumb'):
        with open(f'{PLAYERS_IMG}/id_and_filename.dumb', 'rb') as f:
            id_and_filename = pickle.load(f)
    else:
        id_and_filename = dict()

    if image_id in id_and_filename:
        return QPixmap(id_and_filename[image_id])
    return None


def get_id_and_filename() -> dict:
    """Возвращает дамп-файл."""
    if exists(f'{PLAYERS_IMG}/id_and_filename.dumb'):
        with open(f'{PLAYERS_IMG}/id_and_filename.dumb', 'rb') as f:
            id_and_filename = pickle.load(f)
    else:
        id_and_filename = dict()

    return id_and_filename


def save_image_and_get_pixmap(image_id: int, image_bytes: bytes, image_format: str) -> QPixmap:
    """Сохраняет изображение и возварщает QPixmap."""
    return QPixmap(save_image(image_id, image_bytes, image_format))


def get_existing_images_ids() -> set:
    """Возвращает set из существующих на диске фото по id. Отправляется на сервер (см. connection.py: get_records)."""
    if exists(f'{PLAYERS_IMG}/id_and_filename.dumb'):
        with open(f'{PLAYERS_IMG}/id_and_filename.dumb', 'rb') as f:
            id_and_filename = pickle.load(f)
            return set(id_and_filename.keys())
    return set()
