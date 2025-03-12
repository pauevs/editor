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
    