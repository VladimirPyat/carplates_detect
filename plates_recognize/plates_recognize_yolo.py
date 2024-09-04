import math
import random

from ultralytics import YOLO

import os
import cv2

# Получаем путь к директории, где находится этот модуль
module_dir = os.path.dirname(__file__)

# Формируем полные пути к файлам .pt
model_path = os.path.join(module_dir, "best.pt")
model_plates_path = os.path.join(module_dir, "best-obb_p.pt")
model_symbols_path = os.path.join(module_dir, "best2_s.pt")

# Загрузка обученной модели
model_cars = YOLO(model_path)  # Определение автомобилей и спецтехники
model_plates = YOLO(model_plates_path)  # Обучена на номерных знаках
model_symbols = YOLO(model_symbols_path)  # Обучена на символах

COMMON_CARS = {2}
SPECIAL_CARS = {0, 1, 3}


class PredictProcess:
    def __init__(self, image_in, model, conf=0.6):
        self.orig_img = image_in
        self.predict = model.predict(self.orig_img, conf=conf)[0]
        self.boxes = {}
        self.timer = self.predict.speed
        self._create_boxes()

    def _create_boxes(self):
        pass

    def get_image_by_box(self, box_id):
        pass

    def is_boxes(self):
        return True if len(self.boxes) > 0 else False


class PredictProcessObb(PredictProcess):
    def _create_boxes(self):
        for obb in self.predict.obb:
            x, y = obb.xyxyxyxyn.tolist()[0][0]
            if (x, y) not in self.boxes.keys():
                self.boxes[(x, y)] = obb
            else:
                # если координаты боксов совпали -
                # добавляем случайную небольшую дельту, чтоб у каждого бокса был уникальный id
                random_delta = 0.0001
                x_shift = random.uniform(-random_delta, random_delta)
                y_shift = random.uniform(-random_delta, random_delta)
                self.boxes[(x + x_shift, y + y_shift)] = obb

    def get_image_by_box(self, box_id=None, scale=2):
        if box_id is None:
            box_id = list(self.boxes.keys())[0]
        obb = self.boxes[box_id]
        x1, y1, x2, y2 = obb.xyxy.tolist()[0]
        obb_img = self.orig_img[int(y1):int(y2), int(x1):int(x2)]
        height, width = obb_img.shape[:2]
        # Поворот
        angle_rad = obb.xywhr.tolist()[0][4]
        angle = math.degrees(angle_rad)
        if angle > 90:
            angle = (180 - angle) * -1
        # Создание матрицы преобразования для поворота изображения
        rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)
        obb_img = cv2.warpAffine(obb_img, rotation_matrix, (width, height))
        obb_img_out = cv2.resize(obb_img, (width * scale, height * scale), interpolation=cv2.INTER_LINEAR)

        return obb_img_out


class PredictProcessBox(PredictProcess):
    def _create_boxes(self):
        for box in self.predict.boxes:
            x, y, _, __ = box.xyxyn.tolist()[0]
            if (x, y) not in self.boxes.keys():
                self.boxes[(x, y)] = box
            else:
                # если координаты боксов совпали -
                # добавляем случайную небольшую дельту, чтоб у каждого бокса был уникальный id
                random_delta = 0.0001
                x_shift = random.uniform(-random_delta, random_delta)
                y_shift = random.uniform(-random_delta, random_delta)
                self.boxes[(x + x_shift, y + y_shift)] = box

    def get_box_in_zone(self, x_, y_, w_, h_):
        def is_in_zone(box_, x, y, w, h):
            x11, _, __, y21 = box_
            x12, y12, x22, y22 = x, y, x + w, y + h
            if (x12 <= x11 <= x22) and (y12 <= y21 <= y22):
                return True

            return False

        for box_id, box in self.boxes.items():
            if is_in_zone(box.xyxyn.tolist()[0], x_, y_, w_, h_):
                return box_id

        return None

    def get_image_by_box(self, box_id):
        box = self.boxes[box_id]
        x1, y1, x2, y2 = box.xyxy.tolist()[0]
        image = self.orig_img[int(y1):int(y2), int(x1):int(x2)]

        return image

    def get_box_conf(self, box_id):
        box = self.boxes[box_id]

        return box.conf[0]

    def get_text(self):
        class_names = self.predict.names
        # создаем словарь из классов символов на номере и их координат
        symbols_dict = {key: int(value.cls[0]) for key, value in self.boxes.items()}
        # порог разделения на верхний и нижний ряды. 0 - верх, 1 - низ
        Y_THRESH = 0.45
        # создаем словари из символов и их координат для верхней и нижней строк.
        upper_row = [(x, class_names[value]) for (x, y), value in symbols_dict.items() if y <= Y_THRESH]
        bottom_row = [(x, class_names[value]) for (x, y), value in symbols_dict.items() if y > Y_THRESH]
        # сортируем символы по х координате
        upper_row_sorted = sorted(upper_row, key=lambda item: item[0])
        bottom_row_sorted = sorted(bottom_row, key=lambda item: item[0])
        # Объединяем отсортированные строки
        sorted_values = [value for _, value in upper_row_sorted] + [value for _, value in bottom_row_sorted]

        return ''.join(sorted_values)

    def is_common_car(self, box_id):
        box = self.boxes[box_id]
        box_cls = int(box.cls[0])
        if box_cls in COMMON_CARS:
            return True

        return False

    def is_special_car(self, box_id):
        box = self.boxes[box_id]
        box_cls = int(box.cls[0])
        if box_cls in SPECIAL_CARS:
            return True

        return False




