import pygame
import random
import math
import sys
import os
import json

# ============ 初始化 ============
pygame.init()
WIDTH, HEIGHT = 1024, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("桌面卡牌 · 对战")
clock = pygame.time.Clock()

# ============ 颜色常量 ============
COLOR_PAPER = (240, 230, 210)
COLOR_CARD_BORDER = (100, 75, 50)
COLOR_CARD_TEXT = (40, 30, 20)
COLOR_NOTE_BG = (250, 245, 220)
COLOR_NOTE_LINE = (200, 190, 160)
COLOR_HP = (220, 40, 40)
COLOR_HP_LOST = (80, 80, 80)
COLOR_ATK = (50, 50, 50)
COLOR_ATK_BONUS = (255, 200, 0)
COLOR_ENERGY = (30, 30, 30)

# ============ 字体加载 ============
def load_font(size):
    if os.path.exists("child_font.ttf"):
        try:
            return pygame.font.Font("child_font.ttf", size)
        except:
            pass
    try:
        return pygame.font.Font("C:/Windows/Fonts/simkai.ttf", size)
    except:
        pass
    try:
        return pygame.font.Font("C:/Windows/Fonts/msyh.ttf", size)
    except:
        pass
    return pygame.font.Font(None, size)

# ============ 木纹纹理 ============
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

# ============ 骰子绘制 ============
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

