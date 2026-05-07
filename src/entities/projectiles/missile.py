"""
导弹投射物 - 追踪飞行，爆炸伤害由 Missile 武器处理
"""
import math
import pygame
from core.config import Color, ProjectileConfig, MissileConfig
from .base import Projectile


class MissileProjectile(Projectile):
    """导弹 - 追踪飞行，命中后标记死亡，爆炸由武器处理"""

    def __init__(self, x, y, angle, speed, weapon=None, owner=None,
                 homing=False, targets=None):
        super().__init__(x, y, angle, speed, weapon=weapon, owner=owner)
        self.homing = homing
        self.targets_ref = targets or []
        self.size = MissileConfig.SIZE
        self.max_lifetime = MissileConfig.MAX_LIFETIME
        self.lifetime = 0

    def update(self, dt):
        self.lifetime += dt
        self.trail.append((self.x, self.y))
        if len(self.trail) > ProjectileConfig.TRAIL_LENGTH:
            self.trail.pop(0)

        if self.homing:
            nearest = None
            min_dist = float('inf')
            for m in self.targets_ref:
                if not m.dead:
                    d = math.hypot(m.x - self.x, m.y - self.y)
                    if d < min_dist:
                        min_dist = d
                        nearest = m
            if nearest:
                self.angle = math.atan2(nearest.y - self.y, nearest.x - self.x)

        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt

        if self.lifetime > self.max_lifetime:
            self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        sx, sy = self.x - cam_x, self.y - cam_y

        # 尾焰 - 沿轨迹渐隐
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / max(1, len(self.trail)) * 0.6
            r = max(1, int(3 * alpha))
            color = (int(255 * alpha), int(120 * alpha), 0)
            pygame.draw.circle(surface, color, (int(tx - cam_x), int(ty - cam_y)), r)

        # 弹身线段
        tail_x = sx - math.cos(self.angle) * 12
        tail_y = sy - math.sin(self.angle) * 12
        pygame.draw.line(surface, Color.ORANGE, (int(tail_x), int(tail_y)), (int(sx), int(sy)), 4)
        pygame.draw.line(surface, Color.YELLOW, (int(tail_x), int(tail_y)), (int(sx), int(sy)), 2)

        # 弹头圆
        pygame.draw.circle(surface, Color.RED, (int(sx), int(sy)), self.size)
        pygame.draw.circle(surface, Color.YELLOW, (int(sx), int(sy)), 2)
