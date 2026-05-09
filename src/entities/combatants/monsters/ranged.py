"""远程怪物 - 保持距离射击"""
import math
import pygame
from core.config import Color, CombatConfig
from .base import BaseMonster, MonsterRegistry
from entities.weapons.enemy.rifle import EnemyRifle


@MonsterRegistry.register
class RangedMonster(BaseMonster):
    """远程怪物 - 保持距离攻击"""

    TYPE = "ranged"
    HP_BASE = 15
    HP_PER_LVL = 8
    SPEED_BASE = 60
    SPEED_PER_LVL = 2
    DAMAGE_BASE = 8
    DAMAGE_PER_LVL = 2
    SIZE = 18
    COLOR = Color.PINK
    XP_BASE = 15
    XP_PER_LVL = 4
    MIN_WAVE = 2
    SPAWN_WEIGHT = 0.15
    ATTACK_COOLDOWN = 1.0  # 远程攻击间隔（秒）
    weapon_class = EnemyRifle

    # AI 距离参数
    MELEE_RANGE = 250  # 太近，撤退
    OPTIMAL_RANGE = 400  # 最佳射击距离

    def __init__(self, level, x, y):
        super().__init__(level, x, y)

    def update(self, player, dt):
        """远程怪物 AI - 保持最佳射击距离"""
        self.update_status(dt)

        if self.is_movement_blocked():
            self.flash_timer = max(0, self.flash_timer - dt)
            return

        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)

        if dist > 0:
            nx, ny = dx / dist, dy / dist
            if dist < self.MELEE_RANGE:
                # 太近了，撤退
                self.x -= nx * self.speed * CombatConfig.RETREAT_SPEED_RATIO * dt
                self.y -= ny * self.speed * CombatConfig.RETREAT_SPEED_RATIO * dt
            elif dist < self.OPTIMAL_RANGE:
            # 最佳范围内，缓慢靠近
                speed = self.speed * self.get_speed_multiplier()
                self.x += nx * speed * 0.3 * dt
                self.y += ny * speed * 0.3 * dt
            else:
                # 太远了，正常靠近
                speed = self.speed * self.get_speed_multiplier()
                self.x += nx * speed * dt
                self.y += ny * speed * dt

        self.attack_cooldown = max(0, self.attack_cooldown - dt * self.get_attack_speed_multiplier())
        self.flash_timer = max(0, self.flash_timer - dt)

    def attack(self, targets, dt):
        """通过武器发射子弹，返回 Projectile 列表"""
        if self.is_attack_blocked():
            return [], []

        if not self.can_attack() or not targets:
            return [], []

        # 瞄准最近的目标
        target = min(targets, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))
        self.angle = math.atan2(target.y - self.y, target.x - self.x)
        self.attack_cooldown = self.ATTACK_COOLDOWN

        projs = self.weapon.attack(self, targets, dt)
        return projs, []
    
    def _draw_shape(self, surface, color, sx, sy):
        """菱形 + 眼睛表示远程"""
        points = [(sx, sy - self.size), (sx + self.size, sy),
                  (sx, sy + self.size), (sx - self.size, sy)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, Color.WHITE, points, 1)

        eye_offset = self.size // 3
        pygame.draw.circle(surface, Color.WHITE, (sx - eye_offset, sy - 2), 3)
        pygame.draw.circle(surface, Color.WHITE, (sx + eye_offset, sy - 2), 3)
