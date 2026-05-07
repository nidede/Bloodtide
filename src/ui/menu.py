"""
菜单界面 - 主菜单、结算界面
"""
import pygame
from core.config import Color, ScreenConfig, get_font
from ui.base import MenuButton


class MenuScreen:
    """主菜单"""

    def __init__(self):
        self.title_font = get_font(72)
        self.font = get_font(28)
        self.small_font = get_font(20)
        
        btn_w, btn_h = 240, 55
        btn_x = (ScreenConfig.WIDTH - btn_w) // 2
        btn_gap = 65
        
        self.start_button = MenuButton(
            btn_x, 340, btn_w, btn_h,
            "开始游戏", Color.DARK_GREEN, Color.GREEN
        )
        self.exit_button = MenuButton(
            btn_x, 340 + btn_gap, btn_w, btn_h,
            "退出游戏", Color.DARK_RED, Color.RED
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.start_button.is_clicked((mx, my), True):
                return "start"
            if self.exit_button.is_clicked((mx, my), True):
                return "exit"
        return None

    def draw(self, surface):
        surface.fill(Color.BG_COLOR)
        
        title = self.title_font.render("打怪升级", True, Color.YELLOW)
        surface.blit(title, ((ScreenConfig.WIDTH - title.get_width()) // 2, 120))
        
        subtitle = self.font.render("Monster Slayer", True, Color.CYAN)
        surface.blit(subtitle, ((ScreenConfig.WIDTH - subtitle.get_width()) // 2, 200))
        
        mouse_pos = pygame.mouse.get_pos()
        self.start_button.draw(surface, mouse_pos)
        self.exit_button.draw(surface, mouse_pos)
        
        controls = [
            "WASD/方向键 - 移动",
            "空格 - 冲刺",
        ]
        for i, line in enumerate(controls):
            text = self.small_font.render(line, True, Color.LIGHT_GRAY)
            surface.blit(text, ((ScreenConfig.WIDTH - text.get_width()) // 2, 560 + i * 30))


class GameOverScreen:
    """结算画面"""

    def __init__(self, player, wave, game_time):
        self.player = player
        self.wave = wave
        self.game_time = game_time
        self.title_font = get_font(64)
        self.font = get_font(32)
        self.small_font = get_font(24)

        # 按钮
        btn_w, btn_h = 200, 55
        btn_x = (ScreenConfig.WIDTH - btn_w) // 2
        self.restart_button = MenuButton(
            btn_x, 440, btn_w, btn_h,
            "重新开始", Color.DARK_GREEN, Color.GREEN
        )
        self.menu_button = MenuButton(
            btn_x, 510, btn_w, btn_h,
            "返回大厅", Color.DARK_BLUE, Color.CYAN
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.restart_button.is_clicked((mx, my), True):
                return "restart"
            if self.menu_button.is_clicked((mx, my), True):
                return "menu"
        return None

    def draw(self, surface):
        surface.fill(Color.BG_COLOR)
        
        title = self.title_font.render("游戏结束", True, Color.RED)
        surface.blit(title, ((ScreenConfig.WIDTH - title.get_width()) // 2, 80))
        
        stats = [
            f"存活时间: {int(self.game_time // 60)}分{int(self.game_time % 60):02d}秒",
            f"到达波次: {self.wave}",
            f"玩家等级: {self.player.level}",
            f"击杀数量: {self.player.kills}",
        ]
        
        for i, line in enumerate(stats):
            text = self.font.render(line, True, Color.WHITE)
            surface.blit(text, ((ScreenConfig.WIDTH - text.get_width()) // 2, 180 + i * 50))
        
        mouse_pos = pygame.mouse.get_pos()
        self.restart_button.draw(surface, mouse_pos)
        self.menu_button.draw(surface, mouse_pos)
        
        tip = self.small_font.render("或按 ENTER 重新开始 / ESC 返回大厅", True, Color.YELLOW)
        surface.blit(tip, ((ScreenConfig.WIDTH - tip.get_width()) // 2, 590))
