"""
武器模块
"""
import random
from entities.weapons.player import (Rifle, Blades, Missile, MachineGun, Arc,
                                       Flamethrower, Boomerang, FreezeGun,
                                       SummonWeapon, FlameGun, RainbowMG)


def get_random_weapons(count=None, level=1):
    """获取全部玩家武器（供选择界面展示）"""
    weapons = [Rifle, Blades, Missile, MachineGun, Arc, Flamethrower,
               Boomerang, FreezeGun, SummonWeapon, FlameGun, RainbowMG]
    if count is not None:
        selected = random.sample(weapons, min(count, len(weapons)))
        return selected
    return weapons


__all__ = ['get_random_weapons', 'Rifle', 'Blades', 'Missile', 'MachineGun',
           'Arc', 'Flamethrower', 'Boomerang', 'FreezeGun', 'SummonWeapon',
           'FlameGun', 'RainbowMG']
