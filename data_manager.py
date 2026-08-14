import json
import os

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