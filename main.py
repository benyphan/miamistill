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


class Particle(arcade.SpriteCircle):
    def __init__(self, size, color, dx, dy, life):
        super().__init__(size, color)
        self.dx = dx
        self.dy = dy
        self.life = life

    def update(self, delta_time: float = 0):
        self.center_x += self.dx
        self.center_y += self.dy
        self.life -= 1
        if self.life <= 0:
            self.kill()





class Actor(arcade.Sprite):
    def __init__(self, size=20, color=(255, 255, 255)):
        super().__init__()
        self.texture = arcade.make_circle_texture(size*2, color)
        self.width = size * 2
        self.height = size * 2
        self.alive = True


    def kill_actor(self):
        self.alive = False
        self.kill()



class Player(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__("assets/player.png", scale=0.6)
        self.center_x = x
        self.center_y = y
        self.alive = True
        self.speed = PLAYER_SPEED
        self.width = 40  # примерно визуальный размер
        self.height = 40
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

        def kill_actor(self):
            self.alive = False
            # чтобы спрайт исчезал со сцены
            self.kill()



class Enemy(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__("assets/thug_2.png", scale=0.6)
        self.center_x = x
        self.center_y = y
        self.width = 34 # примерно визуальный размер
        self.height = 34
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
        self.alive = True
        self.stuck_timer = 0

    def kill_actor(self):
        self.alive = False
        self.kill()

    def update_ai(self, player, wall_list, delta_time):


        if self.stuck_timer > 0.4:
            # тупо сменить направление
            self.patrol_target = None
            self.state = 'patrol'
            return None

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
                    self.angle = math.degrees(math.atan2(dy, dx))

                    # Сохраняем старую позицию
                    old_x = self.center_x
                    old_y = self.center_y

                    # Двигаемся
                    old_x = self.center_x
                    self.center_x += move_x
                    if arcade.check_for_collision_with_list(self, wall_list):
                        self.center_x = old_x

                    old_y = self.center_y
                    self.center_y += move_y
                    if arcade.check_for_collision_with_list(self, wall_list):
                        self.center_y = old_y
                    else:
                        self.angle = math.degrees(math.atan2(dy, dx)) + 90

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
                self.angle = math.degrees(math.atan2(-dy, dx)) + 90

                # Сохраняем старую позицию
                old_x = self.center_x
                old_y = self.center_y

                # Двигаемся
                old_x = self.center_x
                self.center_x += move_x
                if arcade.check_for_collision_with_list(self, wall_list):
                    self.center_x = old_x

                old_y = self.center_y
                self.center_y += move_y
                if arcade.check_for_collision_with_list(self, wall_list):
                    self.center_y = old_y
                else:
                    self.angle = math.degrees(math.atan2(-dy, dx)) + 90

                    self.patrol_target = None  # Выбираем новую цель

        return None


# ---------------- Game

class GameWindow(arcade.Window):
    def __init__(self):
        # создаём полноэкранное окно
        super().__init__(width=800, height=600, title=SCREEN_TITLE, fullscreen=True)
        arcade.set_background_color((15, 15, 15))

        # Получаем реальные размеры экрана
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = self.get_size()

        # масштаб тайлов под новый размер, если нужно
        global TILE, MAP_W, MAP_H
        TILE = 48  # можно оставить, или увеличить пропорционально экрану
        MAP_W = self.SCREEN_WIDTH // TILE
        MAP_H = self.SCREEN_HEIGHT // TILE

        # HUD-тексты создаём с учётом новых размеров
        self.hud_message = arcade.Text("", 20, self.SCREEN_HEIGHT - 40, arcade.color.WHITE, 16, font_name="Kenney Future")
        self.hud_enemies = arcade.Text("", 20, self.SCREEN_HEIGHT - 70, arcade.color.RED, 14, font_name="Kenney Future")
        self.hud_weapon = arcade.Text("", 20, self.SCREEN_HEIGHT - 100, arcade.color.WHITE, 14, font_name="Kenney Future")
        self.hud_health = arcade.Text("", 20, self.SCREEN_HEIGHT - 130, arcade.color.GREEN, 14, font_name="Kenney Future")
        self.hud_controls = arcade.Text(
            "WASD: MOVE  MOUSE: AIM  LMB: SHOOT  SPACE: MELEE  1/2: WEAPON  R: RESTART",
            20, 20, arcade.color.LIGHT_GRAY, 12, font_name="Kenney Future"
        )

        self.paused_text = arcade.Text("PAUSED", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2,
                                       arcade.color.YELLOW, 36, anchor_x="center", anchor_y="center",
                                       font_name="Kenney Future")
        self.dead_title = arcade.Text("YOU DIED", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 30,
                                      arcade.color.RED, 36, anchor_x="center", font_name="Kenney Future")
        self.dead_sub = arcade.Text("PRESS R TO RESTART", self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 30,
                                    arcade.color.WHITE, 24, anchor_x="center", font_name="Kenney Future")

        # остальной init код без изменений
        self.flash_timer = 0
        self.shake = 0
        self.blood_splats = []
        self.neon_offset = 0
        self.player: Player = None
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList(use_spatial_hash=True)
        self.bullet_list = arcade.SpriteList()
        self.particle_list = arcade.SpriteList()
        self.floor_list = arcade.SpriteList(use_spatial_hash=True)
        self.decor_list = arcade.SpriteList(use_spatial_hash=True)
        self.corpse_list = arcade.SpriteList()

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
        if self.flash_timer > 0:
            self.flash_timer -= delta_time

    def spawn_decorations(self, decor_textures, count=10):
        """Добавляет случайные декорации на карту без пересечений."""
        tries = 0
        placed = 0
        max_tries = count * 20  # чтобы не застрять в бесконечном цикле

        while placed < count and tries < max_tries:
            tries += 1

            x = random.randint(1, MAP_W - 2) * TILE + TILE / 2
            y = random.randint(1, MAP_H - 2) * TILE + TILE / 2

            decor = arcade.Sprite(random.choice(decor_textures), scale=0.6)
            decor.center_x = x
            decor.center_y = y

            # Проверяем пересечения
            collision = arcade.check_for_collision_with_list(decor, self.wall_list) or \
                        arcade.check_for_collision_with_list(decor, self.player_list) or \
                        arcade.check_for_collision_with_list(decor, self.enemy_list) or \
                        arcade.check_for_collision_with_list(decor, self.decor_list)
            if not collision:
                self.decor_list.append(decor)
                placed += 1

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

    def is_open_space(grid, x, y, radius=1):
        """Проверяет, что вокруг тайла есть хотя бы одно свободное место (0) в квадрате radius*radius"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                    if grid[ny][nx] == 0:
                        return True
        return False

    def setup(self):
        # --- очистка ---
        self.player_list.clear()
        self.enemy_list.clear()
        self.wall_list.clear()
        self.bullet_list.clear()
        self.particle_list.clear()
        self.corpse_list.clear()

        # --- карта ---
        grid = self.make_map()

        for y in range(MAP_H):
            for x in range(MAP_W):
                if grid[y][x] == 1:
                    wx = x * TILE + TILE / 2
                    wy = y * TILE + TILE / 2
                    wall = arcade.Sprite("assets/wall.png", scale=0.1)
                    wall.center_x = wx
                    wall.center_y = wy
                    wall.width = TILE
                    wall.height = TILE
                    self.wall_list.append(wall)

        for y in range(MAP_H):
            for x in range(MAP_W):
                fx = x * TILE + TILE / 2
                fy = y * TILE + TILE / 2
                floor = arcade.Sprite("assets/floor.png", scale=1.0)
                floor.center_x = fx
                floor.center_y = fy
                floor.width = TILE
                floor.height = TILE
                self.floor_list.append(floor)

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
        self.clear((18, 10, 30))  # тёмно-фиолетовый
        self.floor_list.draw()  # Рисуем пол
        self.wall_list.draw()  # Рисуем стены поверх пола
        self.player_list.draw()  # Персонажи
        self.enemy_list.draw()
        self.bullet_list.draw()
        self.particle_list.draw()

        # камера-тряска
        sx = random.randint(-self.shake, self.shake)
        sy = random.randint(-self.shake, self.shake)
        self.shake = max(0, self.shake - 1)


        # --- Тряска экрана (если есть) ---
        shake_x = random.uniform(-getattr(self, "screen_shake", 0), getattr(self, "screen_shake", 0)) if getattr(self,
                                                                                                                 "screen_shake",
                                                                                                                 0) > 0 else 0
        shake_y = random.uniform(-getattr(self, "screen_shake", 0), getattr(self, "screen_shake", 0)) if getattr(self,
                                                                                                                 "screen_shake",
                                                                                                                 0) > 0 else 0

        # --- Рисуем спрайты ---
        for sl in (self.wall_list, self.bullet_list, self.enemy_list, self.player_list, self.particle_list):
            for spr in sl:
                spr.center_x += shake_x
                spr.center_y += shake_y
            sl.draw()
            for spr in sl:
                spr.center_x -= shake_x
                spr.center_y -= shake_y

        # --- Вспышка экрана ---
        if getattr(self, "flash_alpha", 0) > 0:
            arcade.draw_lrtb_rectangle_filled(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0,
                                              (self.flash_color[0], self.flash_color[1], self.flash_color[2],
                                               int(self.flash_alpha)))

        # --- HUD ---
        hud_x, hud_y = shake_x, shake_y  # сдвиг HUD вместе с экраном (опционально)

        self.hud_message.text = self.message
        self.hud_message.x = 20 + hud_x
        self.hud_message.y = SCREEN_HEIGHT - 40 + hud_y
        self.hud_message.draw()

        self.hud_enemies.text = f'ENEMIES: {len(self.enemy_list)}'
        self.hud_enemies.x = 20 + hud_x
        self.hud_enemies.y = SCREEN_HEIGHT - 70 + hud_y
        self.hud_enemies.draw()
        self.corpse_list.draw()

        w = self.player.weapon.upper()
        ammo = self.player.ammo.get(self.player.weapon, 0)
        maxa = self.player.max_ammo.get(self.player.weapon, 0)
        reload_status = ' [RELOADING]' if self.player.reloading else ''
        self.hud_weapon.text = f'{w}: {ammo}/{maxa}{reload_status}'
        self.hud_weapon.x = 20 + hud_x
        self.hud_weapon.y = SCREEN_HEIGHT - 100 + hud_y
        self.hud_weapon.draw()

        # Цвет здоровья
        if self.player.health > 50:
            hc = arcade.color.GREEN
        elif self.player.health > 25:
            hc = arcade.color.YELLOW
        else:
            hc = arcade.color.RED
        self.hud_health.text = f'HEALTH: {self.player.health}'
        self.hud_health.color = hc
        self.hud_health.x = 20 + hud_x
        self.hud_health.y = SCREEN_HEIGHT - 130 + hud_y
        self.hud_health.draw()

        self.hud_controls.x = 20 + hud_x
        self.hud_controls.y = 20 + hud_y
        self.hud_controls.draw()


        # --- Пауза ---
        if self.paused:
            left, right = SCREEN_WIDTH // 2 - 200, SCREEN_WIDTH // 2 + 200
            bottom, top = SCREEN_HEIGHT // 2 - 50, SCREEN_HEIGHT // 2 + 50
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, (0, 0, 0, 120))
            self.paused_text.x = SCREEN_WIDTH // 2 + hud_x
            self.paused_text.y = SCREEN_HEIGHT // 2 + hud_y
            self.paused_text.draw()

        # --- Смерть игрока ---
        if not self.player.alive:
            left, right = SCREEN_WIDTH // 2 - 250, SCREEN_WIDTH // 2 + 250
            bottom, top = SCREEN_HEIGHT // 2 - 75, SCREEN_HEIGHT // 2 + 75
            arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, (0, 0, 0, 120))
            self.dead_title.x = SCREEN_WIDTH // 2 + hud_x
            self.dead_title.y = SCREEN_HEIGHT // 2 + 30 + hud_y
            self.dead_title.draw()
            self.dead_sub.x = SCREEN_WIDTH // 2 + hud_x
            self.dead_sub.y = SCREEN_HEIGHT // 2 - 30 + hud_y
            self.dead_sub.draw()

        if self.flash_timer > 0:
            arcade.draw_rectangle_filled(
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                (255, 255, 255, 90)
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
        if not self.player or not self.player.alive:
            return
        self.mouse_x = x
        self.mouse_y = y



    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.shoot()

    def shoot(self):
        if not self.player or not self.player.alive or self.paused or self.player.reloading:
            return

        # --- вычисляем направление прямо перед выстрелом ---
        dx = self.mouse_x - self.player.center_x
        dy = self.mouse_y - self.player.center_y

        # --- остальной код стрельбы ---

        # остальной код без изменений

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
        if not self.player or not self.player.alive or self.paused:
            return
        # остальной код без изменений

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

    def kill_enemy(self, enemy):
        corpse = arcade.Sprite(
            "assets/bloods.png",  # СПРАЙТ ЛЕЖАЩЕГО ЧУВАКА
            scale=enemy.scale
        )
        corpse.center_x = enemy.center_x
        corpse.center_y = enemy.center_y
        corpse.angle = enemy.angle

        self.corpse_list.append(corpse)
        enemy.remove_from_sprite_lists()

    # ---------------- Основной апдейт
    def update(self, delta_time):
        if self.paused:
            self.particle_list.update()
            self.bullet_list.update()
            return

        if not self.player or not self.player.alive:
            self.particle_list.update()
            self.bullet_list.update()
            if len(self.enemy_list) == 0:
                self.level += 1
                self.setup()
            return

        current_time = time.time()

        # --- Пули ---
        for bullet in self.bullet_list:
            bullet.update(delta_time)
            if arcade.check_for_collision_with_list(bullet, self.wall_list):
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

            enemies_hit = arcade.check_for_collision_with_list(bullet, self.enemy_list)
            if enemies_hit:
                for enemy in enemies_hit:
                    spawn_blood(self.particle_list, enemy.center_x, enemy.center_y)
                    self.kill_enemy(enemy)
                    enemy.kill_actor()
                bullet.kill()
                continue

        self.particle_list.update()

        # --- Перезарядка оружия ---
        if self.player.reloading:
            w = self.player.weapon
            if current_time - self.player.reload_timer > self.player.reload_time[w]:
                self.player.ammo[w] = self.player.max_ammo[w]
                self.player.reloading = False

        # --- AI врагов ---
        for enemy in self.enemy_list:
            action = enemy.update_ai(self.player, self.wall_list, delta_time)
            if action == 'attack':
                if ONE_HIT_PLAYER:
                    self.player.alive = False
                    self.player.kill()
                    self.message = 'YOU DIED - PRESS R TO RESTART'
                    return
                else:
                    self.player.health -= 20
                    if self.player.health <= 0:
                        self.player.alive = False
                        self.player.kill()
                        self.message = 'YOU DIED - PRESS R TO RESTART'
                        return

        # --- Движение игрока ---
        move_x = move_y = 0
        if self.keys_pressed[arcade.key.W]: move_y += 1
        if self.keys_pressed[arcade.key.S]: move_y -= 1
        if self.keys_pressed[arcade.key.A]: move_x -= 1
        if self.keys_pressed[arcade.key.D]: move_x += 1

        if move_x != 0 or move_y != 0:
            # нормализация диагонали
            if move_x != 0 and move_y != 0:
                move_x *= 0.7071
                move_y *= 0.7071

            # движение по X
            old_x = self.player.center_x
            self.player.center_x += move_x * self.player.speed * delta_time
            if arcade.check_for_collision_with_list(self.player, self.wall_list):
                self.player.center_x = old_x

            # движение по Y
            old_y = self.player.center_y
            self.player.center_y += move_y * self.player.speed * delta_time
            if arcade.check_for_collision_with_list(self.player, self.wall_list):
                self.player.center_y = old_y

            # частицы шагов
            if current_time - self.last_update_time > 0.05:
                for _ in range(2):
                    px = Particle(1, (100, 100, 100), 0, 0, life=random.randint(15, 25))
                    px.center_x = self.player.center_x + random.uniform(-5, 5)
                    px.center_y = self.player.center_y + random.uniform(-5, 5)
                    self.particle_list.append(px)
                self.last_update_time = current_time

        # --- Вращение к мышке ---
        dx = self.mouse_x - self.player.center_x
        dy = self.mouse_y - self.player.center_y
        if dx != 0 or dy != 0:
            self.player.angle = math.degrees(math.atan2(-dy, dx)) + 90

        # --- Победа на уровне ---
        if len(self.enemy_list) == 0:
            if not getattr(self, 'level_cleared', False):
                self.level_cleared = True
                self.level_cleared_time = current_time
                self.message = f'LEVEL {self.level} CLEARED! GET READY...'
                for _ in range(20):
                    px = Particle(random.randint(2, 4),
                                  (random.randint(200, 255), random.randint(200, 255), 50),
                                  random.uniform(-10, 10),
                                  random.uniform(-10, 10),
                                  life=random.randint(20, 40))
                    px.center_x = self.player.center_x
                    px.center_y = self.player.center_y
                    self.particle_list.append(px)

            elif current_time - self.level_cleared_time > 1.5:
                self.level_cleared = False
                self.level += 1
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