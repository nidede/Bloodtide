"""快速怪物 - 速度快但血量低"""
import pygame
from core.config import Color
from .base import BaseMonster, MonsterRegistry
from entities.weapons.enemy.melee import EnemyMeleeWeapon


@MonsterRegistry.register
class FastMonster(BaseMonster):
    """快速怪物 - 高速度低血量"""

    TYPE = "fast"
    HP_BASE = 12
    HP_PER_LVL = 6
    SPEED_BASE = 150
    SPEED_PER_LVL = 5
    DAMAGE_BASE = 4
    DAMAGE_PER_LVL = 1.5
    SIZE = 12
    COLOR = Color.CYAN
    XP_BASE = 12
    XP_PER_LVL = 3
    MIN_WAVE = 1
    SPAWN_WEIGHT = 0.25
    weapon_class = EnemyMeleeWeapon

    def _draw_shape(self, surface, color, sx, sy):
        """椭圆形表示运动感"""
        pygame.draw.ellipse(surface, color, (sx - self.size, sy - self.size // 2, self.size * 2, self.size))
        pygame.draw.ellipse(surface, Color.WHITE, (sx - self.size, sy - self.size // 2, self.size * 2, self.size), 1)
