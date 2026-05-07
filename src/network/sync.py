"""
游戏同步协议 - 定义所有网络消息类型
"""
from enum import IntEnum

class MsgType(IntEnum):
    """消息类型枚举"""
    # 连接相关
    JOIN = 1
    JOIN_OK = 2
    JOIN_FAIL = 3
    PLAYER_LEFT = 4
    
    # 房间相关
    PLAYER_LIST = 10
    GAME_START = 11
    
    # 游戏同步 (核心)
    PLAYER_STATE = 100      # 玩家状态 (位置、动画等)
    PLAYER_SHOOT = 101       # 玩家射击
    MONSTER_SPAWN = 102     # 怪物生成
    MONSTER_HIT = 103       # 怪物受伤
    MONSTER_DEATH = 104     # 怪物死亡
    XP_DROP = 105           # 经验掉落
    XP_COLLECT = 106       # 经验拾取
    PLAYER_LEVEL_UP = 107   # 玩家升级
    UPGRADE_SELECT = 108    # 选择升级
    WAVE_CHANGE = 109       # 波次变化


def create_player_state_msg(player_id, x, y, hp, facing_right):
    """创建玩家状态消息"""
    return {
        'type': MsgType.PLAYER_STATE,
        'player_id': player_id,
        'x': x,
        'y': y,
        'hp': hp,
        'facing_right': facing_right
    }


def create_monster_spawn_msg(monster_id, monster_type, x, y, hp):
    """创建怪物生成消息"""
    return {
        'type': MsgType.MONSTER_SPAWN,
        'monster_id': monster_id,
        'monster_type': monster_type,
        'x': x,
        'y': y,
        'hp': hp
    }


def create_monster_hit_msg(monster_id, damage, shooter_id):
    """创建怪物受伤消息"""
    return {
        'type': MsgType.MONSTER_HIT,
        'monster_id': monster_id,
        'damage': damage,
        'shooter_id': shooter_id
    }


def create_monster_death_msg(monster_id, killer_id):
    """创建怪物死亡消息"""
    return {
        'type': MsgType.MONSTER_DEATH,
        'monster_id': monster_id,
        'killer_id': killer_id
    }


def create_xp_drop_msg(orb_id, x, y, value):
    """创建经验掉落消息"""
    return {
        'type': MsgType.XP_DROP,
        'orb_id': orb_id,
        'x': x,
        'y': y,
        'value': value
    }


def create_wave_change_msg(wave):
    """创建波次变化消息"""
    return {
        'type': MsgType.WAVE_CHANGE,
        'wave': wave
    }
