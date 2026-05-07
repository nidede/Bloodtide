"""
战斗实体模块 - 所有可战斗的实体（玩家、怪物）的公共基类
"""
from .base import CombatEntity
from .monsters import *
from .player import Player, Soldier

__all__ = ['CombatEntity']
