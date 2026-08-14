# card.py
import pygame
import random
from config import *
from utils import load_font

class PaperCard:
    def __init__(self, card_id, total_cards, is_enemy=False, data_manager=None):
        self.id = card_id
        self.width = 90
        self.height = 135
        self.face_up = False
        self.scale = 1.0
        self.target_scale = 1.0
        self.y_offset = 0
        self.target_y_offset = 0
        self.is_enemy = is_enemy
        self.data_manager = data_manager
        self.char_data = None
        self.set_random_character()
        self.x = 0
        self.y = 0
        self.rotation = 0.0
        self.paper_noise = self.generate_paper_texture()
        self.draw_rect = pygame.Rect(0, 0, self.width, self.height)
        self.font_small = load_font(18)
        self.font_large = load_font(40)

    def set_random_character(self):
        if self.data_manager is None:
            return
        pool = self.data_manager.enemy_characters if self.is_enemy else self.data_manager.player_characters
        if pool:
            self.char_data = random.choice(pool)

    def generate_paper_texture(self):
        noise = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < 0.01:
                    alpha = random.randint(30, 80)
                    noise.set_at((x, y), (0, 0, 0, alpha))
        return noise

    def update(self, x, y, rotation):
        self.x = x
        self.y = y
        self.rotation = rotation
        self.y_offset += (self.target_y_offset - self.y_offset) * 0.2
        self.scale += (self.target_scale - self.scale) * 0.2
        if abs(self.y_offset - self.target_y_offset) < 0.1:
            self.y_offset = self.target_y_offset
        if abs(self.scale - self.target_scale) < 0.001:
            self.scale = self.target_scale
        cx = self.x
        cy = self.y + self.y_offset
        w = int(self.width * self.scale)
        h = int(self.height * self.scale)
        self.draw_rect = pygame.Rect(cx - w//2, cy - h//2, w, h)

    def draw(self, surface):
        rect = self.draw_rect
        temp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        if self.face_up:
            self.draw_front(temp, rect)
        else:
            self.draw_back(temp, rect)
        if self.rotation != 0:
            rotated = pygame.transform.rotate(temp, self.rotation)
            rotated_rect = rotated.get_rect(center=rect.center)
            surface.blit(rotated, rotated_rect)
        else:
            surface.blit(temp, rect)

    def draw_back(self, surface, rect):
        pygame.draw.rect(surface, COLOR_PAPER, (0, 0, rect.width, rect.height), border_radius=12)
        surface.blit(self.paper_noise, (0, 0))
        pygame.draw.rect(surface, COLOR_CARD_BORDER, (0, 0, rect.width, rect.height), 3, border_radius=12)
        corner_size = 25
        corners = [(0,0), (rect.width,0), (0,rect.height), (rect.width,rect.height)]
        for cx, cy in corners:
            for i in range(3):
                r = corner_size - i * 6
                pygame.draw.arc(surface, COLOR_CARD_BORDER,
                               (cx - r if cx==0 else cx - r,
                                cy - r if cy==0 else cy - r,
                                r*2, r*2),
                               0.1, 1.2, 1 if i==0 else 2)
        center = (rect.width//2, rect.height//2)
        pygame.draw.circle(surface, COLOR_CARD_BORDER, center, 28, 2)
        pygame.draw.circle(surface, COLOR_CARD_BORDER, center, 18, 1)
        text = self.font_large.render("?", True, COLOR_CARD_BORDER)
        text_rect = text.get_rect(center=center)
        surface.blit(text, text_rect)
        shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for i in range(8):
            alpha = 10 - i
            pygame.draw.rect(shadow, (0,0,0,alpha),
                           (i, i, rect.width - i*2, rect.height - i*2),
                           2, border_radius=12)
        surface.blit(shadow, (0, 0))

    def draw_front(self, surface, rect):
        pygame.draw.rect(surface, (255, 248, 235), (0, 0, rect.width, rect.height), border_radius=12)
        surface.blit(self.paper_noise, (0, 0))
        pygame.draw.rect(surface, COLOR_CARD_BORDER, (0, 0, rect.width, rect.height), 3, border_radius=12)
        self.draw_stickman(surface, rect)

    def draw_stickman(self, surface, rect):
        cx, cy = rect.width//2, rect.height//2 - 2
        # 基本身体
        pygame.draw.circle(surface, COLOR_CARD_TEXT, (cx, cy - 25), 11, 2)
        pygame.draw.line(surface, COLOR_CARD_TEXT, (cx, cy - 12), (cx, cy + 14), 3)
        pygame.draw.line(surface, COLOR_CARD_TEXT, (cx, cy - 3), (cx - 18, cy - 6), 3)
        pygame.draw.line(surface, COLOR_CARD_TEXT, (cx, cy - 3), (cx + 18, cy - 6), 3)
        pygame.draw.line(surface, COLOR_CARD_TEXT, (cx, cy + 14), (cx - 12, cy + 34), 3)
        pygame.draw.line(surface, COLOR_CARD_TEXT, (cx, cy + 14), (cx + 12, cy + 34), 3)
        pygame.draw.circle(surface, COLOR_CARD_TEXT, (cx-5, cy-27), 1)
        pygame.draw.circle(surface, COLOR_CARD_TEXT, (cx+5, cy-27), 1)
        pygame.draw.arc(surface, COLOR_CARD_TEXT, (cx-8, cy-28, 16, 10), 0.1, 3.0, 2)

        if self.char_data is None:
            return
        weapon = self.char_data.get("weapon", "")
        if weapon == "none":
            return
        hand_x = cx + 18
        hand_y = cy - 6
        if weapon == "sword":
            pygame.draw.line(surface, COLOR_CARD_TEXT, (hand_x, hand_y - 12), (hand_x, hand_y + 10), 3)
            pygame.draw.line(surface, COLOR_CARD_TEXT, (hand_x - 5, hand_y - 2), (hand_x + 5, hand_y - 2), 2)
        elif weapon == "staff":
            pygame.draw.line(surface, COLOR_CARD_TEXT, (hand_x, hand_y - 14), (hand_x, hand_y + 8), 3)
            pygame.draw.circle(surface, COLOR_CARD_TEXT, (hand_x, hand_y - 16), 5, 2)
        elif weapon == "bow":
            for i in range(-10, 11):
                x = hand_x + i
                y = hand_y + int(abs(i) * 0.8) - 6
                surface.set_at((int(x), int(y)), COLOR_CARD_TEXT)
            pygame.draw.line(surface, COLOR_CARD_TEXT, (hand_x - 10, hand_y - 14), (hand_x + 10, hand_y - 14), 2)
        elif weapon == "shield":
            pygame.draw.circle(surface, COLOR_CARD_TEXT, (hand_x, hand_y - 4), 14, 3)
            pygame.draw.line(surface, COLOR_CARD_TEXT, (hand_x, hand_y - 14), (hand_x, hand_y + 6), 3)
            pygame.draw.line(surface, COLOR_CARD_TEXT, (hand_x - 10, hand_y - 4), (hand_x + 10, hand_y - 4), 3)
        elif weapon == "dagger":
            pygame.draw.line(surface, COLOR_CARD_TEXT, (hand_x - 5, hand_y - 14), (hand_x + 5, hand_y + 6), 3)
        elif weapon == "cross":
            pygame.draw.line(surface, COLOR_CARD_TEXT, (hand_x, hand_y - 16), (hand_x, hand_y + 8), 3)
            pygame.draw.line(surface, COLOR_CARD_TEXT, (hand_x - 8, hand_y - 6), (hand_x + 8, hand_y - 6), 3)
        elif weapon == "axe":
            pygame.draw.line(surface, COLOR_CARD_TEXT, (hand_x - 8, hand_y - 14), (hand_x + 8, hand_y), 3)
            pygame.draw.line(surface, COLOR_CARD_TEXT, (hand_x + 8, hand_y - 14), (hand_x - 8, hand_y), 3)
        elif weapon == "orb":
            pygame.draw.circle(surface, COLOR_CARD_TEXT, (hand_x, hand_y - 6), 10, 2)
            pygame.draw.circle(surface, COLOR_CARD_TEXT, (hand_x, hand_y - 6), 14, 1)

    def update_hover(self, mouse_pos):
        now_hover = self.draw_rect.collidepoint(mouse_pos)
        if now_hover:
            self.target_y_offset = -12
            self.target_scale = 1.05
        else:
            self.target_y_offset = 0
            self.target_scale = 1.0