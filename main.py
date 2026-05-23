import pygame
import sys
import os
import math
import random
from engine import LEVELS, INTRO_SLIDES, LEVEL_INFO, Enemy
from visuals import generate_pixel_wave

pygame.init()
pygame.mixer.set_num_channels(64)

VIRTUAL_WIDTH, VIRTUAL_HEIGHT = 800, 600
virtual_screen = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

info = pygame.display.Info()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
pygame.display.set_caption("ECHOSCOPE")
clock = pygame.time.Clock()

# =====================================================================
# 🔤 ШРИФТИ
# =====================================================================
FONT_PATH = "assets/fonts/pixel_font.ttf"
if os.path.exists(FONT_PATH):
    font = pygame.font.Font(FONT_PATH, 18)
    title_font = pygame.font.Font(FONT_PATH, 44)
else:
    font = pygame.font.SysFont("Courier New", 18, bold=True)
    title_font = pygame.font.SysFont("Courier New", 44, bold=True)

# =====================================================================
# 🖼️ ЗАВАНТАЖЕННЯ СПРАЙТІВ
# =====================================================================
def load_sprite(path, size=None):
    if os.path.exists(path):
        img = pygame.image.load(path).convert_alpha()
        if size: img = pygame.transform.scale(img, size)
        return img
    return None

# Other stuff
spr_player = load_sprite("assets/sprites/other_stuff/player_sprite.png", (32, 32))
spr_finish = load_sprite("assets/sprites/other_stuff/finish.png", (50, 50))

# Sonar stuff
spr_battery_item = load_sprite("assets/sprites/sonar_stuff/battery_item.png", (24, 24))
spr_battery_hud = load_sprite("assets/sprites/sonar_stuff/battery_hud.png", (150, 20))
spr_block_filled = load_sprite("assets/sprites/sonar_stuff/block_filled.png", (10, 12))
spr_sonar_label = load_sprite("assets/sprites/sonar_stuff/sonar_label.png", (100, 15))

# Корінь папки sprites
spr_menu_title = load_sprite("assets/sprites/game_title.png", (400, 100))
icon = load_sprite("assets/sprites/game_icon.png")
if icon: pygame.display.set_icon(icon)

wave_template = generate_pixel_wave(300)

# =====================================================================
# 🔊 ЗВУКОВА СИСТЕМА
# =====================================================================
snd_ping, snd_scream, snd_pickup = None, None, None
snd_level_win, snd_game_over = None, None
snd_steps = {"bunker": None, "mine": None, "lab": None}

try:
    if os.path.exists("assets/audio/sfx/ping.wav"):
        snd_ping = pygame.mixer.Sound("assets/audio/sfx/ping.wav")
    if os.path.exists("assets/audio/sfx/monster.wav"):
        snd_scream = pygame.mixer.Sound("assets/audio/sfx/monster.wav")
        snd_scream.set_volume(0.6)
    if os.path.exists("assets/audio/sfx/pickup.wav"):
        snd_pickup = pygame.mixer.Sound("assets/audio/sfx/pickup.wav")
        
    # Звуки фіналів
    if os.path.exists("assets/audio/sfx/level_win.wav"):
        snd_level_win = pygame.mixer.Sound("assets/audio/sfx/level_win.wav")
        snd_level_win.set_volume(0.5)
    if os.path.exists("assets/audio/sfx/game_over.wav"):
        snd_game_over = pygame.mixer.Sound("assets/audio/sfx/game_over.wav")
        snd_game_over.set_volume(0.5)
        
    # Кроки
    if os.path.exists("assets/audio/sfx/step_bunker.wav"):
        snd_steps["bunker"] = pygame.mixer.Sound("assets/audio/sfx/step_bunker.wav")
        snd_steps["bunker"].set_volume(0.3)
    if os.path.exists("assets/audio/sfx/step_mine.wav"):
        snd_steps["mine"] = pygame.mixer.Sound("assets/audio/sfx/step_mine.wav")
        snd_steps["mine"].set_volume(0.3)
    if os.path.exists("assets/audio/sfx/step_lab.wav"):
        snd_steps["lab"] = pygame.mixer.Sound("assets/audio/sfx/step_lab.wav")
        snd_steps["lab"].set_volume(0.3)
        
    if os.path.exists("assets/audio/music/ambient.ogg"):
        pygame.mixer.music.load("assets/audio/music/ambient.ogg")
        pygame.mixer.music.set_volume(0.4)
        pygame.mixer.music.play(-1)
