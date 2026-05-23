import pygame
from PIL import Image, ImageDraw, ImageFilter

def generate_pixel_wave(size=250):
    small_size = size // 4
    img = Image.new('L', (small_size, small_size), 0)
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, small_size-2, small_size-2), fill=255)
    
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    img = img.resize((size, size), Image.NEAREST)
    
    return pygame.image.frombytes(img.convert("RGBA").tobytes(), img.size, "RGBA")

def draw_text_pixel_by_pixel(screen, text, current_chars, x, y, font, color=(255, 255, 255)):
    printed_text = text[:int(current_chars)]
    lines = printed_text.split('\n')
    
    for i, line in enumerate(lines):
        text_surface = font.render(line, False, color)
        screen.blit(text_surface, (x, y + i * 30))