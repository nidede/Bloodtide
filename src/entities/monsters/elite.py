"""精英怪物 - 比普通怪更强"""
import math
import pygame
from core.config import Color
from .base import BaseMonster


class EliteMonster(BaseMonster):
    """精英怪物 - 高属性"""
    
    TYPE = "elite"
    HP_BASE = 80
    HP_PER_LVL = 25
    SPEED_BASE = 90
    SPEED_PER_LVL = 3
    DAMAGE_BASE = 12
    DAMAGE_PER_LVL = 4
    SIZE = 25
    COLOR = Color.PURPLE
    XP_BASE = 40
    XP_PER_LVL = 8
    MIN_WAVE = 3
    SPAWN_WEIGHT = 0.10
    
    def draw(self, surface, cam_x=0, cam_y=0):
        """绘制为六边形（表示精英）"""
        color = Color.WHITE if self.flash_timer > 0 else self.color
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        
        points = []
        for i in range(6):
            a = math.pi / 3 * i - math.pi / 6
            points.append((int(sx + self.size * math.cos(a)),
                          int(sy + self.size * math.sin(a))))
        pygame.draw.polygon(surface, color, points)
        pygame.draw.polygon(surface, Color.WHITE, points, 2)
        
        self._draw_health_bar(surface, sx, sy)
