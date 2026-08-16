import random
from config import *

SKILL_EFFECTS = {}
PASSIVE_EFFECTS = {}

def register_skill(name):
    def decorator(func):
        SKILL_EFFECTS[name] = func
        return func
    return decorator

def register_passive(name):
    def decorator(func):
        PASSIVE_EFFECTS[name] = func
        return func
    return decorator

def trigger_timing(session, timing, target=None, **kwargs):
    if target is None:
        target = session.player
    effects = []
    skill = target.get("skill")
    if skill and skill.get("timing") == timing:
        func = SKILL_EFFECTS.get(skill.get("name"))
        if func:
            effects.append(("skill", func, skill))
    passive = target.get("passive")
    if passive and passive.get("timing") == timing:
        func = PASSIVE_EFFECTS.get(passive.get("name"))
        if func:
            effects.append(("passive", func, passive))

    for kind, func, obj in effects:
        result = func(session, **kwargs)
        if session.state == "waiting_choice":
            return False
    return True

# ---------- 技能 ----------

@register_skill("沉淀")
def skill_chen_dian(session, **kwargs):
    if session.player["energy"] < 1:
        session.log.append("能量不足！")
        return False
    session.player["energy"] -= 1
    session.player["multiplier"] *= 2
    session.log.append(f"使用技能‘沉淀’，下次攻击×{session.player['multiplier']}")
    return True

@register_skill("多练")
def skill_duo_lian(session, **kwargs):
    if session.player["energy"] < 1:
        session.log.append("能量不足！")
        return False
    session.pending_choice = {
        "type": "skill_duolian",
        "effect_func": lambda choice: _resolve_duolian(session, choice)
    }
    session.state = "waiting_choice"
    return True

def _resolve_duolian(session, choice):
    if choice:
        session.player["energy"] -= 1
        if session.player["skill_uses"] != -1:
            session.player["skill_uses"] -= 1
        session.log.append("使用技能‘多练’，敌方回合无效")
        session.state = "dice_roll"
        session.turn_winner = None
        session.pending_choice = None
    else:
        session.log.append("未使用‘多练’，敌方继续行动")
        session.pending_choice = None
        session.state = "enemy_turn"
        session._execute_enemy_attack()
        if session.state == "enemy_turn":
            session._end_enemy_turn()

@register_skill("博学")
def skill_bo_xue(session, **kwargs):
    if session.player["energy"] < 1:
        session.log.append("能量不足！")
        return False
    session.player["energy"] -= 1
    passive_lib, skill_lib = get_ability_library(session)
    combined = []
    for p in passive_lib:
        combined.append(("passive", p))
    for s in skill_lib:
        combined.append(("skill", s))
    if not combined:
        session.log.append("能力库为空，无法替换")
        session.state = "dice_roll"
        session.turn_winner = None
        return False
    random.shuffle(combined)
    options = combined[:3]
    session.pending_ability_options = options
    session.pending_choice = {"type": "select_ability", "step": "choose_ability"}
    session.state = "waiting_choice"
    session.log.append("博学技能已触发，请选择能力")
    return True

def resolve_bo_xue(session, choice):
    target_type, ability_obj = choice
    key = (ability_obj.get("name"), ability_obj.get("desc"))
    session.used_ability_keys.add(key)
    if target_type == "passive":
        session.player["passive"] = ability_obj.copy()
        session.player["passive_uses"] = session._get_initial_uses(ability_obj)
        session.log.append(f"替换被动为：{ability_obj.get('name')}")
    else:
        new_skill = ability_obj.copy()
        session.player["skill"] = new_skill
        session.player["skill_uses"] = session._get_initial_uses(new_skill)
        session.log.append(f"替换技能为：{new_skill.get('name')}")
    session.pending_choice = None
    session.state = "player_skill"

def get_ability_library(session):
    skill_lib, passive_lib = [], []
    for char in session.all_player_chars:
        if char.get("id") == session.player_id:
            continue
        if char.get("skill"):
            skill_lib.append(char["skill"].copy())
        if char.get("passive"):
            passive_lib.append(char["passive"].copy())
    for char in session.all_enemy_chars:
        if char.get("skill"):
            skill_lib.append(char["skill"].copy())
        if char.get("passive"):
            passive_lib.append(char["passive"].copy())
    unique_skill, seen = [], set()
    for s in skill_lib:
        key = (s.get("name"), s.get("desc"))
        if key in session.used_ability_keys:
            continue
        if key not in seen:
            seen.add(key)
            unique_skill.append(s)
    unique_passive, seen = [], set()
    for p in passive_lib:
        key = (p.get("name"), p.get("desc"))
        if key in session.used_ability_keys:
            continue
        if key not in seen:
            seen.add(key)
            unique_passive.append(p)
    return unique_passive, unique_skill

