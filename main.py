import pygame
import sys
from PIL import Image, ImageDraw, ImageFilter

pygame.init()
pygame.mixer.init()
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()
pygame.mixer.set_num_channels(64)

try:
    click_sound = pygame.mixer.Sound("./assets/sounds/click.ogg")
except FileNotFoundError:
    print("Бро, ти десь файл звуку загубив")

base_size = 200
pil_image = Image.new('L', (base_size, base_size), 0)
draw = ImageDraw.Draw(pil_image)
draw.ellipse((10, 10, base_size - 10, base_size - 10), fill = 255)

pil_image = pil_image.filter(ImageFilter.GaussianBlur(radius=15))

wave_template = pygame.image.frombytes(pil_image.convert("RGBA").tobytes(),
                                       pil_image.size,
                                       "RGBA")

waves = []

walls = [pygame.Rect(150, 100, 50, 400),
         pygame.Rect(350, 200, 300, 50),
         pygame.Rect(500, 400, 200, 50)]

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            waves.append({'x': mx,
                          'y': my,
                          'radius': 0})
            if click_sound:
                pan = (event.pos[0] - screen_width / 2) / (screen_width / 2)
                left_vol = max(0, 1 - pan)
                right_vol = max(0, 1 + pan)

                channel = click_sound.play()
            
                if channel is not None:
                    channel.set_volume(left_vol, right_vol)
     
    for wave in waves[:]:
        wave['radius'] += 4
        if wave['radius'] > 400:
            waves.remove(wave)

    screen.fill('black')
    
    mask_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    mask_surface.fill((0, 0, 0, 255))

    for wave in waves:
        r = int(wave['radius'])
        if r > 0:
            scaled_wave = pygame.transform.scale(wave_template, (r * 2, r * 2))
            mask_surface.blit(scaled_wave, (wave['x'] - r, wave['y'] - r), special_flags=pygame.BLEND_RGBA_MAX)

    for wall in walls:
        pygame.draw.rect(screen, (0, 255, 100), wall)

    screen.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()