"""普通怪物 - 最基础的敌人"""
from core.config import Color
from .base import BaseMonster, MonsterRegistry
from entities.weapons.enemy.melee import EnemyMeleeWeapon


@MonsterRegistry.register
class NormalMonster(BaseMonster):
    """普通怪物 - 均衡型敌人"""

    TYPE = "normal"
    HP_BASE = 20
    HP_PER_LVL = 10
    SPEED_BASE = 72
    SPEED_PER_LVL = 3
    DAMAGE_BASE = 5
    DAMAGE_PER_LVL = 2
    SIZE = 15
    COLOR = Color.RED
    XP_BASE = 10
    XP_PER_LVL = 3
    MIN_WAVE = 1
    SPAWN_WEIGHT = 0.45
    weapon_class = EnemyMeleeWeapon

