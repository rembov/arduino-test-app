import json
import tkinter as tk
from tkinter import messagebox, StringVar, ttk
from threading import Thread
import serial.tools.list_ports
from datetime import datetime
import subprocess
import os
from serial_handler import SerialHandler
from pdf_report import PDFReport
import time


class SplashScreen(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("Исправленный стенд НС")
        self.geometry("500x300")
        self.overrideredirect(True)  # Убираем рамку окна

        # Конфигурация заставки
        splash_text = "Исправленный стенд НС"
        splash_image_path = "splash_image.png"  # Укажите путь к изображению заставки

        # Загрузка изображения заставки
        try:
            self.image = tk.PhotoImage(file=splash_image_path)
            image_label = tk.Label(self, image=self.image)
            image_label.pack()
        except Exception as e:
            print(f"Ошибка загрузки изображения: {e}")
            tk.Label(self, text="Не удалось загрузить изображение", fg="red").pack()

        # Текст заставки
        tk.Label(self, text=splash_text, font=("Arial", 16)).pack(pady=10)

        # Закрытие заставки через 5 секунд и открытие основного окна
        self.after(5000, self.destroy)


class PortConfigurationWindow(tk.Toplevel):
    def __init__(self, master=None, refresh_ports_callback=None, on_select_port=None):
        super().__init__(master)
        self.title("Настройка подключения")
        self.geometry("300x200")

        self.refresh_ports_callback = refresh_ports_callback
        self.on_select_port = on_select_port
        self.selected_port = StringVar()

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Выберите COM-порт:").pack(pady=10)

        self.port_menu = ttk.Combobox(self, textvariable=self.selected_port)
        self.port_menu.pack(pady=10)
        self.refresh_ports()

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Подтвердить", command=self.confirm_port).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Отменить", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_menu['values'] = ports
        if not ports:
            messagebox.showwarning("Предупреждение", "Нет доступных COM-портов.")
        self.after(2000, self.refresh_ports)  # Обновление списка каждые 2 секунды

    def confirm_port(self):
        selected_port = self.selected_port.get()
        if selected_port:
            self.on_select_port(selected_port)
            self.destroy()
        else:
            messagebox.showerror("Ошибка", "Выберите COM-порт")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Исправленный стенд НС")
        self.create_reports_folder()
        self.serial_handler = SerialHandler()
        self.pdf_report = PDFReport()
        self.last_report_path = ""
        self.selected_port = StringVar()
        self.auto_connect_var = tk.BooleanVar()
        self.geometry("800x500")
        self.test_results = [""] * 5  # Список для хранения результатов тестов
        self.load_settings()
        self.create_widgets()

    def create_widgets(self):
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Настройка подключения", command=self.configure_connection)
        file_menu.add_command(label="Подключить/отключить", command=self.toggle_connection)
        file_menu.add_command(label="Печать отчета", command=self.print_report)
        file_menu.add_command(label="Архив протоколов", command=self.open_archive)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit)
        menu_bar.add_cascade(label="Меню", menu=file_menu)

        # Поля ввода
        labels = [
            "ФИО оператора", "Дата испытаний", "Объект",
            "Номер блока", "Место испытаний", "Наименование присоединения"
        ]

        self.entries = {}

        for i, label in enumerate(labels):
            tk.Label(self, text=label).grid(row=i + 2, column=0, sticky='e')
            entry = tk.Entry(self, width=40)
            entry.grid(row=i + 2, column=1)
            self.entries[label] = entry

        # Формат даты: 11.11.2024
        self.entries["Дата испытаний"].insert(0, datetime.now().strftime("%d.%m.%Y"))

        self.check_var = tk.BooleanVar()
        tk.Checkbutton(self, text="Исправность подключения блока проверена", variable=self.check_var).grid(row=8,
                                                                                                           column=1,
                                                                                                           sticky='w')

        self.auto_connect_var = tk.BooleanVar()
        tk.Checkbutton(self, text="Автоматическое подключение", variable=self.auto_connect_var,
                       command=self.save_settings).grid(row=8, column=2, sticky='w')

        # Кнопки тестов с индикаторами
        self.result_vars = []
        for i in range(5):
            tk.Button(self, text=f"Запуск теста {i + 1}", command=lambda i=i: self.start_test(i)).grid(row=9 + i,
                                                                                                       column=0)

            # Круглый индикатор статуса
            status_indicator = tk.Canvas(self, width=20, height=20, highlightthickness=0)
            circle = status_indicator.create_oval(2, 2, 18, 18, fill="gray")
            status_indicator.grid(row=9 + i, column=1)

            # Поле результата теста
            result_var = StringVar(value="Поле результата для теста")
            tk.Label(self, textvariable=result_var, width=30).grid(row=9 + i, column=2)

            # Сохраняем индикатор и переменную результата
            self.result_vars.append((result_var, status_indicator, circle))

        # Напряжение сети
        tk.Label(self, text="Напряжение сети:").grid(row=14, column=0)
        self.voltage_display = tk.Label(self, text="0 V", bg="white", width=10)
        self.voltage_display.grid(row=14, column=1)

        # Открытие последнего отчета и дата
        tk.Button(self, text="Открыть последний отчет", command=self.open_last_report).grid(row=15, column=0)
        self.last_report_label = tk.Label(self,
                                          text=f"Дата и время последнего отчета: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        self.last_report_label.grid(row=15, column=1)

        # Индикатор подключения (круг)
        self.connection_indicator = tk.Canvas(self, width=100, height=100, highlightthickness=0)
        self.connection_indicator.place(relx=0.95, rely=0.95, anchor='se')

        # Изначально красный круг (отключено)
        self.circle = self.connection_indicator.create_oval(10, 10, 90, 90, fill="red")

        # Автоматическая настройка подключения, если включена
        if self.auto_connect_var.get() and self.selected_port.get():
            self.toggle_connection()

    def create_reports_folder(self):
        """Проверка и создание каталога для отчетов."""
        if not os.path.exists('reports'):
            os.makedirs('reports')

    def load_settings(self):
        """Загружает настройки подключения из JSON файла."""
        try:
            with open("connection_settings.json", "r") as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            return {"selected_port": "", "auto_connect": False}
        except json.JSONDecodeError:
            return {"selected_port": "", "auto_connect": False}

    def save_settings(self):
        """Сохраняет настройки в файл"""
        settings = {
            "selected_port": self.selected_port.get(),
            "auto_connect": self.auto_connect_var.get()
        }
        with open("settings.json", "w") as f:
            json.dump(settings, f)

    def create_reports_folder(self):
        """Проверка и создание каталога для отчетов."""
        if not os.path.exists('reports'):
            os.makedirs('reports')

    def update_voltage_display(self):
        """Обновление значения напряжения в реальном времени"""
        if self.serial_handler.connection and self.serial_handler.connection.is_open:
            try:
                # Прочитаем данные с Arduino, предположим, что данные приходят в виде "3.3"
                voltage_data = self.serial_handler.read_data()
                if voltage_data:
                    voltage = voltage_data.strip()  # Очистка от лишних пробелов
                    self.voltage_display.config(text=f"{voltage} В")
                else:
                    self.voltage_display.config(text="Нет данных")
            except Exception as e:
                self.voltage_display.config(text="Ошибка чтения")
        self.after(1000, self.update_voltage_display)  # Обновление каждую секунду

    def update_indicator(self, color):
        """Обновляет цвет индикатора подключения."""
        self.connection_indicator.itemconfig(self.circle, fill=color)

    def toggle_connection(self):
        """Переключает состояние подключения к порту."""
        port = self.selected_port.get()
        if self.serial_handler.connection and self.serial_handler.connection.is_open:
            # Закрываем подключение
            self.serial_handler.connection.close()
            self.update_indicator("red")
            messagebox.showinfo("Информация", "Подключение закрыто.")
        else:
            try:
                # Открываем подключение
                self.serial_handler.connect(port, 9600)
                if self.serial_handler.connection and self.serial_handler.connection.is_open:
                    self.update_indicator("green")
                    messagebox.showinfo("Информация", "Успешное подключение.")
                else:
                    raise Exception("Не удалось подключиться")
            except Exception as e:
                self.update_indicator("red")
                messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")

    def start_test(self, test_number):
        if not all(entry.get() for entry in self.entries.values()):
            # Подсвечиваем незаполненные поля
            for label, entry in self.entries.items():
                if not entry.get():
                    entry.config(bg="red")
                else:
                    entry.config(bg="white")
            messagebox.showerror("Ошибка", "Заполните все обязательные поля")
            return

        def test_operation():
            command = ["UNUSED"] * 5
            command[test_number] = "START"
            self.serial_handler.send_command(";".join(command) + "\n")

            time.sleep(2)  # Задержка для получения ответа

            response = self.serial_handler.read_data()

            if response:
                self.handle_test_response(test_number, response)
                self.generate_report_after_test()  # Генерация отчета после теста
            else:
                messagebox.showerror("Ошибка", "Нет ответа от устройства")

        Thread(target=test_operation).start()

    def generate_report_after_test(self):
        """Генерация отчета после выполнения теста"""
        if not self.entries["ФИО оператора"].get():
            messagebox.showerror("Ошибка", "Заполните данные оператора")
            return

        report_data = {key: entry.get() for key, entry in self.entries.items()}
        test_results = [var.get() for var, _ in self.result_vars]

        # Создание папки reports, если она не существует
        reports_folder = "reports"
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Генерация отчета
        report_path = self.pdf_report.generate(report_data["ФИО оператора"],
                                               report_data["Объект"],
                                               report_data["Номер блока"],
                                               report_data["Место испытаний"],
                                               report_data["Наименование присоединения"],
                                               "success" if "OK" in test_results else "failure")

        # Отображение сообщения о завершении
        messagebox.showinfo("Информация", f"Отчет успешно сгенерирован!\nСохранен по пути: {report_path}")

    def handle_test_response(self, test_number, response):
        """Обрабатывает ответ от устройства."""
        result_var, status_indicator, circle = self.result_vars[test_number]

        try:
            if "ERROR" in response:
                result = "Ошибка"
                status_indicator.itemconfig(circle, fill="red")
            elif "OK" in response:
                result = "Успех"
                status_indicator.itemconfig(circle, fill="green")
            else:
                result = "Неизвестный результат"
                status_indicator.itemconfig(circle, fill="gray")

            result_var.set(result)
        except Exception as e:
            result_var.set(f"Ошибка: {e}")
            status_indicator.itemconfig(circle, fill="red")

    def configure_connection(self):
        PortConfigurationWindow(master=self, on_select_port=self.on_port_selected)

    def on_port_selected(self, port):
        """Вызывается, когда порт выбран."""
        self.selected_port.set(port)
        # Автоматически сохраняем настройки
        self.save_settings()

        # Если автоподключение включено, пытаемся подключиться
        if self.auto_connect_var.get():
            self.toggle_connection()

    def print_report(self):
        """Печать отчета"""
        if not self.entries["ФИО оператора"].get():
            messagebox.showerror("Ошибка", "Заполните данные оператора")
            return

        report_data = {key: entry.get() for key, entry in self.entries.items()}
        test_results = [var.get() for var, _ in self.result_vars]

        self.pdf_report.generate(report_data, test_results)
        messagebox.showinfo("Информация", "Отчет успешно сгенерирован!")

    def open_last_report(self):
        """Открытие последнего отчета"""
        if self.last_report_path:
            subprocess.Popen(["open", self.last_report_path])
        else:
            messagebox.showerror("Ошибка", "Отчет не найден")

    def open_archive(self):
        """Открытие архива отчетов"""
        archive_folder = "reports"
        if os.path.exists(archive_folder):
            # Открытие папки в проводнике Windows
            subprocess.Popen(["explorer", archive_folder])
        else:
            messagebox.showerror("Ошибка", f"Архив не найден: {archive_folder}")


def main():
    root = App()
    # Показываем заставку перед запуском основного окна
    splash = SplashScreen(root)
    root.withdraw()  # Скрываем основное окно на время заставки
    splash.wait_window()  # Ждём закрытия заставки
    root.deiconify()  # Показываем основное окно
    root.mainloop()
