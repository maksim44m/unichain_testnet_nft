import json
from pathlib import Path

from utils.config import logger


def update_json(file_name: str, path: Path, data: dict) -> None:
    try:
        file_name = file_name if '.json' in file_name else f'{file_name}.json'
        file_path = Path(path) / file_name
        if not file_path.exists():
            file_path.touch()  # Создаст пустой файл, если его нет

        with open(file_path, 'r+') as f:
            try:
                content = f.read()
                json_data = json.loads(content) if content else {}
            except json.JSONDecodeError as e:
                logger.error(f'write_to_json: JSONDecodeError\n{e}')
                json_data = {}  # Если файл пуст или содержит некорректный JSON

            # Обновляем данные
            json_data.update(data)
            # Перемещаем указатель в начало файла
            f.seek(0)
            # Записываем обновленные данные
            f.write(json.dumps(json_data, indent=4))
            # Обрезаем файл
            f.truncate()

    except Exception as e:
        logger.error(f'write_to_json: {data=}\n{e}')


def read_from_json(file_name: str, path: Path, search_key: str = '') -> dict:
    try:
        file_name = file_name if '.json' in file_name else f'{file_name}.json'
        file_path = Path(path) / file_name

        if not file_path.exists():
            logger.error(f'read_from_json: Файл {file_path} не существует')
            return {}

        with open(file_path, 'r') as f:
            content = f.read()
            json_data = json.loads(content)
            if search_key:
                return json_data.get(search_key)
            else:
                return json_data

    except Exception as e:
        logger.error(f'read_from_json: Error reading {file_name}\n{e}')
        return {}


if __name__ == '__main__':
    pass
