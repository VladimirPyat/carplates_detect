import cv2


class VideoFrameGenerator:
    """
    Создает объект генератор на основе видео.
    get_image(self) - возвращает следующий кадр.
    """

    def __init__(self, video_path):
        self.capture = cv2.VideoCapture(video_path)
        self.is_video_opened = self.capture.isOpened()
        self.current_frame_index = 0  # Индекс текущего кадра
        self.fps = self.capture.get(cv2.CAP_PROP_FPS)

    def __iter__(self):
        return self

    def __next__(self):
        frame_ = self.get_image()
        if frame_ is None:
            raise StopIteration
        return frame_

    def get_image(self, frames_skip=0):
        if not self.is_video_opened:
            return None

        while True:
            ret, frame_ = self.capture.read()

            if not ret:
                self.is_video_opened = False
                self.capture.release()
                #return None

            # Проверяем, нужно ли возвращать текущий кадр
            if self.current_frame_index % (frames_skip + 1) == 0:
                self.current_frame_index += 1  # Увеличиваем индекс кадра
                return frame_

            self.current_frame_index += 1  # Увеличиваем индекс кадра для пропуска

    def release(self):
        self.capture.release()

    def set_frame_index(self, index):
        self.current_frame_index = index
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, index)

    def __del__(self):
        if self.capture.isOpened():
            self.capture.release()

    def reset(self):
        self.current_frame_index = 0
        self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Сбросить позицию на начало видео
        self.is_video_opened = self.capture.isOpened()  # Проверяем, открыто ли видео


class ImgProcess:
    def __init__(self, image):
        self.image = image.copy()

    def draw_rect(self, coords=None, color=(255, 0, 0), thickness=2):
        """
        Рисует прямоугольник на изображении.

        :param coords: Кортеж (x, y, w, h), где (x, y) - координаты верхнего левого угла,
                       w - ширина, h - высота (в % от размера изображения)
        :param color: Цвет прямоугольника в формате BGR (по умолчанию красный).
        :param thickness: Толщина линии (по умолчанию 2).
        """
        height, width = self.image.shape[:2]

        if coords is None:
            x, y, w, h = 0, 0, int(width * 0.5), int(height * 0.5)
        else:
            x, y, w, h = int(coords[0]*width), int(coords[1]*height), int(coords[2]*width), int(coords[3]*height)
        cv2.rectangle(self.image, (x, y), (x + w, y + h), color, thickness)

    def put_text(self, text='Lorem ipsum blah blah', font_size_ratio=1,  position=None, color=(0, 0, 0),
                 font=cv2.FONT_HERSHEY_SIMPLEX, thickness=2):
        """
        Размещает текст на изображении.

        :param font_size_ratio:  Множитель для размера шрифта
        :param text: Текст для отображения.
        :param position: Кортеж (x, y) для размещения текста (по умолчанию - низ по центру).
        :param font: Шрифт текста (по умолчанию FONT_HERSHEY_SIMPLEX).
        :param color: Цвет текста в формате BGR (по умолчанию черный).
        :param thickness: Толщина текста (по умолчанию 2).
        """
        # Определяем параметры текста
        max_chars_per_line = 80
        max_lines = 40

        # Получаем размеры изображения
        image_height, image_width = self.image.shape[:2]

        max_symbol_width = image_width / max_chars_per_line
        max_symbol_height = image_height / max_lines

        # Вычисляем размер текста для масштаба 1
        text_1_width, text_1_height = cv2.getTextSize(text, font, 1, thickness)[0]
        font_scale = font_size_ratio*10 * min(max_symbol_width / text_1_width, max_symbol_height / text_1_height)

        if position is None:
            # Положение по умолчанию - центр
            position = (int((image_width) / 2), int((image_height) / 2))

        # Размещаем текст на изображении
        cv2.putText(self.image, text, position, font, font_scale, color, thickness)


if __name__ == '__main__':
    video_generator = VideoFrameGenerator(r'..\..\_test\10.121.15.252_01_test_4.mp4')
    while True:
        frame = video_generator.get_image(frames_skip=5)
        if frame is None:
            break
        img = ImgProcess(frame)
        img.draw_rect()
        img.put_text()
        cv2.imshow('Frame', img.image)
        if cv2.waitKey(1) & 0xFF == ord('q'):  # Нажмите 'q' для выхода
            break

    cv2.waitKey(0)
    cv2.destroyAllWindows()
