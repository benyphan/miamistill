import arcade
import random
import math
import time

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 640
SCREEN_TITLE = "Hotline Miami Style"

TILE = 48
MAP_W = SCREEN_WIDTH // TILE
MAP_H = SCREEN_HEIGHT // TILE

PLAYER_SPEED = 350  # Быстрое плавное движение
BULLET_SPEED = 1000  # Очень быстрые пули
ENEMY_SPEED = 180
MELEE_RANGE = 44
MELEE_COOLDOWN = 0.3
PLAYER_SIZE = 22
ENEMY_SIZE = 20
BULLET_SIZE = 4
WALL_COLOR = (35, 35, 35)

FIRE_RATE_PISTOL = 0.15
FIRE_RATE_SHOTGUN = 0.8
SHOTGUN_PELLETS = 7
SHOTGUN_SPREAD_DEG = 28

# Gameplay settings
ONE_HIT_PLAYER = True
ONE_HIT_ENEMY = True


# ---------------- Utilities

def normalize(vx, vy):
    dist = math.hypot(vx, vy)
    if dist == 0:
        return 0.0, 0.0
    return vx / dist, vy / dist


def sample_line_clear(x1, y1, x2, y2, wall_list, step=8):
    """Проверка прямой видимости."""
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist == 0:
        return True
    nx = dx / dist
    ny = dy / dist
    steps = int(dist / step)
    for i in range(1, steps + 1):
        sx = x1 + nx * (i * step)
        sy = y1 + ny * (i * step)
        hits = arcade.get_sprites_at_point((sx, sy), wall_list)
        if hits:
            return False
    return True


# ---------------- Entities

class Wall(arcade.SpriteSolidColor):
    def __init__(self, w, h, color, center_x, center_y):
        super().__init__(w, h, color)
        self.center_x = center_x
        self.center_y = center_y


class Bullet(arcade.SpriteCircle):
    def __init__(self, dx, dy):
        super().__init__(BULLET_SIZE, (255, 255, 100))
        self.vx = dx * BULLET_SPEED
        self.vy = dy * BULLET_SPEED
        self.lifetime = 1.0  # 1 секунда жизни
        self.spawn_time = time.time()

    def update(self, delta_time):
        current_time = time.time()
        if current_time - self.spawn_time > self.lifetime:
            self.kill()
            return

        self.center_x += self.vx * delta_time
        self.center_y += self.vy * delta_time


class Particle(arcade.Sprite):
    def __init__(self, size, color, dx, dy, life):
        super().__init__()
        self.dx = dx
        self.dy = dy
        self.life = life
        # возможно еще center_x, center_y и sprite image

    def update(self, delta_time: float = 0):  # <- важно добавить delta_time!
        self.center_x += self.dx
        self.center_y += self.dy
        self.life -= 1
        if self.life <= 0:
            self.kill()



class Actor(arcade.SpriteCircle):
    def __init__(self, size, color):
        super().__init__(size, color)
        self.alive = True

    def kill_actor(self):
        self.alive = False
        self.kill()


class Player(Actor):
    def __init__(self, x, y):
        super().__init__(PLAYER_SIZE, (60, 200, 255))
        self.center_x = x
        self.center_y = y
        self.speed = PLAYER_SPEED
        self.angle = 0
        self.last_fire = 0
        self.last_melee = 0
        self.weapon = 'pistol'
        self.ammo = {'pistol': 24, 'shotgun': 8}
        self.max_ammo = {'pistol': 24, 'shotgun': 8}
        self.reloading = False
        self.reload_timer = 0
        self.reload_time = {'pistol': 1.5, 'shotgun': 2.1}
        self.health = 100
        self.width -= 6
        self.height -= 6


