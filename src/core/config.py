"""
游戏全局配置 - 所有常量、颜色、参数集中管理，方便调整和扩展
"""
import pygame

# ============ 游戏基础 ============
class GameConfig:
    FPS = 60
    TITLE = "打怪升级 - Monster Slayer"

# 保持向后兼容
FPS = GameConfig.FPS
GAME_TITLE = GameConfig.TITLE


# ============ 窗口 ============
class ScreenConfig:
    WIDTH = 1200
    HEIGHT = 800
    FULLSCREEN = False
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800


# ============ 世界地图 ============
class WorldConfig:
    WIDTH = 3000
    HEIGHT = 3000

# 保持向后兼容
WORLD_WIDTH = WorldConfig.WIDTH
WORLD_HEIGHT = WorldConfig.HEIGHT

# ============ 颜色 ============
class Color:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (220, 50, 50)
    GREEN = (50, 200, 50)
    BLUE = (50, 100, 220)
    YELLOW = (240, 220, 40)
    PURPLE = (160, 50, 220)
    ORANGE = (240, 150, 30)
    DARK_GRAY = (40, 40, 40)
    LIGHT_GRAY = (180, 180, 180)
    DARK_GREEN = (30, 120, 30)
    DARK_BLUE = (30, 60, 120)
    CYAN = (50, 200, 220)
    PINK = (240, 100, 150)
    DARK_RED = (150, 30, 30)
    GOLD = (255, 215, 0)
    BG_COLOR = (20, 20, 30)
    GRID_COLOR = (30, 30, 45)
    HUD_BG = (15, 15, 25)
    CARD_BG = (60, 60, 80)
    CARD_BG_HOVER = (80, 80, 110)


# ============ 字体 ============
import os
import sys

_FONT_CACHE = {}

def _get_bundle_font_path():
    """获取捆绑字体路径"""
    # 方式1: 开发环境 - 从 resources/fonts 获取
    current_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(current_dir)
    resources_dir = os.path.join(src_dir, "resources")
    fonts_dir = os.path.join(resources_dir, "fonts")
    
    if os.path.exists(fonts_dir):
        for filename in os.listdir(fonts_dir):
            if filename.endswith(('.ttf', '.ttc', '.otf')):
                return os.path.join(fonts_dir, filename)
    
    # 方式2: 打包后环境 - 从 _internal/resources/fonts 获取
    if hasattr(sys, '_MEIPASS'):
        bundle_fonts = os.path.join(sys._MEIPASS, 'resources', 'fonts')
        if os.path.exists(bundle_fonts):
            for filename in os.listdir(bundle_fonts):
                if filename.endswith(('.ttf', '.ttc', '.otf')):
                    return os.path.join(bundle_fonts, filename)
    
    return None

def get_font(size):
    """获取字体，带缓存和跨平台回退"""
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    
    font = None
    
    # 优先使用捆绑字体
    bundle_font_path = _get_bundle_font_path()
    if bundle_font_path:
        try:
            f = pygame.font.Font(bundle_font_path, size)
            f.render("测试", True, (255, 255, 255))
            font = f
        except Exception:
            pass
    
    # 回退到系统字体
    if font is None:
        candidates = [
            "microsoftyahei", "simhei", "pingfang sc",
            "noto sans cjk sc", "wenquanyi micro hei",
            "arial", None,
        ]
        for name in candidates:
            try:
                f = pygame.font.SysFont(name, size)
                f.render("测试", True, (255, 255, 255))
                font = f
                break
            except Exception:
                continue
    
    # 最终回退
    if font is None:
        font = pygame.font.Font(None, size)
    
    _FONT_CACHE[size] = font
    return font


