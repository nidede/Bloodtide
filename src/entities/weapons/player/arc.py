"""
电弧 - 链式闪电，范围多目标
"""
import math
import random
import pygame
from ..base import Weapon, Upgrade, DamageResult, UPGRADE_ONCE, EffectType, TriggerType
from core.config import Color


class Arc(Weapon):
    name = "电弧"
    desc = "连锁 | 链式电击"
    color = Color.PURPLE
    damage = 18
    fire_rate = 25
    # 电弧专属属性
    arc_range = 200          # 起始搜索范围
    chain_range = 120        # 跳跃范围（比搜索范围小）
    chain_count = 2          # 跳跃次数
    chain_damage_decay = 0.7 # 每次跳跃伤害衰减
    stun_duration = 0        # 眩晕时长（升级解锁）

    # 闪电视觉数据（每帧更新）
    _chain_points = []  # [(x, y), ...] 闪电路径点

    upgrades = [
        Upgrade("arc_damage", "高压电流", "电弧伤害 +5", Color.RED,
                lambda p, w: setattr(w, 'damage', w.damage + 5)),
        Upgrade("arc_chain", "链式传导", "跳跃次数 +1", Color.YELLOW,
                lambda p, w: setattr(w, 'chain_count', w.chain_count + 1)),
        Upgrade("arc_range", "扩弧", "搜索范围 +40", Color.BLUE,
                lambda p, w: (setattr(w, 'arc_range', w.arc_range + 40),
                              setattr(w, 'chain_range', w.chain_range + 25))),
        Upgrade("arc_stun", "电击麻痹", "命中眩晕1秒", Color.GREEN,
                lambda p, w: setattr(w, 'stun_duration', 1.0), UPGRADE_ONCE),
        Upgrade("arc_rapid", "快充", "攻速提升", Color.BLUE,
                lambda p, w: setattr(w, 'fire_rate', max(10, w.fire_rate - 3))),
    ]

    def attack(self, attacker, targets, dt=None):
        """电弧不需要发射投射物"""
        return []

    def _deal_damage(self, target, targets, attacker, proj):
        """电弧伤害"""
        actual, reaction = target.take_damage(self.damage, attacker=attacker)
        effects = []
        if self.stun_duration > 0:
            effects.append({"type": EffectType.STUN, "duration": self.stun_duration})
        return [DamageResult(target, actual, effects=effects)] + reaction

    def update(self, attacker, targets, dt):
        """电弧攻击：找范围内敌人，链式跳跃"""
        # 攻击冷却
        if not hasattr(self, '_cooldown'):
            self._cooldown = 0
        self._cooldown -= dt
        if self._cooldown > 0:
            # 不攻击时也保留上一帧的视觉（短暂残留）
            if hasattr(self, '_fade'):
                self._fade -= dt
                if self._fade <= 0:
                    self._chain_points = []
            return []

        if not targets:
            self._chain_points = []
            return []

        # 找范围内最近的敌人
        nearest = None
        min_dist = self.arc_range
        for t in targets:
            if t.dead:
                continue
            d = math.hypot(t.x - attacker.x, t.y - attacker.y)
            if d < min_dist:
                min_dist = d
                nearest = t

        if not nearest:
            self._chain_points = []
            return []

        self._cooldown = self.fire_rate / 60
        self._fade = 0.15  # 闪电残留时间

        # 链式攻击
        results = []
        hit_set = set()
        chain_targets = [nearest]
        hit_set.add(id(nearest))

        # 找跳跃目标
        for _ in range(self.chain_count):
            last = chain_targets[-1]
            best = None
            best_dist = self.chain_range
            for t in targets:
                if t.dead or id(t) in hit_set:
                    continue
                d = math.hypot(t.x - last.x, t.y - last.y)
                if d < best_dist:
                    best_dist = d
                    best = t
            if best:
                chain_targets.append(best)
                hit_set.add(id(best))
            else:
                break

        # 对每个目标造成伤害（递减）
        for i, target in enumerate(chain_targets):
            decay = self.chain_damage_decay ** i
            if i == 0:
                dmg_result = self.deal_damage(target, targets, attacker, None)
            else:
                # 跳跃目标：手动计算衰减伤害
                actual_dmg = max(1, int(self.damage * decay))
                actual, reaction = target.take_damage(actual_dmg, attacker=attacker)
                effects = []
                if self.stun_duration > 0:
                    effects.append({"type": EffectType.STUN, "duration": self.stun_duration})
                dmg_result = [DamageResult(target, actual, effects=effects)] + reaction
                # 触发攻击者效果
                if attacker and hasattr(attacker, 'trigger'):
                    for r in dmg_result:
                        if r.target is not None and r.damage > 0:
                            attacker.trigger(TriggerType.ON_DEAL_DAMAGE, target=r.target, damage=r.damage)
            results.extend(dmg_result)

        # 记录闪电路径（用于绘制）
        self._chain_points = [(attacker.x, attacker.y)]
        for t in chain_targets:
            self._chain_points.append((t.x, t.y))

        return results

    def draw(self, surface, cam_x=0, cam_y=0, px=0, py=0):
        """绘制闪电链"""
        if len(self._chain_points) < 2:
            return

        # 每对相邻点之间画锯齿闪电
        for i in range(len(self._chain_points) - 1):
            x1, y1 = self._chain_points[i]
            x2, y2 = self._chain_points[i + 1]
            self._draw_lightning(surface, x1 - cam_x, y1 - cam_y,
                                x2 - cam_x, y2 - cam_y, i)

    def _draw_lightning(self, surface, x1, y1, x2, y2, chain_index):
        """在两点之间绘制锯齿闪电"""
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist < 1:
            return

        segments = max(3, int(dist / 15))
        points = [(x1, y1)]

        for s in range(1, segments):
            t = s / segments
            bx = x1 + dx * t
            by = y1 + dy * t
            # 垂直于方向的随机偏移
            offset = random.uniform(-8, 8) * (1 - chain_index * 0.2)
            nx, ny = -dy / dist, dx / dist  # 法线方向
            bx += nx * offset
            by += ny * offset
            points.append((bx, by))

        points.append((x2, y2))

        # 外层辉光
        int_points = [(int(p[0]), int(p[1])) for p in points]
        if len(int_points) >= 2:
            # 衰减越后面的链越暗
            alpha = max(0.3, 1.0 - chain_index * 0.25)
            glow_color = (int(120 * alpha), int(80 * alpha), int(200 * alpha))
            core_color = (int(180 * alpha), int(140 * alpha), int(255 * alpha))
            pygame.draw.lines(surface, glow_color, False, int_points, 4)
            pygame.draw.lines(surface, core_color, False, int_points, 2)
            # 白色核心
            white_color = (int(220 * alpha), int(220 * alpha), int(255 * alpha))
            pygame.draw.lines(surface, white_color, False, int_points, 1)

    def get_display_stats(self):
        attacks_per_sec = 60 / self.fire_rate if self.fire_rate > 0 else 0
        return [
            f"伤害: {self.damage}",
            f"攻速: {attacks_per_sec:.1f}/s",
            f"链数: {self.chain_count + 1}",
            f"范围: {self.arc_range}",
        ]