# ============ 数据加载 ============
class DataManager:
    def __init__(self):
        self.player_characters = []
        self.enemy_characters = []
        self.load_characters()

    def load_characters(self):
        try:
            with open("data/characters.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                self.player_characters = data.get("player", [])
                self.enemy_characters = data.get("enemy", [])
        except FileNotFoundError:
            print("警告: data/characters.json 未找到，使用默认角色。")
            self.player_characters = [
                {"id": "unknown_player", "name": "未知的角色", "hp": 3, "atk": 1, "weapon": "none",
                 "energy": 0, "skill": None, "passive": None}
            ]
            self.enemy_characters = [
                {"id": "unknown_enemy", "name": "未知的对手", "hp": 3, "atk": 1, "weapon": "none",
                 "energy": 0, "skill": None, "passive": None}
            ]

# ============ 卡牌类 ============
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

# ============ 战斗面板（草稿纸） ============
class BattlePanel:
    def __init__(self, player_data, enemy_data):
        self.player_data = player_data
        self.enemy_data = enemy_data
        self.width = 420
        self.height = 640
        self.x = WIDTH + 50
        self.target_x = WIDTH - self.width - 5
        self.y = (HEIGHT - self.height) // 2
        self.target_y = self.y
        self.progress = 0.0
        self.duration = 0.6
        self.active = False
        self.start_time = 0.0
        self.font_title = load_font(22)
        self.font_text = load_font(16)
        self.font_small = load_font(14)

        self.player_skill = player_data.get("skill")
        self.player_passive = player_data.get("passive")
        self.enemy_skill = enemy_data.get("skill")
        self.enemy_passive = enemy_data.get("passive")

        self.hover_rects = []
        self.skill_button_rect = None
        self.player_multiplier = 1
        self.energy_multiplier_display = 1

    def start_animation(self, elapsed_time):
        self.active = True
        self.start_time = elapsed_time
        self.progress = 0.0

    def update(self, elapsed_time):
        if not self.active:
            return
        if self.progress >= 1.0:
            return
        elapsed = elapsed_time - self.start_time
        self.progress = min(1.0, elapsed / self.duration)
        ease = 1 - math.pow(1 - self.progress, 2)
        self.x = self.target_x + (WIDTH + 50 - self.target_x) * (1 - ease)

    def draw(self, surface, mouse_pos=None, player_energy=0, player_multiplier=1, energy_multiplier=1):
        if not self.active:
            return
        self.player_multiplier = player_multiplier
        self.energy_multiplier_display = energy_multiplier
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, COLOR_NOTE_BG, rect, border_radius=6)
        for i in range(1, 45):
            line_y = self.y + 14 + i * 14
            if line_y > self.y + self.height - 10:
                break
            offset = random.randint(-1, 1)
            pygame.draw.line(surface, COLOR_NOTE_LINE,
                             (self.x + 12 + offset, line_y),
                             (self.x + self.width - 12 + offset, line_y), 1)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, rect, 2, border_radius=6)

        mid_y = self.y + self.height // 2
        pygame.draw.line(surface, COLOR_CARD_BORDER,
                         (self.x + 20, mid_y),
                         (self.x + self.width - 20, mid_y), 3)

        self.hover_rects = []
        self.skill_button_rect = None

        self._draw_char_info(surface, self.enemy_data, self.x + 12, self.y + 16, self.width - 24,
                             self.enemy_skill, self.enemy_passive, False, 0)
        self._draw_char_info(surface, self.player_data, self.x + 12, mid_y + 16, self.width - 24,
                             self.player_skill, self.player_passive, True, player_energy)

    def _draw_char_info(self, surface, char_data, x, y, width,
                        skill_obj, passive_obj, is_player, player_energy):
        name_surf = self.font_title.render(char_data["name"], True, COLOR_CARD_TEXT)
        surface.blit(name_surf, (x, y))
        attr_x = x + name_surf.get_width() + 8

        hp = char_data.get("hp", 0)
        max_hp = char_data.get("max_hp", hp)
        atk = char_data.get("atk", 0)
        bonus = 0
        if is_player:
            bonus = max(0, self.player_multiplier - 1)
        energy = char_data.get("energy", 0)

        self._draw_hearts(surface, attr_x, y + 2, hp, max_hp)
        attr_x += max_hp * 16 + 6 if max_hp > 0 else 6

        self._draw_swords(surface, attr_x, y + 2, atk, color=COLOR_ATK)
        attr_x += atk * 18 + 6 if atk > 0 else 6

        if bonus > 0:
            self._draw_swords(surface, attr_x, y + 2, bonus, color=COLOR_ATK_BONUS)
            attr_x += bonus * 18 + 6

        self._draw_energy(surface, attr_x, y + 2, energy)

        row_y = y + 34
        if passive_obj:
            passive_name = passive_obj.get("name", "")
            passive_desc = passive_obj.get("desc", "")
            uses = char_data.get("passive_uses", 0)
            if uses > 0 or uses == -1:
                display = passive_name
                if uses == 0:
                    display += "（已失效）"
                elif uses == -1:
                    display += "（∞）"
                else:
                    display += f"（剩余{uses}次）"
                text = f"被动：{display}"
                color = (180, 80, 80) if uses == 0 else COLOR_CARD_TEXT
            else:
                text = "被动：无"
                color = COLOR_CARD_TEXT
        else:
            text = "被动：无"
            color = COLOR_CARD_TEXT
        surf = self.font_text.render(text, True, color)
        surface.blit(surf, (x, row_y))
        rect = pygame.Rect(x, row_y, surf.get_width(), surf.get_height())
        if passive_obj:
            self.hover_rects.append((rect, passive_obj.get("desc", ""), "被动"))

        row_y += 22
        if is_player and skill_obj:
            skill_name = skill_obj.get("name", "")
            skill_desc = skill_obj.get("desc", "")
            cost = skill_obj.get("cost", 999)
            uses = char_data.get("skill_uses", 0)
            can_use = (player_energy >= cost) and (uses != 0)
            display_name = skill_name
            if uses == -1:
                display_name += "（∞）"
            elif uses > 0:
                display_name += f"（剩余{uses}次）"
            text = f"技能：{display_name}"
            surf = self.font_text.render(text, True, COLOR_CARD_TEXT)
            surface.blit(surf, (x, row_y))
            btn_x = x + surf.get_width() + 10
            btn_y = row_y - 2
            btn_w = 40
            btn_h = 22
            color = (120, 200, 120) if can_use else (180, 180, 180)
            pygame.draw.rect(surface, color, (btn_x, btn_y, btn_w, btn_h), border_radius=4)
            pygame.draw.rect(surface, (60, 60, 60), (btn_x, btn_y, btn_w, btn_h), 1, border_radius=4)
            btn_text = self.font_small.render("使用", True, (0,0,0))
            surface.blit(btn_text, (btn_x + 5, btn_y + 3))
            self.skill_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            desc_rect = pygame.Rect(x, row_y, surf.get_width(), surf.get_height())
            self.hover_rects.append((desc_rect, skill_desc, "技能"))
        elif is_player and not skill_obj:
            text = "技能：无"
            surf = self.font_text.render(text, True, COLOR_CARD_TEXT)
            surface.blit(surf, (x, row_y))
        else:
            if skill_obj:
                text = f"技能：{skill_obj.get('name', '')}"
            else:
                text = "技能：无"
            surf = self.font_text.render(text, True, COLOR_CARD_TEXT)
            surface.blit(surf, (x, row_y))
            if skill_obj:
                rect = pygame.Rect(x, row_y, surf.get_width(), surf.get_height())
                self.hover_rects.append((rect, skill_obj.get("desc", ""), "技能"))

        # 显示能量倍率
        if is_player and self.energy_multiplier_display > 1:
            row_y += 22
            text = f"能量倍率：×{self.energy_multiplier_display}"
            surf = self.font_small.render(text, True, (200, 150, 0))
            surface.blit(surf, (x, row_y))

    def get_hover_text(self, mouse_pos):
        if not self.active or mouse_pos is None:
            return None
        for rect, desc, title in self.hover_rects:
            if rect.collidepoint(mouse_pos):
                if desc:
                    return (title, desc)
        return None

    def get_skill_button_rect(self):
        return self.skill_button_rect

    # ---------- 绘图辅助 ----------
    def _draw_hearts(self, surface, x, y, current_hp, max_hp):
        for i in range(max_hp):
            cx = x + i * 16
            cy = y
            if i < current_hp:
                self._draw_heart(surface, cx, cy, 6, filled=True, color=COLOR_HP)
            else:
                self._draw_heart(surface, cx, cy, 6, filled=False, color=COLOR_HP_LOST)

    def _draw_heart(self, surface, cx, cy, size, filled=True, color=COLOR_HP):
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

    def _draw_swords(self, surface, x, y, count, color=COLOR_ATK):
        for i in range(min(count, 10)):
            sx = x + i * 18
            sy = y
            pygame.draw.line(surface, color, (sx, sy-9), (sx, sy+9), 2)
            pygame.draw.line(surface, color, (sx-5, sy+2), (sx+5, sy+2), 2)

    # ---------- 正字绘制（修正版） ----------
    def _draw_single_zheng(self, surface, x, y, pens=5):
        cx = x + 6
        cy = y + 6
        strokes = [
            ((-5, -5), (5, -5)),   # 上横
            ((0, -5), (0, 5)),     # 中竖
            ((0, 0), (5, 0)),      # 中横（只画右边！）
            ((-3, 0), (-3, 5)),    # 下竖（偏左）
            ((-5, 5), (5, 5))      # 下横
        ]
        for i in range(min(pens, 5)):
            start, end = strokes[i]
            start_x = cx + start[0]
            start_y = cy + start[1]
            end_x = cx + end[0]
            end_y = cy + end[1]
            pygame.draw.line(surface, COLOR_ENERGY, (start_x, start_y), (end_x, end_y), 2)

    def _draw_energy(self, surface, x, y, count):
        if count <= 0:
            return
        full = count // 5
        remain = count % 5
        for f in range(full):
            self._draw_single_zheng(surface, x + f * 16, y, 5)
        if remain > 0:
            self._draw_single_zheng(surface, x + full * 16, y, remain)

    def update_data(self, player_data, enemy_data):
        self.player_data = player_data
        self.enemy_data = enemy_data
        self.player_skill = player_data.get("skill")
        self.player_passive = player_data.get("passive")
        self.enemy_skill = enemy_data.get("skill")
        self.enemy_passive = enemy_data.get("passive")

