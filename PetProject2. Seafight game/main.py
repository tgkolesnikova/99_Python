import os
import pygame
import random

SIZE = WIDTH, HEIGHT = 972, 600
STEP = 8
FPS = 60

pygame.init()
random.seed(version=2)
pygame.key.set_repeat(100, 70)
clock = pygame.time.Clock()
screen = pygame.display.set_mode(SIZE)


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname).convert()
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)

    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()

    return image


def load_mom_hands():
    mom_hands = []
    for i in range(10):
        image = load_image('mom_hands/mom_hands' + str(i + 1) + '.gif')
        mom_hands.append(image)
    return mom_hands


def draw_my_hands():
    # Ребенок попросил монетку
    screen.blit(my_hands, (130, 325))   # картинка с протянутыми ладошками
    # текст в пузыре
    font = pygame.font.Font(None, 40)
    text = font.render("Мам, дай монетку!", True, (0, 120, 175))
    text_x = WIDTH // 4 - text.get_width() // 2
    text_y = HEIGHT // 2 - text.get_height() // 2
    text_w = text.get_width()
    text_h = text.get_height()
    screen.blit(text, (text_x, text_y))
    pygame.draw.ellipse(screen, (0, 120, 175), (text_x - 20, text_y - 20, text_w + 40, text_h + 40), 2)
    pygame.draw.ellipse(screen, (0, 120, 175), (10, 480, 50, 25), 2)
    pygame.draw.ellipse(screen, (0, 120, 175), (30, 420, 80, 40), 2)
    pygame.draw.ellipse(screen, (0, 120, 175), (50, 350, 130, 45), 2)


