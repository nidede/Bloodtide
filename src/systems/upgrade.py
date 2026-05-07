"""
升级系统 - 通用强化 + 武器专属强化
"""
import random
from entities.weapons.base import Upgrade
from entities import GENERAL_UPGRADES


def roll_upgrades(player, weapon, count=3):
    """从通用强化和武器专属强化中随机抽取"""
    weapon_upgrades = []
    if weapon:
        weapon_upgrades = [
            Upgrade(u.id, u.name, u.desc, u.icon_color, u.apply_fn)
            for u in weapon.upgrades
        ]

    available = []
    for uid, name, desc, color, fn in GENERAL_UPGRADES:
        if uid == "dash" and player.has_dash:
            continue
        available.append(Upgrade(uid, name, desc, color, fn))

    all_pool = available + weapon_upgrades
    if len(all_pool) < count:
        return all_pool

    return random.sample(all_pool, count)