# ============ 战斗管理器 ============
class BattleSession:
    def __init__(self, player_char, enemy_char):
        self.player = player_char.copy()
        self.enemy = enemy_char.copy()
        self.player["max_hp"] = player_char["hp"]
        self.enemy["max_hp"] = enemy_char["hp"]
        self.player["hp"] = player_char["hp"]
        self.enemy["hp"] = enemy_char["hp"]
        self.player["energy"] = 0
        self.enemy["energy"] = 0
        self.player["skill_uses"] = self._get_initial_uses(player_char.get("skill"))
        self.enemy["skill_uses"] = self._get_initial_uses(enemy_char.get("skill"))
        self.player["passive_uses"] = self._get_initial_uses(player_char.get("passive"))
        self.enemy["passive_uses"] = self._get_initial_uses(enemy_char.get("passive"))
        self.player["multiplier"] = 1
        self.enemy["multiplier"] = 1
        self.player["energy_multiplier"] = 1

        self.state = "dice_roll"
        self.dice_player = 0
        self.dice_enemy = 0
        self.turn_winner = None
        self.log = []
        self.pending_passive = False
        self.passive_target = None
        self.passive_damage = 0
        self.result_timer = 0.0
        self.pending_choice = None

        self.player_id = player_char.get("id", "")
        self.enemy_id = enemy_char.get("id", "")

        self.skill_effects = {
            "huangfu_lai": self._skill_huangfu_lai,
            "shui_niu": self._skill_shui_niu,
        }
        self.passive_effects = {
            "huangfu_lai": self._passive_huangfu_lai,
        }

    def _get_initial_uses(self, ability_obj):
        if ability_obj is None:
            return 0
        return ability_obj.get("uses", 0)

    # ---------- 技能效果 ----------
    def _skill_huangfu_lai(self):
        if "multiplier" not in self.player:
            self.player["multiplier"] = 1
        self.player["multiplier"] *= 2
        self.log.append(f"皇甫赖使用技能，下次攻击×{self.player['multiplier']}")
        return True

    def _skill_shui_niu(self):
        return True

    # ---------- 被动效果 ----------
    def _passive_huangfu_lai(self, defender, damage):
        self.pending_passive = True
        self.passive_target = defender
        self.passive_damage = damage
        return True

    # ---------- 核心方法 ----------
    def set_dice_results(self, player_val, enemy_val):
        self.dice_player = player_val
        self.dice_enemy = enemy_val
        if self.dice_player > self.dice_enemy:
            self.turn_winner = 'player'
        elif self.dice_player < self.dice_enemy:
            self.turn_winner = 'enemy'
        else:
            self.turn_winner = None
        self.state = "dice_result"
        self.result_timer = 1.2

    def update(self, dt):
        if self.state == "dice_result":
            self.result_timer -= dt
            if self.result_timer <= 0:
                self.start_turn()

    def start_turn(self):
        if self.turn_winner == 'player':
            self.state = "player_turn"
        elif self.turn_winner == 'enemy' and self.player_id == "shui_niu":
            skill = self.player.get("skill")
            if skill and self.player["energy"] >= skill.get("cost", 999) and self.player.get("skill_uses", 0) != 0:
                self.pending_choice = {"type": "skill_duolian"}
                self.state = "waiting_choice"
                return
            else:
                self.state = "enemy_turn"
                self.ai_turn()
        elif self.turn_winner == 'enemy':
            self.state = "enemy_turn"
            self.ai_turn()
        else:
            self.state = "dice_roll"
            self.turn_winner = None

    def resolve_choice(self, choice):
        if not self.pending_choice:
            return
        choice_type = self.pending_choice["type"]
        if choice_type == "skill_duolian":
            if choice:
                skill = self.player.get("skill")
                cost = skill.get("cost", 999)
                self.player["energy"] -= cost
                uses = self.player.get("skill_uses", 0)
                if uses != -1:
                    self.player["skill_uses"] -= 1
                self.log.append("水牛使用技能‘多练’，敌方回合无效")
                self.pending_choice = None
                self.state = "dice_roll"
                self.turn_winner = None
            else:
                self.log.append("水牛未使用技能‘多练’，敌方继续行动")
                self.pending_choice = None
                self.state = "enemy_turn"
                self.ai_turn()

    def player_action(self, action):
        if self.state != "player_turn":
            return
        if action == "attack":
            self._execute_attack('player', 'enemy')
            if not self.pending_passive:
                self._end_player_turn()
        elif action == "energy":
            gain = self.player.get("energy_multiplier", 1)
            self.player["energy"] += gain
            if gain > 1:
                self.log.append(f"玩家获得 {gain} 能量（倍率×{self.player['energy_multiplier']}）")
            else:
                self.log.append("玩家获得1能量")
            self.player["energy_multiplier"] = 1
            self._end_player_turn()
        elif action == "passive_cai":
            if self.player_id == "shui_niu" and self.player.get("passive_uses", 0) != 0:
                self.player["energy_multiplier"] *= 2
                self.log.append(f"水牛启用被动‘菜’，能量倍率变为×{self.player['energy_multiplier']}")
                self._end_player_turn()
            else:
                self.log.append("被动不可用")

    def _try_apply_passive(self, defender, timing, damage):
        if defender is not self.player:
            return False
        passive = self.player.get("passive")
        if passive is None or passive.get("timing") != timing:
            return False
        if self.player.get("passive_uses", 0) == 0:
            return False
        effect = self.passive_effects.get(self.player_id)
        if effect:
            return effect(defender, damage)
        return False

    def _execute_attack(self, attacker_key, defender_key):
        attacker = self.player if attacker_key == 'player' else self.enemy
        defender = self.player if defender_key == 'player' else self.enemy
        base_atk = attacker["atk"]
        mult = attacker.get("multiplier", 1)
        damage = base_atk * mult
        attacker["multiplier"] = 1

        if self._try_apply_passive(defender, "on_take_damage", damage):
            return

        defender["hp"] -= damage
        if defender["hp"] < 0:
            defender["hp"] = 0
        self.log.append(f"{attacker['name']} 攻击 {defender['name']}，造成 {damage} 伤害")
        self._check_game_over()

    def resolve_passive(self, use_passive):
        if not self.pending_passive:
            return
        if use_passive:
            if self.player["passive_uses"] != -1:
                self.player["passive_uses"] -= 1
            self.log.append(f"{self.passive_target['name']} 使用耍赖，免疫了攻击！")
        else:
            self.passive_target["hp"] -= self.passive_damage
            if self.passive_target["hp"] < 0:
                self.passive_target["hp"] = 0
            self.log.append(f"{self.passive_target['name']} 受到 {self.passive_damage} 伤害")
        self.pending_passive = False
        self.passive_target = None
        self.passive_damage = 0
        if self._check_game_over():
            return
        if self.state == "player_turn":
            self._end_player_turn()
        else:
            self.state = "dice_roll"
            self.turn_winner = None

    def _end_player_turn(self):
        if self.state == "game_over" or self._check_game_over():
            return
        self.state = "dice_roll"
        self.turn_winner = None

    def _end_enemy_turn(self):
        if self.state == "game_over" or self._check_game_over():
            return
        self.state = "dice_roll"
        self.turn_winner = None

    def ai_turn(self):
        if self.state != "enemy_turn":
            return
        self._execute_attack('enemy', 'player')
        if not self.pending_passive and self.state != "game_over":
            self._end_enemy_turn()

    def _check_game_over(self):
        if self.player["hp"] <= 0:
            self.state = "game_over"
            self.log.append("玩家战败...")
            return True
        elif self.enemy["hp"] <= 0:
            self.state = "game_over"
            self.log.append("玩家胜利！")
            return True
        return False

    def get_display_data(self):
        p_data = self.player.copy()
        e_data = self.enemy.copy()
        p_data["multiplier"] = self.player["multiplier"]
        e_data["multiplier"] = self.enemy["multiplier"]
        return p_data, e_data

    def use_skill(self):
        skill = self.player.get("skill")
        if skill is None:
            self.log.append("没有技能")
            return False
        cost = skill.get("cost", 999)
        uses = self.player.get("skill_uses", 0)
        if self.player["energy"] < cost:
            self.log.append("能量不足！")
            return False
        if uses == 0:
            self.log.append("技能次数已用完！")
            return False
        self.player["energy"] -= cost
        if uses != -1:
            self.player["skill_uses"] -= 1
        effect = self.skill_effects.get(self.player_id)
        if effect:
            return effect()
        else:
            self.log.append("该角色没有技能效果实现")
            return False

