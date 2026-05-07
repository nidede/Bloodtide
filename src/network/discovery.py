"""
局域网房间发现服务
使用 UDP 广播实现房间搜索
"""
import socket
import threading
import time
import json
import struct
from dataclasses import dataclass, asdict
from typing import List, Optional, Callable


# 广播配置
BROADCAST_PORT = 9999
DISCOVERY_INTERVAL = 1.0  # 秒
ROOM_TTL = 5.0  # 房间列表过期时间


def _get_broadcast_addresses():
    """获取可用的广播地址列表"""
    addresses = []
    
    # 方式1: 通用广播地址
    addresses.append('<broadcast>')
    addresses.append('255.255.255.255')
    
    # 方式2: 获取本机网络的广播地址
    try:
        hostname = socket.gethostname()
        local_ips = socket.gethostbyname_ex(hostname)[2]
        for ip in local_ips:
            parts = ip.split('.')
            if len(parts) == 4:
                # 假设 /24 子网，计算广播地址
                broadcast = f"{parts[0]}.{parts[1]}.{parts[2]}.255"
                if broadcast not in addresses:
                    addresses.append(broadcast)
    except Exception:
        pass
    
    return addresses


@dataclass
class RoomInfo:
    """房间信息"""
    room_id: str
    host_name: str
    host_ip: str
    player_count: int
    max_players: int
    game_mode: str = "survival"
    last_seen: float = 0
    
    def is_valid(self) -> bool:
        """检查房间是否还有效"""
        return time.time() - self.last_seen < ROOM_TTL


class DiscoveryService:
    """房间发现服务"""
    
    def __init__(self, player_name: str = "Player"):
        self.player_name = player_name
        self.rooms: List[RoomInfo] = []
        self._running = False
        self._lock = threading.Lock()
        
        # 回调函数
        self.on_rooms_updated: Optional[Callable[[List[RoomInfo]], None]] = None
    
    def start_broadcast(self, room_id: str, player_count: int, max_players: int = 4):
        """开始广播自己的房间"""
        self._running = True
        self._room_id = room_id
        self._player_count = player_count
        self._max_players = max_players
        
        self._broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self._broadcast_thread.start()
    
    def stop_broadcast(self):
        """停止广播"""
        self._running = False
    
    def _broadcast_loop(self):
        """广播循环"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # 绑定到特定端口，确保发送和接收在同一端口
        try:
            sock.bind(('', BROADCAST_PORT))
        except OSError:
            pass
        sock.settimeout(0.5)
        
        broadcast_addresses = _get_broadcast_addresses()
        
        while self._running:
            msg = {
                'type': 'room_announce',
                'room_id': self._room_id,
                'host_name': self.player_name,
                'player_count': self._player_count,
                'max_players': self._max_players,
                'game_mode': 'survival',
            }
            data = json.dumps(msg).encode('utf-8')
            for addr in broadcast_addresses:
                try:
                    sock.sendto(data, (addr, BROADCAST_PORT))
                except Exception:
                    pass
            time.sleep(DISCOVERY_INTERVAL)
        
        sock.close()
    
    def start_listening(self):
        """开始监听房间列表"""
        self._running = True
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
    
    def stop_listening(self):
        """停止监听"""
        self._running = False
    
    def _listen_loop(self):
        """监听循环"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        
        try:
            sock.bind(('', BROADCAST_PORT))
        except OSError:
            # 端口被占用，尝试其他方式
            sock.close()
            return
        
        while self._running:
            try:
                data, addr = sock.recvfrom(4096)
                msg = json.loads(data.decode('utf-8'))
                
                if msg.get('type') == 'room_announce':
                    room = RoomInfo(
                        room_id=msg['room_id'],
                        host_name=msg['host_name'],
                        host_ip=addr[0],
                        player_count=msg['player_count'],
                        max_players=msg['max_players'],
                        game_mode=msg.get('game_mode', 'survival'),
                        last_seen=time.time(),
                    )
                    self._add_or_update_room(room)
                    
            except socket.timeout:
                continue
            except Exception:
                continue
        
        sock.close()
    
    def _add_or_update_room(self, room: RoomInfo):
        """添加或更新房间"""
        with self._lock:
            for i, r in enumerate(self.rooms):
                if r.room_id == room.room_id and r.host_ip == room.host_ip:
                    self.rooms[i] = room
                    break
            else:
                self.rooms.append(room)
            
            # 清理过期房间
            self.rooms = [r for r in self.rooms if r.is_valid()]
            
            # 触发回调
            if self.on_rooms_updated:
                self.on_rooms_updated(self.rooms.copy())
    
    def request_room_list(self):
        """发送房间列表请求"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            msg = json.dumps({'type': 'room_list_request'}).encode('utf-8')
            broadcast_addresses = _get_broadcast_addresses()
            for addr in broadcast_addresses:
                try:
                    sock.sendto(msg, (addr, BROADCAST_PORT))
                except Exception:
                    pass
        finally:
            sock.close()
    
    def get_rooms(self) -> List[RoomInfo]:
        """获取有效房间列表"""
        with self._lock:
            return [r for r in self.rooms if r.is_valid()]
