"""
怪物模块
"""
from entities.monsters.base import BaseMonster
from entities.monsters.normal import NormalMonster
from entities.monsters.fast import FastMonster
from entities.monsters.tank import TankMonster
from entities.monsters.elite import EliteMonster
from entities.monsters.ranged import RangedMonster
from entities.monsters.boss import BossMonster


class MonsterRegistry:
    """怪物注册表"""
    _types = {}
    
    @classmethod
    def register(cls, monster_cls):
        """注册怪物类型"""
        if hasattr(monster_cls, 'TYPE'):
            cls._types[monster_cls.TYPE] = monster_cls
    
    @classmethod
    def get(cls, monster_type):
        """获取怪物类型"""
        return cls._types.get(monster_type)
    
    @classmethod
    def get_spawn_candidates(cls, wave):
        """获取当前波次可生成的怪物列表"""
        candidates = []
        weights = []
        for monster_cls in cls._types.values():
            if monster_cls.TYPE != "boss" and monster_cls.MIN_WAVE <= wave:
                candidates.append(monster_cls.TYPE)
                weights.append(monster_cls.SPAWN_WEIGHT)
        return candidates, weights
    
    @classmethod
    def all_types(cls):
        """获取所有注册的怪物类型"""
        return list(cls._types.keys())


# 注册所有怪物类型
MonsterRegistry.register(NormalMonster)
MonsterRegistry.register(FastMonster)
MonsterRegistry.register(TankMonster)
MonsterRegistry.register(EliteMonster)
MonsterRegistry.register(RangedMonster)
MonsterRegistry.register(BossMonster)


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