# ============ 发牌动画控制器 ============
class DealController:
    def __init__(self, cards, data_manager):
        self.cards = cards
        self.total = len(cards)
        self.phase = 0
        self.elapsed_time = 0.0
        self.delays = [i * 0.2 for i in range(self.total)]
        self.stack_positions = self.calculate_stack_positions()
        self.spread_positions = self.calculate_spread_positions()
        self.start_positions = [(WIDTH//2, HEIGHT + 100) for _ in range(self.total)]
        self.hold_time = 0.5
        self.spread_start_time = 0.0
        self.spread_triggered = False
        self.selected_card = None
        self.select_start_positions = []
        self.select_target_positions = []
        self.select_duration = 0.6
        self.select_start_time = 0.0
        self.flip_wait_time = 0.5
        self.flip_wait_start = 0.0
        self.waiting_flip = False
        self.data_manager = data_manager
        self.enemy_card = None
        self.enemy_start_pos = (WIDTH//2, -100)
        self.enemy_target_pos = (WIDTH//2, 150)
        self.enemy_phase = 0
        self.enemy_start_time = 0.0
        self.enemy_duration = 0.8
        self.battle_panel = None
        self.player_selected_char = None
        self.battle_session = None
        self.game_started = False

    def calculate_stack_positions(self):
        cx, cy = WIDTH//2, HEIGHT//2 + 20
        positions = []
        for i in range(self.total):
            offset_x = (i - self.total/2) * 2.5
            offset_y = (i - self.total/2) * 1.5
            positions.append((cx + offset_x, cy + offset_y))
        return positions

    def calculate_spread_positions(self):
        spacing = 130
        total_width = (self.total - 1) * spacing
        start_x = (WIDTH - total_width) // 2
        y = HEIGHT//2 - 20
        return [(start_x + i * spacing, y) for i in range(self.total)]

    def trigger_spread(self):
        if self.phase == 1 and not self.spread_triggered:
            self.spread_triggered = True
            self.phase = 2
            self.spread_start_time = self.elapsed_time

    def select_card(self, card):
        if self.phase != 3 or self.waiting_flip:
            return
        self.selected_card = card
        self.player_selected_char = card.char_data.copy()
        card.face_up = True
        self.waiting_flip = True
        self.flip_wait_start = self.elapsed_time
        target_x = WIDTH//2
        target_y = HEIGHT - 180
        self.select_target_positions = []
        for c in self.cards:
            if c == card:
                self.select_target_positions.append((target_x, target_y))
            else:
                self.select_target_positions.append((-c.width - 50, c.y))

    def spawn_enemy_card(self):
        if self.enemy_card is not None:
            return
        enemy_char = random.choice(self.data_manager.enemy_characters)
        enemy = PaperCard(-1, 1, is_enemy=True, data_manager=self.data_manager)
        enemy.char_data = enemy_char.copy()
        enemy.face_up = False
        enemy.x, enemy.y = self.enemy_start_pos
        enemy.scale = 1.0
        self.enemy_card = enemy
        self.enemy_phase = 1
        self.enemy_start_time = self.elapsed_time

    def update_enemy_card(self):
        if self.enemy_phase != 1:
            return
        elapsed = self.elapsed_time - self.enemy_start_time
        progress = min(1.0, elapsed / self.enemy_duration)
        if progress >= 1.0:
            self.enemy_card.face_up = True
            self.enemy_phase = 2
            if self.player_selected_char and self.enemy_card.char_data:
                self.battle_panel = BattlePanel(self.player_selected_char, self.enemy_card.char_data)
                self.battle_panel.start_animation(self.elapsed_time)
                self.battle_session = BattleSession(self.player_selected_char, self.enemy_card.char_data)
                self.game_started = True
        else:
            ease = 1 - math.pow(1 - progress, 2)
            sx, sy = self.enemy_start_pos
            tx, ty = self.enemy_target_pos
            x = sx + (tx - sx) * ease
            y = sy + (ty - sy) * ease
            self.enemy_card.update(x, y, 0)

    def update(self, dt):
        self.elapsed_time += dt

        if self.battle_session:
            self.battle_session.update(dt)

        if self.phase == 0:
            all_done = True
            for i, card in enumerate(self.cards):
                t = self.elapsed_time - self.delays[i]
                if t < 0:
                    card.update(self.start_positions[i][0], self.start_positions[i][1], 15)
                    all_done = False
                elif t < 0.8:
                    progress = t / 0.8
                    ease = 1 - math.pow(1 - progress, 2.5)
                    start_x, start_y = self.start_positions[i]
                    target_x, target_y = self.stack_positions[i]
                    x = start_x + (target_x - start_x) * ease
                    y = start_y + (target_y - start_y) * ease
                    arc = -120 * math.sin(progress * math.pi) * (1 - progress * 0.3)
                    y += arc
                    rotation = 15 * (1 - ease)
                    card.update(x, y, rotation)
                    all_done = False
                else:
                    card.update(self.stack_positions[i][0], self.stack_positions[i][1], 0)
            if all_done:
                self.phase = 1
                self.hold_time = 0.5

        elif self.phase == 1:
            pass

        elif self.phase == 2:
            duration = 0.8
            progress = min(1.0, (self.elapsed_time - self.spread_start_time) / duration)
            if progress >= 1.0:
                for i, card in enumerate(self.cards):
                    card.update(self.spread_positions[i][0], self.spread_positions[i][1], 0)
                self.phase = 3
            else:
                ease = 1 - math.pow(1 - progress, 2)
                for i, card in enumerate(self.cards):
                    sx, sy = self.stack_positions[i]
                    tx, ty = self.spread_positions[i]
                    x = sx + (tx - sx) * ease
                    y = sy + (ty - sy) * ease
                    card.update(x, y, 0)

        elif self.phase == 3:
            for i, card in enumerate(self.cards):
                card.update(self.spread_positions[i][0], self.spread_positions[i][1], 0)

            if self.waiting_flip:
                if self.elapsed_time - self.flip_wait_start >= self.flip_wait_time:
                    self.waiting_flip = False
                    self.phase = 4
                    self.select_start_time = self.elapsed_time
                    self.select_start_positions = [(c.x, c.y) for c in self.cards]
                    self.spawn_enemy_card()

        elif self.phase == 4:
            duration = self.select_duration
            progress = min(1.0, (self.elapsed_time - self.select_start_time) / duration)
            if progress >= 1.0:
                for i, card in enumerate(self.cards):
                    tx, ty = self.select_target_positions[i]
                    card.update(tx, ty, 0)
                self.phase = 5
            else:
                ease = 1 - math.pow(1 - progress, 2)
                for i, card in enumerate(self.cards):
                    sx, sy = self.select_start_positions[i]
                    tx, ty = self.select_target_positions[i]
                    x = sx + (tx - sx) * ease
                    y = sy + (ty - sy) * ease
                    card.update(x, y, 0)

        elif self.phase == 5:
            pass

        self.update_enemy_card()
        if self.battle_panel:
            self.battle_panel.update(self.elapsed_time)
            if self.battle_session:
                p_data, e_data = self.battle_session.get_display_data()
                self.battle_panel.update_data(p_data, e_data)

    def get_phase(self):
        return self.phase

    def is_waiting_flip(self):
        return self.waiting_flip

    def is_enemy_ready(self):
        return self.enemy_phase == 2

# ============ 主程序 ============
def main():
    data_manager = DataManager()
    wood_texture = generate_wood_texture(WIDTH, HEIGHT)
    total = 5
    cards = [PaperCard(i, total, is_enemy=False, data_manager=data_manager) for i in range(total)]
    controller = DealController(cards, data_manager)
    hint_font = load_font(24)

    dice_rolled = False
    dice_values = (1, 1)
    dice_animating = False
    dice_anim_start = 0.0
    dice_anim_duration = 0.8
    dice_anim_values = [1, 1]
    final_vals = [1, 1]
    button_rects = {}

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    cards = [PaperCard(i, total, is_enemy=False, data_manager=data_manager) for i in range(total)]
                    controller = DealController(cards, data_manager)
                    dice_rolled = False
                    dice_animating = False
                    button_rects = {}
                elif event.key == pygame.K_SPACE:
                    if controller.get_phase() == 1:
                        controller.trigger_spread()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 骰子按钮
                if controller.battle_session and controller.battle_session.state == "dice_roll":
                    btn_rect = pygame.Rect(80, HEIGHT//2 - 30, 160, 50)
                    if btn_rect.collidepoint(event.pos):
                        dice_animating = True
                        dice_anim_start = controller.elapsed_time
                        final_vals[0] = random.randint(1, 6)
                        final_vals[1] = random.randint(1, 6)

                # 选牌
                if controller.get_phase() == 3 and not controller.is_waiting_flip():
                    for card in cards:
                        if card.draw_rect.collidepoint(event.pos):
                            controller.select_card(card)
                            break

                # 玩家回合按钮
                if controller.battle_session and controller.battle_session.state == "player_turn":
                    for name, rect in button_rects.items():
                        if rect.collidepoint(event.pos):
                            if name == "attack":
                                controller.battle_session.player_action("attack")
                            elif name == "energy":
                                controller.battle_session.player_action("energy")
                            elif name == "passive_cai":
                                controller.battle_session.player_action("passive_cai")

                # 技能按钮（草稿纸上的“使用”）
                if controller.battle_panel:
                    skill_rect = controller.battle_panel.get_skill_button_rect()
                    if skill_rect and skill_rect.collidepoint(event.pos):
                        if controller.battle_session:
                            controller.battle_session.use_skill()

                # 皇甫赖被动选择
                if controller.battle_session and controller.battle_session.pending_passive:
                    btn_yes = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 20, 80, 40)
                    btn_no = pygame.Rect(WIDTH//2 + 20, HEIGHT//2 + 20, 80, 40)
                    if btn_yes.collidepoint(event.pos):
                        controller.battle_session.resolve_passive(True)
                    elif btn_no.collidepoint(event.pos):
                        controller.battle_session.resolve_passive(False)

                # 水牛技能选择（多练）
                if controller.battle_session and hasattr(controller.battle_session, 'pending_choice') and controller.battle_session.pending_choice:
                    choice_type = controller.battle_session.pending_choice["type"]
                    if choice_type == "skill_duolian":
                        btn_yes = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 20, 80, 40)
                        btn_no = pygame.Rect(WIDTH//2 + 20, HEIGHT//2 + 20, 80, 40)
                        if btn_yes.collidepoint(event.pos):
                            controller.battle_session.resolve_choice(True)
                        elif btn_no.collidepoint(event.pos):
                            controller.battle_session.resolve_choice(False)

        controller.update(dt)

        # 骰子动画
        if dice_animating:
            elapsed = controller.elapsed_time - dice_anim_start
            if elapsed >= dice_anim_duration:
                dice_animating = False
                dice_rolled = True
                if controller.battle_session:
                    controller.battle_session.set_dice_results(final_vals[0], final_vals[1])
                    dice_values = (final_vals[0], final_vals[1])
            else:
                if int(elapsed * 30) % 2 == 0:
                    dice_anim_values[0] = random.randint(1, 6)
                    dice_anim_values[1] = random.randint(1, 6)

        if controller.get_phase() == 3 and not controller.is_waiting_flip():
            mouse_pos = pygame.mouse.get_pos()
            for card in cards:
                card.update_hover(mouse_pos)
        else:
            for card in cards:
                card.target_y_offset = 0
                card.target_scale = 1.0

        screen.blit(wood_texture, (0, 0))

        for card in cards:
            card.draw(screen)
        if controller.enemy_card is not None:
            controller.enemy_card.draw(screen)

        # 战斗面板
        if controller.battle_panel:
            mouse_pos = pygame.mouse.get_pos()
            player_energy = 0
            player_multiplier = 1
            energy_multiplier = 1
            if controller.battle_session:
                player_energy = controller.battle_session.player.get("energy", 0)
                player_multiplier = controller.battle_session.player.get("multiplier", 1)
                energy_multiplier = controller.battle_session.player.get("energy_multiplier", 1)
            controller.battle_panel.draw(screen, mouse_pos, player_energy, player_multiplier, energy_multiplier)
            hover_info = controller.battle_panel.get_hover_text(mouse_pos)
            if hover_info:
                title, desc = hover_info
                tip_font = load_font(18)
                lines = [f"{title}：", desc] if desc else [f"{title}"]
                max_width = 0
                line_surfs = []
                for line in lines:
                    surf = tip_font.render(line, True, (40, 30, 20))
                    line_surfs.append(surf)
                    if surf.get_width() > max_width:
                        max_width = surf.get_width()
                padding = 10
                box_width = max_width + padding * 2
                box_height = len(lines) * 26 + padding * 2
                tip_x = mouse_pos[0] + 16
                tip_y = mouse_pos[1] + 16
                if tip_x + box_width > WIDTH:
                    tip_x = mouse_pos[0] - box_width - 16
                if tip_y + box_height > HEIGHT:
                    tip_y = mouse_pos[1] - box_height - 16
                s = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
                s.fill((250, 245, 220, 230))
                pygame.draw.rect(s, (100, 75, 50, 200), s.get_rect(), 2, border_radius=4)
                screen.blit(s, (tip_x, tip_y))
                for i, surf in enumerate(line_surfs):
                    screen.blit(surf, (tip_x + padding, tip_y + padding + i * 26))

        # 提示信息
        phase = controller.get_phase()
        if phase == 0:
            hint = hint_font.render("发牌中... | ESC退出 | R重新发牌", True, (255,255,230))
        elif phase == 1:
            hint = hint_font.render("按 空格键 展开卡牌 | ESC退出 | R重新发牌", True, (255,255,230))
        elif phase == 2:
            hint = hint_font.render("展开中...", True, (255,255,230))
        elif phase == 3:
            if controller.is_waiting_flip():
                hint = hint_font.render("翻面中...", True, (255,255,230))
            else:
                hint = hint_font.render("点击一张卡牌选择 | ESC退出 | R重新发牌", True, (255,255,230))
        elif phase == 4:
            hint = hint_font.render("选牌中...", True, (255,255,230))
        elif phase == 5:
            if controller.battle_session:
                state = controller.battle_session.state
                if state == "dice_roll":
                    hint = hint_font.render("点击左侧按钮投骰子拼点！", True, (255,255,230))
                elif state == "dice_result":
                    winner = controller.battle_session.turn_winner
                    if winner == 'player':
                        hint = hint_font.render("玩家赢！", True, (255, 255, 200))
                    elif winner == 'enemy':
                        hint = hint_font.render("敌方赢！", True, (255, 255, 200))
                    else:
                        hint = hint_font.render("平局！重新掷骰...", True, (255, 255, 200))
                elif state == "player_turn":
                    hint = hint_font.render("【玩家回合】选择攻击、获得能量或启用被动", True, (255,255,230))
                elif state == "enemy_turn":
                    hint = hint_font.render("敌方攻击！（玩家仍可使用技能）", True, (255,255,230))
                elif state == "waiting_choice":
                    hint = hint_font.render("请选择是否使用技能", True, (255, 255, 200))
                elif state == "game_over":
                    hint = hint_font.render("游戏结束！按 R 重新开始", True, (255,255,230))
                else:
                    hint = hint_font.render("战斗进行中...", True, (255,255,230))
            else:
                hint = hint_font.render("敌方出现！", True, (255,255,230))
        screen.blit(hint, (20, HEIGHT - 40))

        # 骰子按钮
        if controller.battle_session and controller.battle_session.state == "dice_roll":
            btn_rect = pygame.Rect(80, HEIGHT//2 - 30, 160, 50)
            pygame.draw.rect(screen, (200, 180, 160), btn_rect, border_radius=10)
            pygame.draw.rect(screen, (100, 80, 60), btn_rect, 3, border_radius=10)
            btn_text = hint_font.render("骰子", True, (40, 30, 20))
            btn_text_rect = btn_text.get_rect(center=btn_rect.center)
            screen.blit(btn_text, btn_text_rect)

        # 骰子显示
        if dice_animating or dice_rolled:
            show_player = dice_anim_values[0] if dice_animating else dice_values[0]
            show_enemy = dice_anim_values[1] if dice_animating else dice_values[1]
            dice_size = 70
            total_width = dice_size*2 + 30
            start_x = WIDTH//2 - total_width//2
            y_pos = HEIGHT//2 - dice_size//2
            draw_dice(screen, start_x, y_pos, dice_size, show_player, (50, 100, 200))
            draw_dice(screen, start_x + dice_size + 30, y_pos, dice_size, show_enemy, (200, 50, 50))

        # 玩家回合按钮
        if controller.battle_session and controller.battle_session.state == "player_turn":
            button_rects.clear()
            # 攻击
            attack_rect = pygame.Rect(WIDTH//2 - 160, HEIGHT//2 + 120, 80, 40)
            pygame.draw.rect(screen, (180, 120, 120), attack_rect, border_radius=8)
            pygame.draw.rect(screen, (80, 40, 40), attack_rect, 2, border_radius=8)
            txt = hint_font.render("攻击", True, (255,255,255))
            screen.blit(txt, (attack_rect.x+10, attack_rect.y+5))
            button_rects["attack"] = attack_rect

            # 能量（显示倍率）
            energy_rect = pygame.Rect(WIDTH//2 - 50, HEIGHT//2 + 120, 100, 40)
            pygame.draw.rect(screen, (120, 180, 120), energy_rect, border_radius=8)
            pygame.draw.rect(screen, (40, 80, 40), energy_rect, 2, border_radius=8)
            mult = controller.battle_session.player.get("energy_multiplier", 1)
            if mult > 1:
                txt = hint_font.render(f"能量×{mult}", True, (255,255,255))
            else:
                txt = hint_font.render("能量", True, (255,255,255))
            screen.blit(txt, (energy_rect.x+10, energy_rect.y+5))
            button_rects["energy"] = energy_rect

            # 水牛被动“菜”
            if controller.battle_session.player_id == "shui_niu" and controller.battle_session.player.get("passive_uses", 0) != 0:
                passive_rect = pygame.Rect(WIDTH//2 + 70, HEIGHT//2 + 120, 100, 40)
                pygame.draw.rect(screen, (180, 180, 80), passive_rect, border_radius=8)
                pygame.draw.rect(screen, (80, 80, 40), passive_rect, 2, border_radius=8)
                txt = hint_font.render("启用菜", True, (255,255,255))
                screen.blit(txt, (passive_rect.x+10, passive_rect.y+5))
                button_rects["passive_cai"] = passive_rect

        # 皇甫赖被动弹窗
        if controller.battle_session and controller.battle_session.pending_passive:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            screen.blit(overlay, (0, 0))
            prompt = hint_font.render("受到攻击！是否使用“耍赖”免疫？", True, (255, 255, 200))
            prompt_rect = prompt.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
            screen.blit(prompt, prompt_rect)
            btn_yes = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 20, 80, 40)
            btn_no = pygame.Rect(WIDTH//2 + 20, HEIGHT//2 + 20, 80, 40)
            pygame.draw.rect(screen, (100, 200, 100), btn_yes, border_radius=6)
            pygame.draw.rect(screen, (200, 100, 100), btn_no, border_radius=6)
            txt_yes = hint_font.render("耍赖", True, (0,0,0))
            txt_no = hint_font.render("承受", True, (0,0,0))
            screen.blit(txt_yes, (btn_yes.x+15, btn_yes.y+5))
            screen.blit(txt_no, (btn_no.x+15, btn_no.y+5))

        # 水牛技能弹窗
        if controller.battle_session and hasattr(controller.battle_session, 'pending_choice') and controller.battle_session.pending_choice:
            choice_type = controller.battle_session.pending_choice["type"]
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            screen.blit(overlay, (0, 0))
            if choice_type == "skill_duolian":
                prompt = hint_font.render("敌方即将行动！是否使用“多练”（消耗1能量）无效敌方回合？", True, (255, 255, 200))
                prompt_rect = prompt.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
                screen.blit(prompt, prompt_rect)
                btn_yes = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 20, 80, 40)
                btn_no = pygame.Rect(WIDTH//2 + 20, HEIGHT//2 + 20, 80, 40)
                pygame.draw.rect(screen, (100, 200, 100), btn_yes, border_radius=6)
                pygame.draw.rect(screen, (200, 100, 100), btn_no, border_radius=6)
                txt_yes = hint_font.render("使用", True, (0,0,0))
                txt_no = hint_font.render("不用", True, (0,0,0))
                screen.blit(txt_yes, (btn_yes.x+15, btn_yes.y+5))
                screen.blit(txt_no, (btn_no.x+15, btn_no.y+5))

        # 游戏结束
        if controller.battle_session and controller.battle_session.state == "game_over":
            msg = controller.battle_session.log[-1] if controller.battle_session.log else ""
            over_text = hint_font.render(msg, True, (255, 200, 100))
            over_rect = over_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
            screen.blit(over_text, over_rect)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()