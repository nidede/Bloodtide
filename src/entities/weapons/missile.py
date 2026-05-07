"""
导弹 - 范围爆炸，可追踪
"""
import math
import random
import pygame
from .base import Weapon
from core.config import Color, MonsterConfig
from core.weapon_upgrades import build_missile_upgrades
from ui.effects import Particle, FloatingText
from entities.projectiles import Projectile, MissileProjectile


class Missile(Weapon):
    name = "导弹"
    desc = "爆炸 | 范围伤害"
    color = Color.ORANGE
    damage = 20
    fire_rate = 50
    projectile_count = 1
    projectile_speed = 4
    explosion_radius = 65
    homing = False

    # 武器升级颜色标准：伤害-RED | 追踪-GREEN | 爆炸-ORANGE | 数量-YELLOW
    upgrades = build_missile_upgrades()

    def fire(self, px, py, angle, player, monsters=None, dt=None):
        count = self.projectile_count
        projectiles = []
        for i in range(count):
            a = angle if count == 1 else angle - 0.15 + i * 0.3
            p = MissileProjectile(
                px, py, a, self.damage, self.projectile_speed,
                0, 1.0,  # 导弹不暴击
                0, player.life_steal, player,
                self.explosion_radius, self.homing,
                monsters or []
            )
            projectiles.append(p)
        return projectiles

    def get_stats(self):
        return [
            ("伤害", str(self.damage)),
            ("射速", f"{60/self.fire_rate:.1f}/s"),
            ("爆炸范围", str(self.explosion_radius)),
            ("追踪", "是" if self.homing else "否"),
        ]

    def apply_upgrade(self, player, upgrade_id):
        upgrade = self.get_upgrade_by_id(upgrade_id)
        if upgrade:
            upgrade.apply(player, self)
