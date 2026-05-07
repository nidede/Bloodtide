"""
视觉特效 - 粒子、浮动文字
"""
import math
import random
import pygame
from core.config import Color, get_font, ParticleConfig


def pygame_draw_circle(surface, color, x, y, radius):
    """安全绘制圆形，确保参数合法"""
    pygame.draw.circle(surface, color, (int(x), int(y)), max(1, int(radius)))


class Particle:
    """粒子特效"""

    def __init__(self, x, y, color, speed=None, lifetime=None, size=None):
        """speed: 像素/秒, lifetime: 秒"""
        self.x = x
        self.y = y
        self.color = color
        speed = speed if speed is not None else ParticleConfig.DEFAULT_SPEED
        lifetime = lifetime if lifetime is not None else ParticleConfig.DEFAULT_LIFETIME
        size = size if size is not None else ParticleConfig.DEFAULT_SIZE
        angle = random.uniform(0, 2 * math.pi)
        spd = speed / 60
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        # 帧率无关衰减：decay_per_frame^(dt*60) 等价于每帧衰减在60FPS下的效果
        decay = ParticleConfig.VELOCITY_DECAY ** (dt * 60)
        self.vx *= decay
        self.vy *= decay
        self.lifetime -= dt

    def draw(self, surface, cam_x=0, cam_y=0):
        alpha = max(0, self.lifetime / self.max_lifetime)
        r = max(1, int(self.size * alpha))
        color = tuple(min(255, int(c * alpha)) for c in self.color)
        pygame_draw_circle(surface, color, int(self.x - cam_x), int(self.y - cam_y), r)

    @property
    def dead(self):
        return self.lifetime <= 0


class FloatingText:
    """浮动伤害/经验数字"""

    def __init__(self, x, y, text, color, size=None, lifetime=None):
        """lifetime: 秒"""
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        lifetime = lifetime if lifetime is not None else ParticleConfig.FLOATING_TEXT_LIFETIME
        size = size if size is not None else ParticleConfig.FLOATING_TEXT_SIZE
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.font = get_font(size)
        self.vy = ParticleConfig.FLOATING_TEXT_SPEED

    def update(self, dt):
        self.y += self.vy * dt
        self.lifetime -= dt

    def draw(self, surface, cam_x=0, cam_y=0):
        alpha = max(0, self.lifetime / self.max_lifetime)
        color = tuple(min(255, int(c * alpha)) for c in self.color)
        text_surf = self.font.render(self.text, True, color)
        rect = text_surf.get_rect(center=(int(self.x - cam_x), int(self.y - cam_y)))
        surface.blit(text_surf, rect)

    @property
    def dead(self):
        return self.lifetime <= 0



