"""
升级系统 - 通用强化 + 武器专属强化
"""
import random
from entities.weapons.base import Upgrade, UPGRADE_UNLIMITED


def roll_upgrades(player, weapon, count=3):
    """从通用强化和武器专属强化中随机抽取，过滤已达上限的升级"""
    counts = player._upgrade_counts

    weapon_upgrades = []
    if weapon:
        for u in weapon.upgrades:
            cur = counts.get(u.id, 0)
            if cur >= u.max_count:
                continue
            weapon_upgrades.append(
                Upgrade(u.id, u.name, u.desc, u.icon_color, u.apply_fn, u.max_count, cur)
            )

    available = []
    for uid, name, desc, color, fn, *rest in player.GENERAL_UPGRADES:
        max_count = rest[0] if rest else UPGRADE_UNLIMITED
        cur = counts.get(uid, 0)
        if cur >= max_count:
            continue
        available.append(Upgrade(uid, name, desc, color, fn, max_count, cur))

    all_pool = available + weapon_upgrades
    if len(all_pool) < count:
        return all_pool

    return random.sample(all_pool, count)
