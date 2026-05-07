"""坦克怪物 - 血量高但速度慢"""
import pygame
from core.config import Color
from .base import BaseMonster, MonsterRegistry
from entities.weapons.enemy.melee import EnemyMeleeWeapon


@MonsterRegistry.register
class TankMonster(BaseMonster):
    """坦克怪物 - 高血量低速度"""

    TYPE = "tank"
    HP_BASE = 50
    HP_PER_LVL = 20
    SPEED_BASE = 42
    SPEED_PER_LVL = 2
    DAMAGE_BASE = 8
    DAMAGE_PER_LVL = 3
    SIZE = 22
    COLOR = Color.ORANGE
    XP_BASE = 18
    XP_PER_LVL = 5
    MIN_WAVE = 1
    SPAWN_WEIGHT = 0.15
    weapon_class = EnemyMeleeWeapon

    def _draw_shape(self, surface, color, sx, sy):
        """方形表示坦克"""
        rect = pygame.Rect(sx - self.size, sy - self.size, self.size * 2, self.size * 2)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, Color.WHITE, rect, 2)
