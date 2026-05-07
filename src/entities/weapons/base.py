"""
武器基类 - 统一攻击和伤害接口

所有武器的伤害都通过 deal_damage() 结算：
- deal_damage(target, targets, attacker, ...) 中 target 为首要命中目标
- 远程武器：CombatSystem 碰撞检测后调用 weapon.deal_damage()
- 近战武器：武器自己的 update() 中调用 deal_damage()
"""
import random


class Upgrade:
    def __init__(self, uid, name, desc, icon_color, apply_fn):
        self.id = uid
        self.name = name
        self.desc = desc
        self.icon_color = icon_color
        self.apply_fn = apply_fn

    def apply(self, player, weapon):
        if self.apply_fn:
            self.apply_fn(player, weapon)


class Weapon:
    """武器基类

    通用属性: name, desc, color, damage, fire_rate, upgrades
    子类必须重写: attack() 或 deal_damage()

    接口说明：
    - attacker: 攻击方实体，只要有 x, y, angle 属性即可（玩家/怪物通用）
    - targets: 对方阵营列表（玩家武器传怪物列表，敌人武器传玩家列表）
    """

    name = "武器"
    desc = ""
    color = (200, 200, 200)
    damage = 10
    fire_rate = 25
    upgrades = []
    handles_own_particles = False  # 子类设 True 表示 deal_damage 自行处理命中特效

    def attack(self, attacker, targets, dt=None):
        """执行攻击 - 远程返回投射物列表，近战返回空列表

        Args:
            attacker: 攻击方实体 (需有 x, y, angle)
            targets: 对方阵营实体列表
            dt: 帧间隔
        """
        return []

    def deal_damage(self, target, targets, attacker, proj, particles, floating_texts):
        """命中事件 - 子类重写定义伤害逻辑（可多次触发，如穿透）

        Args:
            target: 首要命中目标 (CombatEntity)
            targets: 对方全体列表 (List[CombatEntity])，AoE 遍历用
            attacker: 攻击方 (CombatEntity)，效果触发需要
            proj: 投射物实例（爆炸等需要位置信息）
            particles: 粒子列表
            floating_texts: 浮动文字列表
        """
        actual = target.take_damage(self.damage, attacker=attacker)
        self._create_damage_text(target, actual, False, floating_texts)
        # 触发攻击者的效果（吸血等）
        if attacker and hasattr(attacker, 'trigger'):
            attacker.trigger(attacker.ON_DEAL_DAMAGE, target=target, damage=actual)

    def _create_damage_text(self, target, damage, is_crit, floating_texts):
        """创建伤害浮动文字 - 武器决定浮动文字的样式"""
        if floating_texts is None or damage <= 0:
            return
        from core.config import Color
        from ui.effects import FloatingText
        color = Color.GOLD if is_crit else Color.WHITE
        size = 28 if is_crit else 20
        text = f"{damage}!" if is_crit else str(damage)
        floating_texts.append(FloatingText(
            target.x + random.randint(-10, 10),
            target.y - target.size - 5,
            text, color, size
        ))

    def update(self, attacker, targets, particles, floating_texts, dt):
        """持续效果（如飞刀旋转）

        Args:
            attacker: 攻击方实体
            targets: 对方阵营实体列表
            particles: 粒子列表
            floating_texts: 浮动文字列表
            dt: 帧间隔
        """
        pass

    def draw(self, surface, cam_x=0, cam_y=0, px=0, py=0):
        """绘制武器效果"""
        pass

    def get_display_stats(self):
        """返回要显示的属性列表，子类可重写"""
        attacks_per_sec = 60 / self.fire_rate if self.fire_rate > 0 else 0
        return [
            f"伤害: {self.damage}",
            f"攻速: {attacks_per_sec:.1f}/s",
        ]

    def apply_upgrade(self, player, upgrade_id):
        upgrade = self.get_upgrade_by_id(upgrade_id)
        if upgrade:
            upgrade.apply(player, self)

    def get_upgrade_by_id(self, upgrade_id):
        for upgrade in self.upgrades:
            if upgrade.id == upgrade_id:
                return upgrade
        return None
