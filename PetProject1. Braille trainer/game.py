import sqlite3
import time
import sys
import random

import BEGIN  # первый файл (класс StartMenu)

from PyQt5 import uic
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QPushButton, QFrame, QLCDNumber, QLineEdit, QCheckBox

SCREEN_SIZE = [600, 450]
SYMBOL_NUMBER = 33
DOTS = [chr(0x25ef),  # белый круг - пустая точка
        chr(0x2b24)]  # черный круг - закрашенная точка


class ChoiceGame(QWidget):     # выбор игры
    def __init__(self):
        super().__init__()
        uic.loadUi('choice.ui', self)

        self.pushButton_1.clicked.connect(self.run)  # игра "Буквы"
        self.pushButton_2.clicked.connect(self.run)  # игра "Точки"

    def run(self):
        self.hide()
        if self.sender() == self.pushButton_1:
            self.game_chars_form = GameChars()
            self.game_chars_form.show()
        else:
            self.game_dots_form = GameDots()
            self.game_dots_form.show()

    def closeEvent(self, event):
        self.start_form = BEGIN.StartMenu()     # Открываем форму с кнопочным меню
        self.start_form.show()


class GameBase(QWidget):    # вспомогательный класс, общий для классов игр
    def __init__(self, game_type):
        super().__init__()
        self.game_type = game_type      # тип игры: "Буквы" или "Точки"
        self.gamer_name = ''            # имя игрока
        self.win_score, self.lose_score = 0, 0  # счет в игре (угаданые / не угаданные буквы)

        # Подключение к БД, получение списка кортежей (Буква, Код Брайля)
        con = sqlite3.connect("braille.db")
        cur = con.cursor()
        self.braille = cur.execute("SELECT * FROM braille").fetchall()
        con.close()  # Закрываем подключение к БД

    def closeEvent(self, event):
        date = time.strftime("%B %d, %Y, %X", time.localtime())
        new_data = (self.game_type, self.gamer_name, str(self.win_score),
                    str(self.lose_score), date)  # для записи в БД

        # проверка, чтобы не писать в БД пустые игры
        if not(self.gamer_name == '' or (self.win_score == 0 and self.lose_score == 0)):
            con = sqlite3.connect("braille.db")
            cur = con.cursor()
            cur.execute("INSERT INTO results VALUES(?, ?, ?, ?, ?)", new_data)  # запись в БД
            con.commit()
            con.close()  # Закрываем подключение к БД

        self.start_form = BEGIN.StartMenu()      # Открываем форму с кнопочным меню
        self.start_form.show()