@register_skill("大海")
def skill_ocean(session, **kwargs):
    if session.player["ocean_activated"]:
        session.log.append("大海已激活")
        return False
    if session.player["atk"] <= 0:
        session.log.append("攻击力不足，无法激活大海")
        return False
    session.player["atk"] -= 1
    session.player["ocean_activated"] = True
    if session.player["skill_uses"] != -1:
        session.player["skill_uses"] -= 1
    session.log.append("激活技能‘大海’，受到伤害时可消耗1能量反弹伤害")
    return True

@register_skill("录音")
def skill_lu_yin(session, **kwargs):
    if session.player["energy"] < 1:
        session.log.append("能量不足！")
        return False
    session.pending_choice = {
        "type": "skill_luyin",
        "effect_func": lambda choice: _resolve_luyin(session, choice)
    }
    session.state = "waiting_choice"
    return True

def _resolve_luyin(session, choice):
    if choice:
        session.player["energy"] -= 1
        if session.player["skill_uses"] != -1:
            session.player["skill_uses"] -= 1
        session.log.append("使用技能‘录音’，敌方回合变为己方回合")
        session.state = "player_select"
        session.turn_winner = None
        session.pending_choice = None
    else:
        session.log.append("未使用‘录音’，敌方继续行动")
        session.pending_choice = None
        session.state = "enemy_turn"
        session._execute_enemy_attack()
        if session.state == "enemy_turn":
            session._end_enemy_turn()

@register_skill("进食")
def skill_eat(session, **kwargs):
    if session.player["energy"] < 1:
        session.log.append("能量不足！")
        return False
    session.player["energy"] -= 1
    session.start_skill_dice("zhu_eat")
    session.log.append("触发技能‘进食’，请掷骰拼点！")
    return True

@register_skill("亢奋")
def skill_excite(session, **kwargs):
    if session.player["energy"] < 1:
        session.log.append("能量不足！")
        return False
    session.player["energy"] -= 1
    session.start_skill_dice("da_diao_excite")
    session.log.append("触发技能‘亢奋’，请掷骰拼点！")
    return True

@register_skill("嘎嘎")
def skill_gaga(session, **kwargs):
    if session.player["energy"] < 1:
        session.log.append("能量不足！")
        return False
    session.player["energy"] -= 1
    session._gaga_active = True
    session._gaga_win_count = 0
    session.start_skill_dice("gaga")
    session.log.append("触发技能‘嘎嘎’，请掷骰拼点！")
    return True

# ---------- 被动 ----------

@register_passive("装嫩")
def passive_zhuangnen(session, **kwargs):
    return True

@register_passive("耍赖")
def passive_huangfu_lai(session, **kwargs):
    defender = kwargs.get("defender")
    damage = kwargs.get("damage")
    attacker = kwargs.get("attacker")
    if session.player.get("passive_uses", 0) == 0:
        return True
    session.pending_choice = {
        "type": "passive_huangfu_lai",
        "defender": defender,
        "damage": damage,
        "attacker": attacker,
        "effect_func": lambda choice: _resolve_huangfu_lai(session, choice, defender, damage, attacker)
    }
    session.state = "waiting_choice"
    return True

def _resolve_huangfu_lai(session, choice, defender, damage, attacker):
    if choice:
        if session.player["passive_uses"] != -1:
            session.player["passive_uses"] -= 1
        session.log.append(f"{defender['name']} 使用‘耍赖’，免疫了攻击！")
    else:
        defender["hp"] -= damage
        if defender["hp"] < 0:
            defender["hp"] = 0
        session.log.append(f"{defender['name']} 承受了 {damage} 伤害")
        session._check_game_over()
        if session.state != "game_over":
            trigger_timing(session, "on_damage_after", target=defender, defender=defender, damage=damage, attacker=attacker)
    session.pending_choice = None
    if session.state != "game_over":
        session.state = "dice_roll"
        session.turn_winner = None

@register_passive("孤独")
def passive_lonely(session, **kwargs):
    session.player["damage_taken_bonus"] += 1
    session.log.append(f"触发被动‘孤独’，受到的伤害永久+1（当前+{session.player['damage_taken_bonus']}）")
    return True

