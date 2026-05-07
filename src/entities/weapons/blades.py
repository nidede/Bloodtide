"""
环绕飞刀 - 持续旋转攻击
"""
import math
import pygame
from .base import Weapon
from core.config import Color, MonsterConfig
from core.weapon_upgrades import build_blade_upgrades
from ui.effects import Particle, FloatingText


class Blades(Weapon):
    name = "飞刀"
    desc = "环绕 | 持续切割"
    color = Color.CYAN
    blade_count = 4
    rotation_speed = 3.6
    orbit_radius = 40
    damage = 12
    blade_size = 10
    blade_length = 30

    # 武器升级颜色标准：伤害-RED | 数量-YELLOW | 范围/速度-CYAN
    upgrades = build_blade_upgrades()

    def __init__(self):
        self.angles = self._calc_angles()
        self.total_rotations = [0.0] * self.blade_count
        self.cooldowns = {i: {} for i in range(self.blade_count)}

    def _calc_angles(self):
        return [i * 2 * math.pi / self.blade_count for i in range(self.blade_count)]

    def update(self, player, monsters, particles, floating_texts, dt):
        for i in range(len(self.angles)):
            self.angles[i] = (self.angles[i] + self.rotation_speed * dt) % (2 * math.pi)
            self.total_rotations[i] += self.rotation_speed * dt

        for blade_idx in list(self.cooldowns.keys()):
            self.cooldowns[blade_idx] = {
                mid: rot for mid, rot in self.cooldowns[blade_idx].items()
                if any(id(m) == mid for m in monsters)
            }

        for i, angle in enumerate(self.angles):
            if i not in self.cooldowns:
                self.cooldowns[i] = {}
            sx = player.x + math.cos(angle) * self.orbit_radius
            sy = player.y + math.sin(angle) * self.orbit_radius
            ex = player.x + math.cos(angle) * (self.orbit_radius + self.blade_length)
            ey = player.y + math.sin(angle) * (self.orbit_radius + self.blade_length)
            
            for monster in monsters:
                if monster.dead:
                    continue
                mid = id(monster)
                last_rot = self.cooldowns[i].get(mid)
                if last_rot is not None:
                    rot_diff = self.total_rotations[i] - last_rot
                    if rot_diff < 2 * math.pi:
                        continue
                mx, my = monster.x, monster.y
                mr = monster.size
                dist = self._point_to_segment_dist(mx, my, sx, sy, ex, ey)
                if dist < mr + self.blade_size:
                    self.deal_damage(monster, player, particles, floating_texts)
                    self.cooldowns[i][mid] = self.total_rotations[i]
                    hit_x, hit_y = self._closest_point_on_segment(mx, my, sx, sy, ex, ey)
                    particles.append(Particle(hit_x, hit_y, Color.CYAN, speed=120, lifetime=0.17))

    def _point_to_segment_dist(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(px - x1, py - y1)
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        nearest_x = x1 + t * dx
        nearest_y = y1 + t * dy
        return math.hypot(px - nearest_x, py - nearest_y)

    def _closest_point_on_segment(self, px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            return x1, y1
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        return x1 + t * dx, y1 + t * dy

    def draw(self, surface, cam_x=0, cam_y=0, px=0, py=0):
        for angle in self.angles:
            bx = px + math.cos(angle) * self.orbit_radius - cam_x
            by = py + math.sin(angle) * self.orbit_radius - cam_y
            ex = bx + math.cos(angle) * self.blade_length
            ey = by + math.sin(angle) * self.blade_length
            pygame.draw.line(surface, Color.CYAN, (bx, by), (ex, ey), 3)
            pygame.draw.line(surface, Color.WHITE, (bx + 1, by + 1), (ex - 1, ey - 1), 2)
            pygame.draw.circle(surface, (100, 200, 255, 80), (int(ex), int(ey)), self.blade_size, 1)

    def deal_damage(self, monster, player, particles, floating_texts):
        """飞刀造成伤害 - 无暴击，直接扣血"""
        monster.take_damage(self.damage, False, particles, floating_texts)

    def fire(self, px, py, angle, player, monsters=None, dt=None):
        return []

    def get_stats(self):
        return [
            ("飞刀", f"{self.blade_count}把"),
            ("伤害", str(self.damage)),
            ("半径", str(self.orbit_radius)),
        ]

    def apply_upgrade(self, player, upgrade_id):
        upgrade = self.get_upgrade_by_id(upgrade_id)
        if upgrade:
            upgrade.apply(player, self)
