"""
投射物基类
"""
import math
import random
from core.config import Color, WorldConfig, ProjectileConfig, FPS
from ui.effects import pygame_draw_circle


class Projectile:
    def __init__(self, x, y, angle, damage, speed, crit_chance, crit_damage,
                 piercing, life_steal, owner):
        self.x = x
        self.y = y
        self.angle = angle
        self.damage = damage
        self.speed = speed * FPS  # 像素/秒
        self.crit_chance = crit_chance
        self.crit_damage = crit_damage
        self.piercing = piercing
        self.life_steal = life_steal
        self.owner = owner
        self.size = ProjectileConfig.DEFAULT_SIZE
        self.alive = True
        self.hit_monsters = set()
        self.trail = []

    def deal_damage(self, monster, player, particles, floating_texts):
        """对怪物造成伤害 - 子类可重写自定义伤害逻辑"""
        is_crit = random.random() < self.crit_chance
        damage = int(self.damage * (self.crit_damage if is_crit else 1))
        monster.take_damage(damage, is_crit, particles, floating_texts)

        # 吸血
        if self.life_steal > 0 and player:
            heal = max(1, int(damage * self.life_steal))
            player.hp = min(player.max_hp, player.hp + heal)

        self.hit_monsters.add(id(monster))

        # 穿透
        if self.piercing > 0:
            self.piercing -= 1
        else:
            self.alive = False

        return damage, is_crit

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
