"""
武器基类 - 统一攻击和伤害接口

所有武器的伤害都通过 deal_damage() 结算：
- deal_damage(target, targets, attacker, ...) 中 target 为首要命中目标
- 远程武器：CombatSystem 碰撞检测后调用 weapon.deal_damage()
- 近战武器：武器自己的 update() 中调用 deal_damage()

武器不直接创建 UI 对象（粒子/浮动文字），而是返回 DamageResult 数据，
由 CombatSystem 统一处理视觉特效。
"""


class DamageResult:
    """武器伤害结果 - 纯数据，不含 UI 逻辑

    CombatSystem 根据此数据创建浮动文字和粒子特效。
    effects 字典列表描述武器专属特效（如爆炸、飞刀命中光效）。
    """
    __slots__ = ('target', 'damage', 'is_crit', 'effects')

    def __init__(self, target, damage, is_crit=False, effects=None):
        self.target = target
        self.damage = damage
        self.is_crit = is_crit
        self.effects = effects or []  # list of dict: {"type": "explosion"|"particle", ...}


UPGRADE_ONCE = 1      # 只能选一次的升级
UPGRADE_UNLIMITED = 1000  # 可无限选择的升级（默认）


class Upgrade:
    def __init__(self, uid, name, desc, icon_color, apply_fn, max_count=UPGRADE_UNLIMITED, current_count=0):
        self.id = uid
        self.name = name
        self.desc = desc
        self.icon_color = icon_color
        self.apply_fn = apply_fn
        self.max_count = max_count
        self.current_count = current_count

    def apply(self, player, weapon):
        if self.apply_fn:
            self.apply_fn(player, weapon)
        player._upgrade_counts[self.id] = player._upgrade_counts.get(self.id, 0) + 1


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

    def attack(self, attacker, targets, dt=None):
        """执行攻击 - 远程返回投射物列表，近战返回空列表

        Args:
            attacker: 攻击方实体 (需有 x, y, angle)
            targets: 对方阵营实体列表
            dt: 帧间隔
        """
        return []

    def deal_damage(self, target, targets, attacker, proj):
        """命中事件 - 模板方法：子类重写 _deal_damage 定义伤害逻辑

        基类统一处理 ON_DEAL_DAMAGE 触发和 DamageResult 组装。
        子类只需在 _deal_damage 中计算伤害并返回结果列表。

        Args:
            target: 首要命中目标 (CombatEntity)
            targets: 对方全体列表 (List[CombatEntity])，AoE 遍历用
            attacker: 攻击方 (CombatEntity)，效果触发需要
            proj: 投射物实例（爆炸等需要位置信息）

        Returns:
            list[DamageResult]: 伤害结果列表，由 CombatSystem 处理视觉特效
        """
        results = self._deal_damage(target, targets, attacker, proj)
        # 统一触发攻击者效果（吸血等）
        if attacker and hasattr(attacker, 'trigger'):
            for r in results:
                if r.target is not None and r.damage > 0:
                    attacker.trigger(attacker.ON_DEAL_DAMAGE, target=r.target, damage=r.damage)
        return results

    def _deal_damage(self, target, targets, attacker, proj):
        """计算伤害并返回 DamageResult 列表 - 子类重写

        默认实现：对 target 造成 self.damage 点伤害。
        子类重写时可实现暴击、AoE 等特殊逻辑，但不需要触发 ON_DEAL_DAMAGE。
        """
        actual, reaction = target.take_damage(self.damage, attacker=attacker)
        return [DamageResult(target, actual)] + reaction

    def update(self, attacker, targets, dt):
        """持续效果（如飞刀旋转）

        Args:
            attacker: 攻击方实体
            targets: 对方阵营实体列表
            dt: 帧间隔

        Returns:
            list[DamageResult]: 命中结果列表，由 CombatSystem 处理视觉特效
        """
        return []

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
