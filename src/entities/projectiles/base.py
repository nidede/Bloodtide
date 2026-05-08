"""
投射物基类 - 纯飞行实体，只负责移动和绘制
伤害由 Weapon.deal_damage() 处理
"""
import math
from core.config import Color, WorldConfig, ProjectileConfig, FPS
from core.render import pygame_draw_circle


class Projectile:
    def __init__(self, x, y, angle, speed, weapon=None, owner=None, piercing=0, is_enemy=None):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed * FPS  # 像素/秒
        self.weapon = weapon      # 所属武器，用于回调 deal_damage
        self.owner = owner        # 所属实体（玩家/怪物），用于敌我识别
        self.piercing = piercing  # 剩余穿透次数（由武器设置，CombatSystem 管理）
        # 自动从 owner 推断阵营，也可手动指定
        self.is_enemy = is_enemy if is_enemy is not None else getattr(owner, 'is_enemy', False)
        self.size = ProjectileConfig.DEFAULT_SIZE
        self.alive = True
        self.hit_set = set()      # 已命中实体ID集合（防止重复命中）
        self.trail = []

    def on_hit(self, target):
        """命中目标后的处理 - 记录命中、消耗穿透、判断存活"""
        self.hit_set.add(id(target))
        if self.piercing > 0:
            self.piercing -= 1
        else:
            self.alive = False

    def update(self, dt):
        self.trail.append((self.x, self.y))
        if len(self.trail) > ProjectileConfig.TRAIL_LENGTH:
            self.trail.pop(0)

        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt

        margin = ProjectileConfig.DESPAWN_MARGIN
        if (self.x < -margin or self.x > WorldConfig.WIDTH + margin or
                self.y < -margin or self.y > WorldConfig.HEIGHT + margin):
            self.alive = False

    def draw(self, surface, cam_x=0, cam_y=0):
        color = getattr(self, 'color', Color.YELLOW)
        for i, (tx, ty) in enumerate(self.trail):
            alpha = (i + 1) / max(1, len(self.trail)) * 0.5
            r = max(1, int(self.size * alpha))
            trail_color = tuple(int(c * alpha) for c in color)
            pygame_draw_circle(surface, trail_color, tx - cam_x, ty - cam_y, r)
        pygame_draw_circle(surface, color, self.x - cam_x, self.y - cam_y, self.size)
