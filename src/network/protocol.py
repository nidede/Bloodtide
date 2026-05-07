"""
网络协议 - 定义消息格式
"""
import struct
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional
import json


class MessageType(IntEnum):
    """消息类型"""
    # 房间相关
    ROOM_CREATE = 1       # 创建房间
    ROOM_JOIN = 2         # 加入房间
    ROOM_LEAVE = 3        # 离开房间
    ROOM_LIST = 4         # 房间列表请求
    ROOM_LIST_RESP = 5    # 房间列表响应
    
    # 游戏状态同步
    PLAYER_JOIN = 10      # 玩家加入游戏
    PLAYER_LEAVE = 11     # 玩家离开游戏
    PLAYER_INPUT = 12     # 玩家输入
    PLAYER_STATE = 13     # 玩家状态更新
    GAME_STATE = 14       # 完整游戏状态
    
    # 心跳
    PING = 100
    PONG = 101


@dataclass
class GameMessage:
    """游戏消息"""
    msg_type: MessageType
    player_id: Optional[int] = None
    data: dict = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
    
    def to_bytes(self) -> bytes:
        """序列化为字节"""
        json_data = json.dumps(self.data, ensure_ascii=False)
        json_bytes = json_data.encode('utf-8')
        header = struct.pack('!BI', self.msg_type.value, len(json_bytes))
        return header + json_bytes
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'GameMessage':
        """从字节反序列化"""
        msg_type = MessageType(data[0])
        length = struct.unpack('!I', data[1:5])[0]
        json_data = data[5:5+length].decode('utf-8')
        msg_data = json.loads(json_data)
        return cls(msg_type, msg_data.get('player_id'), msg_data)


def create_message(msg_type: MessageType, player_id: int = None, **kwargs) -> GameMessage:
    """快捷创建消息"""
    return GameMessage(msg_type, player_id, kwargs)
