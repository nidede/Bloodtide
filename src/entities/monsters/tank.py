"""坦克怪物 - 血量高但速度慢"""
import pygame
from core.config import Color
from .base import BaseMonster


class TankMonster(BaseMonster):
    """坦克怪物 - 高血量低速度"""
    
    TYPE = "tank"
    HP_BASE = 50
    HP_PER_LVL = 20
    SPEED_BASE = 42
    SPEED_PER_LVL = 2
    DAMAGE_BASE = 8
    DAMAGE_PER_LVL = 3
    SIZE = 22
    COLOR = Color.ORANGE
    XP_BASE = 18
    XP_PER_LVL = 5
    MIN_WAVE = 1
    SPAWN_WEIGHT = 0.15
    
    def draw(self, surface, cam_x=0, cam_y=0):
        """绘制为方形（表示坦克）"""
        color = Color.WHITE if self.flash_timer > 0 else self.color
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        
        rect = pygame.Rect(sx - self.size, sy - self.size, self.size * 2, self.size * 2)
        pygame.draw.rect(surface, color, rect)
        pygame.draw.rect(surface, Color.WHITE, rect, 2)
        
        self._draw_health_bar(surface, sx, sy)
