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