@register_passive("菜")
def passive_cai(session, **kwargs):
    return True

@register_passive("独行")
def passive_du_xing(session, **kwargs):
    pass

def action_recover_hp(session):
    max_hp = session.player.get("max_hp", 3)
    if session.player["hp"] < max_hp:
        session.player["hp"] += 1
        if session.player["hp"] > max_hp:
            session.player["hp"] = max_hp
        session.log.append("使用‘独行’，恢复1点HP")
        return True
    else:
        session.log.append("HP已满，无法恢复")
        return False

@register_passive("上面有人")
def passive_gao_da(session, **kwargs):
    attacker = kwargs.get("attacker")
    session.pending_choice = {
        "type": "passive_gao_da",
        "attacker": attacker,
        "effect_func": lambda choice: _resolve_gao_da(session, choice, attacker)
    }
    session.state = "waiting_choice"
    return True

def _resolve_gao_da(session, choice, attacker):
    if choice:
        session.player["attack_buff"] = session.player.get("attack_buff", 0) + 1
        session.log.append(f"触发被动‘上面有人’，下次攻击+1（当前攻击加成层数：{session.player['attack_buff']}）")
    else:
        session.log.append("未触发‘上面有人’")
    session.pending_choice = None
    if session.state != "game_over":
        session.state = "dice_roll"
        session.turn_winner = None

@register_passive("傲慢")
def passive_zhu(session, **kwargs):
    defender = kwargs.get("defender")
    if defender is not session.player:
        return False
    session.player["damage_count"] = session.player.get("damage_count", 0) + 1
    if session.player["damage_count"] >= 2:
        session.player["damage_count"] = 0
        if session.player["hp"] < session.player.get("max_hp", 5):
            session.player["hp"] += 1
            session.log.append("触发被动‘傲慢’，回复1点HP")
        else:
            session.log.append("触发被动‘傲慢’，但HP已满，无法回复")
    return True

@register_passive("强撑")
def passive_qiang_cheng(session, **kwargs):
    session.player["force_damage_1"] = True
    return True

# ---------- 大海反弹辅助 ----------
def trigger_ocean_reflect(session, defender, attacker, damage):
    if not session.player.get("ocean_activated", False):
        return False
    if session.player["energy"] < 1:
        session.log.append("能量不足，无法反弹")
        return False
    session.pending_choice = {
        "type": "ocean_reflect",
        "attacker": attacker,
        "damage": damage,
        "effect_func": lambda choice: _resolve_ocean_reflect(session, choice, attacker, damage)
    }
    session.state = "waiting_choice"
    return True

def _resolve_ocean_reflect(session, choice, attacker, damage):
    if choice:
        session.log.append(f"消耗1能量，反弹 {damage} 伤害给 {attacker['name']}")
        session.player["energy"] -= 1
        attacker["hp"] -= damage
        if attacker["hp"] < 0:
            attacker["hp"] = 0
        session._check_game_over()
    else:
        session.log.append("未反弹，正常承受伤害")
        session.player["hp"] -= damage
        if session.player["hp"] < 0:
            session.player["hp"] = 0
        session._check_game_over()
        if session.state != "game_over":
            trigger_timing(session, "on_damage_after", target=session.player, defender=session.player, damage=damage, attacker=attacker)
    session.pending_choice = None
    if session.state != "game_over":
        session.state = "dice_roll"
        session.turn_winner = None

# ---------- 玩家选择阶段额外动作 ----------
def get_player_select_actions(session):
    actions = []
    skill = session.player.get("skill")
    passive = session.player.get("passive")

    if skill and skill.get("name") == "大海" and not session.player.get("ocean_activated") and session.player.get("atk", 0) >= 1:
        def do_activate_ocean():
            return skill_ocean(session)
        actions.append(("activate_ocean", "激活大海", (100, 180, 200), do_activate_ocean))

    if passive and passive.get("name") == "菜" and session.player.get("passive_uses", 0) != 0:
        def do_cai():
            session.player["energy_multiplier"] *= 2
            session.log.append(f"启用被动‘菜’，能量倍率变为×{session.player['energy_multiplier']}")
            return True
        actions.append(("passive_cai", "菜", (180, 180, 80), do_cai))

    if passive and passive.get("name") == "独行":
        def do_recover():
            return action_recover_hp(session)
        actions.append(("recover_hp", "恢复HP", (200, 180, 120), do_recover))

    return actions