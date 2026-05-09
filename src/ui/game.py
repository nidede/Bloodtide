"""
游戏内 UI - HUD、武器选择、升级选择
"""
import pygame
from core.config import Color, ScreenConfig, get_font, PlayerConfig
from entities.weapons.base import UPGRADE_UNLIMITED


class HUD:
    """游戏内 HUD"""

    def __init__(self):
        self.font_sm = get_font(18)
        self.pause_btn_rect = None  # 暂停按钮区域

    def get_pause_button_rect(self):
        """返回暂停按钮的矩形区域（供点击检测用）"""
        if self.pause_btn_rect:
            return self.pause_btn_rect
        # 暂停按钮默认位置：波次右边
        btn_w, btn_h = 32, 32
        btn_x = ScreenConfig.WIDTH - 230
        btn_y = 4
        return pygame.Rect(btn_x, btn_y, btn_w, btn_h)

    def draw(self, surface, player, wave, game_time):
        pygame.draw.rect(surface, Color.HUD_BG, (0, 0, ScreenConfig.WIDTH, 40))
        pygame.draw.line(surface, (50, 50, 70), (0, 40), (ScreenConfig.WIDTH, 40), 2)

        hp_w, hp_h = 200, 18
        hp_x, hp_y = 10, 10
        pygame.draw.rect(surface, Color.DARK_GRAY, (hp_x, hp_y, hp_w, hp_h))
        hp_ratio = max(0, player.hp / player.max_hp)
        pygame.draw.rect(surface, Color.RED, (hp_x, hp_y, int(hp_w * hp_ratio), hp_h))
        
        hp_text = self.font_sm.render(f"{player.hp}/{player.max_hp}", True, Color.WHITE)
        surface.blit(hp_text, (hp_x + 5, hp_y + 2))

        xp_w, xp_h = 150, 8
        xp_x, xp_y = hp_x + hp_w + 20, hp_y + 5
        pygame.draw.rect(surface, Color.DARK_GRAY, (xp_x, xp_y, xp_w, xp_h))
        xp_ratio = player.xp / player.xp_to_next if player.xp_to_next > 0 else 0
        pygame.draw.rect(surface, Color.GREEN, (xp_x, xp_y, int(xp_w * xp_ratio), xp_h))

        level_text = self.font_sm.render(f"Lv.{player.level}", True, Color.YELLOW)
        surface.blit(level_text, (xp_x + xp_w + 15, xp_y - 2))

        # 角色属性（移动速度）- 生命条下方
        speed_text = self.font_sm.render(f"移速: {player.speed:.0f}", True, Color.LIGHT_GRAY)
        surface.blit(speed_text, (hp_x, hp_y + hp_h + 8))

        wave_text = self.font_sm.render(f"波次 {wave}", True, Color.CYAN)
        surface.blit(wave_text, (ScreenConfig.WIDTH // 2 - wave_text.get_width() // 2, 12))

        time_text = self.font_sm.render(f"{int(game_time // 60)}:{int(game_time % 60):02d}", True, Color.WHITE)
        surface.blit(time_text, (ScreenConfig.WIDTH - 80, 12))

        # 暂停按钮
        self._draw_pause_button(surface)

        kill_text = self.font_sm.render(f"击杀 {player.kills}", True, Color.WHITE)
        surface.blit(kill_text, (ScreenConfig.WIDTH - 180, 12))

        if player.has_dash:
            dash_ratio = 1 - player.dash_cooldown / (PlayerConfig.DASH_COOLDOWN_FRAMES / 60)
            dash_ratio = max(0, min(1, dash_ratio))
            pygame.draw.rect(surface, Color.DARK_GRAY, (10, ScreenConfig.HEIGHT - 20, 100, 10))
            pygame.draw.rect(surface, Color.BLUE, (10, ScreenConfig.HEIGHT - 20, int(100 * dash_ratio), 10))

        if player.weapon:
            self._draw_weapon(surface, player)
            self._draw_weapon_stats(surface, player)

    def _draw_pause_button(self, surface):
        """绘制暂停按钮"""
        btn_w, btn_h = 32, 32
        btn_x = ScreenConfig.WIDTH - 230  # 放在击杀左边，波次右边
        btn_y = 4

        mx, my = pygame.mouse.get_pos()
        is_hover = btn_x <= mx <= btn_x + btn_w and btn_y <= my <= btn_y + btn_h

        # 按钮背景
        bg_color = Color.CARD_BG_HOVER if is_hover else Color.DARK_GRAY
        pygame.draw.rect(surface, bg_color, (btn_x, btn_y, btn_w, btn_h), border_radius=6)

        # 暂停图标：两个竖条
        bar_w, bar_h = 3, 12
        gap = 5
        bar_y = btn_y + (btn_h - bar_h) // 2
        left_x = btn_x + (btn_w - gap - bar_w * 2) // 2
        right_x = left_x + bar_w + gap

        icon_color = Color.WHITE if is_hover else Color.LIGHT_GRAY
        pygame.draw.rect(surface, icon_color, (left_x, bar_y, bar_w, bar_h), border_radius=2)
        pygame.draw.rect(surface, icon_color, (right_x, bar_y, bar_w, bar_h), border_radius=2)

        self.pause_btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

    def _draw_weapon(self, surface, player):
        """绘制武器信息"""
        weapon = player.weapon
        if not hasattr(weapon, 'name'):
            return
        
        weapon_name = weapon.name
        text = self.font_sm.render(weapon_name, True, Color.WHITE)
        
        x = 10
        y = ScreenConfig.HEIGHT - 40
        pygame.draw.rect(surface, Color.DARK_GRAY, (x, y, 120, 25), border_radius=5)
        surface.blit(text, (x + 10, y + 4))
    
    def _draw_weapon_stats(self, surface, player):
        """绘制右下角武器属性"""
        weapon = player.weapon
        if not weapon:
            return
        
        # 调用武器的 get_display_stats 获取要显示的属性
        stats = weapon.get_display_stats()
        
        # 绘制背景
        bg_width = 100
        bg_height = len(stats) * 22 + 10
        bg_x = ScreenConfig.WIDTH - bg_width - 10
        bg_y = ScreenConfig.HEIGHT - bg_height - 10
        
        pygame.draw.rect(surface, (0, 0, 0, 128), (bg_x, bg_y, bg_width, bg_height), border_radius=8)
        pygame.draw.rect(surface, Color.DARK_GRAY, (bg_x, bg_y, bg_width, bg_height), 1, border_radius=8)
        
        # 绘制每个属性
        for i, stat in enumerate(stats):
            text = self.font_sm.render(stat, True, Color.WHITE)
            surface.blit(text, (bg_x + 8, bg_y + 5 + i * 22))


class WeaponSelectScreen:
    """武器选择界面 - 自适应网格布局，支持滚动"""

    def __init__(self, weapons):
        self.weapons = weapons
        self.selected = None
        self.font_title = get_font(36)
        self.font_name = get_font(28)
        self.font_desc = get_font(16)
        self.card_w = 200
        self.card_h = 240
        self.padding_x = 30
        self.padding_y = 30
        # 计算每行最多放几个卡片
        max_usable_w = ScreenConfig.WIDTH - 80  # 左右各留40边距
        self.cols = max(1, (max_usable_w + self.padding_x) // (self.card_w + self.padding_x))
        # 网格总尺寸
        self.rows = (len(weapons) + self.cols - 1) // self.cols
        grid_w = self.cols * self.card_w + (self.cols - 1) * self.padding_x
        self.grid_w = grid_w
        self.grid_start_x = (ScreenConfig.WIDTH - grid_w) // 2
        self.grid_start_y_base = 200  # 标题下方的起始 y
        # 可视区域
        self.view_top = 0
        self.view_h = ScreenConfig.HEIGHT - self.grid_start_y_base - 40  # 底部留40
        # 内容总高度
        self.content_h = self.rows * self.card_h + (self.rows - 1) * self.padding_y
        # 滚动条
        self.scrollbar_w = 8
        # 拖拽滑动状态
        self._dragging = False
        self._drag_start_y = 0
        self._drag_scroll_start = 0

    def _max_scroll(self):
        return max(0, self.content_h - self.view_h)

    def _card_pos(self, i):
        """计算第i个卡片的 (x, y)"""
        col = i % self.cols
        row = i // self.cols
        cx = self.grid_start_x + col * (self.card_w + self.padding_x)
        cy = self.grid_start_y_base + row * (self.card_h + self.padding_y) - self.view_top
        return cx, cy

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # 记录拖拽起点
            if self.grid_start_y_base <= my <= self.grid_start_y_base + self.view_h:
                self._dragging = True
                self._drag_start_y = my
                self._drag_scroll_start = self.view_top
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                # 拖拽距离很小视为点击
                mx, my = event.pos
                drag_dist = abs(my - self._drag_start_y)
                self._dragging = False
                if drag_dist < 10:
                    # 当作点击选择卡片
                    for i, weapon_cls in enumerate(self.weapons):
                        cx, cy = self._card_pos(i)
                        if (cx <= mx <= cx + self.card_w and
                            self.grid_start_y_base <= my <= self.grid_start_y_base + self.view_h and
                            cy <= my <= cy + self.card_h):
                            self.selected = weapon_cls
                            return True
        elif event.type == pygame.MOUSEMOTION:
            if self._dragging:
                _, my = event.pos
                delta = self._drag_start_y - my
                self.view_top = max(0, min(self._max_scroll(), self._drag_scroll_start + delta))
        elif event.type == pygame.MOUSEWHEEL:
            self.view_top -= event.y * 40
            self.view_top = max(0, min(self._max_scroll(), self.view_top))
        return False

    def draw(self, surface):
        surface.fill(Color.BG_COLOR)

        title = self.font_title.render("选择武器", True, Color.WHITE)
        surface.blit(title, ((ScreenConfig.WIDTH - title.get_width()) // 2, 120))

        subtitle = self.font_desc.render("选择一件武器开始游戏（拖拽或滚轮滑动）", True, Color.LIGHT_GRAY)
        surface.blit(subtitle, ((ScreenConfig.WIDTH - subtitle.get_width()) // 2, 170))

        # 裁剪可视区域
        clip_rect = pygame.Rect(0, self.grid_start_y_base,
                                ScreenConfig.WIDTH, self.view_h)
        surface.set_clip(clip_rect)

        mx, my = pygame.mouse.get_pos()
        for i, weapon_cls in enumerate(self.weapons):
            cx, cy = self._card_pos(i)
            # 跳过不在可视区域的卡片
            if cy + self.card_h < self.grid_start_y_base or cy > self.grid_start_y_base + self.view_h:
                continue
            is_hover = (cx <= mx <= cx + self.card_w and
                       self.grid_start_y_base <= my <= self.grid_start_y_base + self.view_h and
                       cy <= my <= cy + self.card_h)

            # 卡片背景
            card_rect = pygame.Rect(cx, cy, self.card_w, self.card_h)
            if is_hover:
                pygame.draw.rect(surface, Color.CARD_BG_HOVER, card_rect, border_radius=15)
                pygame.draw.rect(surface, weapon_cls.color, card_rect, 3, border_radius=15)
            else:
                pygame.draw.rect(surface, Color.CARD_BG, card_rect, border_radius=15)
                pygame.draw.rect(surface, weapon_cls.color, card_rect, 2, border_radius=15)

            # 顶部装饰条
            pygame.draw.rect(surface, weapon_cls.color, (cx + 20, cy + 20, self.card_w - 40, 6), border_radius=3)

            # 武器图标
            icon_x = cx + self.card_w // 2
            icon_y = cy + 80
            pygame.draw.circle(surface, weapon_cls.color, (icon_x, icon_y), 40)
            pygame.draw.circle(surface, Color.BG_COLOR, (icon_x, icon_y), 32)
            pygame.draw.circle(surface, weapon_cls.color, (icon_x, icon_y), 28)

            # 武器名称
            name = self.font_name.render(weapon_cls.name, True, Color.WHITE)
            surface.blit(name, (cx + (self.card_w - name.get_width()) // 2, icon_y + 55))

            # 武器描述
            desc_lines = weapon_cls.desc.split('|')
            for j, line in enumerate(desc_lines):
                desc = self.font_desc.render(line.strip(), True, Color.LIGHT_GRAY)
                surface.blit(desc, (cx + (self.card_w - desc.get_width()) // 2, icon_y + 90 + j * 20))

            # 点击提示
            hint = self.font_desc.render("点击选择", True, Color.LIGHT_GRAY if is_hover else (100, 100, 120))
            surface.blit(hint, (cx + (self.card_w - hint.get_width()) // 2, cy + self.card_h - 30))

        # 取消裁剪
        surface.set_clip(None)

        # 滚动条
        if self.content_h > self.view_h:
            sb_x = self.grid_start_x + self.grid_w + 15
            sb_track_h = self.view_h
            # 滚动条轨道
            pygame.draw.rect(surface, (60, 60, 70),
                           (sb_x, self.grid_start_y_base, self.scrollbar_w, sb_track_h),
                           border_radius=4)
            # 滚动条滑块
            ratio = self.view_h / self.content_h
            thumb_h = max(30, int(sb_track_h * ratio))
            thumb_y = self.grid_start_y_base + int((self.view_top / self._max_scroll()) * (sb_track_h - thumb_h))
            pygame.draw.rect(surface, (150, 150, 170),
                           (sb_x, thumb_y, self.scrollbar_w, thumb_h),
                           border_radius=4)


class UpgradeScreen:
    """升级选择界面"""

    def __init__(self, upgrades):
        self.upgrades = upgrades
        self.selected = None
        self.card_width = 220
        self.card_height = 280
        self.card_padding = 30
        self.font_title = get_font(32)
        self.font_name = get_font(24)
        self.font_desc = get_font(16)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            total_width = self.card_width * len(self.upgrades) + self.card_padding * (len(self.upgrades) - 1)
            start_x = (ScreenConfig.WIDTH - total_width) // 2
            y = (ScreenConfig.HEIGHT - self.card_height) // 2

            for i, upg in enumerate(self.upgrades):
                cx = start_x + i * (self.card_width + self.card_padding)
                if cx <= mx <= cx + self.card_width and y <= my <= y + self.card_height:
                    self.selected = upg
                    return True
        return False

    def draw(self, surface):
        surface.fill(Color.BG_COLOR)

        total_width = self.card_width * len(self.upgrades) + self.card_padding * (len(self.upgrades) - 1)
        start_x = (ScreenConfig.WIDTH - total_width) // 2
        y = (ScreenConfig.HEIGHT - self.card_height) // 2

        title = self.font_title.render("选择升级", True, Color.WHITE)
        surface.blit(title, ((ScreenConfig.WIDTH - title.get_width()) // 2, y - 60))

        mx, my = pygame.mouse.get_pos()
        for i, upg in enumerate(self.upgrades):
            cx = start_x + i * (self.card_width + self.card_padding)

            is_hover = cx <= mx <= cx + self.card_width and y <= my <= y + self.card_height

            # 卡片背景
            card_rect = pygame.Rect(cx, y, self.card_width, self.card_height)
            if is_hover:
                pygame.draw.rect(surface, Color.CARD_BG_HOVER, card_rect, border_radius=15)
                pygame.draw.rect(surface, upg.icon_color, card_rect, 3, border_radius=15)
            else:
                pygame.draw.rect(surface, Color.CARD_BG, card_rect, border_radius=15)
                pygame.draw.rect(surface, upg.icon_color, card_rect, 2, border_radius=15)

            # 顶部装饰条
            pygame.draw.rect(surface, upg.icon_color, (cx + 20, y + 20, self.card_width - 40, 6), border_radius=3)

            # 图标圆圈
            icon_x = cx + self.card_width // 2
            icon_y = y + 80
            pygame.draw.circle(surface, upg.icon_color, (icon_x, icon_y), 35)
            pygame.draw.circle(surface, Color.BG_COLOR, (icon_x, icon_y), 28)
            pygame.draw.circle(surface, upg.icon_color, (icon_x, icon_y), 25)

            # 升级名称
            name_surf = self.font_name.render(upg.name, True, Color.WHITE)
            surface.blit(name_surf, (cx + (self.card_width - name_surf.get_width()) // 2, icon_y + 50))

            # 描述文字
            desc_lines = upg.desc.split('\n')
            for j, line in enumerate(desc_lines):
                desc_surf = self.font_desc.render(line, True, Color.LIGHT_GRAY)
                surface.blit(desc_surf, (cx + (self.card_width - desc_surf.get_width()) // 2, icon_y + 90 + j * 22))

            # 选择计数（仅有限次数时显示，如 0/1）
            if upg.max_count < UPGRADE_UNLIMITED:
                count_text = f"{upg.current_count}/{upg.max_count}"
                count_surf = self.font_desc.render(count_text, True, Color.LIGHT_GRAY)
                surface.blit(count_surf, (cx + (self.card_width - count_surf.get_width()) // 2, y + self.card_height - 50))

            # 点击提示
            hint = self.font_desc.render("点击选择", True, Color.LIGHT_GRAY if is_hover else (100, 100, 120))
            surface.blit(hint, (cx + (self.card_width - hint.get_width()) // 2, y + self.card_height - 30))


class PauseScreen:
    """暂停界面"""

    def __init__(self):
        self.font_title = get_font(56)
        self.font_btn = get_font(28)
        self.btn_width = 200
        self.btn_height = 60
        self.btn_gap = 20
        # 继续按钮
        self.resume_y = ScreenConfig.HEIGHT // 2 + 20
        self.resume_x = ScreenConfig.WIDTH // 2 - self.btn_width // 2
        # 返回大厅按钮
        self.menu_y = self.resume_y + self.btn_height + self.btn_gap
        self.menu_x = ScreenConfig.WIDTH // 2 - self.btn_width // 2

    def get_resume_button_rect(self):
        """返回继续按钮区域"""
        return pygame.Rect(self.resume_x, self.resume_y, self.btn_width, self.btn_height)

    def get_menu_button_rect(self):
        """返回大厅按钮区域"""
        return pygame.Rect(self.menu_x, self.menu_y, self.btn_width, self.btn_height)

    def handle_event(self, event):
        """处理点击事件，返回 'resume' / 'menu' / None"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.get_resume_button_rect().collidepoint(event.pos):
                return "resume"
            if self.get_menu_button_rect().collidepoint(event.pos):
                return "menu"
        return None

    def draw(self, surface):
        """绘制暂停界面"""
        # 半透明遮罩
        overlay = pygame.Surface((ScreenConfig.WIDTH, ScreenConfig.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        # 暂停文字
        title = self.font_title.render("暂停", True, Color.WHITE)
        surface.blit(title, title.get_rect(center=(ScreenConfig.WIDTH // 2, ScreenConfig.HEIGHT // 2 - 60)))

        mx, my = pygame.mouse.get_pos()

        # 继续按钮
        resume_rect = self.get_resume_button_rect()
        is_hover_resume = resume_rect.collidepoint(mx, my)
        btn_bg = Color.CARD_BG_HOVER if is_hover_resume else Color.DARK_GRAY
        pygame.draw.rect(surface, btn_bg, resume_rect, border_radius=10)
        pygame.draw.rect(surface, Color.GREEN, resume_rect, 2, border_radius=10)
        btn_text = self.font_btn.render("继续游戏", True, Color.WHITE if is_hover_resume else Color.LIGHT_GRAY)
        surface.blit(btn_text, btn_text.get_rect(center=resume_rect.center))

        # 返回大厅按钮
        menu_rect = self.get_menu_button_rect()
        is_hover_menu = menu_rect.collidepoint(mx, my)
        btn_bg = Color.CARD_BG_HOVER if is_hover_menu else Color.DARK_GRAY
        pygame.draw.rect(surface, btn_bg, menu_rect, border_radius=10)
        pygame.draw.rect(surface, Color.RED, menu_rect, 2, border_radius=10)
        btn_text = self.font_btn.render("返回大厅", True, Color.WHITE if is_hover_menu else Color.LIGHT_GRAY)
        surface.blit(btn_text, btn_text.get_rect(center=menu_rect.center))
