"""Boss怪物 - 每5波出现"""
import math
import pygame
from core.config import Color
from .base import BaseMonster, MonsterRegistry
from entities.weapons.enemy.homing import BossHomingRifle


@MonsterRegistry.register
class BossMonster(BaseMonster):
    """Boss怪物 - 超高属性，发射追踪弹"""

    TYPE = "boss"
    HP_BASE = 500
    HP_PER_LVL = 100
    SPEED_BASE = 48
    SPEED_PER_LVL = 1
    DAMAGE_BASE = 25
    DAMAGE_PER_LVL = 8
    SIZE = 45
    COLOR = Color.DARK_RED
    XP_BASE = 300
    XP_PER_LVL = 50
    MIN_WAVE = 5
    SPAWN_WEIGHT = 0.08
    ATTACK_COOLDOWN = 1.5  # 追踪弹攻击间隔（秒）
    weapon_class = BossHomingRifle

    def attack(self, targets, dt):
        """发射追踪弹"""
        if self.is_attack_blocked():
            return [], []

        if not self.can_attack() or not targets:
            return [], []

        target = min(targets, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))
        self.angle = math.atan2(target.y - self.y, target.x - self.x)
        self.attack_cooldown = self.ATTACK_COOLDOWN

        projs = self.weapon.attack(self, targets, dt)
        return projs, []
    
    def _draw_shape(self, surface, color, sx, sy):
        """大菱形 + 外发光 + 皇冠装饰"""
        s = self.size

        # 外发光效果（多层轮廓）
        for i in range(3, 0, -1):
            glow_size = s + i * 4
            glow_points = [
                (sx, sy - glow_size), (sx + glow_size, sy),
                (sx, sy + glow_size), (sx - glow_size, sy)
            ]
            glow_color = (color[0] // 3, color[1] // 3, color[2] // 3)
            pygame.draw.polygon(surface, glow_color, glow_points)

        # 主菱形
        points = [(sx, sy - s), (sx + s, sy), (sx, sy + s), (sx - s, sy)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, Color.YELLOW, points, 3)

        # 内菱形
        inner_s = s * 0.6
        inner_points = [
            (sx, sy - inner_s), (sx + inner_s, sy),
            (sx, sy + inner_s), (sx - inner_s, sy)
        ]
        pygame.draw.polygon(surface, (color[0] // 2, color[1] // 2, color[2] // 2), inner_points)
        pygame.draw.polygon(surface, Color.YELLOW, inner_points, 1)

        # 皇冠装饰（顶部三个小三角）
        crown_y = sy - s - 8
        for offset in [-12, 0, 12]:
            cx = sx + offset
            crown_size = 6
            crown = [(cx, crown_y - crown_size), (cx - crown_size // 2, crown_y), (cx + crown_size // 2, crown_y)]
            pygame.draw.polygon(surface, Color.YELLOW, crown)
