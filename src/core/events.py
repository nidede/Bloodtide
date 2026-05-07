"""
事件系统 - 解耦游戏系统间的通信
"""
from enum import Enum, auto
from collections import defaultdict
from typing import Callable, Dict, List, Any


class EventType(Enum):
    """游戏事件类型"""
    # 战斗相关
    MONSTER_DIED = auto()
    PLAYER_HIT = auto()
    PROJECTILE_HIT = auto()
    
    # 掉落相关
    ORB_COLLECTED = auto()
    
    # UI相关
    FLOATING_TEXT = auto()
    PARTICLE_SPAWN = auto()
    
    # 升级相关
    LEVEL_UP = auto()
    UPGRADE_SELECTED = auto()


class Event:
    """事件对象"""
    def __init__(self, event_type: EventType, data: dict = None):
        self.type = event_type
        self.data = data or {}


class EventBus:
    """事件总线 - 发布/订阅模式"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners: Dict[EventType, List[Callable]] = defaultdict(list)
        return cls._instance
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """订阅事件"""
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """取消订阅"""
        if callback in self._listeners[event_type]:
            self._listeners[event_type].remove(callback)
    
    def emit(self, event: Event):
        """发布事件"""
        for callback in self._listeners[event.type]:
            try:
                callback(event)
            except Exception as e:
                print(f"Event handler error: {e}")
    
    def clear(self):
        """清空所有订阅"""
        self._listeners.clear()


# 全局事件总线实例
event_bus = EventBus()