# ============ 玩家初始参数 ============
class PlayerConfig:
    SIZE = 20
    SPEED = 210  # 像素/秒（原3.5像素/帧 × 60帧）
    MAX_HP = 100
    ATTACK = 15
    DEFENSE = 0
    CRIT_CHANCE = 0.05
    CRIT_DAMAGE = 1.5
    LIFE_STEAL = 0.0
    REGEN = 0
    XP_MULTIPLIER = 1.0
    THORNS = 0
    DASH_SPEED_BOOST = 720  # 像素/秒（原12像素/帧 × 60帧）
    DASH_DURATION_DECAY = 0.85
    DASH_COOLDOWN_FRAMES = 180  # 帧（转换为秒：/60）
    INVINCIBLE_FRAMES = 20  # 帧（转换为秒：/60）


# ============ 怪物参数 ============
class MonsterConfig:
    ATTACK_COOLDOWN = 0.67  # 秒（原40帧/60）
    FLASH_FRAMES = 0.1  # 秒（原6帧/60）


# ============ 波次参数 ============
class WaveConfig:
    INITIAL_MONSTERS = 5
    MONSTERS_PER_WAVE = 3
    INITIAL_SPAWN_INTERVAL = 1.0  # 秒
    SPAWN_INTERVAL_DECREASE = 0.05  # 秒
    WAVE_COOLDOWN = 3.0  # 秒
    MIN_SPAWN_INTERVAL = 0.3  # 秒
    XP_TO_LEVEL_BASE = 50
    XP_TO_LEVEL_MULTIPLIER = 1.4


# ============ 粒子特效 ============
class ParticleConfig:
    # 基础参数
    DEFAULT_SPEED = 120  # 像素/秒
    DEFAULT_LIFETIME = 0.5  # 秒
    DEFAULT_SIZE = 3
    VELOCITY_DECAY = 0.96  # 速度衰减系数

    # 浮动文字
    FLOATING_TEXT_SPEED = -90  # 像素/秒（向上）
    FLOATING_TEXT_LIFETIME = 0.5  # 秒
    FLOATING_TEXT_SIZE = 20



# ============ 战斗系统 ============
class CombatConfig:
    # 怪物可见性检测
    MONSTER_VISIBLE_RANGE = 600  # 像素（屏幕外检测）

    # 远程怪物AI
    MELEE_RANGE = 250  # 像素（进入后撤退）
    OPTIMAL_RANGE = 400  # 像素（保持距离）
    DETECTION_RANGE = 1500  # 像素（检测玩家）
    RETREAT_SPEED_RATIO = 0.3  # 撤退时速度比例
    CHASE_SPEED_RATIO = 0.5  # 屏幕外追击速度比例

    # 死亡特效
    DEATH_PARTICLE_COUNT = 15  # 死亡粒子数量
    PLAYER_DEATH_PARTICLE_COUNT = 50
    PARTICLE_DEATH_SPEED = 240  # 死亡粒子速度
    PARTICLE_DEATH_LIFETIME = 0.42  # 秒
    PARTICLE_PLAYER_DEATH_SPEED = 360
    PARTICLE_PLAYER_DEATH_LIFETIME = 0.67
    HIT_PARTICLE_COUNT = 3  # 命中粒子数量
    HIT_PARTICLE_SPEED = 60
    HIT_PARTICLE_LIFETIME = 0.17


# ============ 怪物生成器 ============
class SpawnerConfig:
    BOSS_SPAWN_DISTANCE = 400  # Boss生成距离
    SPAWN_OFFSET_RANGE = 200  # 生成位置随机偏移
    SPAWN_MARGIN = 100  # 生成边距


# ============ 投射物 ============
class ProjectileConfig:
    DEFAULT_SIZE = 5
    TRAIL_LENGTH = 8
    DESPAWN_MARGIN = 200  # 边界外消失边距


# ============ 导弹投射物 ============
class MissileConfig:
    SIZE = 6
    MAX_LIFETIME = 3.0  # 秒
    EXPLOSION_PARTICLE_COUNT = 30
    EXPLOSION_PARTICLE_SPEED_MIN = 120
    EXPLOSION_PARTICLE_SPEED_MAX = 360
    EXPLOSION_PARTICLE_LIFETIME = 0.33  # 秒
    EXPLOSION_PARTICLE_SIZE = 4
    EXPLOSION_OFFSET_RATIO = 0.5  # 爆炸粒子偏移比例（相对于爆炸半径）
