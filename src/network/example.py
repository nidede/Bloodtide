"""
网络模块使用示例
展示如何在游戏主循环中集成局域网多人功能
"""

from network import DiscoveryService, RoomManager, GameSync, RoomInfo


def example_as_host():
    """作为房主创建房间"""
    # 1. 创建房间管理器
    room = RoomManager(is_host=True)
    
    # 2. 设置回调
    def on_player_joined(player):
        print(f"玩家加入: {player.name}")
    
    def on_player_left(player_id):
        print(f"玩家离开: {player_id}")
    
    def on_game_start():
        print("所有玩家准备，开始游戏!")
    
    room.on_player_joined = on_player_joined
    room.on_player_left = on_player_left
    room.on_game_start = on_game_start
    
    # 3. 启动房间（监听端口 8888）
    room.start_as_host(host_port=8888)
    
    # 4. 启动房间广播（供其他玩家发现）
    discovery = DiscoveryService(player_name="Host")
    discovery.start_broadcast(
        room_id=room.room_id,
        player_count=room.player_count,
        max_players=room.max_players
    )
    
    print(f"房间已创建! ID: {room.room_id}")
    return room, discovery


def example_as_client():
    """作为客户端加入房间"""
    # 1. 创建发现服务
    discovery = DiscoveryService(player_name="Player")
    
    # 2. 设置房间更新回调
    def on_rooms_updated(rooms):
        print(f"发现 {len(rooms)} 个房间:")
        for r in rooms:
            print(f"  - {r.host_name}: {r.player_count}/{r.max_players} 人")
    
    discovery.on_rooms_updated = on_rooms_updated
    discovery.start_listening()
    
    # 3. 请求房间列表
    discovery.request_room_list()
    
    # 4. 等待用户选择房间
    import time
    time.sleep(3)  # 等待发现结果
    
    rooms = discovery.get_rooms()
    if rooms:
        # 选择第一个房间加入
        target_room = rooms[0]
        print(f"正在加入 {target_room.host_name} 的房间...")
        
        room = RoomManager(is_host=False)
        if room.connect_to_host(target_room.host_ip, player_name="Player"):
            print("加入成功!")
            return room
    
    return None


def example_in_game_loop(game_sync: GameSync, room: RoomManager):
    """游戏循环中的同步示例"""
    
    # 每帧获取本地玩家输入
    def get_local_input():
        # 从游戏引擎获取
        return {
            'left': False,
            'right': False,
            'up': False,
            'down': False,
            'dash': False,
        }
    
    # 广播本地玩家状态（作为房主）
    if room.is_host:
        # 每隔几帧广播一次（降低网络负载）
        if game_sync.frame % 3 == 0:
            # state = game_sync.pack_game_state(player, wave, monsters)
            # room.send_to_all({'type': 'game_state', 'data': state})
            pass
    
    # 更新远程玩家状态
    for player_id in game_sync.remote_states:
        state = game_sync.get_interpolated_state(player_id)
        if state and game_sync.on_remote_player_update:
            game_sync.on_remote_player_update(player_id, state)


# ============ UI 集成提示 ============
"""
在 UI 中添加多人选项:

1. 主菜单增加 "多人游戏" 按钮
2. 多人菜单包含:
   - "创建房间" -> example_as_host()
   - "加入房间" -> 显示房间列表 -> example_as_client()
3. 游戏结束后显示 "返回大厅" 而不是直接结束

在 core/main.py 的 MenuScreen 中添加多人按钮，
在 Game 类中添加网络相关的状态和方法。
"""
