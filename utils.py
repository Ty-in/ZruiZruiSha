import pygame
import random
import math
import os
from config import *

def load_font(size):
    candidates = ["child_font.ttf", "C:/Windows/Fonts/simkai.ttf", "C:/Windows/Fonts/msyh.ttf"]
    for path in candidates:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except:
                pass
    return pygame.font.Font(None, size)

def generate_wood_texture(width, height):
    surf = pygame.Surface((width, height))
    pixels = pygame.surfarray.pixels3d(surf)
    base_r, base_g, base_b = 160, 110, 70
    col_offsets = [random.randint(-20, 20) for _ in range(width)]
    for x in range(width):
        for y in range(height):
            stripe = math.sin(x * 0.04 + y * 0.01 + col_offsets[x] * 0.02) * 0.5 + 0.5
            noise = random.random() * 0.1 - 0.05
            val = max(0, min(1, stripe + noise))
            r = int(base_r * (0.7 + 0.3 * val))
            g = int(base_g * (0.7 + 0.3 * val))
            b = int(base_b * (0.7 + 0.3 * val))
            pixels[x][y] = [r, g, b]
    del pixels
    return surf

def draw_dice(surface, x, y, size, value, color):
    pygame.draw.rect(surface, color, (x, y, size, size), 3, border_radius=6)
    pygame.draw.rect(surface, (255, 255, 255), (x+3, y+3, size-6, size-6), border_radius=4)
    dot_positions = {
        1: [(0.5, 0.5)],
        2: [(0.2, 0.2), (0.8, 0.8)],
        3: [(0.2, 0.2), (0.5, 0.5), (0.8, 0.8)],
        4: [(0.2, 0.2), (0.8, 0.2), (0.2, 0.8), (0.8, 0.8)],
        5: [(0.2, 0.2), (0.8, 0.2), (0.5, 0.5), (0.2, 0.8), (0.8, 0.8)],
        6: [(0.2, 0.2), (0.8, 0.2), (0.2, 0.5), (0.8, 0.5), (0.2, 0.8), (0.8, 0.8)],
    }
    dot_radius = size // 12
    for (rx, ry) in dot_positions.get(value, []):
        dx = x + rx * size
        dy = y + ry * size
        pygame.draw.circle(surface, (0, 0, 0), (int(dx), int(dy)), dot_radius)

def draw_heart(surface, cx, cy, size, filled=True, color=COLOR_HP):
    points = []
    scale = size / 16.0
    for t in range(0, 360, 6):
        rad = math.radians(t)
        x = 16 * math.sin(rad) ** 3
        y = 13 * math.cos(rad) - 5 * math.cos(2*rad) - 2 * math.cos(3*rad) - math.cos(4*rad)
        px = cx + x * scale
        py = cy - y * scale
        points.append((px, py))
    if filled:
        pygame.draw.polygon(surface, color, points)
    else:
        pygame.draw.polygon(surface, color, points, 2)

def draw_sword(surface, x, y, color=COLOR_ATK):
    pygame.draw.line(surface, color, (x, y-9), (x, y+9), 2)
    pygame.draw.line(surface, color, (x-5, y+2), (x+5, y+2), 2)

def draw_single_zheng(surface, x, y, pens=5):
    cx = x + 6
    cy = y + 6
    strokes = [
        ((-5, -5), (5, -5)),
        ((0, -5), (0, 5)),
        ((0, 0), (5, 0)),
        ((-3, 0), (-3, 5)),
        ((-5, 5), (5, 5))
    ]
    for i in range(min(pens, 5)):
        start, end = strokes[i]
        start_x = cx + start[0]
        start_y = cy + start[1]
        end_x = cx + end[0]
        end_y = cy + end[1]
        pygame.draw.line(surface, COLOR_ENERGY, (start_x, start_y), (end_x, end_y), 2)

def draw_energy(surface, x, y, count):
    if count <= 0:
        return
    full = count // 5
    remain = count % 5
    for f in range(full):
        draw_single_zheng(surface, x + f * 16, y, 5)
    if remain > 0:
        draw_single_zheng(surface, x + full * 16, y, remain)