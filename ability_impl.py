import random
from config import *

# ---------- 技能效果注册表 ----------
SKILL_EFFECTS = {}

def register_skill(name):
    def decorator(func):
        SKILL_EFFECTS[name] = func
        return func
    return decorator

# ---------- 被动效果注册表 ----------
PASSIVE_EFFECTS = {}

def register_passive(name):
    def decorator(func):
        PASSIVE_EFFECTS[name] = func
        return func
    return decorator

# ---------- 皇甫赖 ----------
@register_skill("沉淀")
def skill_huangfu_lai(session):
    session.player["multiplier"] *= 2
    session.log.append(f"使用技能‘沉淀’，下次攻击×{session.player['multiplier']}")
    return True

@register_passive("耍赖")
def passive_huangfu_lai(session, defender, damage, attacker):
    session.pending_passive = True
    session.passive_target = defender
    session.passive_damage = damage
    session.passive_attacker = attacker
    return True

# ---------- 李博 ----------
@register_skill("博学")
def skill_bo_xue(session):
    return trigger_bo_xue(session)

def trigger_bo_xue(session):
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
    session.state = "dice_roll"
    session.turn_winner = None

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
    # 去重 + 排除已选
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

# ---------- zrui哥 ----------
@register_passive("孤独")
def passive_lonely(session):
    session.player["damage_taken_bonus"] += 1
    session.log.append(f"触发被动‘孤独’，受到的伤害永久+1（当前+{session.player['damage_taken_bonus']}）")

def activate_ocean(session):
    if session.player["ocean_activated"]:
        session.log.append("大海已激活")
        return False
    if session.player["atk"] <= 0:
        session.log.append("攻击力不足，无法激活大海")
        return False
    session.player["atk"] -= 1
    session.player["ocean_activated"] = True
    uses = session.player.get("skill_uses", 0)
    if uses != -1:
        session.player["skill_uses"] -= 1
    session.log.append("激活技能‘大海’，受到伤害时可消耗1能量反弹伤害")
    return True

def trigger_ocean_reflect(session, defender, attacker, damage):
    if not session.player.get("ocean_activated", False):
        return False
    if session.player["energy"] < 1:
        session.log.append("能量不足，无法反弹")
        return False
    session.pending_choice = {"type": "ocean_reflect"}
    session.passive_target = attacker
    session.passive_damage = damage
    session.state = "waiting_choice"
    return True

def resolve_ocean_reflect(session, choice):
    if choice:
        session.log.append(f"消耗1能量，反弹 {session.passive_damage} 伤害给 {session.passive_target['name']}")
        session.player["energy"] -= 1
        session.passive_target["hp"] -= session.passive_damage
        if session.passive_target["hp"] < 0:
            session.passive_target["hp"] = 0
        session._check_game_over()
    else:
        session.log.append("未反弹，正常承受伤害")
        session.player["hp"] -= session.passive_damage
        if session.player["hp"] < 0:
            session.player["hp"] = 0
        session._check_game_over()
    session.pending_choice = None
    session.passive_target = None
    session.passive_damage = 0
    if session.state != "game_over":
        session.state = "dice_roll"
        session.turn_winner = None

# ---------- 水牛 ----------
def trigger_duolian(session):
    skill = session.player.get("skill")
    cost = skill.get("cost", 999) if skill else 999
    if session.player["energy"] < cost or session.player.get("skill_uses", 0) == 0:
        return False
    session.pending_choice = {"type": "skill_duolian"}
    session.state = "waiting_choice"
    return True

def resolve_duolian(session, choice):
    if choice:
        skill = session.player.get("skill")
        cost = skill.get("cost", 999)
        session.player["energy"] -= cost
        uses = session.player.get("skill_uses", 0)
        if uses != -1:
            session.player["skill_uses"] -= 1
        session.log.append("使用技能‘多练’，敌方回合无效")
        session.pending_choice = None
        session.state = "dice_roll"
        session.turn_winner = None
    else:
        session.log.append("未使用‘多练’，敌方继续行动")
        session.pending_choice = None
        session.state = "enemy_turn"
        session.ai_turn()

# ---------- 搞大 ----------
@register_passive("上面有人")
def passive_gao_da(session, defender, damage, attacker):
    session.pending_choice = {"type": "passive_gao_da", "attacker": attacker}
    session.state = "waiting_choice"
    return True

def resolve_gao_da(session, choice):
    if choice:
        session.player["attack_buff"] = session.player.get("attack_buff", 0) + 1
        session.log.append(f"触发被动‘上面有人’，下次攻击+1（当前攻击加成层数：{session.player['attack_buff']}）")
    else:
        session.log.append("未触发‘上面有人’")
    session.pending_choice = None

def trigger_luyin(session):
    skill = session.player.get("skill")
    if not skill or skill.get("name") != "录音":
        return False
    if session.player["energy"] < 1 or session.player.get("skill_uses", 0) == 0:
        return False
    session.pending_choice = {"type": "skill_luyin"}
    session.state = "waiting_choice"
    return True

def resolve_luyin(session, choice):
    if choice:
        skill = session.player.get("skill")
        cost = skill.get("cost", 1)
        session.player["energy"] -= cost
        uses = session.player.get("skill_uses", 0)
        if uses != -1:
            session.player["skill_uses"] -= 1
        session.log.append("使用技能‘录音’，敌方回合变为己方回合")
        session.pending_choice = None
        session.state = "player_turn"
        session.turn_winner = None
    else:
        session.log.append("未使用‘录音’，敌方继续行动")
        session.pending_choice = None
        session.state = "enemy_turn"
        session.ai_turn()