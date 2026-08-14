import pygame
import random
import math
from config import *
from utils import load_font, draw_heart, draw_sword, draw_energy

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
        self.duration = PANEL_ANIM_DURATION
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
        if not self.active or self.progress >= 1.0:
            return
        elapsed = elapsed_time - self.start_time
        self.progress = min(1.0, elapsed / self.duration)
        ease = 1 - math.pow(1 - self.progress, 2)
        self.x = self.target_x + (WIDTH + 50 - self.target_x) * (1 - ease)

    def draw(self, surface, mouse_pos=None, player_energy=0, player_multiplier=1, energy_multiplier=1, player_id="", ocean_activated=False, attack_buff=0):
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

        # 敌方（上）
        self._draw_char_info(surface, self.enemy_data, self.x + 12, self.y + 16, self.width - 24,
                             self.enemy_skill, self.enemy_passive, False, 0, "", False, 0)
        # 玩家（下）
        self._draw_char_info(surface, self.player_data, self.x + 12, mid_y + 16, self.width - 24,
                             self.player_skill, self.player_passive, True, player_energy, player_id, ocean_activated, attack_buff)

    def _draw_char_info(self, surface, char_data, x, y, width,
                        skill_obj, passive_obj, is_player, player_energy, player_id, ocean_activated, attack_buff=0):
        # 名字
        name_surf = self.font_title.render(char_data["name"], True, COLOR_CARD_TEXT)
        surface.blit(name_surf, (x, y))
        attr_x = x + name_surf.get_width() + 8

        hp = char_data.get("hp", 0)
        max_hp = char_data.get("max_hp", hp)
        atk = char_data.get("atk", 0)
        bonus = 0
        if is_player:
            bonus = max(0, self.player_multiplier - 1) + attack_buff
        energy = char_data.get("energy", 0)

        # 血量
        for i in range(max_hp):
            cx = attr_x + i * 16
            cy = y + 2
            draw_heart(surface, cx, cy, 6, filled=(i < hp), color=COLOR_HP if i < hp else COLOR_HP_LOST)
        attr_x += max_hp * 16 + 6 if max_hp > 0 else 6

        # 攻击力（黑剑）
        for i in range(atk):
            draw_sword(surface, attr_x + i * 18, y + 2, color=COLOR_ATK)
        attr_x += atk * 18 + 6 if atk > 0 else 6

        # 额外加成（黄剑）
        for i in range(bonus):
            draw_sword(surface, attr_x + i * 18, y + 2, color=COLOR_ATK_BONUS)
        attr_x += bonus * 18 + 6 if bonus > 0 else 6

        # 能量
        draw_energy(surface, attr_x, y + 2, energy)

        # 被动
        row_y = y + 34
        if passive_obj:
            passive_name = passive_obj.get("name", "")
            passive_desc = passive_obj.get("desc", "")
            uses = char_data.get("passive_uses", 0)
            if uses > 0 or uses == -1:
                display = passive_name
                if uses == -1:
                    display += "（∞）"
                else:
                    display += f"（剩余{uses}次）"
            elif uses == 0:
                display = passive_name + "（已失效）"
            else:
                display = "无"
            text = f"被动：{display}"
            color = (180, 80, 80) if uses == 0 else COLOR_CARD_TEXT
        else:
            text = "被动：无"
            color = COLOR_CARD_TEXT
        surf = self.font_text.render(text, True, color)
        surface.blit(surf, (x, row_y))
        rect = pygame.Rect(x, row_y, surf.get_width(), surf.get_height())
        if passive_obj:
            self.hover_rects.append((rect, passive_obj.get("desc", ""), "被动"))

        # 技能
        row_y += 22
        if is_player and skill_obj:
            skill_name = skill_obj.get("name", "")
            skill_desc = skill_obj.get("desc", "")
            if skill_name == "大海":
                display_name = skill_name + ("（已激活）" if ocean_activated else "（未激活）")
                text = f"技能：{display_name}"
                surf = self.font_text.render(text, True, COLOR_CARD_TEXT)
                surface.blit(surf, (x, row_y))
                desc_rect = pygame.Rect(x, row_y, surf.get_width(), surf.get_height())
                self.hover_rects.append((desc_rect, skill_desc, "技能"))
            else:
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

        # 能量倍率
        if is_player and self.energy_multiplier_display > 1:
            row_y += 22
            text = f"能量倍率：×{self.energy_multiplier_display}"
            surf = self.font_small.render(text, True, (200, 150, 0))
            surface.blit(surf, (x, row_y))

    def get_hover_text(self, mouse_pos):
        if not self.active or mouse_pos is None:
            return None
        for rect, desc, title in self.hover_rects:
            if rect.collidepoint(mouse_pos) and desc:
                return (title, desc)
        return None

    def get_skill_button_rect(self):
        return self.skill_button_rect

    def update_data(self, player_data, enemy_data):
        self.player_data = player_data
        self.enemy_data = enemy_data
        self.player_skill = player_data.get("skill")
        self.player_passive = player_data.get("passive")
        self.enemy_skill = enemy_data.get("skill")
        self.enemy_passive = enemy_data.get("passive")