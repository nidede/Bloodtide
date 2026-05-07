"""
导弹投射物 - 追踪、爆炸
"""
import math
import random
import pygame
from core.config import Color, ProjectileConfig, MissileConfig
from ui.effects import Particle
from .base import Projectile


class MissileProjectile(Projectile):
    def __init__(self, x, y, angle, damage, speed, crit_chance, crit_damage,
                 piercing, life_steal, owner, explosion_radius, homing, monsters=None):
        super().__init__(x, y, angle, damage, speed, crit_chance, crit_damage,
                         piercing, life_steal, owner)
        self.explosion_radius = explosion_radius
        self.homing = homing
        self.monsters_ref = monsters or []
        self.size = MissileConfig.SIZE
        self.max_lifetime = MissileConfig.MAX_LIFETIME
        self.lifetime = 0

    def deal_damage(self, monster, player, particles, floating_texts):
        """导弹命中 - 不直接造成伤害，标记死亡等待爆炸处理"""
        self.hit_monsters.add(id(monster))
        self.alive = False
        return 0, False

    def update(self, dt):
        self.lifetime += dt
        self.trail.append((self.x, self.y))
        if len(self.trail) > ProjectileConfig.TRAIL_LENGTH:
            self.trail.pop(0)

        if self.homing:
            if int(self.lifetime * 10) % 10 == 0:
                nearest = None
                min_dist = float('inf')
                for m in self.monsters_ref:
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

    def explode(self, game_monsters, particles, floating_texts):
        for monster in list(game_monsters):
            if monster.dead:
                continue
            dist = math.hypot(self.x - monster.x, self.y - monster.y)
            if dist < self.explosion_radius:
                ratio = 1 - dist / self.explosion_radius
                dmg = max(1, int(self.damage * ratio))
                monster.take_damage(dmg, False, particles, floating_texts)

        offset = int(self.explosion_radius * MissileConfig.EXPLOSION_OFFSET_RATIO)
        for _ in range(MissileConfig.EXPLOSION_PARTICLE_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(MissileConfig.EXPLOSION_PARTICLE_SPEED_MIN,
                                 MissileConfig.EXPLOSION_PARTICLE_SPEED_MAX)
            particles.append(Particle(
                self.x + math.cos(angle) * random.randint(0, offset),
                self.y + math.sin(angle) * random.randint(0, offset),
                Color.ORANGE, spd,
                MissileConfig.EXPLOSION_PARTICLE_LIFETIME,
                MissileConfig.EXPLOSION_PARTICLE_SIZE
            ))

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
