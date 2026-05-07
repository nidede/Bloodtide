"""
战斗系统 - 统一编排战斗管线
"""
import math
from core.config import Color, CombatConfig


class CombatSystem:
    """战斗系统 - 处理所有战斗相关逻辑，对外提供统一的 update() 接口"""

    def __init__(self):
        self._dead_monsters = set()

    def update(self, monsters, player, projectiles, particles, floating_texts, dt, is_visible):
        """执行完整的战斗管线：投射物碰撞 → 怪物AI/攻击 → 死亡处理 → 清理

        Returns:
            (damage_taken, leveled_players): 玩家受伤量, 升级的玩家集合
        """
        hp_before = player.hp

        # 1. 投射物碰撞
        self.update_projectiles(projectiles, monsters, [player], particles, floating_texts, dt)

        # 2. 怪物AI、移动和攻击
        self.update_monsters(monsters, player, projectiles, particles, floating_texts, dt, is_visible)

        # 3. 死亡处理
        damage_taken = max(0, hp_before - player.hp)
        leveled_players = self.process_dead_monsters(monsters, [player], particles, floating_texts)

        # 4. 清理
        self.cleanup(monsters)
        projectiles[:] = [p for p in projectiles if p.alive]

        return damage_taken, leveled_players

    def update_projectiles(self, projectiles, monsters, players, particles, floating_texts, dt):
        """处理投射物碰撞 - 碰撞检测委托武器 deal_damage() 处理伤害"""
        for proj in projectiles:
            if not proj.alive:
                continue

            proj.update(dt)

            # 出界/超时死亡（proj.update() 内部设 alive=False），直接消失
            if not proj.alive:
                continue

            if proj.is_enemy:
                # 敌方投射物：检查与玩家的碰撞
                for player in players:
                    if id(player) in proj.hit_set:
                        continue
                    dist = math.hypot(proj.x - player.x, proj.y - player.y)
                    if dist < proj.size + player.size:
                        proj.weapon.deal_damage(player, players, proj.owner, proj, particles, floating_texts)
                        proj.on_hit(player)
                        break
            else:
                # 玩家投射物：碰撞检测 + 委托武器处理伤害
                for monster in monsters:
                    if monster.dead or id(monster) in proj.hit_set:
                        continue
                    dist = math.hypot(proj.x - monster.x, proj.y - monster.y)
                    if dist < proj.size + monster.size:
                        attacker = proj.owner or players[0] if players else None
                        proj.weapon.deal_damage(monster, monsters, attacker, proj, particles, floating_texts)

                        # 武器自行处理命中特效时（如导弹爆炸），跳过默认粒子
                        if not getattr(proj.weapon, 'handles_own_particles', False):
                            for _ in range(CombatConfig.HIT_PARTICLE_COUNT):
                                particles.append(
                                    self._create_particle(proj.x, proj.y, Color.YELLOW,
                                                          speed=CombatConfig.HIT_PARTICLE_SPEED,
                                                          lifetime=CombatConfig.HIT_PARTICLE_LIFETIME)
                                )

                        proj.on_hit(monster)
                        break

    def update_monsters(self, monsters, player, projectiles, particles, floating_texts, dt, is_visible):
        """处理怪物AI、移动和攻击 - 统一调用 monster.update() + monster.attack()"""
        hp_before = player.hp
        for monster in monsters:
            if is_visible(monster.x, monster.y, CombatConfig.MONSTER_VISIBLE_RANGE):
                monster.update(player, dt)
            else:
                # 屏幕外：简单追击
                monster.attack_cooldown = max(0, monster.attack_cooldown - dt)
                monster.flash_timer = max(0, monster.flash_timer - dt)
                dx = player.x - monster.x
                dy = player.y - monster.y
                dist = math.hypot(dx, dy)
                if dist > 0 and dist < CombatConfig.DETECTION_RANGE:
                    monster.x += (dx / dist) * monster.speed * CombatConfig.CHASE_SPEED_RATIO * dt
                    monster.y += (dy / dist) * monster.speed * CombatConfig.CHASE_SPEED_RATIO * dt

            # 统一攻击：远程返回 Projectile[]，近战内部处理碰撞伤害
            new_projs = monster.attack([player], particles, floating_texts, dt)
            projectiles.extend(new_projs)
        return max(0, hp_before - player.hp)

    def process_dead_monsters(self, monsters, players, particles, floating_texts):
        """处理怪物死亡 - 直接给所有玩家加经验，返回升级的玩家集合"""
        leveled_players = set()
        for m in monsters:
            if m.dead:
                for player in players:
                    player.kills += 1
                    if player.gain_xp(m.xp_value):
                        leveled_players.add(player)
                for _ in range(CombatConfig.DEATH_PARTICLE_COUNT):
                    particles.append(
                        self._create_particle(m.x, m.y, m.color,
                                              speed=CombatConfig.PARTICLE_DEATH_SPEED,
                                              lifetime=CombatConfig.PARTICLE_DEATH_LIFETIME)
                    )
                self._dead_monsters.add(id(m))
        return leveled_players

    def cleanup(self, monsters):
        """清理死亡的怪物"""
        monsters[:] = [m for m in monsters if id(m) not in self._dead_monsters]
        self._dead_monsters.clear()

    def check_player_death(self, player, particles):
        """检查玩家是否死亡"""
        return player.hp <= 0

    def spawn_death_particles(self, player, particles):
        """生成玩家死亡粒子"""
        for _ in range(CombatConfig.PLAYER_DEATH_PARTICLE_COUNT):
            particles.append(
                self._create_particle(player.x, player.y, Color.RED,
                                      speed=CombatConfig.PARTICLE_PLAYER_DEATH_SPEED,
                                      lifetime=CombatConfig.PARTICLE_PLAYER_DEATH_LIFETIME,
                                      size=5)
            )

    def _create_particle(self, x, y, color, speed=120, lifetime=0.25, size=3):
        """创建粒子"""
        from ui.effects import Particle
        return Particle(x, y, color, speed, lifetime, size)

    def _create_floating_text(self, x, y, text, color, size, lifetime=0.5):
        """创建浮动文字"""
        from ui.effects import FloatingText
        return FloatingText(x, y, text, color, size, lifetime)
