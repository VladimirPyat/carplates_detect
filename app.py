import numpy as np
import streamlit as st
import pandas as pd
import tempfile


from utils.logger import create_csv_log
from utils.media_utils import VideoFrameGenerator, ImgProcess
from plates_recognize.plates_recognize_yolo import model_cars, model_plates, model_symbols, PredictProcessBox, \
    PredictProcessObb
from utils.time_utils import get_date, get_time


def main(frames_skip=5):
    # Загрузка видеофайла
    uploaded_file = st.sidebar.file_uploader("Выберите видеофайл", type=["mp4", "avi", "mov"])

    if uploaded_file is not None:
        # Сохранение загруженного видео во временный файл
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_file.read())
        video_path = tfile.name

        # Инициализация сессионного состояния
        if 'current_frame_index' not in st.session_state:
            st.session_state.current_frame_index = 0

        # Создание генератора кадров видео
        video_gen = VideoFrameGenerator(video_path)

        fps = video_gen.fps

        # Ползунки для задания положения и размера прямоугольника
        st.sidebar.header("Координаты зоны детекции")
        x = st.sidebar.slider("Положение X (0-100%)", 0.0, 1.0, 0.25)
        y = st.sidebar.slider("Положение Y (0-100%)", 0.0, 1.0, 0.35)
        w = st.sidebar.slider("Ширина (0-100%)", 0.0, 1.0, 0.35)
        h = st.sidebar.slider("Высота (0-100%)", 0.0, 1.0, 0.35)

        show_timer = st.sidebar.checkbox("Показывать время детекции", value=True)
        show_boxes = st.sidebar.checkbox("Выделять обнаруженные объекты ", value=False)

        # Ввод текста
        user_text = st.sidebar.text_input("Введите искомый номер", "А111АА69")
        detect_text = ''
        access_text = ''
        access_allowed = False
        empty_image = np.zeros((1, 1, 3), dtype=np.uint8)

        # управление воспроизведением
        with st.container():
            restart = st.button("Перезапустить видео")
            is_playing = st.checkbox("Воспроизведение видео", value=True)

        # Создаем два столбца: один для видео и один для результатов детекции
        col1, col2 = st.columns([2, 1])  # Пропорции колонок

        with col1:
            frame_placeholder = st.empty()  # Плейсхолдер для видео
        with col1.container():  # Используем контейнер в первой колонке
            frame_text_placeholder = st.empty()  # Плейсхолдер для текста
        with col2:
            detected_frame_placeholder = st.empty()  # Плейсхолдер для детекции
            detected_text_placeholder = st.empty()  # Плейсхолдер для текста
        plate_placeholder = st.empty()
        plate_text_placeholder = st.empty()

        # Перезапускаем видео только при нажатии на кнопку
        if restart:
            video_gen.reset()  # Сбрасываем генератор кадров
            st.session_state.current_frame_index = 0  # Сбрасываем индекс в сессии

        # Запускаем воспроизведение видео
        while True:
            plate_text = 'n/a'
            frame_index = st.session_state.current_frame_index
            video_gen.set_frame_index(frame_index if is_playing else frame_index - 1)
            frame = video_gen.get_image(frames_skip)

            if frame is None:
                break  # Завершаем воспроизведение, если видео закончилось

            # Создание объекта ImgProcess из кадра
            img_processor = ImgProcess(frame)

            # Нарисовать прямоугольник зоны детекции
            img_processor.draw_rect((x, y, w, h))

            # Отображение изображения в Streamlit
            frame_placeholder.image(img_processor.image, channels="BGR")
            detected_text_placeholder.text(detect_text)

            # Сохраняем текущий индекс кадра в сессии
            st.session_state.current_frame_index = video_gen.current_frame_index

            # определяем машины в зоне детекции
            predict_cars = PredictProcessBox(frame, model_cars)
            detect_time = sum(predict_cars.timer.values())
            box_xyn = predict_cars.get_box_in_zone(x, y, w, h)
            if box_xyn is not None:
                recognize_time = 0
                # показываем обнаруженное авто в зоне детекции
                car_image = predict_cars.get_image_by_box(box_xyn)
                detected_frame_placeholder.image(car_image)
                car_class = 'Спецтранспорт' if predict_cars.is_special_car(box_xyn) else 'Обычная машина'
                # определяем тип машин
                if predict_cars.is_common_car(box_xyn):
                    detect_text = f'{car_class} (conf= {predict_cars.get_box_conf(box_xyn):.2f})'

                    #  определяем автономер
                    predict_plates = PredictProcessObb(car_image, model_plates)
                    if predict_plates.is_boxes():
                        if show_boxes:
                            detected_frame_placeholder.image(predict_plates.predict.plot())
                        plate_image = predict_plates.get_image_by_box()
                        plate_placeholder.image(plate_image)

                        #  распознаем символы на номере
                        predict_symbols = PredictProcessBox(plate_image, model_symbols)
                        if show_boxes and predict_symbols.is_boxes():
                            plate_placeholder.image(predict_symbols.predict.plot(font_size=.7, font="javatext.ttf"))
                        plate_text = predict_symbols.get_text()
                        recognition_text = f'Распознан номер {plate_text}'
                        recognize_time = sum(predict_plates.timer.values()) + sum(predict_symbols.timer.values())
                        # проверка номера
                        access_allowed = True if plate_text == user_text else False
                    else:
                        recognition_text = 'Не удалось распознать номер'

                    # Вывод результатов
                    total_time = recognize_time + detect_time
                    if show_timer:
                        recognition_text += f'\nВремя распознавания: {recognize_time:.1f}мс'
                        recognition_text += f'\nСуммарное время: {total_time:.1f}мс'
                    plate_text_placeholder.text(recognition_text)

                if predict_cars.is_special_car(box_xyn):
                    detect_text = f'{car_class} (conf= {predict_cars.get_box_conf(box_xyn):.2f})'
                    access_allowed = True

                if show_timer:
                    detect_text += f'\nВремя обнаружения: {detect_time:.1f}мс'

                # Вывод
                access_color = 'green' if access_allowed else 'red'
                access_text = 'Доступ разрешен' if access_allowed else 'Доступ запрещен'
                if predict_cars.is_special_car(box_xyn):
                    access_text += f': {car_class}'

                frame_text_placeholder.markdown(f'<span style=\"color: {access_color};\">{access_text}</span>',
                                                unsafe_allow_html=True)

                # записываем события в лог
                total_time = recognize_time + detect_time
                create_csv_log({'car_num': plate_text, 'car_type': car_class, 'action_type': access_text,
                                'date': get_date(), 'time': get_time(), 'duration_ms': f'{total_time: .1f}'})

            # Очистка фреймов если нет авто в зоне
            else:
                # Очистка строк
                # frame_text_placeholder.text('')
                access_allowed = False
                detect_text = ''
                detected_frame_placeholder.image(empty_image)

            # Задержка для воспроизведения с правильной частотой кадров
            # time.sleep(1 / (fps / frames_skip + 1))

        # Освобождение ресурсов
        video_gen.release()


        # очистка
        frame_text_placeholder.text('')
        plate_text_placeholder.text('')
        plate_placeholder.image(empty_image)

        # Загрузка файла CSV
        uploaded_file = 'log.csv'

        if uploaded_file is not None:
            # Читаем CSV файл в DataFrame
            df = pd.read_csv(uploaded_file)

            # Отображаем DataFrame в виде таблицы
            st.dataframe(df)  # Используйте st.table(df) для статической таблицы

        st.session_state.clear()

if __name__ == "__main__":
    main()
