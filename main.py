import pygame
import sys
import random
from config import *
from utils import load_font, generate_wood_texture, draw_dice
from data_manager import DataManager
from card import PaperCard
from deal_controller import DealController

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("桌面卡牌 · 对战")
    clock = pygame.time.Clock()

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
                elif event.key == pygame.K_SPACE and controller.get_phase() == 1:
                    controller.trigger_spread()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 优先处理等待选择弹窗
                if controller.battle_session and controller.battle_session.state == "waiting_choice":
                    if controller.battle_session.pending_choice:
                        choice_type = controller.battle_session.pending_choice["type"]
                        if choice_type in ["skill_duolian", "ocean_reflect", "passive_gao_da", "skill_luyin", "passive_huangfu_lai"]:
                            btn_yes = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 20, 80, 40)
                            btn_no = pygame.Rect(WIDTH//2 + 20, HEIGHT//2 + 20, 80, 40)
                            if btn_yes.collidepoint(event.pos):
                                controller.battle_session.resolve_choice(True)
                            elif btn_no.collidepoint(event.pos):
                                controller.battle_session.resolve_choice(False)
                        elif choice_type == "select_ability":
                            options = controller.battle_session.pending_ability_options
                            for idx, (opt_type, ability) in enumerate(options):
                                btn_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 20 + idx * 50, 300, 40)
                                if btn_rect.collidepoint(event.pos):
                                    controller.battle_session.resolve_choice((opt_type, ability))
                                    break
                    continue

                # 骰子按钮
                if controller.battle_session:
                    if controller.battle_session.state in ["dice_roll", "skill_dice"]:
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

                # player_select 按钮
                if controller.battle_session and controller.battle_session.state == "player_select":
                    for action_id, rect in button_rects.items():
                        if rect.collidepoint(event.pos):
                            controller.battle_session.execute_action(action_id)
                            break

                # player_skill 按钮
                if controller.battle_session and controller.battle_session.state == "player_skill":
                    for name, rect in button_rects.items():
                        if name.startswith("skill_"):
                            skill_name = name[6:]
                            if rect.collidepoint(event.pos):
                                controller.battle_session.use_skill_in_phase(skill_name)
                        elif name == "end_skill" and rect.collidepoint(event.pos):
                            controller.battle_session.end_skill_phase()

                # 草稿纸 anytime 技能按钮
                if controller.battle_panel:
                    skill_rect = controller.battle_panel.get_skill_button_rect()
                    if skill_rect and skill_rect.collidepoint(event.pos):
                        if controller.battle_session:
                            skill = controller.battle_session.player.get("skill")
                            if skill and skill.get("timing") == "anytime":
                                controller.battle_session.use_anytime_skill(skill.get("name"))

        controller.update(dt)

        # 骰子动画
        if dice_animating:
            elapsed = controller.elapsed_time - dice_anim_start
            if elapsed >= DICE_ANIM_DURATION:
                dice_animating = False
                dice_rolled = True
                if controller.battle_session:
                    if controller.battle_session.state == "skill_dice":
                        controller.battle_session.resolve_skill_dice(final_vals[0], final_vals[1])
                    else:
                        controller.battle_session.set_dice_results(final_vals[0], final_vals[1])
                    dice_values = (final_vals[0], final_vals[1])
            else:
                if int(elapsed * 30) % 2 == 0:
                    dice_anim_values[0] = random.randint(1, 6)
                    dice_anim_values[1] = random.randint(1, 6)

        # 卡牌悬停
        if controller.get_phase() == 3 and not controller.is_waiting_flip():
            mouse_pos = pygame.mouse.get_pos()
            for card in cards:
                card.update_hover(mouse_pos)
        else:
            for card in cards:
                card.target_y_offset = 0
                card.target_scale = 1.0

        # 绘制背景
        screen.blit(wood_texture, (0, 0))

        # 绘制卡牌
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
            ocean_activated = False
            attack_buff = 0
            damage_count = 0
            if controller.battle_session:
                player_energy = controller.battle_session.player.get("energy", 0)
                player_multiplier = controller.battle_session.player.get("multiplier", 1)
                energy_multiplier = controller.battle_session.player.get("energy_multiplier", 1)
                ocean_activated = controller.battle_session.player.get("ocean_activated", False)
                attack_buff = controller.battle_session.player.get("attack_buff", 0)
                damage_count = controller.battle_session.player.get("damage_count", 0)
            controller.battle_panel.draw(screen, mouse_pos, player_energy, player_multiplier, energy_multiplier,
                                         controller.battle_session.player_id if controller.battle_session else "",
                                         ocean_activated, attack_buff, damage_count)
            hover_info = controller.battle_panel.get_hover_text(mouse_pos)
            if hover_info:
                tip_font = load_font(18)
                lines = [f"{hover_info[0]}：", hover_info[1]] if hover_info[1] else [hover_info[0]]
                max_width = max(tip_font.render(line, True, (40,30,20)).get_width() for line in lines)
                padding = 10
                box_width = max_width + padding * 2
                box_height = len(lines) * 26 + padding * 2
                tip_x = min(mouse_pos[0] + 16, WIDTH - box_width - 16)
                tip_y = min(mouse_pos[1] + 16, HEIGHT - box_height - 16)
                s = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
                s.fill((250, 245, 220, 230))
                pygame.draw.rect(s, (100, 75, 50, 200), s.get_rect(), 2, border_radius=4)
                screen.blit(s, (tip_x, tip_y))
                for i, line in enumerate(lines):
                    surf = tip_font.render(line, True, (40,30,20))
                    screen.blit(surf, (tip_x + padding, tip_y + padding + i * 26))

        # 底部提示
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
                elif state == "skill_dice":
                    hint = hint_font.render("【技能拼点】点击左侧按钮投骰子！", True, (255,255,230))
                elif state == "dice_result":
                    winner = controller.battle_session.turn_winner
                    hint = hint_font.render("玩家赢！" if winner == 'player' else "敌方赢！" if winner == 'enemy' else "平局！", True, (255,255,230))
                elif state == "skill_dice_result":
                    result_text = controller.battle_session._skill_dice_result_text
                    hint = hint_font.render(result_text, True, (255, 255, 230))
                elif state == "player_select":
                    hint = hint_font.render("【选择行动】", True, (255,255,230))
                elif state == "player_skill":
                    hint = hint_font.render("【技能阶段】点击技能按钮使用", True, (255,255,230))
                elif state == "enemy_turn":
                    hint = hint_font.render("敌方攻击中...", True, (255,255,230))
                elif state == "waiting_choice":
                    hint = hint_font.render("请选择", True, (255,255,230))
                elif state == "game_over":
                    hint = hint_font.render("游戏结束！按 R 重新开始", True, (255,255,230))
                else:
                    hint = hint_font.render("战斗进行中...", True, (255,255,230))
            else:
                hint = hint_font.render("敌方出现！", True, (255,255,230))
        screen.blit(hint, (20, HEIGHT - 40))

        # 骰子按钮（左）
        if controller.battle_session and controller.battle_session.state in ["dice_roll", "skill_dice"]:
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
            draw_dice(screen, start_x, y_pos, dice_size, show_player, DICE_PLAYER_COLOR)
            draw_dice(screen, start_x + dice_size + 30, y_pos, dice_size, show_enemy, DICE_ENEMY_COLOR)

        # player_select 按钮
        if controller.battle_session and controller.battle_session.state == "player_select":
            actions = controller.battle_session.get_available_actions()
            button_rects.clear()
            btn_width = 100
            btn_height = 40
            spacing = 10
            total_btns = len(actions)
            total_width = total_btns * (btn_width + spacing) - spacing
            start_x = WIDTH//2 - total_width//2
            y_pos = HEIGHT//2 + 120

            for idx, (action_id, label, color) in enumerate(actions):
                x = start_x + idx * (btn_width + spacing)
                rect = pygame.Rect(x, y_pos, btn_width, btn_height)
                pygame.draw.rect(screen, color, rect, border_radius=8)
                pygame.draw.rect(screen, (60, 60, 60), rect, 2, border_radius=8)
                txt = hint_font.render(label, True, (255, 255, 255))
                screen.blit(txt, (rect.x + (btn_width - txt.get_width()) // 2, rect.y + (btn_height - txt.get_height()) // 2))
                button_rects[action_id] = rect

        # player_skill 按钮
        elif controller.battle_session and controller.battle_session.state == "player_skill":
            button_rects.clear()
            skill = controller.battle_session.player.get("skill")
            if skill and skill.get("timing") == "player_skill":
                skill_name = skill.get("name")
                cost = skill.get("cost", 999)
                uses = controller.battle_session.player.get("skill_uses", 0)
                can_use = (controller.battle_session.player["energy"] >= cost and uses != 0)
                btn_color = (120, 200, 120) if can_use else (180, 180, 180)
                btn_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 120, 120, 40)
                pygame.draw.rect(screen, btn_color, btn_rect, border_radius=8)
                pygame.draw.rect(screen, (80, 80, 80), btn_rect, 2, border_radius=8)
                txt = hint_font.render(skill_name, True, (0,0,0))
                screen.blit(txt, (btn_rect.x + 10, btn_rect.y + 5))
                button_rects[f"skill_{skill_name}"] = btn_rect

            end_rect = pygame.Rect(WIDTH//2 + 40, HEIGHT//2 + 120, 100, 40)
            pygame.draw.rect(screen, (180, 180, 180), end_rect, border_radius=8)
            pygame.draw.rect(screen, (80, 80, 80), end_rect, 2, border_radius=8)
            txt = hint_font.render("结束", True, (0,0,0))
            screen.blit(txt, (end_rect.x + 20, end_rect.y + 5))
            button_rects["end_skill"] = end_rect

        # ---------- 统一弹窗绘制 ----------
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

            elif choice_type == "ocean_reflect":
                damage = controller.battle_session.pending_choice.get('damage', 0)
                prompt = hint_font.render(f"受到 {int(damage)} 点伤害！是否消耗1能量反弹？", True, (255, 255, 200))
                prompt_rect = prompt.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
                screen.blit(prompt, prompt_rect)
                btn_yes = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 20, 80, 40)
                btn_no = pygame.Rect(WIDTH//2 + 20, HEIGHT//2 + 20, 80, 40)
                pygame.draw.rect(screen, (100, 200, 100), btn_yes, border_radius=6)
                pygame.draw.rect(screen, (200, 100, 100), btn_no, border_radius=6)
                txt_yes = hint_font.render("反弹", True, (0,0,0))
                txt_no = hint_font.render("承受", True, (0,0,0))
                screen.blit(txt_yes, (btn_yes.x+15, btn_yes.y+5))
                screen.blit(txt_no, (btn_no.x+15, btn_no.y+5))

            elif choice_type == "passive_gao_da":
                prompt = hint_font.render("受到攻击！是否触发被动“上面有人”，使下次攻击+1？", True, (255, 255, 200))
                prompt_rect = prompt.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
                screen.blit(prompt, prompt_rect)
                btn_yes = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 20, 80, 40)
                btn_no = pygame.Rect(WIDTH//2 + 20, HEIGHT//2 + 20, 80, 40)
                pygame.draw.rect(screen, (100, 200, 100), btn_yes, border_radius=6)
                pygame.draw.rect(screen, (200, 100, 100), btn_no, border_radius=6)
                txt_yes = hint_font.render("触发", True, (0,0,0))
                txt_no = hint_font.render("不触发", True, (0,0,0))
                screen.blit(txt_yes, (btn_yes.x+15, btn_yes.y+5))
                screen.blit(txt_no, (btn_no.x+15, btn_no.y+5))

            elif choice_type == "passive_huangfu_lai":
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

            elif choice_type == "skill_luyin":
                prompt = hint_font.render("敌方即将行动！是否使用“录音”（消耗1能量）变为己方回合？", True, (255, 255, 200))
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

            elif choice_type == "select_ability":
                options = controller.battle_session.pending_ability_options
                if not options:
                    controller.battle_session.resolve_choice(None)
                else:
                    prompt = hint_font.render("选择一个能力替换：", True, (255, 255, 200))
                    prompt_rect = prompt.get_rect(center=(WIDTH//2, HEIGHT//2 - 80))
                    screen.blit(prompt, prompt_rect)
                    for idx, (opt_type, ability) in enumerate(options):
                        btn_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 20 + idx * 50, 300, 40)
                        pygame.draw.rect(screen, (200, 200, 200), btn_rect, border_radius=6)
                        pygame.draw.rect(screen, (80, 80, 80), btn_rect, 2, border_radius=6)
                        type_label = "被动" if opt_type == "passive" else "技能"
                        txt = hint_font.render(f"[{type_label}] {ability['name']}", True, (0,0,0))
                        screen.blit(txt, (btn_rect.x+10, btn_rect.y+5))
                    # 悬停描述
                    mouse_pos = pygame.mouse.get_pos()
                    for idx, (opt_type, ability) in enumerate(options):
                        btn_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 20 + idx * 50, 300, 40)
                        if btn_rect.collidepoint(mouse_pos):
                            tip_font = load_font(18)
                            lines = ["描述：", ability.get("desc", "无")]
                            max_width = max(tip_font.render(line, True, (40,30,20)).get_width() for line in lines)
                            padding = 10
                            box_width = max_width + padding * 2
                            box_height = len(lines) * 26 + padding * 2
                            tip_x = min(mouse_pos[0] + 16, WIDTH - box_width - 16)
                            tip_y = min(mouse_pos[1] + 16, HEIGHT - box_height - 16)
                            s = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
                            s.fill((250, 245, 220, 230))
                            pygame.draw.rect(s, (100, 75, 50, 200), s.get_rect(), 2, border_radius=4)
                            screen.blit(s, (tip_x, tip_y))
                            for i, line in enumerate(lines):
                                surf = tip_font.render(line, True, (40,30,20))
                                screen.blit(surf, (tip_x + padding, tip_y + padding + i * 26))
                            break

        # 游戏结束信息
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