import math
import random
from config import *
from card import PaperCard
from battle_panel import BattlePanel
from battle_session import BattleSession

class DealController:
    def __init__(self, cards, data_manager):
        self.cards = cards
        self.total = len(cards)
        self.phase = 0
        self.elapsed_time = 0.0
        self.delays = [i * 0.2 for i in range(self.total)]
        self.stack_positions = self._calc_stack_positions()
        self.spread_positions = self._calc_spread_positions()
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

        self.fixed_player_char = None
        if self.data_manager and self.data_manager.player_characters:
            self.fixed_player_char = random.choice(self.data_manager.player_characters).copy()

        for card in self.cards:
            if self.fixed_player_char:
                card.set_fixed_character(self.fixed_player_char)
            else:
                card.set_random_character()

        self.enemy_card = None
        self.enemy_start_pos = (WIDTH//2, -100)
        self.enemy_target_pos = (WIDTH//2, 150)
        self.enemy_phase = 0
        self.enemy_start_time = 0.0
        self.enemy_duration = DEAL_ANIM_DURATION
        self.battle_panel = None
        self.player_selected_char = None
        self.battle_session = None
        self.game_started = False

    def _calc_stack_positions(self):
        cx, cy = WIDTH//2, HEIGHT//2 + 20
        return [(cx + (i - self.total/2) * 2.5, cy + (i - self.total/2) * 1.5) for i in range(self.total)]

    def _calc_spread_positions(self):
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
        self.player_selected_char = self.fixed_player_char.copy() if self.fixed_player_char else card.char_data.copy()
        card.face_up = True
        self.waiting_flip = True
        self.flip_wait_start = self.elapsed_time
        target_x = WIDTH//2
        target_y = HEIGHT - 180
        self.select_target_positions = [
            (target_x, target_y) if c == card else (-c.width - 50, c.y)
            for c in self.cards
        ]

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
                self.battle_session = BattleSession(
                    self.player_selected_char,
                    self.enemy_card.char_data,
                    self.data_manager.player_characters,
                    self.data_manager.enemy_characters
                )
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
                    y += -120 * math.sin(progress * math.pi) * (1 - progress * 0.3)
                    rotation = 15 * (1 - ease)
                    card.update(x, y, rotation)
                    all_done = False
                else:
                    card.update(self.stack_positions[i][0], self.stack_positions[i][1], 0)
            if all_done:
                self.phase = 1

        elif self.phase == 2:
            progress = min(1.0, (self.elapsed_time - self.spread_start_time) / SPREAD_ANIM_DURATION)
            if progress >= 1.0:
                for i, card in enumerate(self.cards):
                    card.update(self.spread_positions[i][0], self.spread_positions[i][1], 0)
                self.phase = 3
            else:
                ease = 1 - math.pow(1 - progress, 2)
                for i, card in enumerate(self.cards):
                    sx, sy = self.stack_positions[i]
                    tx, ty = self.spread_positions[i]
                    card.update(sx + (tx - sx) * ease, sy + (ty - sy) * ease, 0)

        elif self.phase == 3:
            for i, card in enumerate(self.cards):
                card.update(self.spread_positions[i][0], self.spread_positions[i][1], 0)
            if self.waiting_flip and self.elapsed_time - self.flip_wait_start >= self.flip_wait_time:
                self.waiting_flip = False
                self.phase = 4
                self.select_start_time = self.elapsed_time
                self.select_start_positions = [(c.x, c.y) for c in self.cards]
                self.spawn_enemy_card()

        elif self.phase == 4:
            progress = min(1.0, (self.elapsed_time - self.select_start_time) / self.select_duration)
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
                    card.update(sx + (tx - sx) * ease, sy + (ty - sy) * ease, 0)

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