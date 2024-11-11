import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime


class PDFReport:
    def __init__(self):
        self.file_path = ""

    def generate(self, operator, object_name, block_number, test_place, connection_name, status):
        """Генерирует PDF отчет."""

        # Создание папки, если она не существует
        reports_folder = "reports"
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Формирование пути для отчета
        self.file_path = os.path.join(reports_folder, f"report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf")

        try:
            c = canvas.Canvas(self.file_path, pagesize=A4)
            width, height = A4

            # Заголовок
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width / 2, height - 20, "Протокол проверки блока (ячейки)")

            # Данные отчета
            c.setFont("Helvetica", 12)
            y_position = height - 40

            data = [
                f"Объект: {object_name}",
                f"Номер блока: {block_number}",
                f"Место испытаний: {test_place}",
                f"Наименование присоединения: {connection_name}",
                f"Дата: {datetime.now().strftime('%Y-%m-%d')}",
            ]

            for line in data:
                c.drawString(20, y_position)
                c.drawString(20, y_position, line)
                y_position -= 10

            # Текст в зависимости от результата теста
            if status == "success":
                result_text = [
                    "В результате проведенной проверки установлено, что:",
                    "Напряжение срабатывания и отпускания контакторов в цепи",
                    "соответствует существующей схеме блока, которая соответствует",
                    "электрической принципиальной схеме.",
                    "После визуального осмотра и проведенной проверки блок",
                    "считать исправным и работоспособным."
                ]
            else:
                result_text = [
                    "В результате проведенной проверки установлено, что:",
                    "Напряжение срабатывания и отпускания контакторов в цепи",
                    "не соответствует, существующая схема блока не соответствует",
                    "электрической принципиальной схеме.",
                    "После визуального осмотра и проведенной проверки блок",
                    "считать неисправным и не работоспособным."
                ]

            for line in result_text:
                c.drawString(20, y_position, line)
                y_position -= 10

            # Подпись оператора
            c.drawString(20, y_position - 20, f"Оператор: _______________ {operator}")

            # Завершение страницы и сохранение
            c.showPage()
            c.save()

            return self.file_path

        except Exception as e:
            print(f"Ошибка при создании отчета: {e}")
            return None
