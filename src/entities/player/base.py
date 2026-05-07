"""
角色基类
"""
from core.config import Color, WORLD_WIDTH, WORLD_HEIGHT


class Character:
    """角色基类"""
    size = 20
    speed = 150
    max_hp = 100
    attack = 0
    defense = 0
    crit_chance = 0.05
    crit_damage = 1.5
    life_steal = 0
    thorns = 0
    regen = 0
    xp_multiplier = 1.0
    magnet_range = 80

    # 可选：角色专属升级列表
    upgrades = []
