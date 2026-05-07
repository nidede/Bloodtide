"""
菜单界面 - 主菜单、多人游戏、房间相关界面
"""
import pygame
import socket
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
        self.multiplayer_button = MenuButton(
            btn_x, 340 + btn_gap, btn_w, btn_h,
            "多人游戏", Color.DARK_BLUE, Color.CYAN
        )
        self.exit_button = MenuButton(
            btn_x, 340 + btn_gap * 2, btn_w, btn_h,
            "退出游戏", Color.DARK_RED, Color.RED
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.start_button.is_clicked((mx, my), True):
                return "start"
            if self.multiplayer_button.is_clicked((mx, my), True):
                return "multiplayer"
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
        self.multiplayer_button.draw(surface, mouse_pos)
        self.exit_button.draw(surface, mouse_pos)
        
        controls = [
            "WASD/方向键 - 移动",
            "空格 - 冲刺",
        ]
        for i, line in enumerate(controls):
            text = self.small_font.render(line, True, Color.LIGHT_GRAY)
            surface.blit(text, ((ScreenConfig.WIDTH - text.get_width()) // 2, 560 + i * 30))


class NameInputScreen:
    """名字输入界面"""

    def __init__(self):
        self.title_font = get_font(48)
        self.font = get_font(28)
        self.small_font = get_font(20)

        # 默认名字
        try:
            default_name = socket.gethostname()
        except:
            default_name = "玩家"
        self.player_name = default_name[:12]  # 限制长度
        self.input_active = True

        # 输入框
        self.input_width = 300
        self.input_height = 50
        self.input_x = (ScreenConfig.WIDTH - self.input_width) // 2
        self.input_y = 280

        # 确认按钮
        btn_w, btn_h = 200, 55
        self.confirm_button = MenuButton(
            (ScreenConfig.WIDTH - btn_w) // 2, 380, btn_w, btn_h,
            "确认", Color.DARK_GREEN, Color.GREEN
        )
        self.back_button = MenuButton(
            (ScreenConfig.WIDTH - btn_w) // 2, 450, btn_w, btn_h,
            "返回", Color.DARK_GRAY, Color.LIGHT_GRAY
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # 检查输入框点击
            if (self.input_x <= mx <= self.input_x + self.input_width and
                self.input_y <= my <= self.input_y + self.input_height):
                self.input_active = True
                return None
            # 检查按钮点击
            if self.confirm_button.is_clicked((mx, my), True):
                return "confirm"
            if self.back_button.is_clicked((mx, my), True):
                return "back"
            self.input_active = False
            return None

        if event.type == pygame.KEYDOWN:
            if self.input_active:
                if event.key == pygame.K_BACKSPACE:
                    self.player_name = self.player_name[:-1]
                elif event.key == pygame.K_RETURN:
                    return "confirm"
                elif event.key == pygame.K_ESCAPE:
                    return "back"
                else:
                    # 添加字符
                    char = event.unicode
                    if char and len(self.player_name) < 12:
                        # 只允许字母、数字、中文
                        if char.isalnum() or '\u4e00' <= char <= '\u9fff':
                            self.player_name += char
        return None

    def draw(self, surface):
        surface.fill(Color.BG_COLOR)

        title = self.title_font.render("输入名字", True, Color.CYAN)
        surface.blit(title, ((ScreenConfig.WIDTH - title.get_width()) // 2, 100))

        hint = self.small_font.render("给角色取个名字，方便联机时识别", True, Color.LIGHT_GRAY)
        surface.blit(hint, ((ScreenConfig.WIDTH - hint.get_width()) // 2, 180))

        # 绘制输入框
        input_rect = pygame.Rect(self.input_x, self.input_y, self.input_width, self.input_height)
        bg_color = Color.CARD_BG_HOVER if self.input_active else Color.DARK_GRAY
        pygame.draw.rect(surface, bg_color, input_rect, border_radius=8)
        pygame.draw.rect(surface, Color.CYAN if self.input_active else Color.LIGHT_GRAY,
                         input_rect, 2, border_radius=8)

        # 绘制输入文字
        text_surface = self.font.render(self.player_name, True, Color.WHITE)
        text_x = self.input_x + 15
        text_y = self.input_y + (self.input_height - text_surface.get_height()) // 2
        surface.blit(text_surface, (text_x, text_y))

        # 绘制光标
        if self.input_active:
            cursor_x = text_x + text_surface.get_width() + 5
            if cursor_x < self.input_x + self.input_width - 15:
                pygame.draw.line(surface, Color.WHITE,
                               (cursor_x, self.input_y + 10),
                               (cursor_x, self.input_y + self.input_height - 10), 2)

        # 提示文字
        tip = self.small_font.render("← → 或点击输入，最多12个字符", True, Color.LIGHT_GRAY)
        surface.blit(tip, ((ScreenConfig.WIDTH - tip.get_width()) // 2, self.input_y + self.input_height + 10))

        mouse_pos = pygame.mouse.get_pos()
        self.confirm_button.draw(surface, mouse_pos)
        self.back_button.draw(surface, mouse_pos)


class MultiplayerMenuScreen:
    """多人游戏菜单"""

    def __init__(self, player_name=""):
        self.title_font = get_font(48)
        self.font = get_font(28)
        self.small_font = get_font(20)

        btn_w, btn_h = 220, 55
        btn_x = (ScreenConfig.WIDTH - btn_w) // 2
        btn_gap = 70

        self.create_button = MenuButton(
            btn_x, 280, btn_w, btn_h,
            "创建房间", Color.DARK_GREEN, Color.GREEN
        )
        self.join_button = MenuButton(
            btn_x, 280 + btn_gap, btn_w, btn_h,
            "加入房间", Color.DARK_BLUE, Color.CYAN
        )
        self.back_button = MenuButton(
            btn_x, 280 + btn_gap * 2, btn_w, btn_h,
            "返回", Color.DARK_GRAY, Color.LIGHT_GRAY
        )

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.create_button.is_clicked((mx, my), True):
                return "create"
            if self.join_button.is_clicked((mx, my), True):
                return "join"
            if self.back_button.is_clicked((mx, my), True):
                return "back"
        return None

    def draw(self, surface):
        surface.fill(Color.BG_COLOR)

        title = self.title_font.render("多人游戏", True, Color.CYAN)
        surface.blit(title, ((ScreenConfig.WIDTH - title.get_width()) // 2, 100))

        subtitle = self.small_font.render("与朋友一起游玩", True, Color.LIGHT_GRAY)
        surface.blit(subtitle, ((ScreenConfig.WIDTH - subtitle.get_width()) // 2, 160))

        mouse_pos = pygame.mouse.get_pos()
        self.create_button.draw(surface, mouse_pos)
        self.join_button.draw(surface, mouse_pos)
        self.back_button.draw(surface, mouse_pos)


class RoomListScreen:
    """房间列表界面"""

    def __init__(self, rooms=None):
        self.rooms = rooms or []
        self.title_font = get_font(40)
        self.font = get_font(24)
        self.small_font = get_font(18)

        btn_w, btn_h = 180, 45
        btn_x = (ScreenConfig.WIDTH - btn_w) // 2

        self.back_button = MenuButton(
            btn_x, ScreenConfig.HEIGHT - 100, btn_w, btn_h,
            "返回", Color.DARK_GRAY, Color.LIGHT_GRAY
        )
        self.refresh_button = MenuButton(
            btn_x - 200, ScreenConfig.HEIGHT - 100, btn_w, btn_h,
            "刷新", Color.DARK_BLUE, Color.CYAN
        )

        self.room_buttons = []
        self._update_room_buttons()

    def _update_room_buttons(self):
        """更新房间按钮"""
        self.room_buttons = []
        card_h = 60
        card_gap = 10
        start_y = 180

        for i, room in enumerate(self.rooms):
            btn = MenuButton(
                100, start_y + i * (card_h + card_gap),
                ScreenConfig.WIDTH - 200, card_h,
                f"{room.host_name} - {room.player_count}/{room.max_players}人",
                Color.CARD_BG, Color.CARD_BG_HOVER
            )
            self.room_buttons.append((btn, room))

    def set_rooms(self, rooms):
        """设置房间列表"""
        self.rooms = rooms
        self._update_room_buttons()

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            if self.back_button.is_clicked((mx, my), True):
                return "back"
            if self.refresh_button.is_clicked((mx, my), True):
                return "refresh"

            for btn, room in self.room_buttons:
                if btn.is_clicked((mx, my), True):
                    return ("join", room)

        return None

    def draw(self, surface):
        surface.fill(Color.BG_COLOR)

        title = self.title_font.render("房间列表", True, Color.CYAN)
        surface.blit(title, ((ScreenConfig.WIDTH - title.get_width()) // 2, 80))

        mouse_pos = pygame.mouse.get_pos()

        if not self.rooms:
            no_room = self.font.render("暂未发现房间，请点击刷新", True, Color.LIGHT_GRAY)
            surface.blit(no_room, ((ScreenConfig.WIDTH - no_room.get_width()) // 2, 200))
        else:
            for btn, room in self.room_buttons:
                btn.draw(surface, mouse_pos)

                # 绘制 IP 信息
                ip_text = self.small_font.render(f"IP: {room.host_ip}", True, Color.LIGHT_GRAY)
                surface.blit(ip_text, (ScreenConfig.WIDTH - 280, btn.rect.y + 15))

        self.refresh_button.draw(surface, mouse_pos)
        self.back_button.draw(surface, mouse_pos)


class WaitingRoomScreen:
    """等待房间界面"""

    def __init__(self, room_id, is_host=False, player_name="Host", players=None):
        self.room_id = room_id
        self.is_host = is_host
        self.player_name = player_name
        if players is not None:
            self.players = list(players)
        else:
            self.players = [player_name] if is_host else []
        self.title_font = get_font(40)
        self.font = get_font(28)
        self.small_font = get_font(20)

        btn_w, btn_h = 200, 55
        btn_x = (ScreenConfig.WIDTH - btn_w) // 2

        self.start_button = MenuButton(
            btn_x, ScreenConfig.HEIGHT - 160, btn_w, btn_h,
            "开始游戏", Color.DARK_GREEN, Color.GREEN
        )
        self.leave_button = MenuButton(
            btn_x, ScreenConfig.HEIGHT - 90, btn_w, btn_h,
            "离开房间", Color.DARK_RED, Color.RED
        )

    def add_player(self, name):
        """添加玩家"""
        if name not in self.players:
            self.players.append(name)

    def remove_player(self, name):
        """移除玩家"""
        if name in self.players:
            self.players.remove(name)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self.start_button.is_clicked((mx, my), True) and self.is_host:
                return "start"
            if self.leave_button.is_clicked((mx, my), True):
                return "leave"
        return None

    def draw(self, surface):
        surface.fill(Color.BG_COLOR)

        # 标题
        title = self.title_font.render("等待房间", True, Color.CYAN)
        surface.blit(title, ((ScreenConfig.WIDTH - title.get_width()) // 2, 60))

        # 房间ID
        room_text = self.font.render(f"房间号: {self.room_id}", True, Color.YELLOW)
        surface.blit(room_text, ((ScreenConfig.WIDTH - room_text.get_width()) // 2, 120))

        # 玩家列表
        list_title = self.font.render("玩家列表:", True, Color.WHITE)
        surface.blit(list_title, ((ScreenConfig.WIDTH - 200) // 2, 180))

        for i, name in enumerate(self.players):
            is_host_label = " (房主)" if i == 0 else ""
            player_text = self.font.render(f"• {name}{is_host_label}", True, Color.GREEN)
            surface.blit(player_text, ((ScreenConfig.WIDTH - 200) // 2, 220 + i * 40))

        # 提示信息
        if self.is_host:
            hint = self.small_font.render("等待玩家加入...", True, Color.LIGHT_GRAY)
        else:
            hint = self.small_font.render("等待房主开始游戏...", True, Color.LIGHT_GRAY)
        surface.blit(hint, ((ScreenConfig.WIDTH - hint.get_width()) // 2, 380))

        mouse_pos = pygame.mouse.get_pos()
        if self.is_host:
            self.start_button.draw(surface, mouse_pos)
        self.leave_button.draw(surface, mouse_pos)


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
