"""
怪物生成器 - 波次生成、刷新逻辑
"""
import math
import random
from core.config import ScreenConfig, WaveConfig, SpawnerConfig, WORLD_WIDTH, WORLD_HEIGHT
from entities.combatants.monsters import MonsterRegistry, Monster


class Spawner:
    """怪物生成器"""

    def __init__(self):
        self.wave = 1
        self.wave_timer = 0
        self.spawn_timer = 0
        self.spawn_interval = WaveConfig.INITIAL_SPAWN_INTERVAL
        self.monsters_per_wave = WaveConfig.INITIAL_MONSTERS
        self.monsters_spawned = 0
        self.wave_complete = False
        self._prev_wave = 1

    def update(self, dt, monsters, cam_x, cam_y):
        """更新波次和生成逻辑，返回 (spawned_list, wave_complete, wave_changed)"""
        spawned = []
        wave_changed = False
        self.wave_timer += dt
        
        if self.wave_complete:
            if self.wave_timer >= WaveConfig.WAVE_COOLDOWN:
                self._start_next_wave()
                wave_changed = True
            return spawned, self.wave_complete, wave_changed

        if self.monsters_spawned >= self.monsters_per_wave:
            if len(monsters) == 0:
                self.wave_complete = True
            return spawned, self.wave_complete, wave_changed

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            m = self._spawn_monster(cam_x, cam_y)
            if m:
                spawned.append(m)
            self.monsters_spawned += 1
            self.spawn_timer = self.spawn_interval

        return spawned, self.wave_complete, wave_changed

    def spawn_boss(self, wave, cam_x, cam_y):
        """生成 Boss - 在玩家附近固定距离处"""
        angle = random.uniform(0, 2 * math.pi)
        dist = SpawnerConfig.BOSS_SPAWN_DISTANCE
        center_x = cam_x + ScreenConfig.WIDTH // 2
        center_y = cam_y + ScreenConfig.HEIGHT // 2
        x = center_x + math.cos(angle) * dist + random.randint(-SpawnerConfig.SPAWN_OFFSET_RANGE, SpawnerConfig.SPAWN_OFFSET_RANGE)
        y = center_y + math.sin(angle) * dist + random.randint(-SpawnerConfig.SPAWN_OFFSET_RANGE, SpawnerConfig.SPAWN_OFFSET_RANGE)
        return Monster("boss", wave, x, y)

    def _start_next_wave(self):
        """开始下一波"""
        self.wave += 1
        self.wave_timer = 0
        self.spawn_timer = 0
        self.monsters_spawned = 0
        self.wave_complete = False
        self.spawn_interval = max(
            WaveConfig.MIN_SPAWN_INTERVAL,
            WaveConfig.INITIAL_SPAWN_INTERVAL - (self.wave - 1) * WaveConfig.SPAWN_INTERVAL_DECREASE
        )
        self.monsters_per_wave = WaveConfig.INITIAL_MONSTERS + (self.wave - 1) * WaveConfig.MONSTERS_PER_WAVE
        self._prev_wave = self.wave

    def _spawn_monster(self, cam_x, cam_y):
        """在屏幕边缘随机位置生成怪物"""
        candidates, weights = MonsterRegistry.get_spawn_candidates(self.wave)
        if not candidates:
            return None
        
        monster_type = random.choices(candidates, weights=weights, k=1)[0]
        
        side = random.randint(0, 3)
        margin = SpawnerConfig.SPAWN_MARGIN
        if side == 0:
            x = cam_x + random.randint(0, ScreenConfig.WIDTH)
            y = cam_y - margin
        elif side == 1:
            x = cam_x + random.randint(0, ScreenConfig.WIDTH)
            y = cam_y + ScreenConfig.HEIGHT + margin
        elif side == 2:
            x = cam_x - margin
            y = cam_y + random.randint(0, ScreenConfig.HEIGHT)
        else:
            x = cam_x + ScreenConfig.WIDTH + margin
            y = cam_y + random.randint(0, ScreenConfig.HEIGHT)
        
        return Monster(monster_type, self.wave, x, y)
