"""精英怪物 - 比普通怪更强"""
import math
import pygame
from core.config import Color
from .base import BaseMonster, MonsterRegistry
from entities.weapons.enemy.melee import EnemyMeleeWeapon


@MonsterRegistry.register
class EliteMonster(BaseMonster):
    """精英怪物 - 高属性"""

    TYPE = "elite"
    HP_BASE = 80
    HP_PER_LVL = 25
    SPEED_BASE = 90
    SPEED_PER_LVL = 3
    DAMAGE_BASE = 12
    DAMAGE_PER_LVL = 4
    SIZE = 25
    COLOR = Color.PURPLE
    XP_BASE = 40
    XP_PER_LVL = 8
    MIN_WAVE = 3
    SPAWN_WEIGHT = 0.10
    weapon_class = EnemyMeleeWeapon

    def _draw_shape(self, surface, color, sx, sy):
        """六边形表示精英"""
        points = []
        for i in range(6):
            a = math.pi / 3 * i - math.pi / 6
            points.append((int(sx + self.size * math.cos(a)),
                          int(sy + self.size * math.sin(a))))
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, Color.WHITE, points, 2)
