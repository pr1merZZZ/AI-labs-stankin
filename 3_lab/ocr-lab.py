import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import pytesseract
from PIL import Image, ImageTk
import os
from typing import Optional, Tuple

# === Конфигурация ===
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


class OCRApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("OCR: Распознавание текста с изображений")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)

        # --- Данные ---
        self.image_path: str = ""
        self.original_image: Optional[cv2.Mat] = None
        self.processed_image: Optional[cv2.Mat] = None
        self.photo_ref: Optional[ImageTk.PhotoImage] = None

        # --- Стили ---
        self.setup_styles()

        # --- Интерфейс ---
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f5f5f5')
        style.configure('TButton', font=('Segoe UI', 10), padding=6)
        style.configure('TLabel', background='#f5f5f5', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI Semibold', 14), padding=(0, 10))

    def create_widgets(self):
        # Основное разделение: левая панель + правая область
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === Левая панель: настройки ===
        control_frame = ttk.Frame(main_pane, width=280)
        control_frame.pack_propagate(False)

        title_label = ttk.Label(control_frame, text="Настройки OCR", style='Title.TLabel')
        title_label.pack(pady=(0, 10), padx=10, anchor='w')

        # Выбор изображения
        self.select_btn = ttk.Button(
            control_frame, text="📂 Выбрать изображение", command=self.load_image
        )
        self.select_btn.pack(fill=tk.X, padx=10, pady=(0, 5))

        self.path_label = ttk.Label(
            control_frame,
            text="Файл не выбран",
            wraplength=250,
            foreground='#666'
        )
        self.path_label.pack(padx=10, pady=(0, 15), anchor='w')

        # Язык
        ttk.Label(control_frame, text="Язык распознавания:", font=('Segoe UI', 10, 'bold')).pack(
            padx=10, anchor='w'
        )
        self.lang_var = tk.StringVar(value="rus+eng")
        lang_entry = ttk.Entry(control_frame, textvariable=self.lang_var, font=('Consolas', 10))
        lang_entry.pack(fill=tk.X, padx=10, pady=(0, 15))

        # Кнопки действий
        self.recognize_btn = ttk.Button(
            control_frame, text="🔍 Распознать текст", command=self.recognize_text
        )
        self.recognize_btn.pack(fill=tk.X, padx=10, pady=5)

        self.save_btn = ttk.Button(
            control_frame, text="💾 Сохранить текст", command=self.save_text
        )
        self.save_btn.pack(fill=tk.X, padx=10, pady=(5, 0))

        # Статус
        self.status_var = tk.StringVar(value="Готов к работе")
        status_label = ttk.Label(control_frame, textvariable=self.status_var, foreground='#888', font=('Segoe UI', 9))
        status_label.pack(padx=10, pady=(15, 5), anchor='w')

        # Добавляем фрейм в панель
        main_pane.add(control_frame)

        # === Правая область: изображение + текст ===
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame)

        # Разделение изображения и текста
        right_pane = ttk.PanedWindow(right_frame, orient=tk.VERTICAL)
        right_pane.pack(fill=tk.BOTH, expand=True)

        # --- Canvas с изображением ---
        image_frame = ttk.Frame(right_pane)
        self.canvas = tk.Canvas(image_frame, bg='#1e1e1e', highlightthickness=0)
        v_scroll = ttk.Scrollbar(image_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scroll = ttk.Scrollbar(image_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        self.image_container = self.canvas.create_image(0, 0, anchor=tk.NW)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        right_pane.add(image_frame, weight=3)

        # --- Текстовое поле ---
        text_frame = ttk.Frame(right_pane)
        label = ttk.Label(text_frame, text="Распознанный текст:", font=('Segoe UI Semibold', 10))
        label.pack(anchor='w', padx=5, pady=(5, 0))

        self.text_widget = tk.Text(
            text_frame, wrap=tk.WORD, font=('Consolas', 11), bg='#fdf6e3', fg='#002b36'
        )
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        right_pane.add(text_frame, weight=2)

    def on_canvas_resize(self, event):
        """Подстраивает изображение под ширину canvas (без искажения пропорций)"""
        if self.original_image is not None:
            self.display_image(self.original_image)

    def load_image(self):
        filetypes = [("Изображения", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp")]
        path = filedialog.askopenfilename(title="Выберите изображение", filetypes=filetypes)
        if not path:
            return

        img = cv2.imread(path)
        if img is None:
            messagebox.showerror("Ошибка", "Невозможно загрузить изображение.")
            return

        self.image_path = path
        self.original_image = img
        self.processed_image = None
        self.path_label.config(text=os.path.basename(path))
        self.text_widget.delete(1.0, tk.END)
        self.display_image(img)
        self.status_var.set("Изображение загружено")

    def display_image(self, img: cv2.Mat):
        """Отображает изображение с автоматическим масштабированием под canvas"""
        if img is None:
            return

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        # Получаем размеры canvas
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        if canvas_w <= 1 or canvas_h <= 1:
            # Если ещё не отрисовано — отложим до следующего вызова
            self.root.after(50, lambda: self.display_image(img))
            return

        # Масштабируем с сохранением пропорций
        img_w, img_h = pil_img.size
        scale = min(canvas_w / img_w, canvas_h / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)

        resized = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.photo_ref = ImageTk.PhotoImage(resized)

        # Обновляем изображение на canvas
        self.canvas.itemconfig(self.image_container, image=self.photo_ref)
        self.canvas.config(scrollregion=(0, 0, new_w, new_h))

    def recognize_text(self):
        if self.original_image is None:
            messagebox.showwarning("Внимание", "Сначала загрузите изображение.")
            return

        self.status_var.set("Распознавание...")
        self.root.update_idletasks()

        try:
            gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            self.processed_image = thresh

            lang = self.lang_var.get().strip() or "eng"
            config = f'--oem 3 --psm 6 -l {lang}'
            text = pytesseract.image_to_string(thresh, config=config)

            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, text.strip() or "(Текст не найден)")

            self.display_image(thresh)  # Показываем обработанное изображение
            self.status_var.set("Распознавание завершено")

        except pytesseract.TesseractNotFoundError:
            messagebox.showerror("Ошибка", "Tesseract не найден. Проверьте путь к tesseract.exe.")
            self.status_var.set("Ошибка: Tesseract не установлен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось распознать текст:\n{e}")
            self.status_var.set("Ошибка при распознавании")

    def save_text(self):
        content = self.text_widget.get(1.0, tk.END).strip()
        if not content or content == "(Текст не найден)":
            messagebox.showwarning("Внимание", "Нет текста для сохранения.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
            title="Сохранить распознанный текст"
        )
        if not path:
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            messagebox.showinfo("Успех", f"Текст сохранён:\n{os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()