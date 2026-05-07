"""
士兵角色 - 默认角色
"""
import math
import pygame
from core.config import Color, ScreenConfig, WORLD_WIDTH, WORLD_HEIGHT, PlayerConfig
from ui.effects import Particle, pygame_draw_circle
from .base import Character


# ========== 角色通用升级 ==========

def _apply_speed(player, weapon):
    player.speed += 10

def _apply_max_hp(player, weapon):
    player.max_hp += 30
    player.hp += 30

def _apply_defense(player, weapon):
    player.defense += 3

def _apply_life_steal(player, weapon):
    player.life_steal += 0.05

def _apply_regen(player, weapon):
    player.regen += 2

def _apply_xp(player, weapon):
    player.xp_multiplier += 0.2

def _apply_thorns(player, weapon):
    player.thorns += 5

def _apply_magnet(player, weapon):
    player.magnet_range += 50

def _apply_dash(player, weapon):
    player.has_dash = True


# ========== 通用升级颜色标准 ==========
# 机动: CYAN | 防御: BLUE | 生存: GREEN | 进攻: RED | 收益: YELLOW | 特殊: PURPLE | 反伤: ORANGE

GENERAL_UPGRADES = [
    ("speed",      "跑快点",     "移动速度 +10",        Color.CYAN,   _apply_speed),
    ("max_hp",     "血量上限",   "最大生命 +30",         Color.BLUE,   _apply_max_hp),
    ("defense",    "护甲",       "防御力 +3",            Color.BLUE,   _apply_defense),
    ("life_steal", "吸血",       "生命偷取 +5%",         Color.GREEN,  _apply_life_steal),
    ("regen",      "生命恢复",   "每秒回复 +2",          Color.GREEN,  _apply_regen),
    ("xp",         "经验加成",   "经验获取 +20%",        Color.YELLOW, _apply_xp),
    ("thorns",     "反伤",       "敌人受伤 +5",          Color.ORANGE, _apply_thorns),
    ("magnet",     "磁铁",       "经验球吸引范围 +50",   Color.CYAN,   _apply_magnet),
    ("dash",       "冲刺",       "解锁空格冲刺",         Color.CYAN,   _apply_dash),
]


class Soldier(Character):
    """士兵角色"""
    speed = 200
    max_hp = 100
    attack = 0
    defense = 0
    crit_chance = 0.05
    crit_damage = 1.5
    life_steal = 0
    thorns = 0
    regen = 0
    xp_multiplier = 1.0
    magnet_range = 80

    def __init__(self):
        self.x = WORLD_WIDTH // 2
        self.y = WORLD_HEIGHT // 2
        self.size = Soldier.size
        self.speed = Soldier.speed
        self.max_hp = Soldier.max_hp
        self.hp = self.max_hp
        self.attack = Soldier.attack
        self.defense = Soldier.defense
        self.level = 1
        self.xp = 0
        self.xp_to_next = 50
        self.xp_multiplier = Soldier.xp_multiplier
        self.crit_chance = Soldier.crit_chance
        self.crit_damage = Soldier.crit_damage
        self.life_steal = Soldier.life_steal
        self.thorns = Soldier.thorns
        self.cooldown_timer = 0
        self.invincible_timer = 0
        self.regen = Soldier.regen
        self.regen_timer = 0
        self.kills = 0
        self.angle = 0.0
        self.magnet_range = Soldier.magnet_range
        self.has_dash = False
        self.dash_cooldown = 0
        self.dash_speed = 0.0
        self.facing_right = True  # 朝向，True=右，False=左

        self.weapon = None

        self.magnet_boost_timer = 0
        self.magnet_boost_range = 0
        self.global_magnet = False

    def handle_input(self, keys):
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        return dx, dy

    def update(self, keys, monsters, particles, dt):
        dx, dy = self.handle_input(keys)
        total_speed = self.speed + self.dash_speed
        self.x += dx * total_speed * dt
        self.y += dy * total_speed * dt
        # 更新朝向
        if dx > 0:
            self.facing_right = True
        elif dx < 0:
            self.facing_right = False
        self.dash_speed *= PlayerConfig.DASH_DURATION_DECAY
        if self.dash_speed < 10:
            self.dash_speed = 0
        self.x = max(self.size, min(WORLD_WIDTH - self.size, self.x))
        self.y = max(self.size, min(WORLD_HEIGHT - self.size, self.y))
        nearest = self._find_nearest(monsters)
        if nearest:
            self.angle = math.atan2(nearest.y - self.y, nearest.x - self.x)
        self.cooldown_timer = max(0, self.cooldown_timer - dt)
        self.invincible_timer = max(0, self.invincible_timer - dt)
        self.dash_cooldown = max(0, self.dash_cooldown - dt)
        if self.regen > 0:
            self.regen_timer += dt
            if self.regen_timer >= 1.0:
                self.regen_timer = 0
                self.hp = min(self.max_hp, self.hp + self.regen)

        self.magnet_boost_timer = max(0, self.magnet_boost_timer - dt)
        if self.magnet_boost_timer <= 0:
            self.global_magnet = False

    def try_dash(self, particles):
        if not self.has_dash:
            return False
        if self.dash_cooldown > 0 or self.dash_speed > 0:
            return False
        self.dash_speed = PlayerConfig.DASH_SPEED_BOOST
        self.dash_cooldown = PlayerConfig.DASH_COOLDOWN_FRAMES / 60
        for _ in range(15):
            particles.append(Particle(self.x, self.y, Color.BLUE, speed=240, lifetime=0.33))
        return True

    def try_shoot(self, monsters, dt):
        if self.cooldown_timer > 0 or not monsters or not self.weapon:
            return []
        nearest = self._find_nearest(monsters)
        if not nearest:
            return []
        projs = self.weapon.fire(self.x, self.y, self.angle, self, monsters, dt)
        if projs:
            self.cooldown_timer = self.weapon.fire_rate / 60
        return projs

    def take_damage(self, damage, particles):
        if self.invincible_timer > 0:
            return 0
        actual = max(1, damage - self.defense)
        self.hp -= actual
        self.invincible_timer = PlayerConfig.INVINCIBLE_FRAMES / 60
        for _ in range(8):
            particles.append(Particle(self.x, self.y, Color.RED, speed=180, lifetime=0.33))
        return actual

    def gain_xp(self, amount):
        self.xp += int(amount * self.xp_multiplier)
        if self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.4)
            return True
        return False

    def draw(self, surface, cam_x=0, cam_y=0):
        if self.invincible_timer > 0 and int(self.invincible_timer * 15) % 2 == 0:
            return
        sx, sy = self.x - cam_x, self.y - cam_y
        pygame_draw_circle(surface, Color.BLUE, sx, sy, self.size)
        pygame_draw_circle(surface, (80, 140, 255), sx, sy, self.size - 4)
        end_x = sx + math.cos(self.angle) * (self.size + 8)
        end_y = sy + math.sin(self.angle) * (self.size + 8)
        pygame.draw.line(surface, Color.YELLOW,
                         (int(sx), int(sy)),
                         (int(end_x), int(end_y)), 3)

    def _find_nearest(self, monsters):
        if not monsters:
            return None
        nearest = None
        min_dist = float('inf')
        for m in monsters:
            dist = math.hypot(m.x - self.x, m.y - self.y)
            if dist < min_dist:
                min_dist = dist
                nearest = m
        return nearest
