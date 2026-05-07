"""
游戏同步器 - 处理实时游戏状态同步
"""
import json
import threading
import time
import uuid
from collections import defaultdict
from typing import Dict, List, Callable, Optional, Any

from .sync import MsgType, create_player_state_msg, create_monster_spawn_msg
from .sync import create_monster_hit_msg, create_monster_death_msg, create_xp_drop_msg


class RemotePlayer:
    """远程玩家表示"""
    def __init__(self, player_id, name, x=0, y=0, hp=100):
        self.player_id = player_id
        self.name = name
        self.x = x
        self.y = y
        self.hp = hp
        self.facing_right = True
        self.alive = True
        self.last_update = time.time()
    
    def update(self, x, y, hp, facing_right):
        self.x = x
        self.y = y
        self.hp = hp
        self.facing_right = facing_right
        self.last_update = time.time()


class GameSync:
    """游戏同步器 - 处理所有游戏状态的同步"""
    
    # 同步配置
    SYNC_RATE = 20  # 每秒同步次数
    SYNC_INTERVAL = 1.0 / SYNC_RATE
    POSITION_INTERP = 0.2  # 位置插值系数
    
    def __init__(self, is_host=False):
        self.is_host = is_host
        self.player_id = str(uuid.uuid4())[:8]
        self.player_name = "Player"
        
        # 远程玩家
        self.remote_players: Dict[str, RemotePlayer] = {}
        
        # 同步回调
        self.on_remote_player_update: Optional[Callable] = None
        self.on_monster_spawn: Optional[Callable] = None
        self.on_monster_hit: Optional[Callable] = None
        self.on_monster_death: Optional[Callable] = None
        self.on_xp_drop: Optional[Callable] = None
        self.on_player_join: Optional[Callable] = None
        self.on_player_leave: Optional[Callable] = None
        self.on_wave_change: Optional[Callable] = None
        
        # 同步锁
        self._lock = threading.Lock()
        
        # 待发送的消息队列
        self._send_queue = []
        
        # 最后同步时间
        self._last_sync_time = 0
        
    def set_player_info(self, player_id, player_name):
        """设置玩家信息"""
        self.player_id = player_id
        self.player_name = player_name
    
    def add_remote_player(self, player_id, name):
        """添加远程玩家"""
        with self._lock:
            if player_id not in self.remote_players:
                self.remote_players[player_id] = RemotePlayer(player_id, name)
                print(f"[Sync] 添加远程玩家: {name} ({player_id})")
                if self.on_player_join:
                    self.on_player_join(player_id, name)
    
    def remove_remote_player(self, player_id):
        """移除远程玩家"""
        with self._lock:
            if player_id in self.remote_players:
                name = self.remote_players[player_id].name
                del self.remote_players[player_id]
                print(f"[Sync] 移除远程玩家: {name}")
                if self.on_player_leave:
                    self.on_player_leave(player_id)
    
    def queue_player_state(self, x, y, hp, facing_right):
        """将玩家状态加入发送队列"""
        msg = create_player_state_msg(self.player_id, x, y, hp, facing_right)
        with self._lock:
            self._send_queue.append(msg)
    
    def handle_message(self, msg: dict):
        """处理接收到的消息"""
        msg_type = msg.get('type')
        
        if isinstance(msg_type, str):
            try:
                msg_type = MsgType(int(msg_type))
            except:
                return
        
        if msg_type == MsgType.PLAYER_STATE:
            self._handle_player_state(msg)
        elif msg_type == MsgType.PLAYER_LEFT:
            self._handle_player_left(msg)
        elif msg_type == MsgType.MONSTER_SPAWN:
            self._handle_monster_spawn(msg)
        elif msg_type == MsgType.MONSTER_HIT:
            self._handle_monster_hit(msg)
        elif msg_type == MsgType.MONSTER_DEATH:
            self._handle_monster_death(msg)
        elif msg_type == MsgType.XP_DROP:
            self._handle_xp_drop(msg)
        elif msg_type == MsgType.WAVE_CHANGE:
            self._handle_wave_change(msg)
        elif msg_type == MsgType.JOIN:
            # 玩家加入消息
            self.add_remote_player(msg.get('player_id'), msg.get('name', 'Unknown'))
    
    def _handle_player_state(self, msg):
        """处理玩家状态更新"""
        player_id = msg.get('player_id')
        if player_id == self.player_id:
            return  # 忽略自己的消息
        
        with self._lock:
            if player_id in self.remote_players:
                remote = self.remote_players[player_id]
                remote.update(
                    msg.get('x', 0),
                    msg.get('y', 0),
                    msg.get('hp', 100),
                    msg.get('facing_right', True)
                )
            else:
                # 新玩家
                self.add_remote_player(player_id, msg.get('name', 'Player'))
                if player_id in self.remote_players:
                    self.remote_players[player_id].update(
                        msg.get('x', 0),
                        msg.get('y', 0),
                        msg.get('hp', 100),
                        msg.get('facing_right', True)
                    )
        
        if self.on_remote_player_update:
            self.on_remote_player_update(player_id, msg)
    
    def _handle_player_left(self, msg):
        """处理玩家离开"""
        player_id = msg.get('player_id')
        self.remove_remote_player(player_id)
    
    def _handle_monster_spawn(self, msg):
        """处理怪物生成"""
        if self.on_monster_spawn:
            self.on_monster_spawn(
                msg.get('monster_id'),
                msg.get('monster_type'),
                msg.get('x', 0),
                msg.get('y', 0),
                msg.get('hp', 100)
            )
    
    def _handle_monster_hit(self, msg):
        """处理怪物受伤"""
        if self.on_monster_hit:
            self.on_monster_hit(
                msg.get('monster_id'),
                msg.get('damage', 0),
                msg.get('shooter_id')
            )
    
    def _handle_monster_death(self, msg):
        """处理怪物死亡"""
        if self.on_monster_death:
            self.on_monster_death(
                msg.get('monster_id'),
                msg.get('killer_id')
            )
    
    def _handle_xp_drop(self, msg):
        """处理经验掉落"""
        if self.on_xp_drop:
            self.on_xp_drop(
                msg.get('orb_id'),
                msg.get('x', 0),
                msg.get('y', 0),
                msg.get('value', 10)
            )
    
    def _handle_wave_change(self, msg):
        """处理波次变化"""
        if self.on_wave_change:
            self.on_wave_change(msg.get('wave', 1))
    
    def get_messages_to_send(self) -> List[dict]:
        """获取待发送的消息"""
        with self._lock:
            messages = self._send_queue.copy()
            self._send_queue.clear()
            return messages
    
    def broadcast_monster_spawn(self, monster_id, monster_type, x, y, hp):
        """广播怪物生成"""
        msg = create_monster_spawn_msg(monster_id, monster_type, x, y, hp)
        with self._lock:
            self._send_queue.append(msg)
    
    def broadcast_monster_hit(self, monster_id, damage, shooter_id=None):
        """广播怪物受伤"""
        if shooter_id is None:
            shooter_id = self.player_id
        msg = create_monster_hit_msg(monster_id, damage, shooter_id)
        with self._lock:
            self._send_queue.append(msg)
    
    def broadcast_monster_death(self, monster_id):
        """广播怪物死亡"""
        msg = create_monster_death_msg(monster_id, self.player_id)
        with self._lock:
            self._send_queue.append(msg)
    
    def broadcast_xp_drop(self, orb_id, x, y, value):
        """广播经验掉落"""
        msg = create_xp_drop_msg(orb_id, x, y, value)
        with self._lock:
            self._send_queue.append(msg)
    
    def broadcast_wave_change(self, wave):
        """广播波次变化"""
        msg = {'type': MsgType.WAVE_CHANGE, 'wave': wave}
        with self._lock:
            self._send_queue.append(msg)
    
    def get_remote_players(self) -> Dict[str, RemotePlayer]:
        """获取所有远程玩家"""
        with self._lock:
            return dict(self.remote_players)


class SyncMessageHandler:
    """同步消息处理器 - 集成到现有的房间管理器"""
    
    def __init__(self, game_sync: GameSync, send_func: Callable):
        """
        game_sync: GameSync实例
        send_func: 发送消息的函数，接受dict参数
        """
        self.game_sync = game_sync
        self._send_func = send_func
        
        # 消息统计
        self._stats = {
            'sent': 0,
            'received': 0,
            'last_send_time': 0
        }
    
    def update(self):
        """每帧调用，发送排队的消息"""
        messages = self.game_sync.get_messages_to_send()
        for msg in messages:
            try:
                self._send_func(msg)
                self._stats['sent'] += 1
            except Exception as e:
                print(f"[Sync] 发送失败: {e}")
    
    def handle_raw_message(self, data):
        """处理原始消息（JSON字符串或字典）"""
        try:
            if isinstance(data, str):
                msg = json.loads(data)
            else:
                msg = data
            
            self._stats['received'] += 1
            self.game_sync.handle_message(msg)
        except Exception as e:
            print(f"[Sync] 解析消息失败: {e}")
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return dict(self._stats)
