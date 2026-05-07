"""
摄像机系统 - 管理世界坐标到屏幕坐标的转换
"""
import pygame
from core.config import ScreenConfig, WORLD_WIDTH, WORLD_HEIGHT


class Camera:
    """摄像机，将玩家保持在屏幕中心"""

    def __init__(self, player):
        self.player = player

    @property
    def offset_x(self):
        """世界 → 屏幕的 X 偏移"""
        return self.player.x - ScreenConfig.WIDTH // 2

    @property
    def offset_y(self):
        """世界 → 屏幕的 Y 偏移"""
        return self.player.y - ScreenConfig.HEIGHT // 2

    def world_to_screen(self, x, y):
        """将世界坐标转换为屏幕坐标"""
        return x - self.offset_x, y - self.offset_y

    def screen_to_world(self, x, y):
        """将屏幕坐标转换为世界坐标（用于鼠标点击等）"""
        return x + self.offset_x, y + self.offset_y
