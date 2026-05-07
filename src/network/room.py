"""
房间管理 - 处理玩家加入/离开
"""
import socket
import threading
import time
import uuid
import json
from typing import List, Optional, Callable
from dataclasses import dataclass


@dataclass
class Player:
    """网络玩家"""
    player_id: str
    name: str
    ip: str
    connected: bool = True
    last_ping: float = 0


class RoomManager:
    """房间管理器"""
    
    def __init__(self, is_host: bool = False):
        self.is_host = is_host
        self.room_id = str(uuid.uuid4())[:8].upper()
        self.players: List[Player] = []
        self._running = False
        self._lock = threading.Lock()
        self._clients: List[tuple] = []  # 存储 (socket, addr)
        
        # 回调函数
        self.on_player_joined: Optional[Callable[[Player], None]] = None
        self.on_player_left: Optional[Callable[[str], None]] = None
        self.on_game_start: Optional[Callable[[], None]] = None
        self.on_players_list: Optional[Callable[[List[dict]], None]] = None  # 新增：收到玩家列表回调
        self._sync_callback: Optional[Callable[[dict], None]] = None  # 游戏同步消息回调
    
    @property
    def max_players(self) -> int:
        return 4
    
    @property
    def player_count(self) -> int:
        with self._lock:
            return len([p for p in self.players if p.connected])
    
    def add_player(self, player_id: str, name: str, ip: str) -> bool:
        """添加玩家"""
        if self.player_count >= self.max_players:
            return False
        
        with self._lock:
            player = Player(player_id, name, ip, last_ping=time.time())
            self.players.append(player)
        
        if self.on_player_joined:
            self.on_player_joined(player)
        
        return True
    
    def remove_player(self, player_id: str):
        """移除玩家"""
        with self._lock:
            for p in self.players:
                if p.player_id == player_id:
                    p.connected = False
                    break
        
        if self.on_player_left:
            self.on_player_left(player_id)
    
    def get_player(self, player_id: str) -> Optional[Player]:
        """获取玩家"""
        with self._lock:
            for p in self.players:
                if p.player_id == player_id:
                    return p
        return None
    
    def get_all_players(self) -> List[Player]:
        """获取所有玩家"""
        with self._lock:
            return [p for p in self.players if p.connected]
    
    def start_as_host(self, host_port: int = 8888):
        """作为房主启动"""
        self.is_host = True
        self._host_port = host_port
        self._running = True
        
        # 添加房主自己，使用唯一的 player_id
        host_player_id = str(uuid.uuid4())[:8]
        self.add_player(host_player_id, 'Host', '127.0.0.1')
        
        self._server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self._server_thread.start()
    
    def connect_to_host(self, host_ip: str, host_port: int = 8888, player_name: str = "Player"):
        """连接到房主"""
        self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client_socket.settimeout(10)
        
        try:
            self._client_socket.connect((host_ip, host_port))
            self._running = True
            
            # 发送加入请求
            join_msg = {
                'type': 'join',
                'player_id': str(uuid.uuid4()),
                'name': player_name,
            }
            self._client_socket.send(json.dumps(join_msg).encode('utf-8'))
            
            self._client_thread = threading.Thread(target=self._client_loop, daemon=True)
            self._client_thread.start()
            
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def _server_loop(self):
        """服务器循环 - 接受连接"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self._host_port))
        server.listen(3)
        server.settimeout(1.0)
        
        while self._running:
            try:
                client, addr = server.accept()
                threading.Thread(target=self._handle_client, args=(client, addr), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                break
        
        server.close()
    
    def _handle_client(self, client: socket.socket, addr):
        """处理客户端连接"""
        try:
            data = client.recv(4096)
            msg = json.loads(data.decode('utf-8'))
            
            if msg.get('type') == 'join':
                player_id = msg['player_id']
                name = msg['name']
                
                if self.add_player(player_id, name, addr[0]):
                    # 发送确认 + 当前玩家列表
                    current_players = [{'player_id': p.player_id, 'name': p.name} for p in self.get_all_players()]
                    response = {
                        'type': 'join_ok',
                        'room_id': self.room_id,
                        'player_id': player_id,
                        'players': current_players
                    }
                    client.send(json.dumps(response).encode('utf-8'))
                    
                    # 保存客户端连接
                    with self._lock:
                        self._clients.append((client, addr))
                    
                    # 广播给其他玩家
                    self._broadcast({'type': 'player_joined', 'player_id': player_id, 'name': name, 'ip': addr[0]})
                else:
                    response = {'type': 'join_fail', 'reason': '房间已满'}
                    client.send(json.dumps(response).encode('utf-8'))
                    client.close()
        except Exception as e:
            print(f"处理客户端错误: {e}")
            client.close()
    
    def _broadcast(self, msg: dict):
        """广播消息给所有客户端"""
        data = json.dumps(msg).encode('utf-8')
        with self._lock:
            dead_clients = []
            for client, addr in self._clients:
                try:
                    client.send(data)
                except Exception as e:
                    print(f"[Room] 发送失败 -> {addr}: {e}")
                    dead_clients.append((client, addr))
            # 清理断开的客户端
            for client in dead_clients:
                self._clients.remove(client)

    def broadcast_game_start(self):
        """广播游戏开始消息给所有客户端"""
        if self.is_host:
            self._broadcast({'type': 'game_start'})
            print(f"[Room] 已广播 game_start")
    
    def _client_loop(self):
        """客户端循环 - 接收消息"""
        buffer = ""  # 缓冲区，处理粘包
        while self._running:
            try:
                data = self._client_socket.recv(4096)
                if not data:
                    break
                buffer += data.decode('utf-8')
                
                # 逐个解析 JSON 消息（处理粘包）
                while buffer:
                    try:
                        # 尝试解析一条完整的 JSON
                        decoder = json.JSONDecoder()
                        msg, end_idx = decoder.raw_decode(buffer)
                        buffer = buffer[end_idx:].lstrip()
                        self._handle_server_message(msg)
                    except json.JSONDecodeError:
                        # 数据不完整，等待更多数据
                        break
            except socket.timeout:
                continue
            except ConnectionResetError:
                print("[Room:Client] 连接被重置（正常，游戏可能已开始）")
                break
            except Exception as e:
                print(f"[Room:Client] 错误: {e}")
                break
        
        self._running = False
    
    def _handle_server_message(self, msg: dict):
        """处理服务器消息"""
        msg_type = msg.get('type')
        print(f"[Room:Client] 原始消息: {msg}")  # 调试
        
        if msg_type == 'game_start':
            print("[Room:Client] 收到 game_start")
            if self.on_game_start:
                self.on_game_start()
        elif msg_type == 'player_joined':
            player = Player(msg['player_id'], msg['name'], msg['ip'])
            self.add_player(player.player_id, player.name, player.ip)
        elif msg_type == 'join_ok':
            # 收到房间玩家列表
            if self.on_players_list:
                self.on_players_list(msg.get('players', []))
        else:
            # 其他消息类型，传递给游戏同步系统
            print(f"[Room:Client] 传递消息给同步系统: type={msg_type}")
            if hasattr(self, '_sync_callback') and self._sync_callback:
                self._sync_callback(msg)
    
    def send_to_all(self, msg: dict):
        """发送消息给所有玩家（广播）"""
        self._broadcast(msg)
    
    def send_to_host(self, msg: dict):
        """发送消息给房主（客户端调用）"""
        if hasattr(self, '_client_socket') and self._client_socket:
            try:
                self._client_socket.send(json.dumps(msg).encode('utf-8'))
            except Exception as e:
                print(f"[Room] 发送消息给房主失败: {e}")
    
    def broadcast_to_all(self, msg: dict):
        """广播消息给所有客户端（仅房主使用）"""
        if self.is_host:
            self._broadcast(msg)
    
    def set_sync_callback(self, callback: Callable[[dict], None]):
        """设置游戏同步消息回调"""
        self._sync_callback = callback
    
    def close(self):
        """关闭连接"""
        self._running = False
        if hasattr(self, '_client_socket'):
            self._client_socket.close()
