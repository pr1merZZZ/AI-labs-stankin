import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
from PIL import Image, ImageTk
import numpy as np
import os
import time

class ImageMatchingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Поиск образа в реальном времени (SIFT)")
        self.root.geometry("1200x800")

        # Переменные
        self.cap = None
        self.is_running = False
        self.is_processing = False
        self.scene_image = None
        self.object_image = None
        self.scene_path = ""
        self.object_path = ""

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Левая панель управления
        control_frame = ttk.Frame(self.root, width=250)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Заголовок
        title_label = ttk.Label(control_frame, text="Настройки", font=("Arial", 14))
        title_label.pack(pady=(0, 10))

        # Источник изображения
        source_label = ttk.Label(control_frame, text="Выберите источник изображения:")
        source_label.pack(anchor=tk.W, pady=(10, 5))

        self.source_var = tk.StringVar(value="webcam")

        webcam_radio = ttk.Radiobutton(control_frame, text="Включить веб-камеру", variable=self.source_var, value="webcam", command=self.toggle_source)
        webcam_radio.pack(anchor=tk.W)

        image_radio = ttk.Radiobutton(control_frame, text="Загрузить изображение", variable=self.source_var, value="image", command=self.toggle_source)
        image_radio.pack(anchor=tk.W)

        # Выбор изображения сцены
        scene_label = ttk.Label(control_frame, text="Выберите изображение сцены:")
        scene_label.pack(anchor=tk.W, pady=(15, 5))

        self.scene_button = ttk.Button(control_frame, text="Выбрать файл", command=self.load_scene_image)
        self.scene_button.pack(anchor=tk.W, fill=tk.X)

        self.scene_path_label = ttk.Label(control_frame, text="", wraplength=200)
        self.scene_path_label.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))

        # Выбор изображения объекта
        object_label = ttk.Label(control_frame, text="Выберите изображение объекта:")
        object_label.pack(anchor=tk.W, pady=(15, 5))

        self.object_button = ttk.Button(control_frame, text="Выбрать файл", command=self.load_object_image)
        self.object_button.pack(anchor=tk.W, fill=tk.X)

        self.object_path_label = ttk.Label(control_frame, text="", wraplength=200)
        self.object_path_label.pack(anchor=tk.W, fill=tk.X, pady=(0, 5))

        # Чекбоксы
        self.show_markers_var = tk.BooleanVar(value=True)
        show_markers_check = ttk.Checkbutton(control_frame, text="Отобразить маркеры", variable=self.show_markers_var)
        show_markers_check.pack(anchor=tk.W, pady=(15, 5))

        self.connect_markers_var = tk.BooleanVar(value=True)
        connect_markers_check = ttk.Checkbutton(control_frame, text="Соединить подобные маркеры", variable=self.connect_markers_var)
        connect_markers_check.pack(anchor=tk.W, pady=(0, 15))

        # Кнопка "Загрузка видео"
        self.start_button = ttk.Button(control_frame, text="Загрузка видео", command=self.start_matching)
        self.start_button.pack(fill=tk.X, pady=10)

        # Статусная строка
        self.status_label = ttk.Label(control_frame, text="Процессорное время = 0.000000", anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

        # Основной фрейм для отображения видео/изображения
        self.display_frame = ttk.Frame(self.root)
        self.display_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas для прокрутки
        self.canvas = tk.Canvas(self.display_frame, bg="black")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Scrollbars
        self.v_scrollbar = ttk.Scrollbar(self.display_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self.display_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        # Frame внутри Canvas для изображения
        self.image_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.image_frame, anchor=tk.NW)

        # Обновление прокрутки при изменении размера
        self.image_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Фрейм для мини-изображения (объект) — фиксируем внизу
        mini_frame = ttk.Frame(self.display_frame, height=150)
        mini_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)

        self.mini_label = tk.Label(mini_frame, text="Изображение объекта", bg="lightgray", relief="sunken", height=10)
        self.mini_label.pack(fill=tk.X)

        # Привязываем событие изменения размера окна
        self.root.bind("<Configure>", self.on_window_resize)

    def on_window_resize(self, event):
        pass

    def toggle_source(self):
        if self.source_var.get() == "webcam":
            self.scene_button.config(state=tk.DISABLED)
            self.scene_path_label.config(text="")
            self.scene_image = None
        else:
            self.scene_button.config(state=tk.NORMAL)

    def load_scene_image(self):
        file_path = filedialog.askopenfilename(title="Выберите изображение сцены", filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")])
        if file_path:
            self.scene_path = file_path
            self.scene_image = cv2.imread(file_path)
            if self.scene_image is None:
                messagebox.showerror("Ошибка", "Не удалось загрузить изображение сцены.")
                self.scene_path = ""
                self.scene_image = None
            else:
                self.scene_path_label.config(text=os.path.basename(file_path))
                if self.source_var.get() == "image":
                    self.display_image(self.scene_image)

    def load_object_image(self):
        file_path = filedialog.askopenfilename(title="Выберите изображение объекта", filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")])
        if file_path:
            self.object_path = file_path
            self.object_image = cv2.imread(file_path)
            if self.object_image is None:
                messagebox.showerror("Ошибка", "Не удалось загрузить изображение объекта.")
                self.object_path = ""
                self.object_image = None
            else:
                self.object_path_label.config(text=os.path.basename(file_path))
                self.display_mini_object(self.object_image)

    def display_mini_object(self, img):
        if img is None:
            return
        h, w = img.shape[:2]
        scale = min(150 / w, 150 / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        resized_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(resized_rgb)
        photo = ImageTk.PhotoImage(image=pil_img)
        self.mini_label.config(image=photo)
        self.mini_label.image = photo

    def display_image(self, img):
        """Отображает изображение в Canvas с возможностью прокрутки"""
        if img is None:
            return

        # Конвертируем в RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        # Масштабируем, чтобы вписаться в экран (не больше оригинала)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        max_width = screen_width - 300  # Учитываем левую панель
        max_height = screen_height - 250  # Учитываем статус, миниатюру и рамки

        w, h = pil_img.size
        scale = min(max_width / w, max_height / h, 1.0)
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized_pil = pil_img.resize((new_w, new_h), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image=resized_pil)

        # Удаляем предыдущее изображение
        for widget in self.image_frame.winfo_children():
            widget.destroy()

        # Создаем Label с изображением
        label = tk.Label(self.image_frame, image=photo, bg="black")
        label.image = photo  # Сохраняем ссылку
        label.pack()

        # Обновляем область прокрутки
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def start_matching(self):
        if self.object_image is None:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите изображение объекта.")
            return

        if self.source_var.get() == "webcam":
            if not self.is_running:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    messagebox.showerror("Ошибка", "Не удалось открыть веб-камеру. Проверьте подключение и разрешения.")
                    return
                self.is_running = True
                self.start_button.config(text="Остановить")
                self.update_webcam()
            else:
                self.stop_matching()
        else:
            if self.scene_image is None:
                messagebox.showwarning("Предупреждение", "Пожалуйста, выберите изображение сцены.")
                return
            result_img = self.match_objects_sift(self.scene_image, self.object_image)
            self.display_image(result_img)
            self.update_status_time()

    def stop_matching(self):
        if self.is_running and self.cap:
            self.cap.release()
            self.cap = None
        self.is_running = False
        self.start_button.config(text="Загрузка видео")
        self.is_processing = False

    def update_webcam(self):
        if self.is_running:
            ret, frame = self.cap.read()
            if ret:
                if not self.is_processing:
                    self.is_processing = True
                    start_time = time.perf_counter()
                    try:
                        result_img = self.match_objects_sift(frame, self.object_image)
                        end_time = time.perf_counter()
                        elapsed_time = end_time - start_time
                        self.update_status_time(elapsed_time)
                        self.display_image(result_img)
                    except Exception as e:
                        print(f"Ошибка при обработке кадра: {e}")
                    finally:
                        self.is_processing = False
            # Повторный вызов через 30 мс
            self.root.after(30, self.update_webcam)

    def match_objects_sift(self, scene_img, object_img):
        """Выполняет поиск объекта на сцене с помощью SIFT"""
        # Преобразуем в серое изображение для обработки
        gray_scene = cv2.cvtColor(scene_img, cv2.COLOR_BGR2GRAY)
        gray_object = cv2.cvtColor(object_img, cv2.COLOR_BGR2GRAY)

        # Инициализация детектора SIFT
        sift = cv2.SIFT_create()

        # Находим ключевые точки и дескрипторы для обоих изображений
        keypoints_obj, descriptors_obj = sift.detectAndCompute(gray_object, None)
        keypoints_scene, descriptors_scene = sift.detectAndCompute(gray_scene, None)

        if descriptors_obj is None or descriptors_scene is None:
            # Не удалось найти ключевые точки
            return scene_img.copy()

        # Используем Brute Force Matcher с L2 расстоянием (для SIFT)
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)

        # Находим соответствия
        matches = bf.knnMatch(descriptors_obj, descriptors_scene, k=2)

        # Применяем отношение Лоу (Lowes ratio test) для фильтрации хороших соответствий
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:  # Порог можно настроить
                good_matches.append(m)

        # Если нашли достаточно соответствий, рисуем их
        result_img = scene_img.copy()
        if len(good_matches) > 10:  # Минимальное количество хороших соответствий
            # Получаем координаты ключевых точек
            src_pts = np.float32([keypoints_obj[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([keypoints_scene[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

            # Находим гомографию (перспективное преобразование) между объектом и сценой
            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            matchesMask = mask.ravel().tolist()

            if M is not None:
                # Получаем размеры объекта
                h, w = gray_object.shape

                # Находим углы объекта в сцене
                pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                dst = cv2.perspectiveTransform(pts, M)

                # Рисуем прямоугольник вокруг объекта
                cv2.polylines(result_img, [np.int32(dst)], True, (0, 255, 0), 3, cv2.LINE_AA)

                # Рисуем маркеры и линии, если нужно
                if self.show_markers_var.get():
                    for i, match in enumerate(good_matches):
                        if matchesMask[i]:
                            # Координаты точки на сцене
                            x_scene, y_scene = keypoints_scene[match.trainIdx].pt

                            # Рисуем круг в точке на сцене
                            cv2.circle(result_img, (int(x_scene), int(y_scene)), 4, (255, 0, 0), -1)

                            # Соединяем линией, если нужно
                            if self.connect_markers_var.get():
                                # Цвет линии
                                color = (0, 0, 255)  # Красный
                                # Рисуем линию от точки на сцене к центру найденного прямоугольника
                                center_x = int((dst[0][0][0] + dst[2][0][0]) / 2)
                                center_y = int((dst[0][0][1] + dst[2][0][1]) / 2)
                                cv2.line(result_img, (int(x_scene), int(y_scene)), (center_x, center_y), color, 1)

        return result_img

    def update_status_time(self, elapsed_time=None):
        if elapsed_time is None:
            elapsed_time = 0.0
        self.status_label.config(text=f"Процессорное время = {elapsed_time:.6f}")

    def on_closing(self):
        self.stop_matching()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageMatchingApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()