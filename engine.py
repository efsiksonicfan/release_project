import pygame
import math

TILE_SIZE = 50

# Тексти для початкової катсцени (Undertale-style)
INTRO_SLIDES = [
    {"text": "Давно колись... Нижній сектор 'Ехо-Сіті' було законсервовано.", "image": "intro1.png"},
    {"text": "Усі автоматизовані системи безпеки залишилися в темряві.", "image": "intro2.png"},
    {"text": "Маленький робот-розвідник випадково впав у вентиляційну шахту...", "image": "intro3.png"},
    {"text": "Його оптичні сенсори пошкоджено. Видимість: 0%.", "image": "intro4.png"},
    {"text": "Єдиний шанс вижити — вбудований Акустичний Сонар.", "image": "intro5.png"}
]

TUTORIAL_PROMPTS = {
    "start": "Використовуй WASD для руху. Навколо повна темрява...",
    "sonar": "Натисни ПРОБІЛ, щоб запустити Сонар. Хвиля підсвітить стіни.",
    "battery": "Увага! Сонар витрачає БАТАРЕЮ. Вона заряджається, коли ти стоїш.",
    "finish": "Золотий квадрат — це вихід. Доберись до нього."
}

# Опис локацій
LEVEL_INFO = [
    {"name": "ЛОКАЦІЯ 0: ТЕСТОВИЙ СЕКТОР",   "wall_sprite": "wall_tutorial.png", "mechanic": "Навчання."},
    {"name": "ЛОКАЦІЯ 1: ІРЖАВИЙ БУНКЕР",    "wall_sprite": "wall_bunker.png",   "mechanic": "Низька видимість."},
    {"name": "ЛОКАЦІЯ 2: ЗАТОПЛЕНА ШАХТА",   "wall_sprite": "wall_mine.png",     "mechanic": "Рух уповільнено."},
    {"name": "ЛОКАЦІЯ 3: КРИСТАЛЬНІ ПЕЧЕРИ", "wall_sprite": "wall_mine.png",     "mechanic": "Радіус сонара збільшено."},
    {"name": "ЛОКАЦІЯ 4: КІБЕР-ЛАБОРАТОРІЯ", "wall_sprite": "wall_lab.png",      "mechanic": "Батарея відновлюється повільно."},
    {"name": "ЛОКАЦІЯ 5: ГОЛОВНЕ ЯДРО",      "wall_sprite": "wall_lab.png",      "mechanic": "Вороги розлючені!"}
]

# 6 РІВНІВ (0 - Навчальний, 1-5 - Основні)
# 6 РІВНІВ (Кожен рядок має мати РІВНО 16 символів!)
# 6 РІВНІВ (Кожен рядок має СУВОРО 16 символів, усього 7 рядків на рівень)
LEVELS = [
    # Рівень 0 (Навчальний)
    [
        "WWWWWWWWWWWWWWWW",
        "WP..............",
        "W...............",
        "W...............",
        "W...............",
        "W............FWW",
        "WWWWWWWWWWWWWWWW"
    ],
    # Рівень 1 (Іржавий бункер)
    [
        "WWWWWWWWWWWWWWWW",
        "WP.......W.....W",
        "W.WWWW.W.W.WWW.W",
        "W....W.W.W...W.W",
        "W.WW.W.W.WWW.W.W",
        "W............WFW",
        "WWWWWWWWWWWWWWWW"
    ],
    # Рівень 2 (Затоплена шахта)
    [
        "WWWWWWWWWWWWWWWW",
        "WP......B......W",
        "W.WWWW.....WWW.W",
        "W....W...W...W.W",
        "W.W.WWWW.W.W.W.W",
        "W.W.E......W.WFW",
        "WWWWWWWWWWWWWWWW"
    ],
    # Рівень 3 (Кристалічні печери)
    [
        "WWWWWWWWWWWWWWWW",
        "WP.............W",
        "W....WW....WW..W",
        "W....WW.E..WW..W",
        "W.......WW.....W",
        "W..............F",
        "WWWWWWWWWWWWWWWW"
    ],
    # Рівень 4 (Кібер-лабораторія)
    [
        "WWWWWWWWWWWWWWWW",
        "WP......B......W",
        "W...WWWWWWWW...W",
        "W.E.W..B...W...W",
        "W...W.WWWW.W.E.W",
        "W......B.....WFW",
        "WWWWWWWWWWWWWWWW"
    ],
    # Рівень 5 (Сектор ядра)
    [
        "WWWWWWWWWWWWWWWW",
        "WP.............W",
        "W....W.....W...W",
        "W.E..W..B..W.E.W",
        "W....WWWWWWW...W",
        "W......B.....WFW",
        "WWWWWWWWWWWWWWWW"
    ]
]

class Enemy:
    def __init__(self, x, y, level_idx):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.base_x = x
        self.target_pos = None
        
        # Унікальна швидкість ворогів залежно від атмосфери рівня
        if level_idx == 5:
            self.speed = 4
        else:
            self.speed = 2
            
        self.direction = 1

    def update(self):
        if self.target_pos:
            tx, ty = self.target_pos
            dx, dy = tx - self.rect.centerx, ty - self.rect.centery
            dist = math.hypot(dx, dy)
            if dist > 5:
                self.rect.x += (dx / dist) * (self.speed * 1.5)
                self.rect.y += (dy / dist) * (self.speed * 1.5)
            else:
                self.target_pos = None
        else:
            self.rect.x += self.speed * self.direction
            if abs(self.rect.x - self.base_x) > 120:
                self.direction *= -1