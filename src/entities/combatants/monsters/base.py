"""怪物基类 - 所有怪物的父类"""
import math
import pygame
from core.config import Color, MonsterConfig
from entities.combatants.base import CombatEntity


class MonsterRegistry:
    """怪物注册表"""

    _types = {}

    @classmethod
    def register(cls, monster_cls):
        """注册怪物类型（也可作为类装饰器使用）"""
        if hasattr(monster_cls, 'TYPE'):
            cls._types[monster_cls.TYPE] = monster_cls
        return monster_cls

    @classmethod
    def get(cls, monster_type):
        """获取怪物类型"""
        return cls._types.get(monster_type)

    @classmethod
    def get_spawn_candidates(cls, wave):
        """获取当前波次可生成的怪物列表"""
        candidates = []
        weights = []
        for monster_cls in cls._types.values():
            if monster_cls.TYPE != "boss" and monster_cls.MIN_WAVE <= wave:
                candidates.append(monster_cls.TYPE)
                weights.append(monster_cls.SPAWN_WEIGHT)
        return candidates, weights

    @classmethod
    def all_types(cls):
        """获取所有注册的怪物类型"""
        return list(cls._types.keys())


class BaseMonster(CombatEntity):
    """怪物基类
    
    每个怪物类型需要定义:
    - TYPE: 怪物类型标识
    - HP_BASE: 基础生命值
    - HP_PER_LVL: 每级生命值增长
    - SPEED_BASE: 基础速度 (像素/秒)
    - SPEED_PER_LVL: 每级速度增长
    - DAMAGE_BASE: 基础攻击力
    - DAMAGE_PER_LVL: 每级攻击力增长
    - SIZE: 体型大小
    - COLOR: 颜色
    - XP_BASE: 基础经验值
    - XP_PER_LVL: 每级经验值增长
    - MIN_WAVE: 出现的最低波次
    - SPAWN_WEIGHT: 生成权重
    
    攻击模式:
    - 近战怪物: attack() 默认实现碰撞+扣血, 返回 []
    - 远程怪物: 重写 attack() 返回 Projectile[]
    """
    
    TYPE = "base"
    HP_BASE = 20
    HP_PER_LVL = 10
    SPEED_BASE = 72
    SPEED_PER_LVL = 3
    DAMAGE_BASE = 5
    DAMAGE_PER_LVL = 2
    SIZE = 15
    COLOR = Color.RED
    XP_BASE = 10
    XP_PER_LVL = 3
    MIN_WAVE = 1
    SPAWN_WEIGHT = 1.0
    ATTACK_COOLDOWN = 0.67  # 近战攻击间隔（秒）
    weapon_class = None  # 子类必须显式指定武器类（如 EnemyMeleeWeapon、EnemyRifle）
    is_enemy = True
    
    def __init__(self, level, x, y):
        self.monster_type = self.TYPE
        self.level = max(1, level)
        
        # 根据等级计算属性
        self.max_hp = self.HP_BASE + self.level * self.HP_PER_LVL
        self.speed = self.SPEED_BASE + self.level * self.SPEED_PER_LVL
        self.damage = self.DAMAGE_BASE + self.level * self.DAMAGE_PER_LVL
        self.size = self.SIZE
        self.color = self.COLOR
        self.xp_value = self.XP_BASE + self.level * self.XP_PER_LVL

        super().__init__(x, y)

        self.attack_cooldown = 0
        self.weapon = self.weapon_class() if self.weapon_class else None
    
    def update(self, player, dt):
        """更新怪物状态 - 近战怪物默认追击玩家，远程怪物重写此方法"""
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += (dx / dist) * self.speed * dt
            self.y += (dy / dist) * self.speed * dt
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.flash_timer = max(0, self.flash_timer - dt)

    def can_attack(self):
        """检查是否可以攻击"""
        return self.attack_cooldown <= 0

    def attack(self, targets, particles, floating_texts, dt):
        """攻击目标 - 近战怪物默认实现碰撞伤害（委托武器），远程怪物重写返回 Projectile[]

        Args:
            targets: 目标列表（通常是玩家列表）
            particles: 粒子列表
            floating_texts: 浮动文字列表
            dt: 帧间隔时间

        Returns:
            list: 远程怪物返回 Projectile 列表，近战怪物返回空列表
        """
        for target in targets:
            if self.collides_with(target) and self.can_attack():
                self.weapon.deal_damage(target, targets, self, None, particles, floating_texts)
                self.attack_cooldown = self.ATTACK_COOLDOWN
                break
        return []

    def collides_with(self, target):
        dist = math.hypot(self.x - target.x, self.y - target.y)
        return dist < self.size + target.size
    
    def draw(self, surface, cam_x=0, cam_y=0):
        """绘制怪物 - 通用框架：闪白 + 坐标转换 + 形状 + 血条"""
        color = Color.WHITE if self.flash_timer > 0 else self.color
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        self._draw_shape(surface, color, sx, sy)
        self._draw_health_bar(surface, sx, sy)

    def _draw_shape(self, surface, color, sx, sy):
        """绘制怪物形状 - 子类重写此方法实现不同外观，默认圆形"""
        pygame.draw.circle(surface, color, (sx, sy), self.size)
        pygame.draw.circle(surface, Color.WHITE, (sx, sy), self.size, 1)
    
    @classmethod
    def get_spawn_info(cls):
        """获取生成信息，用于波次生成"""
        return {
            "type": cls.TYPE,
            "min_wave": cls.MIN_WAVE,
            "spawn_weight": cls.SPAWN_WEIGHT,
        }
