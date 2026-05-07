"""
武器模块
"""
import random
from entities.weapons.player import Rifle, Blades, Missile


def get_random_weapons(count=3, level=1):
    """随机获取指定数量的玩家武器"""
    weapons = [Rifle, Blades, Missile]
    selected = random.sample(weapons, min(count, len(weapons)))
    return selected


__all__ = ['get_random_weapons', 'Rifle', 'Blades', 'Missile']
