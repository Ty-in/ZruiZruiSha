import random
from config import *
from ability_impl import *

class BattleSession:
    def __init__(self, player_char, enemy_char, all_player_chars=None, all_enemy_chars=None):
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
        self.player["damage_taken_bonus"] = 0
        self.player["ocean_activated"] = False
        self.enemy["attack_debuff"] = 0
        self.player["attack_buff"] = 0

        self.state = "dice_roll"
        self.dice_player = 0
        self.dice_enemy = 0
        self.turn_winner = None
        self.log = []
        self.pending_passive = False
        self.passive_target = None
        self.passive_damage = 0
        self.passive_attacker = None
        self.result_timer = 0.0
        self.pending_choice = None
        self.pending_ability_options = []
        self.used_ability_keys = set()

        self.player_id = player_char.get("id", "")
        self.enemy_id = enemy_char.get("id", "")
        self.all_player_chars = all_player_chars if all_player_chars else []
        self.all_enemy_chars = all_enemy_chars if all_enemy_chars else []

    def _get_initial_uses(self, ability_obj):
        if ability_obj is None:
            return 0
        return ability_obj.get("uses", 0)

    def use_skill(self):
        skill = self.player.get("skill")
        if skill is None:
            self.log.append("没有技能")
            return False
        uses = self.player.get("skill_uses", 0)
        if uses == 0:
            self.log.append("技能次数已用完！")
            return False

        skill_name = skill.get("name")
        effect_func = SKILL_EFFECTS.get(skill_name)
        if effect_func is None:
            self.log.append(f"未找到技能效果：{skill_name}")
            return False

        if skill_name == "博学":
            return effect_func(self)

        cost = skill.get("cost", 999)
        if self.player["energy"] < cost:
            self.log.append("能量不足！")
            return False
        self.player["energy"] -= cost
        if uses != -1:
            self.player["skill_uses"] -= 1
        return effect_func(self)

    def _try_apply_passive(self, defender, timing, damage, attacker):
        if defender is not self.player:
            return False
        passive = self.player.get("passive")
        if passive is None:
            return False
        if passive.get("timing") != timing:
            return False
        if self.player.get("passive_uses", 0) == 0:
            return False
        effect_func = PASSIVE_EFFECTS.get(passive.get("name"))
        if effect_func is None:
            return False
        return effect_func(self, defender, damage, attacker)

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
        self.result_timer = RESULT_DISPLAY_DURATION

    def update(self, dt):
        if self.state == "dice_result":
            self.result_timer -= dt
            if self.result_timer <= 0:
                self.start_turn()

    def start_turn(self):
        if self.turn_winner == 'player':
            passive = self.player.get("passive")
            if passive and passive.get("name") == "孤独":
                effect_func = PASSIVE_EFFECTS.get("孤独")
                if effect_func:
                    effect_func(self)
            self.state = "player_turn"
        elif self.turn_winner == 'enemy':
            skill = self.player.get("skill")
            if skill and skill.get("name") == "录音":
                if trigger_luyin(self):
                    return
            if skill and skill.get("name") == "多练":
                if trigger_duolian(self):
                    return
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
            resolve_duolian(self, choice)
        elif choice_type == "ocean_reflect":
            resolve_ocean_reflect(self, choice)
        elif choice_type == "select_ability":
            step = self.pending_choice.get("step")
            if step == "choose_ability":
                resolve_bo_xue(self, choice)
        elif choice_type == "passive_gao_da":
            resolve_gao_da(self, choice)
        elif choice_type == "skill_luyin":
            resolve_luyin(self, choice)

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
                self.log.append(f"获得 {gain} 能量（倍率×{self.player['energy_multiplier']}）")
            self.player["energy_multiplier"] = 1
            self._end_player_turn()
        elif action == "passive_cai":
            passive = self.player.get("passive")
            if passive and passive.get("name") == "菜" and self.player.get("passive_uses", 0) != 0:
                self.player["energy_multiplier"] *= 2
                self.log.append(f"启用被动‘菜’，能量倍率变为×{self.player['energy_multiplier']}")
                self._end_player_turn()
        elif action == "activate_ocean":
            if activate_ocean(self):
                self._end_player_turn()
            else:
                self.log.append("激活失败")
        elif action == "recover_hp":
            passive = self.player.get("passive")
            if passive and passive.get("name") == "独行":
                max_hp = self.player.get("max_hp", 3)
                if self.player["hp"] < max_hp:
                    self.player["hp"] += 1
                    if self.player["hp"] > max_hp:
                        self.player["hp"] = max_hp
                    self.log.append("使用‘独行’，恢复1点HP")
                else:
                    self.log.append("HP已满，无法恢复")
                self._end_player_turn()

    def _execute_attack(self, attacker_key, defender_key):
        attacker = self.player if attacker_key == 'player' else self.enemy
        defender = self.player if defender_key == 'player' else self.enemy
        damage = attacker["atk"] * attacker.get("multiplier", 1)
        attacker["multiplier"] = 1

        if attacker_key == 'player':
            buff = self.player.get("attack_buff", 0)
            if buff > 0:
                damage += buff
                self.player["attack_buff"] = 0
                self.log.append(f"玩家攻击获得加成，实际伤害 {damage}")

        if attacker_key == 'enemy' and defender_key == 'player':
            debuff = attacker.get("attack_debuff", 0)
            if debuff > 0:
                damage = max(0, damage - debuff)
                attacker["attack_debuff"] = 0
                self.log.append(f"敌方攻击因减益下降，实际伤害 {damage}")

        if defender is self.player and self.player_id == "zrui_ge":
            damage += self.player.get("damage_taken_bonus", 0)

        defender["hp"] -= damage
        if defender["hp"] < 0:
            defender["hp"] = 0
        self.log.append(f"{attacker['name']} 攻击 {defender['name']}，造成 {damage} 伤害")
        if self._check_game_over():
            return

        if defender_key == 'player':
            self._try_apply_passive(defender, "on_take_damage", damage, attacker)

    def resolve_passive(self, use_passive):
        if not self.pending_passive:
            return
        if use_passive:
            if self.player["passive_uses"] != -1:
                self.player["passive_uses"] -= 1
            self.log.append(f"{self.passive_target['name']} 使用‘耍赖’，免疫了攻击！")
            self.passive_target["hp"] += self.passive_damage
            if self.passive_target["hp"] > self.passive_target["max_hp"]:
                self.passive_target["hp"] = self.passive_target["max_hp"]
        else:
            self.log.append(f"{self.passive_target['name']} 承受了伤害")
        self.pending_passive = False
        self.passive_target = None
        self.passive_damage = 0
        self.passive_attacker = None
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
        p_data["attack_buff"] = self.player.get("attack_buff", 0)
        return p_data, e_data