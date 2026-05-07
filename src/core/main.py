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
                        GAME_TITLE, Color, OrbConfig, get_font)
from core.camera import Camera
from entities import Player
from ui.effects import Particle, FloatingText, XPOrb
from systems.upgrade import roll_upgrades, GENERAL_UPGRADES
from ui import (HUD, MenuScreen, NameInputScreen, GameOverScreen, WeaponSelectScreen, UpgradeScreen,
                MultiplayerMenuScreen, RoomListScreen, WaitingRoomScreen, PauseScreen)
from entities.weapons import get_random_weapons
from systems.spawner import Spawner
from systems.combat import CombatSystem

# 多人游戏相关
try:
    from network import DiscoveryService, RoomManager, GameSync, SyncMessageHandler
    NETWORK_AVAILABLE = True
except ImportError:
    NETWORK_AVAILABLE = False


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

        # 多人游戏界面
        self.multiplayer_screen = None
        self.room_list_screen = None
        self.waiting_room_screen = None

        # 多人游戏状态
        self.discovery_service = None
        self.room_manager = None
        self.is_multiplayer_host = False
        
        # 游戏同步系统
        self.game_sync = None
        self.sync_handler = None
        self.remote_players = {}  # 远程玩家字典

        self.state = "menu"
        self.paused = False
        self.player_name = ""  # 玩家名字
        self.name_input_screen = None  # 名字输入界面
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
        self.xp_orbs = []
        self.upgrade_screen = None
        self.spawner = Spawner()
        self.frame = 0
        self.dt = 0
        self.screen_shake = 0
        self.game_time = 0
        self.combat = CombatSystem()

    def _start_game(self):
        self._reset()
        weapon_classes = get_random_weapons(3)
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

        if self.state == "waiting_room" and not self.paused:
            # 在等待室也要处理同步消息，让成员能看到房主的位置
            self._update_sync()
            return
        
        if self.state != "playing" or self.paused:
            return
        
        # 更新网络同步
        self._update_sync()

        self.game_time += dt
        if self.screen_shake > 0:
            self.screen_shake -= 1

        self.player.update(self.pressed, self.monsters, self.particles, dt)

        if self.player.weapon:
            self.player.weapon.update(self.player, self.monsters, self.particles, self.floating_texts, dt)
        if self.pressed[pygame.K_SPACE]:
            self.player.try_dash(self.particles)

        new_proj = self.player.try_shoot(self.monsters, dt)
        self.projectiles.extend(new_proj)

        spawned, wave_complete, wave_changed = self.spawner.update(
            dt, self.monsters, self.camera.offset_x, self.camera.offset_y)
        
        # 广播新生成的怪物（仅房主）
        if self.is_multiplayer_host and spawned:
            for m in spawned:
                self.game_sync.broadcast_monster_spawn(
                    id(m), m.monster_type, m.x, m.y, m.hp
                )
        
        self.monsters.extend(spawned)

        if self.spawner.wave % 5 == 0 and self.spawner.monsters_spawned == 1 and spawned:
            boss = self.spawner.spawn_boss(self.spawner.wave, self.camera.offset_x, self.camera.offset_y)
            self.monsters.append(boss)

        if wave_changed:
            self.floating_texts.append(FloatingText(
                ScreenConfig.WIDTH // 2, ScreenConfig.HEIGHT // 2,
                f"第 {self.spawner.wave} 波!", Color.GOLD, 36, 1.5))
            # 广播波次变化
            if self.is_multiplayer_host:
                self.game_sync.broadcast_wave_change(self.spawner.wave)

        self.combat.update_projectiles(
            self.projectiles, self.monsters, self.player, self.particles, self.floating_texts, dt)

        damage_taken = self.combat.update_monsters(
            self.monsters, self.player, self.projectiles,
            self.particles, self.floating_texts, dt, self._is_visible)
        if damage_taken > 0:
            self.screen_shake = 5

        self.combat.process_dead_monsters(
            self.monsters, self.player, self.xp_orbs, self.particles, self.floating_texts)

        for orb in self.xp_orbs:
            collected, is_magnet = orb.update(self.player, dt)
            if collected:
                if is_magnet:
                    self.player.magnet_boost_timer = OrbConfig.MAGNET_BOOST_DURATION
                    self.player.magnet_boost_range = OrbConfig.MAGNET_BOOST_RANGE
                    self.player.global_magnet = True
                    self.floating_texts.append(FloatingText(
                        self.player.x, self.player.y - 30,
                        "磁力爆发!", Color.GOLD, 28, 1.0))
                    for _ in range(20):
                        self.particles.append(Particle(self.player.x, self.player.y, Color.GOLD, speed=300, lifetime=0.42))
                leveled = self.player.gain_xp(orb.value)
                self.particles.append(Particle(self.player.x, self.player.y, Color.GREEN, speed=120, lifetime=0.25))
                if leveled:
                    self.state = "upgrade"
                    upgrades = roll_upgrades(self.player, self.player.weapon, 3)
                    self.upgrade_screen = UpgradeScreen(upgrades)
                    self.screen_shake = 8
                    self.floating_texts.append(FloatingText(
                        self.player.x, self.player.y - 40,
                        "LEVEL UP!", Color.GOLD, 32, 1.0))
                self.combat.mark_orb_dead(id(orb))
            elif not orb.alive:
                self.combat.mark_orb_dead(id(orb))

        self.combat.cleanup(self.monsters, self.xp_orbs)
        self.combat.handle_explosions(self.projectiles, self.monsters, self.particles, self.floating_texts)
        self.projectiles = [p for p in self.projectiles if p.alive]

        if self.player.hp <= 0 and self.state == "playing":
            self.state = "gameover"
            self.gameover_screen = GameOverScreen(self.player, self.spawner.wave, self.game_time)
            self.combat.spawn_death_particles(self.player, self.particles)

    def draw(self):
        cx, cy = self.camera.offset_x, self.camera.offset_y
        sx = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        sy = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0

        self._draw_world(cx + sx, cy + sy)

        if self.state == "menu":
            self._draw_particles_and_texts(cx, cy)
            self.menu_screen.draw(self.screen)
            return

        # 名字输入界面
        if self.state == "name_input" and self.name_input_screen:
            self.name_input_screen.draw(self.screen)
            return

        # 多人游戏界面
        if self.state == "multiplayer" and self.multiplayer_screen:
            self.multiplayer_screen.draw(self.screen)
            return
        if self.state == "room_list" and self.room_list_screen:
            self.room_list_screen.draw(self.screen)
            return
        if self.state == "waiting_room" and self.waiting_room_screen:
            self.waiting_room_screen.draw(self.screen)
            return

        for orb in self.xp_orbs:
            orb.draw(self.screen, self.frame, cx, cy)
        for m in self.monsters:
            m.draw(self.screen, cx, cy)
        for p in self.projectiles:
            p.draw(self.screen, cx, cy)
        self._draw_particles_and_texts(cx, cy)
        if self.state != "gameover":
            self.player.draw(self.screen, cx, cy)
            if self.player.weapon:
                self.player.weapon.draw(self.screen, cx, cy, self.player.x, self.player.y)
            # 绘制远程玩家
            self._draw_remote_players(cx, cy)

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

        for orb in self.xp_orbs:
            dx = int(orb.x * scale_x)
            dy = int(orb.y * scale_y)
            if 0 <= dx < mm_w and 0 <= dy < mm_h:
                self.screen.set_at((mm_x + dx, mm_y + dy), Color.GREEN)

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
    
    def _draw_remote_players(self, cx, cy):
        """绘制远程玩家"""
        if not self.remote_players:
            return
        
        for player_id, remote in self.remote_players.items():
            if not remote.alive:
                continue
            
            # 计算屏幕坐标
            sx = remote.x - cx
            sy = remote.y - cy
            
            # 绘制远程玩家（用矩形表示）
            size = 40
            rect = pygame.Rect(sx - size//2, sy - size//2, size, size)
            
            # 根据血量设置颜色
            hp_ratio = remote.hp / 100.0
            color = (
                int(255 * (1 - hp_ratio) + 100 * hp_ratio),  # R
                int(100 * hp_ratio + 100 * (1 - hp_ratio)),  # G
                int(255 * (1 - hp_ratio))  # B
            )
            
            pygame.draw.rect(self.screen, color, rect, 3)
            
            # 绘制玩家名字
            font = get_font(16)
            name_text = font.render(remote.name, True, Color.CYAN)
            self.screen.blit(name_text, (sx - name_text.get_width()//2, sy - size//2 - 20))
            
            # 绘制血条
            bar_width = 50
            bar_height = 6
            bar_x = sx - bar_width//2
            bar_y = sy + size//2 + 5
            
            pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(self.screen, Color.GREEN if hp_ratio > 0.3 else Color.RED,
                          (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in self.keys_down:
                return
            self.keys_down.add(event.key)
            
            # 名字输入界面处理键盘事件
            if self.state == "name_input" and self.name_input_screen:
                result = self.name_input_screen.handle_event(event)
                if result == "confirm":
                    self.player_name = self.name_input_screen.player_name
                    self._enter_multiplayer_menu()
                    self.state = "multiplayer"
                elif result == "back":
                    self.name_input_screen = None
                    self.state = "menu"
                return
            
            if event.key == pygame.K_F11:
                self.screen = _toggle_fullscreen(self.screen)
            elif event.key == pygame.K_ESCAPE:
                if self.state == "upgrade":
                    self.state = "playing"
                    self.upgrade_screen = None
                elif self.state == "playing":
                    self.paused = not self.paused
                    if not self.paused:
                        self.pause_screen = None
                elif self.state == "gameover":
                    self.state = "menu"
                elif self.state == "name_input":
                    self.name_input_screen = None
                    self.state = "menu"
                elif self.state in ("multiplayer", "room_list", "waiting_room"):
                    self._exit_multiplayer()
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
                elif result == "multiplayer":
                    self.name_input_screen = NameInputScreen()
                    self.state = "name_input"
                elif result == "exit":
                    pygame.quit()
                    sys.exit()
            elif self.state == "name_input" and self.name_input_screen:
                result = self.name_input_screen.handle_event(event)
                if result == "confirm":
                    self.player_name = self.name_input_screen.player_name
                    self._enter_multiplayer_menu()
                    self.state = "multiplayer"
                elif result == "back":
                    self.name_input_screen = None
                    self.state = "menu"
            elif self.state == "multiplayer" and self.multiplayer_screen:
                result = self.multiplayer_screen.handle_event(event)
                if result == "create":
                    self._create_room()
                elif result == "join":
                    self._enter_room_list()
                elif result == "back":
                    self.state = "menu"
            elif self.state == "room_list" and self.room_list_screen:
                result = self.room_list_screen.handle_event(event)
                if result == "back":
                    self.state = "multiplayer"
                elif result == "refresh":
                    self._refresh_room_list()
                elif isinstance(result, tuple) and result[0] == "join":
                    self._join_room(result[1])
            elif self.state == "waiting_room" and self.waiting_room_screen:
                result = self.waiting_room_screen.handle_event(event)
                if result == "start" and self.is_multiplayer_host:
                    self._start_multiplayer_game()
                elif result == "leave":
                    self._exit_multiplayer()
                    self.state = "multiplayer"
            elif self.state == "weapon_select" and self.weapon_select_screen:
                if self.weapon_select_screen.handle_event(event):
                    chosen_cls = self.weapon_select_screen.selected
                    if chosen_cls:
                        self.player.weapon = chosen_cls()
                        self.weapon_select_screen = None
                        # 多人游戏时，房主选完武器后通知所有成员开始
                        if self.is_multiplayer_host and self.room_manager:
                            self.room_manager.broadcast_game_start()
                        self.state = "playing"
            elif self.state == "upgrade" and self.upgrade_screen:
                if self.upgrade_screen.handle_event(event):
                    selected = self.upgrade_screen.selected
                    if selected:
                        selected.apply(self.player, self.player.weapon)
                    self.state = "playing"
                    self.upgrade_screen = None
            elif self.state in ("playing",) and self.paused:
                # 暂停状态下点击继续按钮
                if self.pause_screen and self.pause_screen.handle_event(event):
                    self.paused = False
                    self.pause_screen = None
                    return
            elif self.state == "playing" and not self.paused:
                # 检查暂停按钮点击
                if self.hud.get_pause_button_rect().collidepoint(event.pos):
                    self.paused = True
                    return
            elif self.state == "gameover" and self.gameover_screen:
                result = self.gameover_screen.handle_event(event)
                if result == "restart":
                    self._start_game()
                elif result == "menu":
                    self.state = "menu"

        elif event.type == pygame.QUIT:
            pass

    # ============ 多人游戏相关方法 ============

    def _enter_multiplayer_menu(self):
        """进入多人游戏菜单"""
        if not NETWORK_AVAILABLE:
            print("[网络] 网络模块不可用")
            return
        self.multiplayer_screen = MultiplayerMenuScreen(self.player_name)
        self.state = "multiplayer"

    def _create_room(self):
        """创建房间"""
        if not NETWORK_AVAILABLE:
            return
        self.room_manager = RoomManager(is_host=True)
        self.room_manager.start_as_host(host_port=8888)

        player_name = self.player_name or "房主"
        self.discovery_service = DiscoveryService(player_name=player_name)
        self.discovery_service.start_broadcast(
            room_id=self.room_manager.room_id,
            player_count=self.room_manager.player_count,
            max_players=self.room_manager.max_players
        )

        self.waiting_room_screen = WaitingRoomScreen(
            room_id=self.room_manager.room_id,
            is_host=True,
            player_name=player_name
        )
        self.is_multiplayer_host = True
        self.state = "waiting_room"
        
        # 初始化游戏同步系统
        self._init_game_sync()

        # 设置玩家回调
        self.room_manager.on_player_joined = self._on_player_joined
        self.room_manager.on_player_left = self._on_player_left

    def _enter_room_list(self):
        """进入房间列表"""
        if not NETWORK_AVAILABLE:
            return
        self.room_list_screen = RoomListScreen()
        player_name = self.player_name or "玩家"
        self.discovery_service = DiscoveryService(player_name=player_name)
        self.discovery_service.on_rooms_updated = self._on_rooms_updated
        self.discovery_service.start_listening()
        self.discovery_service.request_room_list()
        self.state = "room_list"

    def _refresh_room_list(self):
        """刷新房间列表"""
        if self.discovery_service:
            self.discovery_service.request_room_list()

    def _join_room(self, room_info):
        """加入房间"""
        if not NETWORK_AVAILABLE:
            return
        self.room_manager = RoomManager(is_host=False)
        player_name = self.player_name or "玩家"
        
        # 设置玩家列表回调
        self.room_manager.on_players_list = self._on_players_list_received
        # 设置游戏开始回调
        self.room_manager.on_game_start = self._on_game_start_received
        
        # 初始化游戏同步系统
        self._init_game_sync()
        
        if self.room_manager.connect_to_host(room_info.host_ip, player_name=player_name):
            # 初始化等待室玩家列表（包含自己和已在线的玩家）
            initial_players = [player_name]
            if hasattr(self, '_pending_players_list') and self._pending_players_list:
                initial_players = self._pending_players_list
                self._pending_players_list = []
            
            self.waiting_room_screen = WaitingRoomScreen(
                room_id=room_info.room_id,
                is_host=False,
                player_name=player_name,
                players=initial_players
            )
            print(f"[房间] 创建等待室，玩家列表: {initial_players}")
            self.is_multiplayer_host = False
            self.state = "waiting_room"
        else:
            print("[网络] 加入房间失败")

    def _exit_multiplayer(self, keep_network=False):
        """
        退出多人游戏
        keep_network=True: 只清理UI，保持网络连接（用于开始游戏）
        keep_network=False: 完全退出多人游戏
        """
        # 停止发现服务（不再需要）
        if self.discovery_service:
            self.discovery_service.stop_broadcast()
            self.discovery_service.stop_listening()
            self.discovery_service = None
        
        if not keep_network:
            # 完全退出，关闭网络
            if self.room_manager:
                self.room_manager.close()
                self.room_manager = None
            self.game_sync = None
            self.sync_handler = None
            self.remote_players = {}
            self.is_multiplayer_host = False
        
        self.multiplayer_screen = None
        self.room_list_screen = None
        self.waiting_room_screen = None
    
    def _init_game_sync(self):
        """初始化游戏同步系统"""
        self.game_sync = GameSync(is_host=self.is_multiplayer_host)
        # 生成唯一的 player_id
        import uuid
        player_id = str(uuid.uuid4())[:8]
        self.game_sync.set_player_info(
            player_id,
            self.player_name or "Player"
        )
        self.game_sync.on_remote_player_update = self._on_remote_player_update
        self.game_sync.on_player_join = self._on_remote_player_join
        self.game_sync.on_player_leave = self._on_remote_player_leave
        
        # 怪物同步回调
        self.game_sync.on_monster_spawn = self._on_sync_monster_spawn
        self.game_sync.on_wave_change = self._on_sync_wave_change
        
        # 创建消息处理器
        def send_sync_msg(msg):
            if self.room_manager and self.is_multiplayer_host:
                self.room_manager.broadcast_to_all(msg)
            elif self.room_manager:
                self.room_manager.send_to_host(msg)
        
        self.sync_handler = SyncMessageHandler(self.game_sync, send_sync_msg)
        self.remote_players = {}
        
        # 设置房间消息回调以接收同步消息
        if self.room_manager:
            def sync_callback(msg):
                self.sync_handler.handle_raw_message(msg)
            self.room_manager.set_sync_callback(sync_callback)
    
    def _on_remote_player_update(self, player_id, state):
        """远程玩家状态更新"""
        pass  # 后续在update中处理绘制
    
    def _on_remote_player_join(self, player_id, name):
        """远程玩家加入"""
        print(f"[Sync] 玩家 {name} 加入了游戏")
    
    def _on_remote_player_leave(self, player_id):
        """远程玩家离开"""
        print(f"[Sync] 玩家离开了游戏")
    
    def _on_sync_monster_spawn(self, monster_id, monster_type, x, y, hp):
        """同步怪物生成（客户端接收）"""
        if self.is_multiplayer_host:
            return  # 房主不需要处理
        # 从 spawner 获取怪物模板
        from entities.monsters import Slime, Orc, Boss
        monster_map = {
            'slime': Slime,
            'orc': Orc,
            'boss': Boss,
        }
        monster_cls = monster_map.get(monster_type, Slime)
        m = monster_cls(x, y)
        m.hp = hp
        self.monsters.append(m)
    
    def _on_sync_wave_change(self, wave):
        """同步波次变化（客户端接收）"""
        if self.is_multiplayer_host:
            return  # 房主不需要处理
        self.spawner.wave = wave
    
    def _update_sync(self):
        """更新网络同步"""
        if not self.sync_handler or not self.game_sync:
            return
        
        # 处理同步消息
        self.sync_handler.update()
        
        # 发送本地玩家状态
        if self.player:
            self.game_sync.queue_player_state(
                self.player.x,
                self.player.y,
                self.player.hp,
                self.player.facing_right
            )
        
        # 更新远程玩家数据
        self.remote_players = self.game_sync.get_remote_players()

    def _on_rooms_updated(self, rooms):
        """房间列表更新回调"""
        if self.room_list_screen:
            self.room_list_screen.set_rooms(rooms)

    def _on_player_joined(self, player):
        """玩家加入回调"""
        print(f"[房间] {player.name} 加入了游戏")
        if self.waiting_room_screen:
            self.waiting_room_screen.add_player(player.name)

    def _on_player_left(self, player_id):
        """玩家离开回调"""
        print(f"[房间] 玩家 {player_id} 离开了游戏")
        if self.waiting_room_screen:
            self.waiting_room_screen.remove_player(player_id)

    def _on_players_list_received(self, players):
        """收到玩家列表回调"""
        # 保存玩家列表（供后续使用）
        self._pending_players_list = [p['name'] for p in players]
        # 如果等待室已创建，立即更新
        if self.waiting_room_screen:
            self.waiting_room_screen.players = list(self._pending_players_list)

    def _on_game_start_received(self):
        """收到游戏开始回调 - 成员端收到房主的开始指令"""
        self._exit_multiplayer(keep_network=True)  # 保持网络连接
        # 成员直接进入游戏状态，不等待武器选择
        self._reset()
        self.state = "playing"
        # 成员获得默认武器
        from entities.weapons import Missile
        self.player.weapon = Missile()

    def _start_multiplayer_game(self):
        """开始多人游戏"""
        # 注意：不在这里广播 game_start，等房主选完武器后再广播
        self._exit_multiplayer(keep_network=True)  # 保持网络连接
        self._start_game()

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
