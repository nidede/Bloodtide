"""
UI 基础组件
"""
import pygame
from core.config import Color, get_font


class MenuButton:
    """菜单按钮"""
    
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.font = get_font(28)
    
    def draw(self, surface, mouse_pos):
        is_hover = self.rect.collidepoint(mouse_pos)
        bg_color = self.hover_color if is_hover else self.color
        
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, Color.WHITE, self.rect, 2, border_radius=10)
        
        text_surf = self.font.render(self.text, True, Color.WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed
