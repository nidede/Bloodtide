"""怪物基类 - 所有怪物的父类"""
import math
import random
import pygame
from core.config import Color, MonsterConfig


class BaseMonster:
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
    
    def __init__(self, level, x, y):
        self.monster_type = self.TYPE
        self.level = max(1, level)
        self.x = x
        self.y = y
        self.attack_cooldown = 0
        self.flash_timer = 0
        
        # 根据等级计算属性
        self.max_hp = self.HP_BASE + self.level * self.HP_PER_LVL
        self.speed = self.SPEED_BASE + self.level * self.SPEED_PER_LVL
        self.damage = self.DAMAGE_BASE + self.level * self.DAMAGE_PER_LVL
        self.size = self.SIZE
        self.color = self.COLOR
        self.xp_value = self.XP_BASE + self.level * self.XP_PER_LVL
        self.hp = self.max_hp
    
    def update(self, player, dt):
        """更新怪物状态 - 可被子类重写"""
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

    def attack(self, player, projectiles):
        """发射攻击 - 子类可重写"""
        pass  # 默认无远程攻击
    
    def take_damage(self, damage, is_crit, particles, floating_texts):
        """受到伤害 - 可被子类重写"""
        self.hp -= damage
        self.flash_timer = MonsterConfig.FLASH_FRAMES
        
        color = Color.GOLD if is_crit else Color.WHITE
        size = 28 if is_crit else 20
        text = f"{damage}!" if is_crit else str(damage)
        floating_texts.append(FloatingText(
            self.x + random.randint(-10, 10),
            self.y - self.size - 5,
            text, color, size
        ))
        
        hit_color = Color.YELLOW if is_crit else Color.WHITE
        count = 10 if is_crit else 5
        for _ in range(count):
            particles.append(Particle(self.x, self.y, hit_color, speed=120, lifetime=0.25))
    
    @property
    def dead(self):
        return self.hp <= 0
    
    def collides_with_player(self, player):
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist < self.size + player.size
    
    def draw(self, surface, cam_x=0, cam_y=0):
        """绘制怪物 - 子类需要重写此方法"""
        color = Color.WHITE if self.flash_timer > 0 else self.color
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        
        # 默认绘制为圆形
        pygame.draw.circle(surface, color, (sx, sy), self.size)
        pygame.draw.circle(surface, Color.WHITE, (sx, sy), self.size, 1)
        
        # 绘制血条
        self._draw_health_bar(surface, sx, sy)
    
    def _draw_health_bar(self, surface, sx, sy):
        """绘制血条"""
        if self.hp < self.max_hp:
            bw = self.size * 2
            bh = 4
            bx = int(sx - bw // 2)
            by = sy - self.size - 10
            pygame.draw.rect(surface, Color.DARK_GRAY, (bx, by, bw, bh))
            ratio = max(0, self.hp / self.max_hp)
            pygame.draw.rect(surface, Color.RED, (bx, by, int(bw * ratio), bh))
    
    @classmethod
    def get_spawn_info(cls):
        """获取生成信息，用于波次生成"""
        return {
            "type": cls.TYPE,
            "min_wave": cls.MIN_WAVE,
            "spawn_weight": cls.SPAWN_WEIGHT,
        }


# 延迟导入避免循环依赖
from ui.effects import Particle, FloatingText
