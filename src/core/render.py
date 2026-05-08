"""渲染工具函数"""
import pygame


def pygame_draw_circle(surface, color, x, y, radius):
    """安全绘制圆形，确保参数合法"""
    pygame.draw.circle(surface, color, (int(x), int(y)), max(1, int(radius)))
