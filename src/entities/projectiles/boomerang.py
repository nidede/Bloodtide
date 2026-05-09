"""
回旋镖投射物 - 飞出后自动返回，来回各命中一次
"""
import math
import pygame
from core.config import Color, ProjectileConfig
from .base import Projectile


class BoomerangProjectile(Projectile):
    """回旋镖 - 飞到最远距离后返回，返回时清空 hit_set 可再次命中"""

    def __init__(self, x, y, angle, speed, weapon=None, owner=None, max_distance=200):
        super().__init__(x, y, angle, speed, weapon=weapon, owner=owner, piercing=999)
        self.start_x = x
        self.start_y = y
        self.max_distance = max_distance
        self.returning = False
        self.size = 8
        self._spin = 0.0  # 旋转角度（纯视觉）
        self.return_target = owner  # 返回目标，默认为 owner（玩家）

    def update(self, dt):
        self.trail.append((self.x, self.y))
        if len(self.trail) > ProjectileConfig.TRAIL_LENGTH:
            self.trail.pop(0)

        self._spin += dt * 12  # 旋转速度

        if not self.returning:
            # 飞出阶段
            self.x += math.cos(self.angle) * self.speed * dt
            self.y += math.sin(self.angle) * self.speed * dt
            # 到达最远距离，切换返回
            dist = math.hypot(self.x - self.start_x, self.y - self.start_y)
            if dist >= self.max_distance:
                self.returning = True
                self.hit_set.clear()  # 返回时可以再次命中
        else:
            # 返回阶段：朝 return_target 飞行
            target = self.return_target
            if target:
                dx = target.x - self.x
                dy = target.y - self.y
                dist = math.hypot(dx, dy)
                if dist < 20:
                    self.alive = False
                    return
                self.angle = math.atan2(dy, dx)
                self.x += math.cos(self.angle) * self.speed * dt
                self.y += math.sin(self.angle) * self.speed * dt
            else:
                self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        sx, sy = self.x - cam_x, self.y - cam_y

        # 尾迹
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / max(1, len(self.trail)) * 0.4
            r = max(1, int(3 * alpha))
            color = (int(200 * alpha), int(160 * alpha), int(50 * alpha))
            pygame.draw.circle(surface, color, (int(tx - cam_x), int(ty - cam_y)), r)

        # 回旋镖本体：两个交叉的线段，绕中心旋转
        angle = self._spin
        arm_len = self.size
        for offset in (0, math.pi / 2):
            a = angle + offset
            x1 = sx + math.cos(a) * arm_len
            y1 = sy + math.sin(a) * arm_len
            x2 = sx - math.cos(a) * arm_len
            y2 = sy - math.sin(a) * arm_len
            pygame.draw.line(surface, Color.YELLOW, (int(x1), int(y1)), (int(x2), int(y2)), 3)
            pygame.draw.line(surface, Color.WHITE, (int(x1), int(y1)), (int(x2), int(y2)), 1)
