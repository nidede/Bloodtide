"""远程怪物 - 保持距离射击"""
import math
import pygame
from core.config import Color
from .base import BaseMonster


class RangedMonster(BaseMonster):
    """远程怪物 - 保持距离攻击"""
    
    TYPE = "ranged"
    HP_BASE = 15
    HP_PER_LVL = 8
    SPEED_BASE = 60
    SPEED_PER_LVL = 2
    DAMAGE_BASE = 8
    DAMAGE_PER_LVL = 2
    SIZE = 18
    COLOR = Color.PINK
    XP_BASE = 15
    XP_PER_LVL = 4
    MIN_WAVE = 2
    SPAWN_WEIGHT = 0.15
    ATTACK_COOLDOWN = 1.0  # 攻击间隔（秒）
    PROJECTILE_SPEED = 4  # 子弹速度 

    def attack(self, player, projectiles):
        """发射子弹攻击玩家"""
        if not self.can_attack():
            return
        
        angle = math.atan2(player.y - self.y, player.x - self.x)
        from entities.projectiles import Projectile
        proj = Projectile(
            self.x, self.y, angle,
            self.damage, self.PROJECTILE_SPEED,
            0, 1, 0, 0, self  # self 作为 owner
        )
        proj.size = 6
        proj.color = Color.RED  # 敌人子弹为红色
        projectiles.append(proj)
        self.attack_cooldown = self.ATTACK_COOLDOWN
    
    def draw(self, surface, cam_x=0, cam_y=0):
        """绘制为菱形（表示远程）"""
        color = Color.WHITE if self.flash_timer > 0 else self.color
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        
        points = [(sx, sy - self.size), (sx + self.size, sy),
                  (sx, sy + self.size), (sx - self.size, sy)]
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, Color.WHITE, points, 1)
        
        eye_offset = self.size // 3
        pygame.draw.circle(surface, Color.WHITE, (sx - eye_offset, sy - 2), 3)
        pygame.draw.circle(surface, Color.WHITE, (sx + eye_offset, sy - 2), 3)
        
        self._draw_health_bar(surface, sx, sy)
