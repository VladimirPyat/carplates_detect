import os
import csv


def create_csv_log(result_dict, log_name='log.csv'):
    # Определяем режим открытия файла
    mode = 'a' if os.path.exists(log_name) else 'w'  # Дописывать, если файл существует

    # Список уже добавленных значений для проверки дубликатов
    existing_ids = set()

    # Если файл существует, читаем его содержимое
    if mode == 'a':
        with open(log_name, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            existing_ids = {row['car_num'] for row in reader}  # Используем 'car_num' для извлечения значений

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
