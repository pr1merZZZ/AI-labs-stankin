import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import pytesseract
from PIL import Image, ImageTk
import os

# Укажите путь к tesseract.exe, если он не в PATH (только для Windows)
# Здесь указан базовый путь
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Распознавание текста с фото")
        self.root.geometry("1000x700")

        # Переменные
        self.image_path = ""
        self.current_image = None
        self.processed_image = None

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Левая панель управления
        control_frame = ttk.Frame(self.root, width=250)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Заголовок
        title_label = ttk.Label(control_frame, text="Настройки", font=("Arial", 14))
        title_label.pack(pady=(0, 10))

        # Кнопка выбора файла
        select_button = ttk.Button(control_frame, text="Выбрать изображение", command=self.load_image)
        select_button.pack(fill=tk.X, pady=5)

        # Путь к файлу
        self.path_label = ttk.Label(control_frame, text="Файл не выбран", wraplength=200)
        self.path_label.pack(fill=tk.X, pady=(0, 10))

        # Настройки OCR
        settings_label = ttk.Label(control_frame, text="Настройки распознавания:")
        settings_label.pack(anchor=tk.W, pady=(10, 5))

        # Язык распознавания
        lang_label = ttk.Label(control_frame, text="Язык (например: rus, eng, rus+eng):")
        lang_label.pack(anchor=tk.W)

        self.lang_var = tk.StringVar(value="rus+eng")
        lang_entry = ttk.Entry(control_frame, textvariable=self.lang_var)
        lang_entry.pack(fill=tk.X, pady=(0, 5))

        # Кнопка распознавания
        recognize_button = ttk.Button(control_frame, text="Распознать текст", command=self.recognize_text)
        recognize_button.pack(fill=tk.X, pady=10)

        # Кнопка сохранения
        save_button = ttk.Button(control_frame, text="Сохранить текст в файл", command=self.save_text)
        save_button.pack(fill=tk.X, pady=5)

        # Основной фрейм для отображения изображения и текста
        main_frame = ttk.Frame(self.root)
        main_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Фрейм для изображения
        image_frame = ttk.Frame(main_frame)
        image_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 10))

        # Canvas для прокрутки изображения
        self.canvas = tk.Canvas(image_frame, bg="black")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scrollbar = ttk.Scrollbar(image_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        self.image_canvas_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.image_canvas_frame, anchor=tk.NW)

        self.image_canvas_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Фрейм для текста
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        text_label = ttk.Label(text_frame, text="Распознанный текст:")
        text_label.pack(anchor=tk.W)

        # Text widget для вывода результата
        self.text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Courier", 10))
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        # Scrollbar для текста
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.configure(yscrollcommand=text_scrollbar.set)

    def load_image(self):
        """Загружает изображение"""
        file_path = filedialog.askopenfilename(title="Выберите изображение", filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")])
        if file_path:
            self.image_path = file_path
            self.current_image = cv2.imread(file_path)
            if self.current_image is None:
                messagebox.showerror("Ошибка", "Не удалось загрузить изображение.")
                self.image_path = ""
                self.current_image = None
            else:
                self.path_label.config(text=os.path.basename(file_path))
                self.display_image(self.current_image)

    def display_image(self, img):
        """Отображает изображение в Canvas с прокруткой"""
        if img is None:
            return

        # Конвертируем в RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        # Масштабируем под экран
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        max_width = screen_width - 300
        max_height = screen_height - 300

        w, h = pil_img.size
        scale = min(max_width / w, max_height / h, 1.0)
        new_w = int(w * scale)
        new_h = int(h * scale)

        resized_pil = pil_img.resize((new_w, new_h), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image=resized_pil)

        # Удаляем предыдущее изображение
        for widget in self.image_canvas_frame.winfo_children():
            widget.destroy()

        # Создаем Label с изображением
        label = tk.Label(self.image_canvas_frame, image=photo, bg="black")
        label.image = photo
        label.pack()

        # Обновляем область прокрутки
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def recognize_text(self):
        """Выполняет распознавание текста"""
        if self.current_image is None:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите изображение.")
            return

        try:
            # Преобразуем изображение в серое (опционально, но часто улучшает результат)
            gray = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2GRAY)

            # Применяем пороговую обработку (бинаризация) для улучшения качества
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Распознавание текста
            custom_config = f'--oem 3 --psm 6 -l {self.lang_var.get()}'
            text = pytesseract.image_to_string(thresh, config=custom_config)

            # Выводим текст
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, text.strip())

            # Сохраняем обработанное изображение
            self.processed_image = thresh

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при распознавании текста:\n{e}")

    def save_text(self):
        """Сохраняет распознанный текст в файл"""
        if not self.text_widget.get(1.0, tk.END).strip():
            messagebox.showwarning("Предупреждение", "Нет текста для сохранения.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")], title="Сохранить текст как")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_widget.get(1.0, tk.END).strip())
                messagebox.showinfo("Успех", f"Текст сохранен в файл:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()