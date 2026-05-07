"""快速怪物 - 速度快但血量低"""
import pygame
from core.config import Color
from .base import BaseMonster


class FastMonster(BaseMonster):
    """快速怪物 - 高速度低血量"""
    
    TYPE = "fast"
    HP_BASE = 12
    HP_PER_LVL = 6
    SPEED_BASE = 150
    SPEED_PER_LVL = 5
    DAMAGE_BASE = 4
    DAMAGE_PER_LVL = 1.5
    SIZE = 12
    COLOR = Color.CYAN
    XP_BASE = 12
    XP_PER_LVL = 3
    MIN_WAVE = 1
    SPAWN_WEIGHT = 0.25
    
    def draw(self, surface, cam_x=0, cam_y=0):
        """绘制为小圆形（表示速度快）"""
        color = Color.WHITE if self.flash_timer > 0 else self.color
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        
        # 快速怪物绘制为椭圆形表示运动感
        pygame.draw.ellipse(surface, color, (sx - self.size, sy - self.size // 2, self.size * 2, self.size))
        pygame.draw.ellipse(surface, Color.WHITE, (sx - self.size, sy - self.size // 2, self.size * 2, self.size), 1)
        
        self._draw_health_bar(surface, sx, sy)
