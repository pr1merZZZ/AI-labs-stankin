import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk # pip install Pillow

class FaceEyeDetectionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Обнаружение лиц и глаз")
        self.root.geometry("800x600")

        # Переменные для управления камерой
        self.cap = None
        self.is_running = False

        # Загрузка каскадов
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

        if self.face_cascade.empty() or self.eye_cascade.empty():
            messagebox.showerror("Ошибка", "Не удалось загрузить каскады Haar. Проверьте установку OpenCV.")
            self.root.destroy()
            return

        # Создание элементов интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Основной фрейм для видео
        self.video_frame = ttk.Frame(self.root)
        self.video_frame.pack(pady=10)

        # Label для отображения видео
        self.video_label = tk.Label(self.video_frame)
        self.video_label.pack()

        # Фрейм для кнопок
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(pady=10)

        # Кнопка "Запустить"
        self.start_button = ttk.Button(self.button_frame, text="Запустить", command=self.start_detection)
        self.start_button.pack(side=tk.LEFT, padx=5)

        # Кнопка "Остановить"
        self.stop_button = ttk.Button(self.button_frame, text="Остановить", command=self.stop_detection, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Кнопка "Выход"
        self.exit_button = ttk.Button(self.button_frame, text="Выход", command=self.on_closing)
        self.exit_button.pack(side=tk.LEFT, padx=5)

    def start_detection(self):
        if not self.is_running:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Ошибка", "Не удалось открыть веб-камеру.")
                return
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.update_frame() # Запуск обновления кадров

    def stop_detection(self):
        if self.is_running:
            self.is_running = False
            if self.cap:
                self.cap.release()
            self.cap = None
            self.video_label.config(image='') # Очистить изображение
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

    def update_frame(self):
        if self.is_running:
            ret, frame = self.cap.read()
            if ret:
                # Обработка кадра
                processed_frame = self.detect_faces_and_eyes(frame)

                # Конвертация OpenCV BGR -> RGB -> PIL Image -> PhotoImage
                processed_frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                img_pil = Image.fromarray(processed_frame_rgb)
                img_tk = ImageTk.PhotoImage(image=img_pil)

                # Обновление метки с изображением
                self.video_label.imgtk = img_tk  # Сохраняем ссылку, чтобы изображение не исчезло
                self.video_label.configure(image=img_tk)

            # Повторный вызов функции через 10 мс для обновления кадра
            self.root.after(10, self.update_frame)

    def detect_faces_and_eyes(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            
            eyes = self.eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5, minSize=(10, 10))
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)
        
        return frame

    def on_closing(self):
        self.stop_detection()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = FaceEyeDetectionApp(root)
    # Обработка закрытия окна через 'X'
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()