class Enemy(Actor):
    def __init__(self, x, y):
        super().__init__(ENEMY_SIZE, (235, 80, 80))
        self.center_x = x
        self.center_y = y
        self.state = 'patrol'
        self.patrol_target = None
        self.vision_radius = 350
        self.attack_radius = 60
        self.vx = 0
        self.vy = 0
        self.last_attack_time = 0
        self.attack_cooldown = 1.0
        self.speed = ENEMY_SPEED
        self.last_state_change = 0
        self.stun_timer = 0

    def update_ai(self, player, wall_list, delta_time):
        if not self.alive:
            return None

        # Если враг оглушен
        if self.stun_timer > 0:
            self.stun_timer -= delta_time
            return None

        dx = player.center_x - self.center_x
        dy = player.center_y - self.center_y
        dist = math.hypot(dx, dy)

        # Проверка прямой видимости
        can_see = sample_line_clear(self.center_x, self.center_y,
                                    player.center_x, player.center_y, wall_list)

        # Если видим игрока и он в радиусе зрения
        if can_see and dist < self.vision_radius:
            # Если еще не в режиме преследования, переключаемся
            if self.state != 'chase':
                self.state = 'chase'
                self.last_state_change = time.time()

            # Двигаемся к игроку
            if dist > self.attack_radius:
                # Нормализуем вектор направления
                if dist > 0:
                    move_x = dx / dist * self.speed * delta_time
                    move_y = dy / dist * self.speed * delta_time

                    # Сохраняем старую позицию
                    old_x = self.center_x
                    old_y = self.center_y

                    # Двигаемся
                    self.center_x += move_x
                    self.center_y += move_y

                    # Проверяем столкновения со стенами
                    if arcade.check_for_collision_with_list(self, wall_list):
                        self.center_x = old_x
                        self.center_y = old_y

            # Если достаточно близко для атаки
            if dist <= self.attack_radius and time.time() - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = time.time()
                return 'attack'

        else:
            # Если не видим игрока, патрулируем
            if self.state != 'patrol' or self.patrol_target is None:
                self.state = 'patrol'
                self.last_state_change = time.time()
                # Выбираем случайную точку для патрулирования
                self.patrol_target = (self.center_x + random.uniform(-150, 150),
                                      self.center_y + random.uniform(-150, 150))

            tx, ty = self.patrol_target
            pdx = tx - self.center_x
            pdy = ty - self.center_y
            pdist = math.hypot(pdx, pdy)

            if pdist < 20:  # Достигли цели
                self.patrol_target = None
            elif pdist > 0:
                # Двигаемся к цели патрулирования
                move_x = pdx / pdist * (self.speed * 0.6) * delta_time
                move_y = pdy / pdist * (self.speed * 0.6) * delta_time

                # Сохраняем старую позицию
                old_x = self.center_x
                old_y = self.center_y

                # Двигаемся
                self.center_x += move_x
                self.center_y += move_y

                # Проверяем столкновения
                if arcade.check_for_collision_with_list(self, wall_list):
                    self.center_x = old_x
                    self.center_y = old_y
                    self.patrol_target = None  # Выбираем новую цель

        return None


# ---------------- Game

class GameWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color((15, 15, 15))

        self.player: Player = None
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.bullet_list = arcade.SpriteList()
        self.particle_list = arcade.SpriteList()

        self.keys_pressed = {
            arcade.key.W: False,
            arcade.key.S: False,
            arcade.key.A: False,
            arcade.key.D: False
        }
        self.mouse_x = 0
        self.mouse_y = 0

        self.level = 1
        self.message = ''
        self.paused = False
        self.last_update_time = time.time()

        self.setup()
    def on_update(self, delta_time: float):
        self.update(delta_time)  # вызываем твой update каждый кадр

    def make_map(self):
        grid = [[0 for _ in range(MAP_W)] for __ in range(MAP_H)]
        # Границы
        for x in range(MAP_W):
            grid[0][x] = 1
            grid[MAP_H - 1][x] = 1
        for y in range(MAP_H):
            grid[y][0] = 1
            grid[y][MAP_W - 1] = 1

        # Случайные комнаты
        for _ in range(8):  # Меньше стен для тестирования
            w = random.randint(2, 4)
            h = random.randint(2, 4)
            sx = random.randint(1, MAP_W - w - 2)
            sy = random.randint(1, MAP_H - h - 2)
            for yy in range(sy, sy + h):
                for xx in range(sx, sx + w):
                    grid[yy][xx] = 1

        # Создаем несколько проходов
        for _ in range(6):
            x = random.randint(3, MAP_W - 4)
            y = random.randint(3, MAP_H - 4)
            if grid[y][x] == 1:
                grid[y][x] = 0

        return grid

    def setup(self):
        # --- очистка ---
        self.player_list.clear()
        self.enemy_list.clear()
        self.wall_list.clear()
        self.bullet_list.clear()
        self.particle_list.clear()

        # --- карта ---
        grid = self.make_map()

        for y in range(MAP_H):
            for x in range(MAP_W):
                if grid[y][x] == 1:
                    wx = x * TILE + TILE / 2
                    wy = y * TILE + TILE / 2
                    wall = Wall(TILE, TILE, WALL_COLOR, wx, wy)
                    self.wall_list.append(wall)

        # --- СПАВН ИГРОКА (ТОЛЬКО ЕСЛИ НЕТ КОЛЛИЗИЙ) ---
        self.player = None
        center_x, center_y = MAP_W // 2, MAP_H // 2

        for radius in range(1, 10):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x = center_x + dx
                    y = center_y + dy

                    if 1 <= x < MAP_W - 1 and 1 <= y < MAP_H - 1:
                        if grid[y][x] == 0:
                            px = x * TILE + TILE / 2
                            py = y * TILE + TILE / 2

                            temp_player = Player(px, py)

                            if not arcade.check_for_collision_with_list(temp_player, self.wall_list):
                                self.player = temp_player
                                break
                if self.player:
                    break
            if self.player:
                break

        # fallback — если карта говно
        if not self.player:
            self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        self.player_list.append(self.player)

        # --- ВРАГИ ---
        for _ in range(4 + self.level):
            tries = 0
            while tries < 50:
                x = random.randint(1, MAP_W - 2)
                y = random.randint(1, MAP_H - 2)

                if grid[y][x] == 0:
                    ex = x * TILE + TILE / 2
                    ey = y * TILE + TILE / 2

                    dist = math.hypot(
                        ex - self.player.center_x,
                        ey - self.player.center_y
                    )

                    if dist > 200:
                        enemy = Enemy(ex, ey)

                        if not arcade.check_for_collision_with_list(enemy, self.wall_list):
                            self.enemy_list.append(enemy)
                            break
                tries += 1

        self.message = f"LEVEL {self.level} - KILL ALL ENEMIES"
        self.last_update_time = time.time()

    def on_draw(self):
        self.clear()

        # Рисуем в порядке: стены, пули, враги, игрок, частицы
        self.wall_list.draw()
        self.bullet_list.draw()
        self.enemy_list.draw()
        self.player_list.draw()
        self.particle_list.draw()

        # HUD
        arcade.draw_text(
            self.message, 20, SCREEN_HEIGHT - 40,
            arcade.color.WHITE, 16
        )

        alive_enemies = len(self.enemy_list)
        arcade.draw_text(
            f'ENEMIES: {alive_enemies}', 20, SCREEN_HEIGHT - 70,
            arcade.color.RED, 14
        )

        # Оружие и боезапас
        w = self.player.weapon.upper()
        ammo = self.player.ammo.get(self.player.weapon, 0)
        maxa = self.player.max_ammo.get(self.player.weapon, 0)
        reload_status = ' [RELOADING]' if self.player.reloading else ''
        arcade.draw_text(
            f'{w}: {ammo}/{maxa}{reload_status}', 20, SCREEN_HEIGHT - 100,
            arcade.color.WHITE, 14
        )

        # Здоровье игрока
        health_color = arcade.color.GREEN if self.player.health > 50 else \
            arcade.color.YELLOW if self.player.health > 25 else \
                arcade.color.RED
        arcade.draw_text(
            f'HEALTH: {self.player.health}', 20, SCREEN_HEIGHT - 130,
            health_color, 14
        )

        # Управление
        arcade.draw_text(
            'WASD: MOVE  MOUSE: AIM  LMB: SHOOT  SPACE: MELEE  1/2: WEAPON  R: RESTART',
            20, 20, arcade.color.LIGHT_GRAY, 12
        )

        # Пауза
        if self.paused:
            arcade.draw_rectangle_filled(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                400, 100,
                arcade.make_transparent_color(arcade.color.BLACK, 200)
            )
            arcade.draw_text(
                'PAUSED',
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                arcade.color.YELLOW, 36,
                anchor_x="center", anchor_y="center"
            )

        # Смерть игрока
        if not self.player.alive:
            arcade.draw_rectangle_filled(
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2,
                500, 150,
                arcade.make_transparent_color(arcade.color.BLACK, 200)
            )
            arcade.draw_text(
                'YOU DIED',
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30,
                arcade.color.RED, 36,
                anchor_x="center"
            )
            arcade.draw_text(
                'PRESS R TO RESTART',
                SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30,
                arcade.color.WHITE, 24,
                anchor_x="center"
            )

    def on_key_press(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed[key] = True
        elif key == arcade.key.SPACE:
            self.do_melee()
        elif key == arcade.key.R:
            self.level = 1
            self.setup()
        elif key == arcade.key.P:
            self.paused = not self.paused
        elif key == arcade.key.KEY_1 or key == arcade.key.NUM_1:
            if not self.player.reloading:
                self.player.weapon = 'pistol'
        elif key == arcade.key.KEY_2 or key == arcade.key.NUM_2:
            if not self.player.reloading:
                self.player.weapon = 'shotgun'

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed[key] = False

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
        if self.player and self.player.alive:
            dx = x - self.player.center_x
            dy = y - self.player.center_y
            if dx != 0 or dy != 0:
                self.player.angle = math.degrees(math.atan2(dy, dx))

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.shoot()

    def shoot(self):
        if self.paused or not self.player.alive or self.player.reloading:
            return

        current_time = time.time()
        weapon = self.player.weapon

        if self.player.ammo[weapon] <= 0:
            self.player.reloading = True
            self.player.reload_timer = current_time
            return

        rate = FIRE_RATE_PISTOL if weapon == 'pistol' else FIRE_RATE_SHOTGUN
        if current_time - self.player.last_fire < rate:
            return

        self.player.last_fire = current_time

        dx = self.mouse_x - self.player.center_x
        dy = self.mouse_y - self.player.center_y
        if dx == 0 and dy == 0:
            return

        nx, ny = normalize(dx, dy)

        if weapon == 'pistol':
            bx = Bullet(nx, ny)
            bx.center_x = self.player.center_x + nx * 30
            bx.center_y = self.player.center_y + ny * 30
            self.bullet_list.append(bx)
            self.player.ammo['pistol'] -= 1

            # Отдача
            self.player.center_x -= nx * 3
            self.player.center_y -= ny * 3

            # Вспышка
            for _ in range(3):
                px = Particle(2, (255, 255, 200),
                              nx * random.uniform(3, 5) + random.uniform(-1, 1),
                              ny * random.uniform(3, 5) + random.uniform(-1, 1),
                              life=random.randint(5, 10))
                px.center_x = self.player.center_x + nx * 25
                px.center_y = self.player.center_y + ny * 25
                self.particle_list.append(px)

        else:  # shotgun
            spread = SHOTGUN_SPREAD_DEG / 2
            for i in range(SHOTGUN_PELLETS):
                angle = math.atan2(ny, nx) + math.radians(random.uniform(-spread, spread))
                sx = math.cos(angle)
                sy = math.sin(angle)
                b = Bullet(sx, sy)
                b.center_x = self.player.center_x + sx * 30
                b.center_y = self.player.center_y + sy * 30
                self.bullet_list.append(b)

            self.player.ammo['shotgun'] -= 1

            # Сильная отдача
            self.player.center_x -= nx * 6
            self.player.center_y -= ny * 6

            # Большая вспышка
            for _ in range(8):
                px = Particle(3, (255, 220, 100),
                              nx * random.uniform(4, 7) + random.uniform(-2, 2),
                              ny * random.uniform(4, 7) + random.uniform(-2, 2),
                              life=random.randint(8, 15))
                px.center_x = self.player.center_x + nx * 25
                px.center_y = self.player.center_y + ny * 25
                self.particle_list.append(px)

    def do_melee(self):
        if self.paused or not self.player.alive:
            return

        current_time = time.time()
        if current_time - self.player.last_melee < MELEE_COOLDOWN:
            return

        self.player.last_melee = current_time
        angle_rad = math.radians(self.player.angle)
        fx = math.cos(angle_rad)
        fy = math.sin(angle_rad)

        to_kill = []
        for enemy in self.enemy_list:
            dx = enemy.center_x - self.player.center_x
            dy = enemy.center_y - self.player.center_y
            proj = dx * fx + dy * fy
            dist = math.hypot(dx, dy)
            if dist <= MELEE_RANGE and proj > 0:
                to_kill.append(enemy)

        for e in to_kill:
            spawn_blood(self.particle_list, e.center_x, e.center_y)
            e.kill_actor()

        if to_kill:
            self.message = f'MELEE KILL - {len(to_kill)} ENEMIES'

    def update(self, delta_time):
        if self.paused:
            return

        current_time = time.time()

        if not self.player.alive:
            return

        # Перезарядка
        if self.player.reloading:
            if current_time - self.player.reload_timer > self.player.reload_time[self.player.weapon]:
                w = self.player.weapon
                self.player.ammo[w] = self.player.max_ammo[w]
                self.player.reloading = False

        # Обновление пуль
        for bullet in self.bullet_list:
            bullet.update(delta_time)

            # Проверка столкновений со стенами
            if arcade.check_for_collision_with_list(bullet, self.wall_list):
                # Эффект попадания в стену
                for _ in range(2):
                    px = Particle(1, (200, 200, 200),
                                  random.uniform(-2, 2),
                                  random.uniform(-2, 2),
                                  life=random.randint(5, 10))
                    px.center_x = bullet.center_x
                    px.center_y = bullet.center_y
                    self.particle_list.append(px)
                bullet.kill()
                continue

            # Проверка попадания во врагов
            enemies_hit = arcade.check_for_collision_with_list(bullet, self.enemy_list)
            if enemies_hit:
                for enemy in enemies_hit:
                    spawn_blood(self.particle_list, enemy.center_x, enemy.center_y)
                    enemy.kill_actor()
                bullet.kill()
                continue

        # Обновление частиц
        self.particle_list.update()

        # AI врагов - они ДОЛЖНЫ атаковать!
        for enemy in self.enemy_list:
            action = enemy.update_ai(self.player, self.wall_list, delta_time)
            if action == 'attack':
                if self.player.health > 0:
                    self.player.health -= 20
                    spawn_blood(self.particle_list, self.player.center_x, self.player.center_y)







                    # Эффект получения урона
                    for _ in range(5):
                        px = Particle(2, (255, 50, 50),
                                      random.uniform(-3, 3),
                                      random.uniform(-3, 3),
                                      life=random.randint(10, 20))
                        px.center_x = self.player.center_x
                        px.center_y = self.player.center_y
                        self.particle_list.append(px)

                    if self.player.health <= 0:
                        self.player.kill_actor()
                        self.message = 'YOU DIED - PRESS R TO RESTART'
                        return

        # ДВИЖЕНИЕ ИГРОКА - теперь точно работает!
        move_x = 0
        move_y = 0

        if self.keys_pressed[arcade.key.W]:
            move_y += 1
        if self.keys_pressed[arcade.key.S]:
            move_y -= 1
        if self.keys_pressed[arcade.key.A]:
            move_x -= 1
        if self.keys_pressed[arcade.key.D]:
            move_x += 1

        if move_x != 0 or move_y != 0:
            # Нормализуем диагональное движение
            if move_x != 0 and move_y != 0:
                move_x *= 0.7071
                move_y *= 0.7071

            # Вычисляем смещение
            move_x *= self.player.speed * delta_time
            move_y *= self.player.speed * delta_time

            # Сохраняем старую позицию
            old_x = self.player.center_x
            old_y = self.player.center_y

            # Двигаем по X
            self.player.center_x += move_x
            if arcade.check_for_collision_with_list(self.player, self.wall_list):
                self.player.center_x = old_x

            # Двигаем по Y
            self.player.center_y += move_y
            if arcade.check_for_collision_with_list(self.player, self.wall_list):
                self.player.center_y = old_y

            # След от движения
            if current_time - self.last_update_time > 0.05:
                for _ in range(2):
                    px = Particle(1, (100, 100, 100),
                                  0, 0,
                                  life=random.randint(15, 25))
                    px.center_x = old_x + random.uniform(-5, 5)
                    px.center_y = old_y + random.uniform(-5, 5)
                    self.particle_list.append(px)
                self.last_update_time = current_time

        # Проверка победы
        if len(self.enemy_list) == 0:
            self.level += 1
            self.message = f'LEVEL {self.level} CLEARED! GET READY...'
            # Эффект победы
            for _ in range(20):
                px = Particle(random.randint(2, 4),
                              (random.randint(200, 255), random.randint(200, 255), 50),
                              random.uniform(-10, 10),
                              random.uniform(-10, 10),
                              life=random.randint(20, 40))
                px.center_x = self.player.center_x
                px.center_y = self.player.center_y
                self.particle_list.append(px)

            # Небольшая пауза перед следующим уровнем
            time.sleep(1.5)
            self.setup()


def spawn_blood(particle_list, x, y):
    for _ in range(12):
        angle = random.random() * math.pi * 2
        speed = random.uniform(2, 6)
        dx = math.cos(angle) * speed
        dy = math.sin(angle) * speed
        p = Particle(random.randint(2, 4),
                     (random.randint(180, 220), 20, 20),
                     dx, dy,
                     life=random.randint(15, 30))
        p.center_x = x + random.uniform(-5, 5)
        p.center_y = y + random.uniform(-5, 5)
        particle_list.append(p)


if __name__ == '__main__':
    window = GameWindow()
    arcade.run()