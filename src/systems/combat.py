"""
战斗系统 - 统一编排战斗管线，处理所有视觉特效
"""
import math
import random
from core.config import Color, CombatConfig, MissileConfig


class CombatSystem:
    """战斗系统 - 处理所有战斗相关逻辑，对外提供统一的 update() 接口

    武器返回 DamageResult 数据，CombatSystem 通过工厂函数创建粒子/浮动文字等视觉特效。
    不直接依赖任何 UI 类。
    """

    def __init__(self, particle_factory, text_factory):
        """
        Args:
            particle_factory: (x, y, color, speed, lifetime, size) -> particle 对象
            text_factory: (x, y, text, color, size) -> floating_text 对象
        """
        self._particle_factory = particle_factory
        self._text_factory = text_factory
        self._dead_monsters = set()

    def update(self, monsters, player, projectiles, particles, floating_texts, dt, is_visible):
        """执行完整的战斗管线：武器持续效果 → 投射物碰撞 → 怪物AI/攻击 → 死亡处理 → 清理

        Returns:
            (damage_taken, leveled_players): 玩家受伤量（原始伤害，不含吸血回血）, 升级的玩家集合
        """
        raw_damage_to_player = 0

        # 0. 玩家武器持续效果（如飞刀旋转）
        if player.weapon:
            results = player.weapon.update(player, monsters, dt)
            self._process_damage_results(results, particles, floating_texts)

        # 1. 投射物碰撞
        proj_results = self.update_projectiles(projectiles, monsters, [player], dt)
        raw_damage_to_player += sum(r.damage for r in proj_results if r.target is player and r.damage > 0)
        self._process_damage_results(proj_results, particles, floating_texts)

        # 2. 怪物AI、移动和攻击
        monster_results = self.update_monsters(monsters, player, projectiles, dt, is_visible)
        raw_damage_to_player += sum(r.damage for r in monster_results if r.target is player and r.damage > 0)
        self._process_damage_results(monster_results, particles, floating_texts)

        # 3. 死亡处理
        total_levels = self.process_dead_monsters(monsters, [player], particles, floating_texts)

        # 4. 清理
        self.cleanup(monsters)
        projectiles[:] = [p for p in projectiles if p.alive]

        return raw_damage_to_player, total_levels

    def update_projectiles(self, projectiles, monsters, players, dt):
        """处理投射物碰撞 - 返回所有 DamageResult"""
        all_results = []
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
                        results = proj.weapon.deal_damage(player, players, proj.owner, proj)
                        all_results.extend(results)
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
                        results = proj.weapon.deal_damage(monster, monsters, attacker, proj)
                        all_results.extend(results)

                        # 武器没有自带特效时，添加默认命中粒子
                        has_own_effects = any(
                            eff["type"] in ("explosion", "hit_particles", "particle")
                            for r in results for eff in r.effects
                        )
                        if not has_own_effects:
                            for r in results:
                                if r.target is not None:
                                    r.effects.append({
                                        "type": "hit_particles",
                                        "x": proj.x, "y": proj.y,
                                    })
                                    break

                        proj.on_hit(monster)
                        break
        return all_results

    def update_monsters(self, monsters, player, projectiles, dt, is_visible):
        """处理怪物AI、移动和攻击 - 返回所有 DamageResult"""
        all_results = []
        for monster in monsters:
            if monster.dead:
                continue
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
            new_projs, dmg_results = monster.attack([player], dt)
            projectiles.extend(new_projs)
            all_results.extend(dmg_results)
        return all_results

    def _process_damage_results(self, results, particles, floating_texts):
        """从 DamageResult 数据创建视觉特效"""
        if not results:
            return
        for r in results:
            # 伤害浮动文字（只在实际造成伤害时显示）
            if r.target is not None and r.damage > 0:
                self._create_damage_text(r.target, r.damage, r.is_crit, floating_texts)

            # 武器专属特效
            for eff in r.effects:
                if eff["type"] == "particle":
                    particles.append(self._create_particle(
                        eff["x"], eff["y"], eff.get("color", Color.WHITE),
                        speed=eff.get("speed", 120),
                        lifetime=eff.get("lifetime", 0.25),
                        size=eff.get("size", 3)
                    ))
                elif eff["type"] == "explosion":
                    self._create_explosion(eff["x"], eff["y"], eff["radius"], particles)
                elif eff["type"] == "hit_particles":
                    for _ in range(CombatConfig.HIT_PARTICLE_COUNT):
                        particles.append(
                            self._create_particle(eff["x"], eff["y"], Color.YELLOW,
                                                  speed=CombatConfig.HIT_PARTICLE_SPEED,
                                                  lifetime=CombatConfig.HIT_PARTICLE_LIFETIME)
                        )

    def _create_damage_text(self, target, damage, is_crit, floating_texts):
        """创建伤害浮动文字"""
        if floating_texts is None or damage <= 0:
            return
        color = Color.GOLD if is_crit else Color.WHITE
        size = 28 if is_crit else 20
        text = f"{damage}!" if is_crit else str(damage)
        floating_texts.append(self._text_factory(
            target.x + random.randint(-10, 10),
            target.y - target.size - 5,
            text, color, size
        ))

    def _create_explosion(self, x, y, radius, particles):
        """创建导弹爆炸粒子"""
        offset = int(radius * MissileConfig.EXPLOSION_OFFSET_RATIO)
        for _ in range(MissileConfig.EXPLOSION_PARTICLE_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            spd = random.uniform(MissileConfig.EXPLOSION_PARTICLE_SPEED_MIN,
                                 MissileConfig.EXPLOSION_PARTICLE_SPEED_MAX)
            particles.append(self._create_particle(
                x + math.cos(angle) * random.randint(0, offset),
                y + math.sin(angle) * random.randint(0, offset),
                Color.ORANGE, spd,
                MissileConfig.EXPLOSION_PARTICLE_LIFETIME,
                MissileConfig.EXPLOSION_PARTICLE_SIZE
            ))

    def process_dead_monsters(self, monsters, players, particles, floating_texts):
        """处理怪物死亡 - 直接给所有玩家加经验，返回升级次数"""
        total_levels = 0
        for m in monsters:
            if m.dead:
                for player in players:
                    player.kills += 1
                    total_levels += player.gain_xp(m.xp_value)
                for _ in range(CombatConfig.DEATH_PARTICLE_COUNT):
                    particles.append(
                        self._create_particle(m.x, m.y, m.color,
                                              speed=CombatConfig.PARTICLE_DEATH_SPEED,
                                              lifetime=CombatConfig.PARTICLE_DEATH_LIFETIME)
                    )
                self._dead_monsters.add(id(m))
        return total_levels

    def cleanup(self, monsters):
        """清理死亡的怪物"""
        monsters[:] = [m for m in monsters if id(m) not in self._dead_monsters]
        self._dead_monsters.clear()

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
        return self._particle_factory(x, y, color, speed, lifetime, size)
