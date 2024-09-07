import os
import csv

from utils.time_utils import is_timeout

transliteration_dict = {
    'А': 'A',
    'В': 'B',
    'Е': 'E',
    'К': 'K',
    'М': 'M',
    'Н': 'H',
    'О': 'O',
    'Р': 'P',
    'С': 'C',
    'Т': 'T',
    'Х': 'X',
    'У': 'Y'
}


def create_csv_log(result_dict, log_name='log.csv', timeout_sec = 30):
    # Определяем режим открытия файла
    mode = 'a' if os.path.exists(log_name) else 'w'  # Дописывать, если файл существует

    # Список уже добавленных значений для проверки дубликатов
    existing_ids = set()

    # Если файл существует, читаем его содержимое
    if mode == 'a':


        with open(log_name, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            existing_ids = {
                row['car_num'] for row in reader if is_timeout(row['date'], row['time'], timeout_sec)}
            # Используем 'car_num' для извлечения значений, если время меньше порога

        # Проверка на дублирование
        if result_dict['car_num'] in existing_ids:  # Здесь сравниваем строки
            print('Дублирование обнаружено. Запись не добавлена:', result_dict)
            return

    # Запись в CSV
    with open(log_name, mode, newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=result_dict.keys())
        if mode == 'w':
            writer.writeheader()  # Записываем заголовки только при создании нового файла
        writer.writerow(result_dict)  # Записываем новую строку
        print('Запись добавлена:', result_dict)


def translit_txt(input_text):
    out_text = []
    for symbol in input_text.upper().replace(" ", ""):              # убираем пробелы, переводим в заглавные
        # проверяем что строка состоит из цифр либо подходящих символов
        if symbol.isdigit() or symbol in transliteration_dict or symbol in transliteration_dict.values():
            out_text.append(transliteration_dict.get(symbol, symbol))  # Транслитерация или сам символ
        else:
            raise ValueError(f'Недопустимый символ "{symbol}"')

    return ''.join(out_text)


if __name__ == '__main__':
    print(translit_txt('о777оо 98'))