except Exception as e:
    print(f"Помилка завантаження аудіо: {e}")

# Стан гри
game_state = "MENU"
current_level = 0
waves = []
battery = 100.0
player_x, player_y = 100, 100
player_radius = 14

step_cooldown = 0

walls = []
enemies = []
batteries_on_ground = []
finish_rect = None
spr_current_wall = None

# Катсцени
intro_index = 0
text_speed = 0.35
current_chars = 0

# Таймери та змінні для глітчу
glitch_timer = 0
near_enemy_dist = 999999

# =====================================================================
# ✨ ФУНКЦІЯ СВІЧЕННЯ ТЕКСТУ (GLOW EFFECT)
# =====================================================================
def render_glow_text(screen, text, font_obj, main_color, glow_color, center_pos):
    main_surf = font_obj.render(text, False, main_color)
    glow_surf = font_obj.render(text, False, glow_color)
    glow_surf.set_alpha(45) 
    
    cx, cy = center_pos
    w, h = main_surf.get_size()
    
    for radius in [2, 4, 6]:
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            offset_x = int(math.cos(rad) * radius)
            offset_y = int(math.sin(rad) * radius)
            screen.blit(glow_surf, (cx - w // 2 + offset_x, cy - h // 2 + offset_y))
            
    screen.blit(main_surf, (cx - w // 2, cy - h // 2))

def load_game_level(idx):
    global player_x, player_y, walls, enemies, finish_rect, waves, battery, batteries_on_ground, spr_current_wall
    walls, enemies, batteries_on_ground = [], [], []
    waves.clear()
    battery = 100.0
    
    spr_current_wall = load_sprite(f"assets/sprites/walls/{LEVEL_INFO[idx]['wall_sprite']}", (50, 50))
    
    grid = LEVELS[idx]
    for row_idx, row in enumerate(grid):
        for col_idx, char in enumerate(row):
            x = col_idx * 50
            y = row_idx * 50
            if char == "W": walls.append(pygame.Rect(x, y, 50, 50))
            elif char == "P": player_x, player_y = x + 25, y + 25
            elif char == "F": finish_rect = pygame.Rect(x, y, 50, 50)
            elif char == "E": enemies.append(Enemy(x + 10, y + 10, idx))
            elif char == "B": batteries_on_ground.append(pygame.Rect(x + 13, y + 13, 24, 24))

def draw_custom_hud(screen, current_battery, glitch_intensity):
    hud_surf = pygame.Surface((VIRTUAL_WIDTH, 100), pygame.SRCALPHA)
    if spr_sonar_label: hud_surf.blit(spr_sonar_label, (20, 10))
    if spr_battery_hud: hud_surf.blit(spr_battery_hud, (20, 30))
    
    num_blocks = int(current_battery / 10)
    for i in range(num_blocks):
        block_x = 26 + (i * 13)
        block_y = 34
        if spr_block_filled: hud_surf.blit(spr_block_filled, (block_x, block_y))
        else: pygame.draw.rect(hud_surf, (0, 255, 120), (block_x, block_y, 10, 12))
        
    loc_name = font.render(LEVEL_INFO[current_level]["name"], False, (255, 255, 255))
    hud_surf.blit(loc_name, (220, 15))
    
    if glitch_intensity > 0:
        for _ in range(int(glitch_intensity * 2)):
            y = random.randint(0, 99)
            x_shift = random.randint(-4, 4)
            hud_surf.blit(hud_surf, (x_shift, y), (0, y, VIRTUAL_WIDTH, 1))
    screen.blit(hud_surf, (0, 0))

def draw_centered_intro_text(screen, full_text, char_count, y_pos, text_font):
    visible_text = full_text[:int(char_count)]
    text_surface = text_font.render(visible_text, False, (255, 255, 255))
    x_pos = (VIRTUAL_WIDTH // 2) - (text_surface.get_width() // 2)
    screen.blit(text_surface, (x_pos, y_pos))

def apply_full_glitch(screen, intensity):
    if intensity <= 0: return
    temp_surf = screen.copy()
    for _ in range(int(intensity * 3)):
        y = random.randint(0, VIRTUAL_HEIGHT - 1)
        h = random.randint(1, 4)
        x_shift = random.randint(-15, 15)
        color_shift = random.choice([(100, 0, 0), (0, 100, 0), (0, 0, 100)])
        
        line_surf = pygame.Surface((VIRTUAL_WIDTH, h))
        line_surf.blit(temp_surf, (x_shift, 0), (0, y, VIRTUAL_WIDTH, h))
        line_surf.fill(color_shift, special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(line_surf, (0, y))

def draw_danger_vignette(screen, p_x, p_y, enemy_list):
    global near_enemy_dist
    near_enemy_dist = 999999
    if not enemy_list: return
    
    for e in enemy_list:
        dist = math.hypot(e.rect.centerx - p_x, e.rect.centery - p_y)
        if dist < near_enemy_dist: near_enemy_dist = dist
            
    if near_enemy_dist < 180:
        intensity = int((1 - (near_enemy_dist / 180)) * 120) 
        intensity = max(0, min(150, intensity))
        vignette = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        for thickness in range(0, 30, 3):
            alpha = int(intensity * (thickness / 30))
            pygame.draw.rect(vignette, (255, 0, 0, alpha), (thickness, thickness, VIRTUAL_WIDTH - thickness*2, VIRTUAL_HEIGHT - thickness*2), 4)
        screen.blit(vignette, (0, 0))

load_game_level(current_level)

running = True
dt = 0
while running:
    dt = clock.tick(60)
    if step_cooldown > 0:
        step_cooldown -= dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            
            if game_state == "MENU" and event.key == pygame.K_RETURN:
                game_state = "INTRO"
                intro_index, current_chars = 0, 0
                    
            elif game_state == "INTRO" and (event.key == pygame.K_RETURN or event.key == pygame.K_SPACE):
                if current_chars < len(INTRO_SLIDES[intro_index]["text"]):
                    current_chars = len(INTRO_SLIDES[intro_index]["text"])
                else:
                    intro_index += 1
                    current_chars = 0
                    if intro_index >= len(INTRO_SLIDES):
                        game_state = "PLAYING"
                        current_level = 0
                        load_game_level(current_level)

            elif game_state == "PLAYING" and event.key == pygame.K_SPACE:
                cost = 30 if current_level == 4 else 20
                max_r = 450 if current_level == 3 else 300
                
                if battery >= cost:
                    waves.append({'x': player_x, 'y': player_y, 'radius': 0, 'max_r': max_r})
                    battery -= cost
                    if snd_ping: snd_ping.play()
                    
                    glitch_timer = 15 
                    
                    for e in enemies:
                        if pygame.math.Vector2(player_x, player_y).distance_to(e.rect.center) < max_r:
                            e.target_pos = (player_x, player_y)
                            if snd_scream and not pygame.mixer.Channel(2).get_busy():
                                pygame.mixer.Channel(2).play(snd_scream)

            elif game_state == "LEVEL_WIN" and event.key == pygame.K_RETURN:
                current_level += 1
                load_game_level(current_level)
                game_state = "PLAYING"
                            
            elif game_state in ["WIN", "GAMEOVER"] and event.key == pygame.K_RETURN:
                game_state = "MENU"

    if game_state == "INTRO" and current_chars < len(INTRO_SLIDES[intro_index]["text"]):
        current_chars += text_speed

    elif game_state == "PLAYING":
        current_zone = "bunker"
        if "lab" in LEVEL_INFO[current_level]["wall_sprite"]: current_zone = "lab"
        elif "mine" in LEVEL_INFO[current_level]["wall_sprite"]: current_zone = "mine"
        
        active_step_sound = snd_steps.get(current_zone, snd_steps["bunker"])
        
        speed = 1.8 if current_level == 2 else 3.0
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = speed
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy = -speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = speed

        if dx != 0 or dy != 0:
            player_x += dx
            if any(pygame.Rect(player_x-player_radius, player_y-player_radius, player_radius*2, player_radius*2).colliderect(w) for w in walls): player_x -= dx
            player_y += dy
            if any(pygame.Rect(player_x-player_radius, player_y-player_radius, player_radius*2, player_radius*2).colliderect(w) for w in walls): player_y -= dy
            
            if active_step_sound and step_cooldown <= 0:
                pygame.mixer.Channel(1).play(active_step_sound)
                step_cooldown = 320  

        regen = 0.05 if current_level == 4 else 0.15
        battery = min(100.0, battery + regen)

        p_rect = pygame.Rect(player_x-player_radius, player_y-player_radius, player_radius*2, player_radius*2)
        for b_item in batteries_on_ground[:]:
            if p_rect.colliderect(b_item):
                battery = min(100.0, battery + 50.0)
                if snd_pickup: snd_pickup.play()
                batteries_on_ground.remove(b_item)

        for wave in waves[:]:
            wave['radius'] += 5
            if wave['radius'] > wave['max_r']: waves.remove(wave)

        for e in enemies:
            e.update()
            if p_rect.colliderect(e.rect) and game_state == "PLAYING": 
                game_state = "GAMEOVER"
                if snd_game_over: snd_game_over.play()

        if finish_rect and p_rect.colliderect(finish_rect) and game_state == "PLAYING":
            if current_level < len(LEVELS) - 1: game_state = "LEVEL_WIN"
            else: game_state = "WIN"
            if snd_level_win: snd_level_win.play()
            
        if glitch_timer > 0: glitch_timer -= 1

    virtual_screen.fill((0, 0, 0))

    if game_state == "MENU":
        if spr_menu_title: virtual_screen.blit(spr_menu_title, (VIRTUAL_WIDTH//2 - 200, 160))
        if pygame.time.get_ticks() % 1000 < 600:
            start_text = font.render("[ НАТИСНІТЬ ENTER ЩОБ ПОЧАТИ ]", False, (255, 255, 255))
            virtual_screen.blit(start_text, (VIRTUAL_WIDTH//2 - start_text.get_width()//2, 380))

    elif game_state == "INTRO":
        slide_img = load_sprite(f"assets/sprites/intro_scenes/{INTRO_SLIDES[intro_index]['image']}", (400, 250))
        if slide_img: virtual_screen.blit(slide_img, (200, 100))
        draw_centered_intro_text(virtual_screen, INTRO_SLIDES[intro_index]["text"], current_chars, 420, font)

    elif game_state == "PLAYING":
        mask_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        mask_surface.fill((0, 0, 0, 255))
        pygame.draw.circle(mask_surface, (20, 20, 25), (int(player_x), int(player_y)), 45)

        for wave in waves:
            r = int(wave['radius'])
            if r > 0:
                scaled_wave = pygame.transform.scale(wave_template, (r * 2, r * 2))
                mask_surface.blit(scaled_wave, (wave['x'] - r, wave['y'] - r), special_flags=pygame.BLEND_RGBA_MAX)

        world_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        world_surface.fill((3, 3, 5))
        for wall in walls:
            if spr_current_wall: world_surface.blit(spr_current_wall, wall.topleft)
            else: pygame.draw.rect(world_surface, (0, 150, 60), wall, 1)
        if finish_rect:
            if spr_finish: world_surface.blit(spr_finish, finish_rect.topleft)
            else: pygame.draw.rect(world_surface, (255, 200, 0), finish_rect, 2)
        for b_item in batteries_on_ground:
            if spr_battery_item: world_surface.blit(spr_battery_item, b_item.topleft)

        for e in enemies:
            if current_level in [0, 1, 2]: spr_enemy = load_sprite("assets/sprites/enemies/enemy_bunker.png", (32, 32))
            elif current_level == 3: spr_enemy = load_sprite("assets/sprites/enemies/enemy_mine.png", (32, 32)) or load_sprite("assets/sprites/enemies/enemy_mine2.png", (32, 32))
            else: spr_enemy = load_sprite("assets/sprites/enemies/enemy_lab.png", (32, 32))

            if spr_enemy:
                d = math.hypot(e.rect.centerx - player_x, e.rect.centery - player_y)
                if d < 160:
                    alpha_val = int((1 - (d / 160)) * 255)
                    alpha_val = max(0, min(255, alpha_val))
                    temp_sprite = spr_enemy.copy()
                    temp_sprite.set_alpha(alpha_val)
                    world_surface.blit(temp_sprite, e.rect.topleft)
            else:
                pygame.draw.rect(world_surface, (255, 50, 50), e.rect, 2)

        world_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        virtual_screen.blit(world_surface, (0, 0))

        for wave in waves:
            pygame.draw.circle(virtual_screen, (0, 255, 150), (wave['x'], wave['y']), int(wave['radius']), 1)

        if spr_player: virtual_screen.blit(spr_player, (int(player_x-16), int(player_y-16)))
        else: pygame.draw.circle(virtual_screen, (255, 255, 255), (int(player_x), int(player_y)), player_radius)

        draw_danger_vignette(virtual_screen, player_x, player_y, enemies)
        
        current_glitch = 0
        if glitch_timer > 0: current_glitch = 10 
        if near_enemy_dist < 150: current_glitch = max(current_glitch, (1 - (near_enemy_dist / 150)) * 20)

        draw_custom_hud(virtual_screen, battery, current_glitch)
        if current_glitch > 15: apply_full_glitch(virtual_screen, current_glitch - 15)

    elif game_state == "LEVEL_WIN":
        render_glow_text(virtual_screen, f"РІВЕНЬ {current_level} ПРОЙДЕНО!", title_font, (120, 255, 150), (0, 200, 80), (VIRTUAL_WIDTH // 2, 250))
        if pygame.time.get_ticks() % 1000 < 600:
            sub_txt = font.render("[ НАТИСНІТЬ ENTER ЩОБ ПРОДОВЖИТИ ]", False, (255, 255, 255))
            virtual_screen.blit(sub_txt, (VIRTUAL_WIDTH//2 - sub_txt.get_width()//2, 360))

    elif game_state == "WIN":
        render_glow_text(virtual_screen, "ЕВАКУАЦІЯ УСПІШНА", title_font, (120, 255, 150), (0, 200, 80), (VIRTUAL_WIDTH // 2, 250))
        if pygame.time.get_ticks() % 1000 < 600:
            sub_txt = font.render("[ НАТИСНІТЬ ENTER ДЛЯ ВИХОДУ ]", False, (255, 255, 255))
            virtual_screen.blit(sub_txt, (VIRTUAL_WIDTH//2 - sub_txt.get_width()//2, 360))

    elif game_state == "GAMEOVER":
        render_glow_text(virtual_screen, "ЗВ'ЯЗОК ВТРАЧЕНО", title_font, (255, 80, 80), (200, 0, 0), (VIRTUAL_WIDTH // 2, 250))
        if pygame.time.get_ticks() % 1000 < 600:
            sub_txt = font.render("[ НАТИСНІТЬ ENTER ЩОБ СПРОБУВАТИ ЗНОВУ ]", False, (255, 255, 255))
            virtual_screen.blit(sub_txt, (VIRTUAL_WIDTH//2 - sub_txt.get_width()//2, 360))

    scaled_surface = pygame.transform.scale(virtual_screen, (info.current_w, info.current_h))
    screen.blit(scaled_surface, (0, 0))
    pygame.display.flip()

pygame.quit()
sys.exit()