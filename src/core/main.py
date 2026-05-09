"""
游戏主循环 - 入口文件
"""
import os
import sys

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
# src 是脚本的父目录
src_dir = os.path.dirname(script_dir)

# 确保 src 目录在 sys.path 中
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import ctypes
import platform
import pygame
import random

from core.config import (ScreenConfig, WORLD_WIDTH, WORLD_HEIGHT, FPS,
                        GAME_TITLE, Color, get_font)
from core.camera import Camera
from entities import Player
from ui.effects import Particle, FloatingText
from systems.upgrade import roll_upgrades
from ui import (HUD, MenuScreen, GameOverScreen, WeaponSelectScreen, UpgradeScreen, PauseScreen)
from entities.weapons import get_random_weapons
from systems.spawner import Spawner
from systems.combat import CombatSystem


def _disable_ime():
    """禁用输入法，避免干扰按键检测 (Windows only)"""
    if platform.system() == "Windows":
        try:
            hwnd = pygame.display.get_wm_info()['window']
            ctypes.windll.imm32.ImmAssociateContextEx(hwnd, None, 0)
        except Exception:
            pass


def _init_screen(fullscreen=None):
    """初始化窗口"""
    if fullscreen is not None:
        ScreenConfig.FULLSCREEN = fullscreen
    if ScreenConfig.FULLSCREEN:
        info = pygame.display.Info()
        w, h = info.current_w, info.current_h
        screen = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
    else:
        w, h = ScreenConfig.WINDOW_WIDTH, ScreenConfig.WINDOW_HEIGHT
        screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
    ScreenConfig.WIDTH, ScreenConfig.HEIGHT = screen.get_size()
    print(f"[SCREEN] 模式={'全屏' if ScreenConfig.FULLSCREEN else '窗口'} {ScreenConfig.WIDTH}x{ScreenConfig.HEIGHT}")
    return screen


def _toggle_fullscreen(screen):
    """切换全屏/窗口模式"""
    return _init_screen(not ScreenConfig.FULLSCREEN)