class GameDots(GameBase):   # класс игры "Точки" (узнай букву по ее коду)
    def __init__(self):
        super().__init__('Точки')

        self.labels = []   # точки шрифта Брайля 6 штук
        self.buttons = []  # кнопки с буквами 33 штуки

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 100, *SCREEN_SIZE)
        self.setWindowTitle('Тренажер Брайля')
        self.setWindowIcon(QIcon('icon.png'))

        dot_font = QFont()
        dot_font.setPointSize(24)
        dot_font.setBold(True)
        for i in range(2):      # разместить на форме 6 точек шрифта Брайля
            for j in range(3):
                label = QLabel(self)
                label.setFont(dot_font)
                label.setText(DOTS[0])
                label.move(180 + i * 35, 30 + j * 35)
                self.labels.append(label)

        self.toplace_char_buttons()      # разместить на форме 33 кнопки с буквами

        label = QLabel(self)
        label.setText("Какая это буква?")
        label.move(170, 168)

        # вертикальная линия
        self.line = QFrame(self)
        self.line.setGeometry(QRect(425, 0, 2, 450))
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        # место для счета
        score_font = QFont()
        score_font.setPointSize(12)
        score_font.setUnderline(True)
        score_label = QLabel(self)
        score_label.setFont(score_font)
        score_label.setText("Ваш счет:")
        score_label.move(475, 220)
        win_label = QLabel(self)
        win_label.setText("Правильно:")
        win_label.move(455, 260)
        self.LCD_win = QLCDNumber(self)
        self.LCD_win.move(465, 280)
        self.LCD_win.display(self.win_score)
        lose_label = QLabel(self)
        lose_label.setText("Не правильно:")
        lose_label.move(455, 340)
        self.LCD_lose = QLCDNumber(self)
        self.LCD_lose.move(465, 360)
        self.LCD_lose.display(self.lose_score)

        # чекбокс с подсказкой
        self.checkBox = QCheckBox(self)
        self.checkBox.setText('Подсказка')
        self.checkBox.move(475, 425)

        # ввести имя игрока
        self.score_label = QLabel(self)
        self.score_label.setText("Представьтесь, пожалуйста:")
        self.score_label.move(435, 20)
        self.name_input = QLineEdit(self)
        self.name_input.setText('Неизвестный игрок')
        self.name_input.move(445, 40)

        # кнопка "Начать" (старт игры)
        self.button_start = QPushButton(self)
        self.button_start.setText("Начать!")
        self.button_start.resize(100, 20)
        self.button_start.move(460, 80)

        self.button_start.clicked.connect(self.run_game)   # нажата кнопка "Начать!", игра началась

    def run_game(self):
        self.gamer_name = self.name_input.text()

        # эти виджеты отключить
        self.name_input.setEnabled(False)
        self.button_start.setEnabled(False)

        self.generate_new_kod()     # первый код для угадывания

        for i in range(len(self.buttons)):
            self.buttons[i].clicked.connect(self.run_char_buttons)          # проверка нажатой буквы

    def run_char_buttons(self):
        if self.sender().text() == '':      # 3 кнопки лишние, пустые
            return None
        if self.sender().text() == self.symb:
            self.sender().setStyleSheet('background: rgb(0,255,0);')
            self.win_score += 1
            self.LCD_win.display(self.win_score)
        else:
            self.sender().setStyleSheet('background: rgb(255,0,0);')
            self.lose_score += 1
            self.LCD_lose.display(self.lose_score)

        self.generate_new_kod()     # следующий код для угадывания

    def generate_new_kod(self):
        rnd = random.randint(0, SYMBOL_NUMBER - 1)
        self.symb, self.kod = self.braille[rnd][0], self.braille[rnd][1]

        #print(self.braille[rnd])       # !!!!!  ПРАВИЛЬНЫЙ ОТВЕТ  !!!!!!!

        for i in range(6):
            self.labels[i].setText(DOTS[int(self.kod[i])])  # раскрашиваем точки шрифта Брайля

        if self.checkBox.isChecked():       # делаем подсказку игроку (или не делаем)))
            self.checkBox.setText(self.symb)
        else:
            self.checkBox.setText('Подсказка')

    def toplace_char_buttons(self):     # разместить на форме 33 кнопки с буквами
        button_font = QFont()
        button_font.setPointSize(14)
        k = 0
        for j in range(6):
            for i in range(6):
                button = QPushButton(self)
                button.setFont(button_font)
                if k < SYMBOL_NUMBER:
                    button.setText(self.braille[k][0])
                else:
                    button.setText('')
                button.resize(65, 37)
                button.move(10 + i * 68, 198 + j * 41)
                self.buttons.append(button)
                k += 1
        return None


