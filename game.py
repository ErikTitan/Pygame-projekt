import pygame
from player import Player
from enemy import Enemy
from projectile import Projectile
import random

class Game:
    def __init__(self):
        pygame.init()
        screen_info = pygame.display.Info()
        self.screen = pygame.display.set_mode((screen_info.current_w, screen_info.current_h), pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()

        self.BASE_TILE_SIZE = 16
        self.TILE_SIZE = 64   # velkost tile
        self.floor_tiles = [
            pygame.transform.scale(
                pygame.image.load(f"assets/map/floor{i}.png"),
                (self.TILE_SIZE, self.TILE_SIZE)
            ) for i in range(1, 5)
        ]
        self.wall_tiles = [
            pygame.transform.scale(
                pygame.image.load(f"assets/map/wall{i}.png"),
                (self.TILE_SIZE, self.TILE_SIZE)
            ) for i in range(1, 5)
        ]

        self.create_map()
        self.player = Player(3 * self.TILE_SIZE, 3 * self.TILE_SIZE)
        self.camera_x = 0
        self.camera_y = 0

        self.enemies = []
        self.projectiles = []
        self.player_element = "fire" # default element
        self.spawn_timer = 0
        self.spawn_delay = 180
        self.can_shoot = True
        self.shoot_cooldown = 300
        self.last_shot_time = 0

    def create_map(self):
        self.walls = []

        # Create the basic layout
        self.layout = [
            "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
            "W...............................................................W",
            "W...............................................................W",
            "W...............................................................W",
            "W...............................................................W",
            "W....................WWWWWWWWWW...WWWWWWWWWWWW..................W",
            "W...............................................................W",
            "W...............................................................W",
            "WWWWWW...WW......................................................W",
            "W........WW......................................................W",
            "W........WWWWWWWWWWWWWWWWWWWWW....................................W",
            "W.................................................................W",
            "W..........................................WWWWWWWWWWWWWWWWWWW....W",
            "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW........W...................W....W",
            "W..........................W........W...................W....W",
            "W..........................W........W...................W....W",
            "W..........................W........W...................W....W",
            "W..........................WWWWWWWWW...................W....W",
            "W..........................W........W...................W....W",
            "W..........................W........W...................W....W",
            "W..........................W........W...................W....W",
            "WWWWWWWWWWWWWWWWWWWWWW....WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW....W",
            "W...............................................................W",
            "W...............................................................W",
            "W...............................................................W",
            "W.WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW................W",
            "W.W.........................................................W...W",
            "W.W.........................................................W...W",
            "W.W.........................................................W...W",
            "W.W.........................................................W...W",
            "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW"
        ]

        width = len(self.layout[0])
        self.layout = [row.ljust(width, '.') for row in self.layout]

        # Create random floor layout
        self.floor_layout = []
        for y in range(len(self.layout)):
            row = []
            for x in range(len(self.layout[0])):
                if self.layout[y][x] != 'W':
                    row.append(random.randint(0, 3))  # Random floor tile (0-3 for floor1-4)
                else:
                    row.append(-1)  # No floor under walls
            self.floor_layout.append(row)

        # Create random wall layout
        self.wall_layout = []
        for y in range(len(self.layout)):
            row = []
            for x in range(len(self.layout[0])):
                if self.layout[y][x] == 'W':
                    row.append(random.randint(0, 3))  # Random wall tile (0-3 for wall1-4)
                    self.walls.append(pygame.Rect(x * self.TILE_SIZE, y * self.TILE_SIZE,
                                                  self.TILE_SIZE, self.TILE_SIZE))
                else:
                    row.append(-1)
            self.wall_layout.append(row)

    def get_random_spawn_position(self):
        while True:
            # nahodna pozicia v mape
            x = random.randint(1, len(self.layout[0]) - 2) * self.TILE_SIZE
            y = random.randint(1, len(self.layout) - 2) * self.TILE_SIZE

            # test rect pre poziciu
            test_rect = pygame.Rect(x, y, self.TILE_SIZE, self.TILE_SIZE)

            # pozicia nesmie byt v stene
            if not any(test_rect.colliderect(wall) for wall in self.walls):
                if self.layout[y // self.TILE_SIZE][x // self.TILE_SIZE] != 'W':
                    return (x, y)

    def spawn_enemy(self):
        if len(self.enemies) < 10 and self.spawn_timer <= 0:
            spawn_pos = self.get_random_spawn_position()
            element = random.choice(["fire", "water", "ground", "air"])
            self.enemies.append(Enemy(*spawn_pos, element))
            self.spawn_timer = self.spawn_delay

    def handle_input(self):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * self.player.speed
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * self.player.speed
        self.camera_x = self.player.rect.x - self.screen.get_width() // 2
        self.camera_y = self.player.rect.y - self.screen.get_height() // 2
        self.player.move(dx, dy, self.walls)
        if keys[pygame.K_ESCAPE]:
            return False

        # prepinanie elementov
        if keys[pygame.K_1]:
            self.player_element = "fire"
        elif keys[pygame.K_2]:
            self.player_element = "water"
        elif keys[pygame.K_3]:
            self.player_element = "ground"
        elif keys[pygame.K_4]:
            self.player_element = "air"

        # strielanie
        current_time = pygame.time.get_ticks()
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            target_x = mouse_x + self.camera_x
            target_y = mouse_y + self.camera_y
            self.projectiles.append(Projectile(
                self.player.rect.centerx,
                self.player.rect.centery,
                target_x,
                target_y,
                self.player_element
            ))
            self.last_shot_time = current_time
            self.can_shoot = False

        # cooldown pre strelbu
        if not self.can_shoot:
            if current_time - self.last_shot_time >= self.shoot_cooldown:
                self.can_shoot = True

        return True

    def update(self):
        # posunut nepriatelov
        for enemy in self.enemies[:]:
            enemy.move_towards_player(
                (self.player.rect.x, self.player.rect.y),
                self.walls
            )

        # posunut strely
        for projectile in self.projectiles[:]:
            projectile.update()
            if projectile.hits_wall(self.walls):
                self.projectiles.remove(projectile)
            else:
                # kontrola zasahu
                for enemy in self.enemies[:]:
                    if projectile.rect.colliderect(enemy.rect):
                        if self.is_effective_against(projectile.element_type, enemy.element_type):
                            self.enemies.remove(enemy)
                        self.projectiles.remove(projectile)
                        break

        # spawn enemy
        self.spawn_timer -= 1
        self.spawn_enemy()

    def is_effective_against(self, attacker, defender):
        effectiveness = {
            "fire": "water",
            "water": "fire",
            "ground": "air",
            "air": "ground"
        }
        return effectiveness[attacker] == defender

    def draw(self):
        self.screen.fill((37, 19, 26))

        # Draw all floors and walls
        for y in range(len(self.layout)):
            for x in range(len(self.layout[0])):
                screen_x = x * self.TILE_SIZE - self.camera_x
                screen_y = y * self.TILE_SIZE - self.camera_y

                # Draw floor if present
                if self.floor_layout[y][x] != -1:
                    self.screen.blit(self.floor_tiles[self.floor_layout[y][x]], (screen_x, screen_y))

                # Draw wall if present
                if self.wall_layout[y][x] != -1:
                    self.screen.blit(self.wall_tiles[self.wall_layout[y][x]], (screen_x, screen_y))

        # Draw player
        self.player.draw(self.screen, self.camera_x, self.camera_y)

        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera_x, self.camera_y)

        # Draw projectiles
        for projectile in self.projectiles:
            pygame.draw.rect(
                self.screen,
                projectile.colors[projectile.element_type],
                pygame.Rect(
                    projectile.rect.x - self.camera_x,
                    projectile.rect.y - self.camera_y,
                    16, 16
                )
            )

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            running = self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()