def draw_mom_hands(i):
    screen.fill('white')

    # Мама дала монетку
    font = pygame.font.Font(None, 50)
    text = font.render("Держи!", True, (255, 255, 255))
    text_x = WIDTH - 2 * text.get_width()
    text_y = HEIGHT // 2
    text_w = text.get_width()
    text_h = text.get_height()
    pygame.draw.ellipse(screen, (0, 120, 175), (text_x - 20, text_y - 40, text_w + 40, text_h + 40), 0)
    screen.blit(text, (text_x, text_y - 20))
    pygame.draw.ellipse(screen, (0, 120, 175), (WIDTH - 60, HEIGHT // 3 - 100, 60, 25), 0)
    pygame.draw.ellipse(screen, (0, 120, 175), (WIDTH - 110, HEIGHT // 3 - 60, 90, 40), 0)
    pygame.draw.ellipse(screen, (0, 120, 175), (WIDTH - 180, HEIGHT // 3, 130, 50), 0)

    draw_my_hands()                             # вернули руки ребенка
    screen.blit(mom_hands[i % 10], (420, -45))  # картинка рука мамы

    clock.tick(12)


def draw_title(i):
    screen.fill('white')
    title1 = pygame.transform.scale(title, (3 * i, 3 * i + 30))
    screen.blit(title1, (3 * i - 60, i - 60))

    clock.tick(20)


def draw_arrow():
    font = pygame.font.Font(None, 28)
    text = font.render("Кинь монетку >>", True, (255, 255, 255))
    screen.blit(text, (290, 510))


def draw_torpedos_count(count):
    font = pygame.font.Font(None, 15)
    color = 'darkgreen' if count > 3 else ((255, 204, 0) if count == 0 else 'red')
    text = "Торпед\n осталось: " + str(count) if count > 0 else "Нажмите <Пробел> для продолжения"
    image = font.render(text, True, color)
    screen.blit(image, (30, 550))


class Torpedo(pygame.sprite.Sprite):            # класс "Торпеда"
    def __init__(self, x, y):
        super().__init__(torpedo_sprites)
        self.image = load_image('torpedo.png')  # спрайт торпеды
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        pygame.mixer.music.load('data/torpedo.mp3')       # звук взрыва
        pygame.mixer.music.play()

    def update(self):                           # метод update()
        if self.rect.y >= 410:                  # торпеда ещё в море
            self.rect = self.rect.move(0, -5)
        else:
            self.kill()                         # улетела мимо


class Ship(pygame.sprite.Sprite):               # класс "Корабль"
    def __init__(self, filename, x=None, diff_x=1):
        super().__init__(ships_sprites)
        self.ship_image = load_image(filename)
        self.deth_image = load_image("ship6.gif")

        self.image = self.ship_image            # начальное изображение корабля

        self.rect = self.image.get_rect()       # размеры ограничивающего прямоугольника
        self.rect[0] -= 5                       # сократить на 5 пикселей с каждой стороны
        self.rect[2] -= 5                       # чтобы было труднее попасть
        self.rect[3] -= 5

        # место зарождения корабля
        if x:
            self.rect.x = x
        else:
            self.rect.x = random.choice([-160, WIDTH + 160])

        self.rect.y = 330                                       # линия горизонта
        self.diff_x, self.diff_y = diff_x, 0                    # смещения по осям
        self.transform_angel = random.randrange(-90, 90, 10)    # угол, на который повернется изображение при потоплении
        self.revert = 1                                         # изображение развернуто (да / нет)
        self.live = True                                        # кораблик жив / потоплен

    def reverse(self):                                          # разворот за экраном
        if self.rect.x > (WIDTH + 80) or self.rect.x < -150:
            self.diff_x = -self.diff_x
            self.image = pygame.transform.flip(self.image, True, False)
            self.revert = -self.revert

    def deth(self):                                             # кораблик тонет
        self.diff_y = 1
        self.diff_x = 0
        if self.revert == 1:
            self.image = self.deth_image
        else:
            self.image = pygame.transform.flip(self.deth_image, True, False)

        self.image = pygame.transform.rotate(self.image, self.transform_angel)

        if self.rect.y >= HEIGHT - 125:
            self.rect.y = HEIGHT - 125
        else:
            self.rect.y += self.diff_y

    def update(self):                           # метод update()
        global result
        if self.live:
            self.reverse()
            self.rect.x += self.diff_x
            if pygame.sprite.spritecollideany(self, torpedo_sprites) and self.image != self.deth_image:
                x = self.rect.x + 35
                center = x, 365
                expl = Explosion(center)
                ships_sprites.add(expl)
                result += 1
                self.live = False
        else:
            self.deth()


class Explosion(pygame.sprite.Sprite):          # класс "Взрыв"
    def __init__(self, center):
        pygame.sprite.Sprite.__init__(self)

        self.explosion_anim = []                # загрузка всех кадров взрыва (9 штук)
        for i in range(11):
            filename = 'explosions/explosion' + str(i + 1) + '.gif'
            img = load_image(filename)
            img_lg = pygame.transform.scale(img, (105, 105))
            self.explosion_anim.append(img_lg)

        self.image = self.explosion_anim[0]     # начальный кадр
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50

    def update(self):                                       # метод update()
        global result
        now = pygame.time.get_ticks()
        pygame.mixer.music.load('data/explosion.mp3')       # звук взрыва
        pygame.mixer.music.play()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(self.explosion_anim):
                filename = 'ship' + str(random.randrange(1, 5)) + '.gif'
                Ship(filename, -150, result // 3 + 1)       # создаем новый корабль, взамен потопленного
                self.kill()
            else:
                center = self.rect.center
                self.image = self.explosion_anim[self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center


#      ОСНОВНАЯ ПРОГРАММА       #
my_hands = load_image('hands.jpg')      # руки ребенка
mom_hands = load_mom_hands()            # рука мамы
title = load_image('title.jpg')         # изображение игрального автомата
coin = load_image('coin.png', -1)       # монетка 15 копеек (курсор)
pygame.mixer.music.load('data/insert_coin.mp3')  # звук монетки, упавшей в монетоприемник

scene = load_image('scene.gif')         # море, небо, скалы
scene4 = load_image('scene4.gif')       # только скалы (чтобы кораблики прятались за ними)
background = load_image('background.gif')       # видоискатель перископа
x = -243                                # начальное положение видоискателя

cur_sprites = pygame.sprite.Group()     # группа спрайтов для замены курсора
cursor = pygame.sprite.Sprite(cur_sprites)
cursor.image = coin
cursor.rect = coin.get_rect()
w_coin, h_coin = coin.get_rect()[2], coin.get_rect()[3]

ships_sprites = pygame.sprite.Group()   # группа спрайтов с корабликами
coords, ships = [], []
while len(coords) < 6:                  # нагенерируем 5 разных координат по х для размещения кораблей
    coord = random.randrange(-80, WIDTH + 80, 140)
    if coord not in coords:
        coords.append(coord)
for j in range(5):                      # 5 начальных кораблей, скорость = 1
    filename = 'ship' + str(j + 1) + '.gif'
    ships.append(Ship(filename, coords[j]))

torpedo_sprites = pygame.sprite.Group()     # группа спрайтов для торпеды

torpedos_count = 10                     # количество выстрелов
result = 0                              # количество попаданий
fight = False                           # признак стрельбы торпедой
running = True
game = 0                                # 0 - заставка;  1 - игра;   2 - конец игры
i = 0                                   # счетчик внутри игрового цикла
while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill('white')
    pygame.mouse.set_visible(False)     # скрываем системный курсор мыши
    if i < 70:
        draw_my_hands()                 # заставка 1.1
    elif i < 80:
        draw_mom_hands(i)               # заставка 1.2
    elif i < 110:
        draw_title(i)                   # заставка 2.1
    else:                               # собственно игра

        if game == 0:                   # game == 0 - игра еще не началась, надо засунуть монетку в автомат
            screen.blit(title, ((WIDTH - 506) // 2, 0))  # изображение игрального автомата
            draw_arrow()

            if event.type == pygame.MOUSEMOTION:
                if game == 0:
                    cursor.rect.x, cursor.rect.y = event.pos[0], event.pos[1]   # курсор - монетка

            if event.type == pygame.MOUSEBUTTONDOWN:
                if 465 <= event.pos[0] <= 525 and 470 <= event.pos[1] <= 540:

                    if w_coin > 30 and h_coin > 30:
                        pygame.mixer.music.play()
                        coin = pygame.transform.scale(coin, (w_coin, h_coin))
                        w_coin -= 20
                        h_coin -= 20
                        cursor.image = coin
                        cursor.rect = coin.get_rect()
                        cursor.rect.x, cursor.rect.y = event.pos[0], event.pos[1]
                    else:
                        game = 1                    # монетку засунули, переходим к игре

            if pygame.mouse.get_focused():
                cur_sprites.draw(screen)

        elif game == 1:                             # game == 1 - играем!
            if torpedos_count >= 0:                 # когда 0 торпед - работает все, кроме нажатия на пробел (выстрел)

                cursor.kill()                       # удаляем курсор-монетку, дальше только клавиатура

                screen.blit(scene, (0, 0))          # рисуем небо, море

                ships_sprites.draw(screen)          # запускаем корабли
                ships_sprites.update()

                screen.blit(scene4, (0, 0))         # рисуем скалы
                screen.blit(background, (x, 0))     # рисуем видоискатель

                draw_torpedos_count(torpedos_count)

                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:             # смотрим, что там слева
                    x -= STEP
                    fight = False
                    if x >= -364:
                        screen.blit(background, (x, 0))
                    else:
                        x = -364
                elif keys[pygame.K_RIGHT]:          # смотрим, что там справа
                    x += STEP
                    fight = False
                    if x <= -58:
                        screen.blit(background, (x, 0))
                    else:
                        x = -58
                elif keys[pygame.K_SPACE] and not fight and torpedos_count > 0:       # стреляем, но только если:
                    Torpedo(x + 700, 510)                                                # в данный момент нет выстрела
                    torpedos_count -= 1                                                  # есть хотя бы 1 торпеда
                    if torpedos_count == 0:
                        j = i                       # запомним момент, когда торпеды кончились
                    # print('Товарищ капитан!', torpedos_count, 'торпед осталось!')
                    fight = True                    # есть выстрел! Следующий выстрел заблокирован до нажатия на стрелки

                elif keys[pygame.K_SPACE] and torpedos_count == 0:
                    if abs(j - i) > 50:             # пауза перед третьей частью (итоги игры)
                        game = 2                    # торпеды кончились, игра завершается

                torpedo_sprites.draw(screen)        # рисуем спрайт с торпедой
                torpedo_sprites.update()

        elif game == 2:                             # game == 2 - итоги игры
            end = load_image('end.jpg')             # фон
            screen.blit(end, (0, 0))

            coords = [(42, 173), (77, 153), (112, 137), (147, 126), (182, 123), (217, 123),
                      (252, 126), (287, 137), (322, 153), (357, 173)]       # координаты кружков с цифрами

            if result > 10:                                                 # на всякий случай
                result = 10                                                 # (есть шанс убить одной торпедой 2 корабля)
            # result = 0                                                    # никакой кружок не закрашен
            if result > 0:
                pygame.draw.ellipse(screen, (250, 220, 5),                  # выделение цветом кружка с результатом
                                    (coords[result - 1][0], coords[result - 1][1], 35, 35), 0)

            font = pygame.font.Font(None, 40)                               # цифры в кружках
            for j in range(10):
                pygame.draw.ellipse(screen, (75, 5, 5), (coords[j][0], coords[j][1], 35, 35), 4)
                digit = font.render(str(j + 1), True, (65, 5, 5))
                if j != 9:
                    screen.blit(digit, (coords[j][0] + 10, coords[j][1] + 5))
            screen.blit(digit, (coords[9][0] + 2, coords[9][1] + 5))

    i += 1
    clock.tick(FPS)
    pygame.display.flip()
