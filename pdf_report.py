from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from datetime import datetime

class PDFReport:
    def __init__(self):
        self.file_path = ""

    def generate(self, operator, object_name, block_number, test_place, connection_name, status):
        """Генерирует PDF отчет."""
        self.file_path = f"report_{datetime.now().strftime('%d.%m.%Y_%H%M%S')}.pdf"
        c = canvas.Canvas(self.file_path, pagesize=A4)
        width, height = A4

        # Заголовок
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 20 * mm, "Протокол проверки блока (ячейки)")

        # Данные отчета
        c.setFont("Helvetica", 12)
        y_position = height - 40 * mm

        data = [
            f"ФИО оператора: {operator}",
            f"Объект: {object_name}",
            f"Номер блока: {block_number}",
            f"Место испытаний: {test_place}",
            f"Наименование присоединения: {connection_name}",
            f"Дата: {datetime.now().strftime('%Y-%m-%d')}",
        ]

        for line in data:
            c.drawString(20 * mm, y_position, line)
            y_position -= 10 * mm

        # Результаты проверки
        if status == "success":
            result_text = (
                "В результате проверки блок признан исправным и работоспособным.\n"
                "Все тесты пройдены успешно."
            )
        else:
            result_text = (
                "В результате проверки блок признан неисправным.\n"
                "Один или более тестов завершились с ошибкой."
            )

        for line in result_text.split("\n"):
            c.drawString(20 * mm, y_position, line)
            y_position -= 10 * mm

        # Подпись оператора
        c.drawString(20 * mm, y_position - 20 * mm, "Подпись оператора: ____________________")

        # Завершение создания PDF
        c.showPage()
        c.save()

        return self.file_path
