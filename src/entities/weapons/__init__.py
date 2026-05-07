"""
武器模块
"""
import random
from entities.weapons.rifle import Rifle
from entities.weapons.blades import Blades
from entities.weapons.missile import Missile


def get_random_weapons(count=3, level=1):
    """随机获取指定数量的武器"""
    weapons = [Rifle, Blades, Missile]
    selected = random.sample(weapons, min(count, len(weapons)))
    return selected


__all__ = ['get_random_weapons', 'Rifle', 'Blades', 'Missile']