class GameChars(GameBase):      # класс игры "Буквы" (натыкай код для буквы)
    def __init__(self):
        super().__init__('Буквы')

        self.dot_counts = [0, 0, 0, 0, 0, 0]    # сколько раз нажали на соотв. точку Брайля
        self.dot_labels = []    # QLabel - виджеты с надписями - точками
        self.dot_buttons = []   # QButtons для управления состоянием точек

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 100, *SCREEN_SIZE)
        self.setWindowTitle('Тренажер Брайля')
        self.setWindowIcon(QIcon('icon.png'))

        # вертикальная линия
        self.line = QFrame(self)
        self.line.setGeometry(QRect(425, 0, 2, 450))
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        # место для счета
        score_font = QFont()
        score_font.setPointSize(12)
        score_font.setUnderline(True)
        score_label = QLabel(self)
        score_label.setFont(score_font)
        score_label.setText("Ваш счет:")
        score_label.move(475, 220)
        win_label = QLabel(self)
        win_label.setText("Правильно:")
        win_label.move(455, 260)
        self.LCD_win = QLCDNumber(self)
        self.LCD_win.move(465, 280)
        self.LCD_win.display(self.win_score)
        lose_label = QLabel(self)
        lose_label.setText("Не правильно:")
        lose_label.move(455, 340)
        self.LCD_lose = QLCDNumber(self)
        self.LCD_lose.move(465, 360)
        self.LCD_lose.display(self.lose_score)

        # место для случайной буквы
        font = QFont()
        font.setFamily('Arial')
        font.setPointSize(90)
        font.setBold(True)
        self.random_symbol = QLabel('?', self)
        self.random_symbol.setFont(font)
        self.random_symbol.move(170, 40)

        label = QLabel(self)
        label.setText("Какой код у этой буквы?")
        label.move(150, 190)

        # разместить 6 пустых точек Брайля, заполнить ими список QLabel'ов
        self.create_dots()
        self.dot_labels[0].move(175, 230)
        self.dot_labels[1].move(175, 265)
        self.dot_labels[2].move(175, 300)
        self.dot_labels[3].move(210, 230)
        self.dot_labels[4].move(210, 265)
        self.dot_labels[5].move(210, 300)

        # разместить 6 управляющих кнопок для точек, заполнить ими список кнопок
        for i in range(6):
            button = QPushButton(str(i + 1), self)
            button.resize(35, 35)
            button.setEnabled(False)
            self.dot_buttons.append(button)
        self.dot_buttons[0].move(130, 235)
        self.dot_buttons[1].move(130, 270)
        self.dot_buttons[2].move(130, 305)
        self.dot_buttons[3].move(250, 235)
        self.dot_buttons[4].move(250, 270)
        self.dot_buttons[5].move(250, 305)

        # кнопка и надпись для проверки ответа
        self.check_button = QPushButton(self)
        self.check_button.setText('...')
        self.check_button.move(170, 400)
        self.check_button.setEnabled(False)

        self.check_label = QLabel('', self)
        self.check_label.move(175, 360)

        # ввести имя игрока
        self.score_label = QLabel(self)
        self.score_label.setText("Представьтесь, пожалуйста:")
        self.score_label.move(435, 20)
        self.name_input = QLineEdit(self)
        self.name_input.setText('Неизвестный игрок')
        self.name_input.move(445, 40)

        # кнопка "Начать" (старт игры)
        self.button_start = QPushButton(self)
        self.button_start.setText("Начать!")
        self.button_start.resize(100, 20)
        self.button_start.move(460, 80)

        self.button_start.clicked.connect(self.start_game)  # нажата кнопка "Начать!", игра началась

    def start_game(self):
        # эти виджеты отключить
        self.gamer_name = self.name_input.text()
        self.name_input.setEnabled(False)

        # эти виджеты подключить
        self.button_start.setEnabled(False)
        self.check_button.setEnabled(True)
        self.check_button.setText('Проверить')
        for i in range(6):
            self.dot_buttons[i].setEnabled(True)

        # первую букву сгенерировать
        self.generate_new_char()

        # менять цвет точек, когда игрок тыкает на кнопки 1,2,3,4,5,6
        for i in range(6):
            self.dot_buttons[i].clicked.connect(self.dot_labels_change)

        # при нажатии на кнопку "Проверить"
        self.check_button.clicked.connect(self.run_check)

    def run_check(self):
        # сначала проверить ответ игрока
        self.check_answer()

        # очистить точки от предыдущей попытки
        self.dot_counts = [0, 0, 0, 0, 0, 0]
        for i in range(6):
            self.dot_labels[i].setText(DOTS[0])

        # сгенерировать новую букву
        self.generate_new_char()

    def generate_new_char(self):
        # сгенерировать новую букву и вывести ее в QLabel
        rnd = random.randint(0, SYMBOL_NUMBER - 1)
        self.symb, self.kod = self.braille[rnd][0], self.braille[rnd][1]

        self.random_symbol.setText(self.symb)
        self.random_symbol.resize(self.random_symbol.sizeHint())

    def create_dots(self):
        # разместить 6  точек Брайля (ПУСТЫХ), заполнить или список QLabel'ов
        self.dot_labels.clear()
        dot_font = QFont()
        dot_font.setPointSize(24)
        dot_font.setBold(True)
        for i in range(6):
            label = QLabel(self)
            label.setFont(dot_font)
            label.setText(DOTS[0])
            self.dot_labels.append(label)

    def check_answer(self):
        # ответ игрока, собираем из количеств нажатий на кнопки 1,2,3,4,5,6
        gamer_answer = ''.join([str(x % 2) for x in self.dot_counts])

        # print(gamer_answer, self.kod)           # !!!! ПРАВИЛЬНЫЙ ОТВЕТ !!!!

        if gamer_answer == self.kod:
            self.check_label.setText('Правильно!')
            self.win_score += 1
            self.LCD_win.display(self.win_score)
        else:
            self.check_label.setText('Не правильно!')
            self.lose_score += 1
            self.LCD_lose.display(self.lose_score)

        self.check_label.resize(self.check_label.sizeHint())

    def dot_labels_change(self):
        # менять точки при щелчках на кнопки 1,2,3,4,5,6
        # четное кол-во раз нажали - белая (пустая) точка, иначе черная точка
        k = int(self.sender().text()) - 1
        self.dot_counts[k] += 1
        self.dot_labels[k].setText(DOTS[self.dot_counts[k] % 2])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ChoiceGame()
    ex.show()
    sys.exit(app.exec())
