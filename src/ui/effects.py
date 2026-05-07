"""
视觉特效 - 粒子、浮动文字、经验球
"""
import math
import random
import pygame
from core.config import Color, get_font, OrbConfig, ParticleConfig


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
        self.vx *= ParticleConfig.VELOCITY_DECAY
        self.vy *= ParticleConfig.VELOCITY_DECAY
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


class XPOrb:
    """经验球"""

    def __init__(self, x, y, value, is_magnet=False):
        self.x = x
        self.y = y
        self.value = value
        self.size = min(OrbConfig.MAX_SIZE, OrbConfig.BASE_SIZE + value // 20)
        self.alive = True
        self.bob_offset = random.uniform(0, math.pi * 2)
        self.is_magnet = is_magnet
        if is_magnet:
            self.size = OrbConfig.MAX_SIZE + 2

    def update(self, player, dt):
        """返回 (collected, is_magnet) 元组，dt: 秒"""
        dist = math.hypot(self.x - player.x, self.y - player.y)

        if self.is_magnet:
            magnet_range = OrbConfig.BASE_MAGNET_RANGE * 3
            speed = ParticleConfig.ORB_MAGNET_SPEED
        else:
            if player.global_magnet:
                magnet_range = ParticleConfig.ORB_GLOBAL_MAGNET_RANGE
                speed = ParticleConfig.ORB_GLOBAL_MAGNET_SPEED
            else:
                boost = player.magnet_boost_range if player.magnet_boost_timer > 0 else 0
                magnet_range = OrbConfig.BASE_MAGNET_RANGE + player.magnet_range + boost
                speed = max(ParticleConfig.ORB_MIN_SPEED, ParticleConfig.ORB_BASE_SPEED * (1 - dist / magnet_range))

        if dist < magnet_range:
            dx = player.x - self.x
            dy = player.y - self.y
            if dist > 0:
                self.x += (dx / dist) * speed * dt
                self.y += (dy / dist) * speed * dt

        if dist < player.size + self.size:
            self.alive = False
            return True, self.is_magnet
        return False, False

    def draw(self, surface, frame, cam_x=0, cam_y=0):
        bob = math.sin(frame * 0.1 + self.bob_offset) * 2
        y = int(self.y + bob - cam_y)
        x = int(self.x - cam_x)
        s = self.size

        if self.is_magnet:
            pulse = abs(math.sin(frame * 0.15)) * 0.3 + 0.7
            r = int(s * pulse)
            pygame_draw_circle(surface, Color.GOLD, x, y, r)
            pygame_draw_circle(surface, (255, 200, 50), x, y, max(1, r - 2))
            for angle in [0, math.pi / 2, math.pi, math.pi * 1.5]:
                sx = x + int(math.cos(angle) * (r + 2))
                sy = y + int(math.sin(angle) * (r + 2))
                pygame_draw_circle(surface, Color.GOLD, sx, sy, 2)
        else:
            pygame_draw_circle(surface, Color.GREEN, x, y, s)
            pygame_draw_circle(surface, (150, 255, 150), x, y, max(1, s - 2))
