import serial

class SerialHandler:
    def __init__(self):
        self.connection = None

    def connect(self, port, baud_rate, timeout=1):
        """
        Устанавливает подключение к порту с заданным параметром baud_rate и тайм-аутом.
        :param port: Порт (например, 'COM3' или '/dev/ttyUSB0')
        :param baud_rate: Скорость передачи данных
        :param timeout: Тайм-аут для операций
        """
        try:
            self.connection = serial.Serial(port, baud_rate, timeout=timeout)
            print("Подключение к Arduino установлено.")
        except Exception as e:
            print(f"Ошибка подключения к Arduino: {e}")
            self.connection = None

    def send_command(self, command):
        """
        Отправляет команду на Arduino.
        :param command: Команда для отправки
        """
        if self.connection and self.connection.is_open:
            try:
                self.connection.write((command + '\n').encode())
                print(f"Команда отправлена: {command}")
            except Exception as e:
                print(f"Ошибка отправки команды: {e}")
        else:
            print("Ошибка: Соединение не установлено.")

    def read_data(self):
        """
        Читает строку данных от Arduino.
        :return: Строка данных или пустая строка в случае ошибки
        """
        if self.connection and self.connection.is_open:
            try:
                data = self.connection.readline().decode().strip()
                if data:
                    print(f"Получены данные: {data}")
                return data
            except Exception as e:
                print(f"Ошибка чтения данных: {e}")
                return ""  # Возврат пустой строки в случае ошибки
        else:
            print("Ошибка: Соединение не установлено.")
            return ""

    def close(self):
        """
        Закрывает подключение.
        """
        if self.connection and self.connection.is_open:
            self.connection.close()
            print("Подключение закрыто.")
        else:
            print("Ошибка: Соединение не было установлено.")
