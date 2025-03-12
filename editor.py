import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# Кастомный модальный диалог для ввода целочисленного значения
class ModalInputDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt, minval=None, maxval=None, initialvalue=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self.minval = minval
        self.maxval = maxval

        # Метка с приглашением
        self.label = tk.Label(self, text=prompt)
        self.label.pack(padx=20, pady=10)
        
        # Поле ввода
        self.entry = tk.Entry(self)
        if initialvalue is not None:
            self.entry.insert(0, str(initialvalue))
        self.entry.pack(padx=20, pady=10)
        
        # Кнопка подтверждения
        self.ok_button = tk.Button(self, text="OK", command=self.on_ok)
        self.ok_button.pack(pady=10)
        
        # Делаем окно модальным (захватываем фокус)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.entry.focus_set()
        self.wait_window(self)

    def on_ok(self):
        try:
            value = int(self.entry.get())
            if self.minval is not None and value < self.minval:
                messagebox.showerror("Ошибка", f"Значение должно быть не меньше {self.minval}")
                return
            if self.maxval is not None and value > self.maxval:
                messagebox.showerror("Ошибка", f"Значение должно быть не больше {self.maxval}")
                return
            self.result = value
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число")
            return
        self.destroy()
    
    def on_close(self):
        self.result = None
        self.destroy()

class ImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Редактор изображений")
        self.image = None
        self.original_image = None
        self.processed_image = None
        self.file_path = None
        self.undo_stack = []

        # Фрейм для холста с добавлением скроллбаров
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.scroll_x = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL)
        self.scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.scroll_y = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL)
        self.scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(self.canvas_frame, bg="gray",
                                xscrollcommand=self.scroll_x.set,
                                yscrollcommand=self.scroll_y.set)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.scroll_x.config(command=self.canvas.xview)
        self.scroll_y.config(command=self.canvas.yview)

        # Привязка событий прокрутки колесом мыши
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_shift_mousewheel)

        # Панель кнопок
        self.frame = tk.Frame(root)
        self.frame.pack(pady=5)
        tk.Button(self.frame, text="Открыть изображение", command=self.load_image).pack(side=tk.LEFT)
        tk.Button(self.frame, text="Сделать снимок", command=self.capture_image).pack(side=tk.LEFT)
        tk.Button(self.frame, text="Изменить размер", command=self.resize_image).pack(side=tk.LEFT)
        tk.Button(self.frame, text="Понизить яркость", command=self.decrease_brightness).pack(side=tk.LEFT)
        tk.Button(self.frame, text="Нарисовать круг", command=self.draw_circle).pack(side=tk.LEFT)
        tk.Button(self.frame, text="Отмена", command=self.undo).pack(side=tk.LEFT)

        self.color_frame = tk.Frame(root)
        self.color_frame.pack(pady=5)
        tk.Button(self.color_frame, text="Красный канал", command=lambda: self.show_channel(2)).pack(side=tk.LEFT)
        tk.Button(self.color_frame, text="Зелёный канал", command=lambda: self.show_channel(1)).pack(side=tk.LEFT)
        tk.Button(self.color_frame, text="Синий канал", command=lambda: self.show_channel(0)).pack(side=tk.LEFT)

    # Утилита для ввода числа с помощью модального окна
    def ask_integer(self, title, prompt, minval=None, maxval=None, initialvalue=None):
        return ModalInputDialog(self.root, title, prompt, minval, maxval, initialvalue).result

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Изображения", "*.png;*.jpg")])
        if not file_path:
            return
        self.image = cv2.imread(file_path)
        if self.image is None:
            messagebox.showerror("Ошибка", "Не удалось загрузить изображение")
            return
        self.original_image = self.image.copy()
        self.processed_image = self.image.copy()
        self.file_path = file_path
        self.undo_stack = []
        self.display_image()

    def capture_image(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Ошибка", "Не удалось открыть веб-камеру")
            return
        ret, frame = cap.read()
        cap.release()
        if not ret:
            messagebox.showerror("Ошибка", "Не удалось сделать снимок")
            return
        self.image = frame
        self.original_image = self.image.copy()
        self.processed_image = self.image.copy()
        self.undo_stack = []
        self.display_image()

    def display_image(self):
        if self.processed_image is None:
            return
        # Конвертация BGR -> RGB и создание PhotoImage
        image_rgb = cv2.cvtColor(self.processed_image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        self.tk_image = ImageTk.PhotoImage(image_pil)
        self.canvas.delete("all")
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width = self.tk_image.width()
        img_height = self.tk_image.height()
        # Устанавливаем область прокрутки равной фактическому размеру изображения
        self.canvas.config(scrollregion=(0, 0, img_width, img_height))
        if img_width < canvas_width and img_height < canvas_height:
            # Если изображение меньше окна, рисуем его по центру
            x = (canvas_width - img_width) // 2
            y = (canvas_height - img_height) // 2
            self.canvas.create_image(x, y, anchor="nw", image=self.tk_image)
        else:
            # Если изображение больше, размещаем его с координатами (0,0)
            self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
            # Центрируем вид, если возможно
            if img_width > canvas_width:
                xfrac = (img_width/2 - canvas_width/2) / (img_width - canvas_width)
                self.canvas.xview_moveto(xfrac)
            if img_height > canvas_height:
                yfrac = (img_height/2 - canvas_height/2) / (img_height - canvas_height)
                self.canvas.yview_moveto(yfrac)

    def resize_image(self):
        if self.processed_image is None:
            return
        width = self.ask_integer("Изменение размера", "Введите ширину:", 1, None, self.processed_image.shape[1])
        height = self.ask_integer("Изменение размера", "Введите высоту:", 1, None, self.processed_image.shape[0])
        if width is not None and height is not None:
            self.undo_stack.append(self.processed_image.copy())
            self.processed_image = cv2.resize(self.processed_image, (width, height))
            self.display_image()

    def decrease_brightness(self):
        if self.processed_image is None:
            return
        # Запрашиваем процент затемнения: 0% – исходное изображение, 100% – полностью чёрное
        value = self.ask_integer("Яркость", "Введите процент затемнения (0 - исходная, 100 - черное):", 0, 100, 0)
        if value is not None:
            self.undo_stack.append(self.processed_image.copy())
            factor = (100 - value) / 100.0
            # Применяем коэффициент ко всем пикселям
            self.processed_image = (self.processed_image.astype(np.float32) * factor).clip(0, 255).astype(np.uint8)
            self.display_image()

    def draw_circle(self):
        if self.processed_image is None:
            return
        # Используем собственное диалоговое окно, чтобы 0 считалось корректным вводом
        x = self.ask_integer("Круг", "Введите X координату:", None, None, 0)
        y = self.ask_integer("Круг", "Введите Y координату:", None, None, 0)
        radius = self.ask_integer("Круг", "Введите радиус:", 1, None, 10)
        if x is not None and y is not None and radius is not None:
            self.undo_stack.append(self.processed_image.copy())
            # Рисуем красный круг (цвет в формате BGR: (0, 0, 255))
            cv2.circle(self.processed_image, (x, y), radius, (0, 0, 255), 2)
            self.display_image()

    def show_channel(self, channel):
        if self.processed_image is None:
            return
        self.undo_stack.append(self.processed_image.copy())
        channel_image = np.zeros_like(self.processed_image)
        channel_image[:, :, channel] = self.processed_image[:, :, channel]
        self.processed_image = channel_image
        self.display_image()

    def undo(self):
        if self.undo_stack:
            self.processed_image = self.undo_stack.pop()
            self.display_image()
        else:
            messagebox.showinfo("Отмена", "Нет действий для отмены")

    # Прокрутка колесом мыши: вертикально или (с зажатым Shift) горизонтально
    def on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * int(event.delta/120), "units")
    
    def on_shift_mousewheel(self, event):
        self.canvas.xview_scroll(-1 * int(event.delta/120), "units")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditor(root)
    root.mainloop()