class Game:
    def __init__(self):
        pygame.display.set_caption(GAME_TITLE)
        self.screen = _init_screen()
        _disable_ime()
        self.clock = pygame.time.Clock()

        self.hud = HUD()
        self.menu_screen = MenuScreen()
        self.gameover_screen = None
        self.weapon_select_screen = None
        self.pause_screen = None

        self.state = "menu"
        self.paused = False
        self.keys_down = set()
        self.pressed = pygame.key.get_pressed()
        self.camera = None
        self._reset()

    def _is_visible(self, x, y, margin=100):
        """视锥裁剪"""
        return (self.camera and
                self.camera.offset_x - margin <= x <= self.camera.offset_x + ScreenConfig.WIDTH + margin and
                self.camera.offset_y - margin <= y <= self.camera.offset_y + ScreenConfig.HEIGHT + margin)

    def _reset(self):
        self.player = Player()
        self.camera = Camera(self.player)
        self.monsters = []
        self.projectiles = []
        self.particles = []
        self.floating_texts = []
        self.upgrade_screen = None
        self.spawner = Spawner()
        self.frame = 0
        self.dt = 0
        self.screen_shake = 0  # 震屏剩余时间（秒）
        self.screen_shake_intensity = 0  # 震屏强度（像素）
        self.game_time = 0
        self.combat = CombatSystem(Particle, FloatingText)
        self.pending_level_ups = 0  # 待选升级次数

    def _start_game(self):
        self._reset()
        weapon_classes = get_random_weapons()
        self.weapon_select_screen = WeaponSelectScreen(weapon_classes)
        self.state = "weapon_select"

    def update(self, dt):
        self.dt = dt
        self.frame += 1
        self.pressed = pygame.key.get_pressed()

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.dead]
        for ft in self.floating_texts:
            ft.update(dt)
        self.floating_texts = [ft for ft in self.floating_texts if not ft.dead]

        if self.state != "playing" or self.paused:
            return

        self.game_time += dt
        if self.screen_shake > 0:
            self.screen_shake = max(0, self.screen_shake - dt)

        self.player.update(self.pressed, self.monsters, dt)

        if self.pressed[pygame.K_SPACE]:
            if self.player.try_dash():
                for _ in range(15):
                    self.particles.append(Particle(self.player.x, self.player.y, Color.BLUE, speed=240, lifetime=0.33))

        new_proj = self.player.try_shoot(self.monsters, dt)
        self.projectiles.extend(new_proj)

        spawned, wave_complete, wave_changed = self.spawner.update(
            dt, self.monsters, self.camera.offset_x, self.camera.offset_y)

        self.monsters.extend(spawned)

        if self.spawner.wave % 5 == 0 and self.spawner.monsters_spawned == 1 and spawned:
            boss = self.spawner.spawn_boss(self.spawner.wave, self.camera.offset_x, self.camera.offset_y)
            self.monsters.append(boss)

        if wave_changed:
            self.floating_texts.append(FloatingText(
                ScreenConfig.WIDTH // 2, ScreenConfig.HEIGHT // 2,
                f"第 {self.spawner.wave} 波!", Color.GOLD, 36, 1.5))

        damage_taken, total_levels = self.combat.update(
            self.monsters, self.player, self.projectiles,
            self.particles, self.floating_texts, dt, self._is_visible)

        if damage_taken > 0:
            self.screen_shake = 0.15
            self.screen_shake_intensity = 5
            for _ in range(8):
                self.particles.append(Particle(self.player.x, self.player.y, Color.RED, speed=180, lifetime=0.33))

        if total_levels > 0:
            self.pending_level_ups += total_levels

        if self.pending_level_ups > 0 and self.state == "playing":
            self.pending_level_ups -= 1
            self.state = "upgrade"
            upgrades = roll_upgrades(self.player, self.player.weapon, 3)
            self.upgrade_screen = UpgradeScreen(upgrades)
            self.screen_shake = 0.2
            self.screen_shake_intensity = 8
            self.floating_texts.append(FloatingText(
                self.player.x, self.player.y - 40,
                "LEVEL UP!", Color.GOLD, 32, 1.0))

        if self.player.hp <= 0 and self.state == "playing":
            self.state = "gameover"
            self.gameover_screen = GameOverScreen(self.player, self.spawner.wave, self.game_time)
            self.combat.spawn_death_particles(self.player, self.particles)

    def draw(self):
        cx, cy = self.camera.offset_x, self.camera.offset_y
        si = self.screen_shake_intensity
        sx = random.randint(-si, si) if self.screen_shake > 0 else 0
        sy = random.randint(-si, si) if self.screen_shake > 0 else 0

        self._draw_world(cx + sx, cy + sy)

        if self.state == "menu":
            self._draw_particles_and_texts(cx, cy)
            self.menu_screen.draw(self.screen)
            return

        for m in self.monsters:
            m.draw(self.screen, cx, cy)
        for p in self.projectiles:
            p.draw(self.screen, cx, cy)
        self._draw_particles_and_texts(cx, cy)
        if self.state != "gameover":
            self.player.draw(self.screen, cx, cy)
            if self.player.weapon:
                self.player.weapon.draw(self.screen, cx, cy, self.player.x, self.player.y)

        if self.state == "weapon_select" and self.weapon_select_screen:
            self.weapon_select_screen.draw(self.screen)
            return

        self.hud.draw(self.screen, self.player, self.spawner.wave, self.game_time)

        if self.paused:
            if not self.pause_screen:
                self.pause_screen = PauseScreen()
            self.pause_screen.draw(self.screen)

        self._draw_minimap()

        if self.state == "upgrade" and self.upgrade_screen:
            self.upgrade_screen.draw(self.screen)

        if self.state == "gameover" and self.gameover_screen:
            self.gameover_screen.draw(self.screen)

    def _draw_world(self, cx, cy):
        screen_w, screen_h = ScreenConfig.WIDTH, ScreenConfig.HEIGHT
        self.screen.fill((0, 0, 0))

        world_left = max(0, cx)
        world_top = max(0, cy)
        world_right = min(WORLD_WIDTH, cx + screen_w)
        world_bottom = min(WORLD_HEIGHT, cy + screen_h)
        w_w = world_right - world_left
        w_h = world_bottom - world_top

        if w_w <= 0 or w_h <= 0:
            return

        world_screen_x = world_left - cx
        world_screen_y = world_top - cy
        self.screen.fill(Color.BG_COLOR, (world_screen_x, world_screen_y, w_w, w_h))

        grid_size = 80
        min_wx = int(world_left // grid_size) * grid_size
        max_wx = int(world_right // grid_size + 1) * grid_size
        for wx in range(min_wx, max_wx + grid_size, grid_size):
            if wx < 0 or wx > WORLD_WIDTH:
                continue
            sx = wx - cx
            pygame.draw.line(self.screen, Color.GRID_COLOR,
                            (sx, world_screen_y), (sx, world_screen_y + w_h))

        min_wy = int(world_top // grid_size) * grid_size
        max_wy = int(world_bottom // grid_size + 1) * grid_size
        for wy in range(min_wy, max_wy + grid_size, grid_size):
            if wy < 0 or wy > WORLD_HEIGHT:
                continue
            sy = wy - cy
            pygame.draw.line(self.screen, Color.GRID_COLOR,
                            (world_screen_x, sy), (world_screen_x + w_w, sy))

        border = (180, 40, 40)
        if cx < 0:
            sx = -cx
            pygame.draw.line(self.screen, border, (sx, world_screen_y), (sx, world_screen_y + w_h), 3)
        if cx + screen_w > WORLD_WIDTH:
            sx = WORLD_WIDTH - cx
            pygame.draw.line(self.screen, border, (sx, world_screen_y), (sx, world_screen_y + w_h), 3)
        if cy < 0:
            sy = -cy
            pygame.draw.line(self.screen, border, (world_screen_x, sy), (world_screen_x + w_w, sy), 3)
        if cy + screen_h > WORLD_HEIGHT:
            sy = WORLD_HEIGHT - cy
            pygame.draw.line(self.screen, border, (world_screen_x, sy), (world_screen_x + w_w, sy), 3)

    def _draw_minimap(self):
        mm_w, mm_h = 150, 150
        mm_x = 10
        mm_y = ScreenConfig.HEIGHT - mm_h - 10
        scale_x = mm_w / WORLD_WIDTH
        scale_y = mm_h / WORLD_HEIGHT

        pygame.draw.rect(self.screen, (10, 10, 20), (mm_x, mm_y, mm_w, mm_h))
        pygame.draw.rect(self.screen, (50, 50, 70), (mm_x, mm_y, mm_w, mm_h), 1)

        for m in self.monsters:
            dx = int(m.x * scale_x)
            dy = int(m.y * scale_y)
            color = (200, 50, 50) if m.monster_type == "boss" else (150, 100, 100)
            self.screen.set_at((mm_x + dx, mm_y + dy), color)

        px = int(self.player.x * scale_x)
        py = int(self.player.y * scale_y)
        if 0 <= px < mm_w and 0 <= py < mm_h:
            pygame.draw.circle(self.screen, Color.CYAN, (mm_x + px, mm_y + py), 3)
            pygame.draw.circle(self.screen, Color.WHITE, (mm_x + px, mm_y + py), 2)

        vx = int(self.camera.offset_x * scale_x)
        vy = int(self.camera.offset_y * scale_y)
        vw = int(ScreenConfig.WIDTH * scale_x)
        vh = int(ScreenConfig.HEIGHT * scale_y)
        pygame.draw.rect(self.screen, (100, 100, 150), (mm_x + vx, mm_y + vy, vw, vh), 1)

    def _draw_particles_and_texts(self, cx, cy):
        for p in self.particles:
            p.draw(self.screen, cx, cy)
        for ft in self.floating_texts:
            ft.draw(self.screen, cx, cy)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in self.keys_down:
                return
            self.keys_down.add(event.key)

            if event.key == pygame.K_F11:
                self.screen = _toggle_fullscreen(self.screen)
            elif event.key == pygame.K_ESCAPE:
                if self.state == "upgrade":
                    self.pending_level_ups = 0
                    self.upgrade_screen = None
                    self.state = "playing"
                elif self.state == "playing":
                    self.paused = not self.paused
                    if not self.paused:
                        self.pause_screen = None
                elif self.state == "gameover":
                    self.state = "menu"
            elif event.key == pygame.K_RETURN:
                if self.state == "menu" or self.state == "gameover":
                    self._start_game()

        elif event.type == pygame.KEYUP:
            self.keys_down.discard(event.key)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "menu":
                result = self.menu_screen.handle_event(event)
                if result == "start":
                    self._start_game()
                elif result == "exit":
                    pygame.quit()
                    sys.exit()
            elif self.state == "weapon_select" and self.weapon_select_screen:
                if self.weapon_select_screen.handle_event(event):
                    chosen_cls = self.weapon_select_screen.selected
                    if chosen_cls:
                        self.player.weapon = chosen_cls()
                        self.weapon_select_screen = None
                        self.state = "playing"
            elif self.state == "upgrade" and self.upgrade_screen:
                if self.upgrade_screen.handle_event(event):
                    selected = self.upgrade_screen.selected
                    if selected:
                        selected.apply(self.player, self.player.weapon)
                    if self.pending_level_ups > 0:
                        self.pending_level_ups -= 1
                        upgrades = roll_upgrades(self.player, self.player.weapon, 3)
                        self.upgrade_screen = UpgradeScreen(upgrades)
                    else:
                        self.state = "playing"
                        self.upgrade_screen = None
            elif self.state in ("playing",) and self.paused:
                if self.pause_screen:
                    result = self.pause_screen.handle_event(event)
                    if result == "resume":
                        self.paused = False
                        self.pause_screen = None
                        return
                    elif result == "menu":
                        self.paused = False
                        self.pause_screen = None
                        self.state = "menu"
                        return
            elif self.state == "playing" and not self.paused:
                if self.hud.get_pause_button_rect().collidepoint(event.pos):
                    self.paused = True
                    return
            elif self.state == "gameover" and self.gameover_screen:
                result = self.gameover_screen.handle_event(event)
                if result == "restart":
                    self._start_game()
                elif result == "menu":
                    self.state = "menu"
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.state == "weapon_select" and self.weapon_select_screen:
                if self.weapon_select_screen.handle_event(event):
                    chosen_cls = self.weapon_select_screen.selected
                    if chosen_cls:
                        self.player.weapon = chosen_cls()
                        self.weapon_select_screen = None
                        self.state = "playing"
        elif event.type == pygame.MOUSEMOTION:
            if self.state == "weapon_select" and self.weapon_select_screen:
                self.weapon_select_screen.handle_event(event)
        elif event.type == pygame.MOUSEWHEEL:
            if self.state == "weapon_select" and self.weapon_select_screen:
                self.weapon_select_screen.handle_event(event)

    def run(self):
        pygame.key.set_repeat(200, 50)
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)
                    if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                            and self.state == "menu"):
                        running = False

            dt = self.clock.tick(FPS) / 1000.0
            self.update(dt)
            self.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


def main():
    pygame.init()
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
