import asyncio
import json
from asyncio import Lock
from pathlib import Path

import aiofiles

from utils.config import logger, ABISDIR


async def update_json(file_name: str, path: Path, data: dict,
                      lock: Lock = None) -> None:
    try:
        file_name = file_name if '.json' in file_name else f'{file_name}.json'
        file_path = Path(path) / file_name
        if not file_path.exists():
            file_path.touch()  # Создаст пустой файл, если его нет

        async def upd():
            async with aiofiles.open(file_path, 'r+') as f:
                try:
                    content = await f.read()
                    json_data = json.loads(content) if content else {}
                except json.JSONDecodeError as e:
                    logger.error(f'write_to_json: JSONDecodeError\n{e}')
                    json_data = {}  # Если файл пуст или содержит некорректный JSON

                # Обновляем данные
                json_data.update(data)
                # Перемещаем указатель в начало файла
                await f.seek(0)
                # Записываем обновленные данные
                await f.write(json.dumps(json_data, indent=4))
                # Обрезаем файл
                await f.truncate()

        if lock:
            async with lock:
                return await upd()
        else:
            return await upd()
    except Exception as e:
        logger.error(f'write_to_json: {data=}\n{e}')


async def read_from_json(file_name: str, path: Path,
                         lock: Lock = None, search_key: str = '') -> dict:
    try:
        file_name = file_name if '.json' in file_name else f'{file_name}.json'
        file_path = Path(path) / file_name

        if not file_path.exists():
            logger.error(f'read_from_json: Файл {file_path} не существует')
            return {}

        async def read():
            async with aiofiles.open(file_path, 'r') as f:
                content = await f.read()
                json_data = json.loads(content)
                if search_key:
                    return json_data.get(search_key)
                else:
                    return json_data

        if lock:
            async with lock:
                return await read()
        else:
            return await read()

    except Exception as e:
        logger.error(f'read_from_json: Error reading {file_name}\n{e}')
        return {}


if __name__ == '__main__':
    async def main():
        print(await read_from_json('OpenEditionERC721.json', ABISDIR))

    asyncio.run(main())
