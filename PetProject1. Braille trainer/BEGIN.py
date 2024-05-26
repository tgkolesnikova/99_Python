import random
import sys
import sqlite3

import game  # второй файл

from PyQt5 import uic
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication, QWidget, QTextBrowser, QLabel, QTableWidgetItem
from PyQt5.QtGui import QPixmap, QFont, QIcon

SCREEN_SIZE = [611, 621]
FACTS_NUMBER = 39      # кол-во фактов в БД


class StartMenu(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)

        self.tableWidget.hide()  # Список предыдущих игр пока скрыть
        self.pushButton.hide()   # и кнопку для ее закрывания - тоже

        self.pushButton_1.clicked.connect(self.run_game)        # Новая игра
        self.pushButton_2.clicked.connect(self.get_records)     # Рекорды
        self.pushButton_5.clicked.connect(self.run_day_fact)     # Факт дня
        self.pushButton_6.clicked.connect(self.run_day_fact)     # О программе
        self.pushButton_7.clicked.connect(self.run_day_fact)     # Выход

    def run_game(self):
        self.close()
        self.choice_form = game.ChoiceGame()  # Начать новую игру (файл game.py, класс Choice_Game())
        self.choice_form.show()

    def get_records(self):
        # Подключение к БД, получение списка кортежей (Игра, Игрок, Угадал, Ошибся, Дата и время игры)
        con = sqlite3.connect("braille.db")
        cur = con.cursor()
        results = cur.execute("SELECT * FROM results").fetchall()
        con.close()  # Закрываем подключение к БД

        # Заполняем данными Таблицу - Список предыдущих игр:
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setHorizontalHeaderLabels([' Режим игры ', ' Имя игрока ', ' Угадал ',
                                                    ' Ошибся ', ' Дата и время игры '])
        for i, row in enumerate(results):
            self.tableWidget.setRowCount(self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                self.tableWidget.setItem(i, j, QTableWidgetItem(elem))
        self.tableWidget.resizeColumnsToContents()

        self.tableWidget.show()  # Показываем готовую таблицу
        self.pushButton.show()   # и кнопку для ее закрывания

        self.pushButton.clicked.connect(self.close_records)

    def close_records(self):    # Убрать таблицу с формы (скрыть)
        self.pushButton.hide()
        self.tableWidget.hide()

    def run_day_fact(self):
        # кнопки "Факт дня", "О программе", "Выход" закрывают окно с меню (StartMenu()),
        # открывают окно с картинкой и текстом факта дня (Hello())
        self.close()
        if self.sender() == self.pushButton_5:
            self.first_form = Hello('Факт дня', random.randint(1, FACTS_NUMBER - 2))  # Hello() со случ.фактом
            self.first_form.show()
        if self.sender() == self.pushButton_6:
            self.first_form = Hello('О программе', 999)     # Hello() с текстом "О программе" (факт № 999)
            self.first_form.show()


class Hello(QWidget):
    def __init__(self, text, number):
        super().__init__()
        self.title_text = text   # Заголовок над фактом дня (три варианта)
        self.fact_id = number    # Id факта в БД, который надо получить (0-Приветствие, 999-О программе, rand-Факт дня)

        # Подключение к БД, получение текста для факта дня
        con = sqlite3.connect("braille.db")
        cur = con.cursor()
        self.fact_text = cur.execute("SELECT * FROM Facts WHERE fact_id = ?", (self.fact_id,)).fetchall()
        con.close()  # Закрываем подключение к БД

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 100, *SCREEN_SIZE)
        self.setWindowTitle('Тренажер Брайля')
        self.setWindowIcon(QIcon('icon.png'))

        # Изображение (подложка)
        self.pixmap = QPixmap('braille.png')
        self.image = QLabel(self)
        self.image.move(0, 0)
        self.image.resize(611, 621)
        self.image.setPixmap(self.pixmap)

        # Заголовок над фактом дня
        self.label = QLabel(self)
        font_label = QFont()
        font_label.setPointSize(16)
        font_label.setBold(True)
        self.label.setFont(font_label)
        self.label.setText(self.title_text)
        self.label.move(25, 20)

        # Текст с фактом дня
        self.textBrowser = QTextBrowser(self)
        self.textBrowser.setGeometry(QRect(20, 52, 571, 201))
        font_text = QFont()
        font_text.setPointSize(10)
        self.textBrowser.setFont(font_text)
        self.textBrowser.setText(self.fact_text[0][1])       # текст факта дня получен из БД

    def closeEvent(self, event):
        self.start_form = StartMenu()      # Открываем форму с кнопочным меню
        self.start_form.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Hello('Привет!', 0)    # Hello() всегда разное, на старте программы это Приветствие (факт № 0)
    ex.show()
    sys.exit(app.exec())
