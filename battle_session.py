import random
from config import *
from ability_impl import trigger_timing, SKILL_EFFECTS, PASSIVE_EFFECTS, \
                      resolve_bo_xue, trigger_ocean_reflect, \
                      action_recover_hp, get_player_select_actions

class BattleSession:
    def __init__(self, player_char, enemy_char, all_player_chars=None, all_enemy_chars=None):
        self.player = player_char.copy()
        self.enemy = enemy_char.copy()
        self.player["max_hp"] = player_char.get("max_hp", player_char["hp"])
        self.enemy["max_hp"] = enemy_char.get("max_hp", enemy_char["hp"])
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
        self.player["damage_count"] = 0
        self.player["force_damage_1"] = False

        self.state = "dice_roll"
        self.dice_player = 0
        self.dice_enemy = 0
        self.turn_winner = None
        self.log = []
        self.result_timer = 0.0
        self.pending_choice = None
        self.pending_ability_options = []
        self.used_ability_keys = set()
        self.skill_dice_data = None
        self._previous_state = None
        self._skill_dice_result_text = ""

        self._pvp_win_count = 0
        self._gaga_active = False
        self._gaga_win_count = 0

        self.player_id = player_char.get("id", "")
        self.enemy_id = enemy_char.get("id", "")
        self.all_player_chars = all_player_chars if all_player_chars else []
        self.all_enemy_chars = all_enemy_chars if all_enemy_chars else []

        self._action_funcs = {}

    def _get_initial_uses(self, ability_obj):
        if ability_obj is None:
            return 0
        return ability_obj.get("uses", 0)

    def _trigger_timing(self, timing, target=None, **kwargs):
        return trigger_timing(self, timing, target=target, **kwargs)

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
                self._resolve_dice_result()
        elif self.state == "skill_dice_result":
            self.result_timer -= dt
            if self.result_timer <= 0:
                if self._gaga_active:
                    self.state = "skill_dice"
                else:
                    if self._previous_state:
                        self.state = self._previous_state
                        self._previous_state = None
                    else:
                        self.state = "dice_roll"
                        self.turn_winner = None
        elif self.state == "skill_dice":
            pass

    def _resolve_dice_result(self):
        if self.turn_winner == 'player':
            passive = self.player.get("passive")
            if passive and passive.get("name") == "装嫩":
                self._on_pvp_win()
            self._trigger_timing("on_dice_win", target=self.player)
            if self.state == "waiting_choice":
                return
            self.state = "player_select"
        elif self.turn_winner == 'enemy':
            self._start_enemy_turn()
        else:
            self.state = "dice_roll"
            self.turn_winner = None
            self.log.append("平局，重新掷骰")

    def _on_pvp_win(self):
        self._pvp_win_count += 1
        if self._pvp_win_count >= 2:
            self._pvp_win_count = 0
            self.player["energy"] += 1
            self.log.append("触发被动‘装嫩’，获得1能量")

    def get_available_actions(self):
        self._action_funcs = {}
        actions = [
            ("attack", "攻击", (180, 120, 120)),
            ("energy", "能量" + ("×"+str(self.player["energy_multiplier"]) if self.player["energy_multiplier"]>1 else ""), (120, 180, 120))
        ]
        extra = get_player_select_actions(self)
        for action_id, label, color, func in extra:
            actions.append((action_id, label, color))
            self._action_funcs[action_id] = func
        return actions

    def execute_action(self, action_id):
        if action_id == "attack":
            self._execute_attack('player', 'enemy')
            if self.state != "game_over" and self.state != "waiting_choice":
                self._end_player_phase()
            return True
        elif action_id == "energy":
            gain = self.player.get("energy_multiplier", 1)
            self.player["energy"] += gain
            self.log.append(f"获得 {gain} 能量" + ("（翻倍）" if gain > 1 else ""))
            self.player["energy_multiplier"] = 1
            if self.state != "game_over" and self.state != "waiting_choice":
                self._end_player_phase()
            return True
        else:
            func = self._action_funcs.get(action_id)
            if func:
                result = func()
                if result and self.state != "game_over" and self.state != "waiting_choice":
                    self._end_player_phase()
                return result
            else:
                self.log.append(f"未知行动：{action_id}")
                return False

    def _end_player_phase(self):
        if self.state == "game_over" or self.state == "waiting_choice":
            return
        skill = self.player.get("skill")
        if skill and skill.get("timing") == "player_skill":
            cost = skill.get("cost", 999)
            uses = self.player.get("skill_uses", 0)
            if self.player["energy"] >= cost and uses != 0:
                self.state = "player_skill"
                self.log.append("【技能阶段】可点击具体技能使用")
            else:
                self.state = "player_skill"
                self.log.append("技能不可用，请点击‘结束’退出")
        else:
            self.state = "dice_roll"
            self.turn_winner = None

    def use_skill_in_phase(self, skill_name):
        if self.state == "game_over":
            return False
        if self.state != "player_skill":
            self.log.append("当前不在技能阶段")
            return False

        skill = self.player.get("skill")
        if skill is None or skill.get("name") != skill_name:
            self.log.append("未找到该技能")
            return False

        uses = self.player.get("skill_uses", 0)
        if uses == 0:
            self.log.append("技能次数已用完！")
            return False

        effect_func = SKILL_EFFECTS.get(skill_name)
        if effect_func is None:
            self.log.append(f"未找到技能效果：{skill_name}")
            return False

        result = effect_func(self)
        if result:
            if self.state in ("skill_dice", "waiting_choice"):
                return True
            if self.state != "game_over":
                skill = self.player.get("skill")
                if skill and skill.get("timing") == "player_skill":
                    cost = skill.get("cost", 999)
                    uses = self.player.get("skill_uses", 0)
                    if self.player["energy"] < cost or uses == 0:
                        self.state = "player_skill"
                        self.log.append("技能不可用，请点击‘结束’退出")
                    else:
                        self.log.append("技能使用成功，可继续使用")
                else:
                    self.state = "dice_roll"
                    self.turn_winner = None
        else:
            self.log.append("技能执行失败")
        return result

    def end_skill_phase(self):
        if self.state == "game_over":
            return
        if self.state == "player_skill":
            self.state = "dice_roll"
            self.turn_winner = None
            self.log.append("结束技能阶段")
        else:
            self.log.append("不在技能阶段")

    def use_anytime_skill(self, skill_name):
        if self.state == "game_over":
            return False
        skill = self.player.get("skill")
        if not skill or skill.get("name") != skill_name:
            self.log.append("没有该技能")
            return False
        if skill.get("timing") != "anytime":
            self.log.append("该技能不是 anytime 技能")
            return False
        uses = self.player.get("skill_uses", 0)
        if uses == 0:
            self.log.append("技能次数已用完！")
            return False
        effect_func = SKILL_EFFECTS.get(skill_name)
        if effect_func is None:
            self.log.append("未找到技能效果")
            return False
        result = effect_func(self)
        if result:
            if self.state == "waiting_choice":
                return True
            self.log.append(f"使用 {skill_name} 成功")
        return result

    def start_skill_dice(self, skill_type, record_previous=True):
        if record_previous:
            self._previous_state = self.state
        self.skill_dice_data = {"type": skill_type}
        self.state = "skill_dice"

    def resolve_skill_dice(self, player_val, enemy_val):
        if self.state == "game_over":
            return
        if self.state != "skill_dice" or not self.skill_dice_data:
            return

        skill_type = self.skill_dice_data["type"]

        if skill_type == "gaga":
            if self._gaga_active:
                if player_val > enemy_val:
                    self._gaga_win_count += 1
                    self.log.append(f"嘎嘎拼点胜利，累计胜利 {self._gaga_win_count} 次")
                    self.start_skill_dice("gaga", record_previous=False)
                    self._skill_dice_result_text = "嘎嘎胜利！继续拼点"
                    self.state = "skill_dice_result"
                    self.result_timer = RESULT_DISPLAY_DURATION
                    return
                elif player_val < enemy_val:
                    heal = self._gaga_win_count
                    self.player["hp"] = min(self.player["hp"] + heal, self.player["max_hp"])
                    self.log.append(f"嘎嘎拼点失败，恢复 {heal} 点HP")
                    self._gaga_active = False
                    self._gaga_win_count = 0
                    self.skill_dice_data = None
                    self._skill_dice_result_text = "嘎嘎失败！"
                    self.state = "skill_dice_result"
                    self.result_timer = RESULT_DISPLAY_DURATION
                    return
                else:
                    self.log.append("嘎嘎平局，重新掷骰")
                    self.start_skill_dice("gaga", record_previous=False)
                    self.state = "skill_dice"
                    return
            else:
                self.log.append("嘎嘎技能已结束")
                self.state = "dice_roll"
                self.turn_winner = None
                self.skill_dice_data = None
                return

        if skill_type == "zhu_eat":
            if player_val > enemy_val:
                self._zhu_eat_win()
                self._skill_dice_result_text = "进食胜利！"
            elif player_val < enemy_val:
                self._zhu_eat_lose()
                self._skill_dice_result_text = "进食失败！"
            else:
                self._zhu_eat_tie()
                self._skill_dice_result_text = "进食平局，重掷！"
                self.state = "skill_dice"
                return
        elif skill_type == "da_diao_excite":
            if player_val > enemy_val:
                self._da_diao_win()
                if self.state == "game_over":
                    return
                self._skill_dice_result_text = "亢奋胜利！"
            elif player_val < enemy_val:
                self._da_diao_lose()
                self._skill_dice_result_text = "亢奋失败！"
            else:
                self._da_diao_tie()
                self._skill_dice_result_text = "亢奋平局，重掷！"
                self.state = "skill_dice"
                return
        else:
            self.skill_dice_data = None
            self.state = "dice_roll"
            self.turn_winner = None
            return

        self.skill_dice_data = None
        self.state = "skill_dice_result"
        self.result_timer = RESULT_DISPLAY_DURATION

    def _zhu_eat_win(self):
        if self.state == "game_over":
            return
        if self.player["hp"] < self.player.get("max_hp", 5):
            self.player["hp"] += 1
            self.log.append("进食拼点胜利，回复1点HP")
        else:
            self.log.append("进食拼点胜利，但HP已满，无法回复")

    def _zhu_eat_lose(self):
        if self.state == "game_over":
            return
        self.player["max_hp"] = self.player.get("max_hp", 5) + 1
        self.log.append(f"进食拼点失败，最大HP+1，当前最大HP：{self.player['max_hp']}")

    def _zhu_eat_tie(self):
        if self.state == "game_over":
            return
        self.log.append("进食拼点平局，重新掷骰")

    def _da_diao_win(self):
        if self.state == "game_over":
            return
        self.log.append("亢奋拼点胜利，执行一次攻击")
        self._execute_attack('player', 'enemy')

    def _da_diao_lose(self):
        if self.state == "game_over":
            return
        self.log.append("亢奋拼点失败，无效果")

    def _da_diao_tie(self):
        if self.state == "game_over":
            return
        self.log.append("亢奋拼点平局，重新掷骰")

    def _start_enemy_turn(self):
        if self.state == "game_over":
            return
        self.state = "enemy_turn"
        result = self._trigger_timing("on_enemy_turn_start", target=self.player)
        if self.state == "waiting_choice":
            return
        if self.state == "enemy_turn":
            self._execute_enemy_attack()

    def _execute_enemy_attack(self):
        if self.state == "game_over":
            return
        attacker = self.enemy
        defender = self.player
        self.log.append(f"{attacker['name']} 开始攻击")
        damage = attacker["atk"] * attacker.get("multiplier", 1)
        attacker["multiplier"] = 1

        debuff = attacker.get("attack_debuff", 0)
        if debuff > 0:
            damage = max(0, damage - debuff)
            attacker["attack_debuff"] = 0
            self.log.append(f"敌方攻击因减益下降，实际伤害 {damage}")

        if self.player.get("passive") and self.player["passive"].get("name") == "孤独":
            damage += self.player.get("damage_taken_bonus", 0)

        if self.player.get("ocean_activated", False) and self.player["energy"] >= 1:
            if trigger_ocean_reflect(self, defender, attacker, damage):
                return

        result = self._trigger_timing("on_damage_before", target=defender, defender=defender, damage=damage, attacker=attacker)
        if self.state == "waiting_choice":
            return

        if self.player.get("force_damage_1", False):
            damage = 1
            self.player["force_damage_1"] = False
        defender["hp"] -= damage
        if defender["hp"] < 0:
            defender["hp"] = 0
        self.log.append(f"{attacker['name']} 攻击 {defender['name']}，造成 {damage} 伤害")
        if self._check_game_over():
            return
        result2 = self._trigger_timing("on_damage_after", target=defender, defender=defender, damage=damage, attacker=attacker)
        if self.state == "waiting_choice":
            return
        self._end_enemy_turn()

    def _end_enemy_turn(self):
        if self.state == "game_over":
            return
        self.state = "dice_roll"
        self.turn_winner = None

    def _execute_attack(self, attacker_key, defender_key):
        if self.state == "game_over":
            return
        attacker = self.player if attacker_key == 'player' else self.enemy
        defender = self.player if defender_key == 'player' else self.enemy
        damage = attacker["atk"] * attacker.get("multiplier", 1)
        attacker["multiplier"] = 1

        self._trigger_timing("on_attack_before", target=attacker, attacker=attacker, defender=defender)
        if self.state == "waiting_choice":
            return

        if attacker_key == 'player':
            buff = self.player.get("attack_buff", 0)
            if buff > 0:
                damage += buff
                self.player["attack_buff"] = 0
                self.log.append(f"玩家攻击获得加成，实际伤害 {damage}")

        if defender_key == 'player':
            if self.player.get("passive") and self.player["passive"].get("name") == "孤独":
                damage += self.player.get("damage_taken_bonus", 0)

        if defender_key == 'player' and self.player.get("ocean_activated", False) and self.player["energy"] >= 1:
            if trigger_ocean_reflect(self, defender, attacker, damage):
                return

        result = self._trigger_timing("on_damage_before", target=defender, defender=defender, damage=damage, attacker=attacker)
        if self.state == "waiting_choice":
            return

        if defender_key == 'player' and self.player.get("force_damage_1", False):
            damage = 1
            self.player["force_damage_1"] = False
        defender["hp"] -= damage
        if defender["hp"] < 0:
            defender["hp"] = 0
        self.log.append(f"{attacker['name']} 攻击 {defender['name']}，造成 {damage} 伤害")
        if self._check_game_over():
            return
        result2 = self._trigger_timing("on_damage_after", target=defender, defender=defender, damage=damage, attacker=attacker)
        if self.state == "waiting_choice":
            return

    def resolve_choice(self, choice):
        if self.state == "game_over":
            return
        if not self.pending_choice:
            return
        if "effect_func" in self.pending_choice:
            self.pending_choice["effect_func"](choice)
            if self.pending_choice is not None:
                return
        else:
            choice_type = self.pending_choice["type"]
            if choice_type == "select_ability":
                step = self.pending_choice.get("step")
                if step == "choose_ability":
                    resolve_bo_xue(self, choice)
        self.pending_choice = None

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
        p_data["damage_count"] = self.player.get("damage_count", 0)
        p_data["pvp_win_count"] = self._pvp_win_count
        return p_data, e_data