"""
士兵角色 - 默认角色，均衡型
"""
import math
import pygame
from core.config import Color, PlayerConfig, WORLD_WIDTH, WORLD_HEIGHT
from core.render import pygame_draw_circle
from .base import Character


class Soldier(Character):
    """士兵角色 - 均衡型，升级自动加血量和防御"""
    speed = 200
    max_hp = 100

    UPG_THORNS = 5

    def __init__(self):
        super().__init__(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
        self.thorns = 0

    def _on_hit_by(self, attacker, damage):
        """反伤 - 对攻击者造成 thorns 点伤害（不走武器，不触发 ON_DEAL_DAMAGE）"""
        if attacker and self.thorns > 0:
            from entities.weapons.base import DamageResult
            actual, _ = attacker.take_damage(self.thorns, attacker=self)
            if actual > 0:
                return [DamageResult(attacker, actual)]
        return []

    def _apply_thorns(self, weapon):
        self.thorns += self.UPG_THORNS

    # 士兵专属升级：在基类通用升级基础上追加反伤
    GENERAL_UPGRADES = Character.GENERAL_UPGRADES + [
        ("thorns", "反伤", f"敌人受伤 +{UPG_THORNS}", Color.ORANGE, lambda p, w: p._apply_thorns(w)),
    ]

    # 注意：thorns 可叠加（每次 +5），不设上限

    def on_level_up(self):
        """士兵升级奖励：+10 最大生命，+1 防御"""
        self.max_hp += 10
        self.hp = min(self.max_hp, self.hp + 10)
        self.defense += 1

    def handle_input(self, keys):
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071
        return dx, dy

    def update(self, keys, monsters, dt):
        dx, dy = self.handle_input(keys)
        total_speed = (self.speed + self.dash_speed) * self.get_speed_multiplier()
        self.x += dx * total_speed * dt
        self.y += dy * total_speed * dt

        # 更新朝向
        if dx > 0:
            self.facing_right = True
        elif dx < 0:
            self.facing_right = False

        # 冲刺衰减（帧率无关）
        self.dash_speed *= PlayerConfig.DASH_DURATION_DECAY ** (dt * 60)
        if self.dash_speed < 10:
            self.dash_speed = 0

        self._clamp_position()

        # 自动瞄准最近敌人
        nearest = self._find_nearest(monsters)
        if nearest:
            self.angle = math.atan2(nearest.y - self.y, nearest.x - self.x)

        self._update_timers(dt)

    def try_dash(self):
        if not self.has_dash:
            return False
        if self.dash_cooldown > 0 or self.dash_speed > 0:
            return False
        self.dash_speed = PlayerConfig.DASH_SPEED_BOOST
        self.dash_cooldown = PlayerConfig.DASH_COOLDOWN_FRAMES / 60
        return True

    def draw(self, surface, cam_x=0, cam_y=0):
        if self.invincible_timer > 0 and int(self.invincible_timer * 15) % 2 == 0:
            return
        sx, sy = self.x - cam_x, self.y - cam_y
        pygame_draw_circle(surface, Color.BLUE, sx, sy, self.size)
        pygame_draw_circle(surface, (80, 140, 255), sx, sy, self.size - 4)
        end_x = sx + math.cos(self.angle) * (self.size + 8)
        end_y = sy + math.sin(self.angle) * (self.size + 8)
        pygame.draw.line(surface, Color.YELLOW,
                         (int(sx), int(sy)),
                         (int(end_x), int(end_y)), 3)
        # 绘制状态效果
        for eff in self.status_effects:
            eff.draw(surface, int(sx), int(sy), self.size)
