"""
怪物模块
"""
from entities.combatants.monsters.base import BaseMonster, MonsterRegistry
from entities.combatants.monsters.normal import NormalMonster
from entities.combatants.monsters.fast import FastMonster
from entities.combatants.monsters.tank import TankMonster
from entities.combatants.monsters.elite import EliteMonster
from entities.combatants.monsters.ranged import RangedMonster
from entities.combatants.monsters.boss import BossMonster


def Monster(monster_type, level, x, y):
    """工厂函数：创建怪物实例"""
    monster_cls = MonsterRegistry.get(monster_type)
    if monster_cls is None:
        raise ValueError(f"Unknown monster type: {monster_type}")
    return monster_cls(level, x, y)


__all__ = [
    'BaseMonster',
    'MonsterRegistry',
    'Monster',
    'NormalMonster',
    'FastMonster',
    'TankMonster',
    'EliteMonster',
    'RangedMonster',
    'BossMonster',
]
