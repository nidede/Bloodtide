"""
玩家武器模块
"""
from .rifle import Rifle
from .blades import Blades
from .missile import Missile
from .mg import MachineGun
from .arc import Arc
from .flamethrower import Flamethrower
from .boomerang import Boomerang
from .freeze_gun import FreezeGun
from .summon import SummonWeapon
from .flame_mg import FlameGun
from .rainbow_mg import RainbowMG

__all__ = ['Rifle', 'Blades', 'Missile', 'MachineGun', 'Arc', 'Flamethrower',
           'Boomerang', 'FreezeGun', 'SummonWeapon', 'FlameGun', 'RainbowMG']
