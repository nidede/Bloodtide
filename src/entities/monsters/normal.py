"""普通怪物 - 最基础的敌人"""
import pygame
from core.config import Color
from .base import BaseMonster


class NormalMonster(BaseMonster):
    """普通怪物 - 均衡型敌人"""
    
    TYPE = "normal"
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
    SPAWN_WEIGHT = 0.45
    
    def draw(self, surface, cam_x=0, cam_y=0):
        """绘制为圆形"""
        color = Color.WHITE if self.flash_timer > 0 else self.color
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        
        pygame.draw.circle(surface, color, (sx, sy), self.size)
        pygame.draw.circle(surface, Color.WHITE, (sx, sy), self.size, 1)
        
        self._draw_health_bar(surface, sx, sy)
