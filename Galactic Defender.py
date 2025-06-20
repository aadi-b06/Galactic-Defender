import pygame
import random
import math
import os
import sys
from pygame import mixer
# ===== VIDEO BACKGROUND IMPORTS =====
# Add these at the VERY TOP with other imports
import threading
import queue
import cv2
import numpy as np
# ====================================

# Initialize pygame
pygame.init()
pygame.mixer.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (225, 0, 0)  # NECESSARY FOR GAME OVER TEXT
GREEN = (0, 255, 0)
GREY = (128, 128, 128)  # FOR ENEMIES/BLOCKS
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# ===== VIDEO INITIALIZATION =====
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Galactic Defender")

video_path = r"D:\VIT\1st year\Module 2\Python for engineers\cp\5-135665794.mp4"  # ← Verify this path is correct!
video_clock = pygame.time.Clock()
video_frame = None

# Initialize video capture
cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("Error: Could not open video file!")
    # Fallback to black background
    video_background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    video_background.fill(BLACK)
else:
    ret, frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.rot90(frame)
        video_background = pygame.surfarray.make_surface(frame)
    else:
        video_background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        video_background.fill(BLACK)
# ================================

# Game clock
clock = pygame.time.Clock()
FPS = 60

def load_image(name, scale=1):
    try:
        image = pygame.image.load(f"assets/{name}.png").convert_alpha()
        width = int(image.get_width() * scale)
        height = int(image.get_height() * scale)
        return pygame.transform.scale(image, (width, height))
    except:
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        if name == "player":
            pygame.draw.polygon(surf, GREEN, [(25, 0), (5, 45), (45, 45)])
            pygame.draw.rect(surf, GREEN, (20, 15, 10, 30))
            pygame.draw.polygon(surf, GREEN, [(0, 30), (20, 30), (10, 40)])
            pygame.draw.polygon(surf, GREEN, [(50, 30), (30, 30), (40, 40)])
        else:
            # Changed from RED to GREY
            pygame.draw.rect(surf, GREY, (0, 0, 50, 50), 2)
        return pygame.transform.scale(surf, (int(50 * scale), int(50 * scale)))

def load_sound(name):
    try:
        return mixer.Sound(f"assets/{name}.wav")
    except:
        return None

# Create assets directory if it doesn't exist
if not os.path.exists("assets"):
    os.makedirs("assets")

# Fonts
font_small = pygame.font.SysFont("arial", 20)
font_medium = pygame.font.SysFont("arial", 30)
font_large = pygame.font.SysFont("arial", 50)

# Game variables
game_state = "menu"  # menu, playing, gameover, level_complete
level = 1
score = 0
high_score = 0
lives = 3

# Load high score
try:
    with open("assets/highscore.txt", "r") as f:
        high_score = int(f.read())
except:
    pass

# Sound effects
try:
    shoot_sound = load_sound("shoot")
    explosion_sound = load_sound("explosion")
    powerup_sound = load_sound("powerup")
    level_complete_sound = load_sound("level_complete")
    game_over_sound = load_sound("game_over")
    background_music = load_sound("background")
    
    if background_music:
        background_music.play(-1)  # Loop background music
except:
    # Placeholder sounds if files not found
    shoot_sound = None
    explosion_sound = None
    powerup_sound = None
    level_complete_sound = None
    game_over_sound = None
    background_music = None
    
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (225, 0, 0)  # NECESSARY FOR GAME OVER TEXT
GREEN = (0, 255, 0)
GREY = (128, 128, 128)  # FOR ENEMIES/BLOCKS
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# Game clock
clock = pygame.time.Clock()
FPS = 60

class Bullet(pygame.sprite.Sprite):  # MOVED ABOVE PLAYER CLASS
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 15))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -10
        
    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=4, angle=0):
        super().__init__()
        self.image = pygame.Surface((5, 15))
        self.image.fill(YELLOW)  # <-- MUST BE YELLOW
        self.rect = self.image.get_rect()
        # ... rest of the code ...
        self.rect.centerx = x
        self.rect.top = y
        self.speed = speed
        self.angle = angle
        self.x_vel = math.sin(angle) * speed if angle != 0 else 0
        self.y_vel = math.cos(angle) * speed
        
    def update(self):
        if self.angle == 0:
            self.rect.y += self.speed
        else:
            self.rect.x += self.x_vel
            self.rect.y += self.y_vel
            
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = load_image("player", 0.7)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed = 8
        self.shoot_delay = 250
        self.last_shot = pygame.time.get_ticks()
        self.rapid_fire = False
        self.rapid_fire_end_time = 0
        self.shield = False
        self.shield_end_time = 0
        self.shield_alpha = 180
        self.shield_radius = 40
        
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
            self.rect.x += self.speed
            
        now = pygame.time.get_ticks()
        if self.rapid_fire and now > self.rapid_fire_end_time:
            self.rapid_fire = False
            self.shoot_delay = 250
            
        if self.shield and now > self.shield_end_time:
            self.shield = False
            
    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            player_bullets.add(bullet)
            if shoot_sound:
                shoot_sound.play()

    def draw_shield(self, surface):
        if self.shield:
            shield_surf = pygame.Surface((self.shield_radius * 2, self.shield_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(shield_surf, (0, 100, 255, self.shield_alpha), 
                              (self.shield_radius, self.shield_radius), self.shield_radius)
            surface.blit(shield_surf, (self.rect.centerx - self.shield_radius, 
                                      self.rect.centery - self.shield_radius))
            
    def activate_powerup(self, type, duration=5000):
        if type == "rapid_fire":
            self.rapid_fire = True
            self.shoot_delay = 100
            self.rapid_fire_end_time = pygame.time.get_ticks() + duration
        elif type == "shield":
            self.shield = True
            self.shield_end_time = pygame.time.get_ticks() + duration
        elif type == "extra_life":
            global lives
            lives += 1
            
        if powerup_sound:
            powerup_sound.play()

def load_image(name, scale=1):
    try:
        image = pygame.image.load(f"assets/{name}.png").convert_alpha()
        width = int(image.get_width() * scale)
        height = int(image.get_height() * scale)
        return pygame.transform.scale(image, (width, height))
    except:
        surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        if name == "player":
            pygame.draw.polygon(surf, GREEN, [(25, 0), (5, 45), (45, 45)])
            pygame.draw.rect(surf, GREEN, (20, 15, 10, 30))
            pygame.draw.polygon(surf, GREEN, [(0, 30), (20, 30), (10, 40)])
            pygame.draw.polygon(surf, GREEN, [(50, 30), (30, 30), (40, 40)])
        else:
            # Fully grey block with dark border
            surf.fill(GREY)  # Fill entire surface with grey
            pygame.draw.rect(surf, (50, 50, 50), (0, 0, 50, 50), 2)  # Dark border
        return pygame.transform.scale(surf, (int(50 * scale), int(50 * scale)))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, enemy_type="basic"):
        super().__init__()
        self.enemy_type = enemy_type
        
        if enemy_type == "basic":
            self.image = load_image("enemy1", 0.4)
            self.health = 1
            self.score_value = 10
            self.speed = 2
        elif enemy_type == "fast":
            self.image = load_image("enemy2", 0.35)
            self.health = 1
            self.score_value = 15
            self.speed = 4
        elif enemy_type == "tank":
            self.image = load_image("enemy3", 0.5)
            self.health = 3
            self.score_value = 30
            self.speed = 1
            
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = 1  # 1 for right, -1 for left
        self.move_counter = 0
        self.move_limit = random.randint(30, 100)
        self.shoot_delay = random.randint(1000, 3000)
        self.last_shot = pygame.time.get_ticks()
        
    def update(self):
        # Horizontal movement
        self.rect.x += self.speed * self.direction
        self.move_counter += 1
        
        # Change direction when hitting screen edge or move limit
        if self.rect.right >= SCREEN_WIDTH or self.rect.left <= 0 or self.move_counter >= self.move_limit:
            self.direction *= -1
            self.move_counter = 0
            self.rect.y += 20  # Move down
            
        # Random shooting
        if random.random() < 0.001 and pygame.time.get_ticks() - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = pygame.time.get_ticks()
            
    def shoot(self):
        bullet = EnemyBullet(self.rect.centerx, self.rect.bottom)
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)
        
    def hit(self):
        self.health -= 1
        if self.health <= 0:
            global score
            score += self.score_value
            if explosion_sound:
                explosion_sound.play()
            # Chance to drop powerup
            if random.random() < 0.15:
                self.drop_powerup()
            self.kill()
            return True
        return False
        
    def drop_powerup(self):
        powerup_type = random.choice(["rapid_fire", "shield", "extra_life"])
        powerup = PowerUp(self.rect.centerx, self.rect.centery, powerup_type)
        all_sprites.add(powerup)
        powerups.add(powerup)

class Boss(Enemy):
    def __init__(self):
        super().__init__(SCREEN_WIDTH // 2 - 50, 50, "boss")
        self.image = load_image("boss", 0.7)
        self.health = 20 * level
        self.score_value = 100 * level
        self.speed = 3
        self.shoot_delay = 1000
        self.last_shot = pygame.time.get_ticks()
        self.pattern = 0
        self.pattern_timer = 0
        self.phase = 1
        
    def update(self):
        # Movement pattern
        self.pattern_timer += 1
        
        if self.pattern == 0:  # Horizontal sweep
            self.rect.x += self.speed
            if self.rect.right > SCREEN_WIDTH or self.rect.left < 0:
                self.speed *= -1
                self.rect.y += 20
                
            if self.pattern_timer > 200:
                self.pattern = random.randint(1, 2)
                self.pattern_timer = 0
                
        elif self.pattern == 1:  # Circle pattern
            angle = self.pattern_timer * 0.05
            radius = 100
            center_x = SCREEN_WIDTH // 2
            center_y = 150
            self.rect.x = center_x + math.cos(angle) * radius - self.rect.width // 2
            self.rect.y = center_y + math.sin(angle) * radius - self.rect.height // 2
            
            if self.pattern_timer > 200:
                self.pattern = random.randint(0, 1)
                self.pattern_timer = 0
                
        # Shooting
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now
            
        # Phase change
        if self.health <= self.health // 2 and self.phase == 1:
            self.phase = 2
            self.speed *= 1.5
            self.shoot_delay = 500
            
    def shoot(self):
        if self.phase == 1:
            # Single shot
            bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, speed=5)
            all_sprites.add(bullet)
            enemy_bullets.add(bullet)
        else:
            # Spread shot
            for angle in range(-30, 31, 15):
                rad = math.radians(angle)
                bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, 
                                   speed=5, angle=rad)
                all_sprites.add(bullet)
                enemy_bullets.add(bullet)

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed=4, angle=0):
        super().__init__()
        self.image = pygame.Surface((5, 15))
        self.image.fill(GREY)  # Changed from RED to GREY
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speed = speed
        self.angle = angle
        self.x_vel = math.sin(angle) * speed if angle != 0 else 0
        self.y_vel = math.cos(angle) * speed
        
    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, type):
        super().__init__()
        self.type = type
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        
        if type == "rapid_fire":
            pygame.draw.circle(self.image, YELLOW, (15, 15), 15)
            pygame.draw.rect(self.image, BLACK, (12, 10, 6, 10))
            pygame.draw.rect(self.image, BLACK, (10, 12, 10, 6))
        elif type == "shield":
            pygame.draw.circle(self.image, BLUE, (15, 15), 15)
            pygame.draw.circle(self.image, BLACK, (15, 15), 15, 2)
        elif type == "extra_life":
            pygame.draw.polygon(self.image, GREEN, [(15, 5), (5, 25), (25, 25)])
            
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.speed = 2
        
    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, size="large"):
        super().__init__()
        self.size = size
        self.images = []
        
        if size == "large":
            radius = 30
            frames = 10
        else:
            radius = 15
            frames = 5
            
        for i in range(frames):
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            alpha = 255 - (i * (255 // frames))
            pygame.draw.circle(surf, (255, 165, 0, alpha), (radius, radius), radius - i * 2)
            self.images.append(surf)
            
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.animation_time = pygame.time.get_ticks()
        self.animation_delay = 50
        
    def update(self):
        now = pygame.time.get_ticks()
        if now - self.animation_time > self.animation_delay:
            self.animation_time = now
            self.index += 1
            if self.index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.index]

# Sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
player_bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()
powerups = pygame.sprite.Group()

# Create player
player = Player()
all_sprites.add(player)

def create_enemies():
    enemies.empty()
    
    if level < 3:
        # Regular level with multiple enemies
        enemy_types = ["basic", "fast", "tank"]
        weights = [0.6, 0.3, 0.1] if level == 1 else [0.4, 0.4, 0.2]
        
        for row in range(4):
            for col in range(8):
                enemy_type = random.choices(enemy_types, weights=weights)[0]
                enemy = Enemy(100 + col * 75, 50 + row * 60, enemy_type)
                all_sprites.add(enemy)
                enemies.add(enemy)
    else:
        # Boss level
        boss = Boss()
        all_sprites.add(boss)
        enemies.add(boss)

def draw_text(text, font, color, x, y, centered=False):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if centered:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    screen.blit(text_surface, text_rect)

def show_menu():
    global game_state, video_background, cap
    
    waiting = True
    while waiting:
        # Update video frame
        if cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                # Loop the video
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                video_background = pygame.surfarray.make_surface(frame)
        
        # Draw video background
        screen.blit(video_background, (0, 0))
        
        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Original menu text
        draw_text("GALACTIC DEFENDER", font_large, WHITE, SCREEN_WIDTH//2, 150, True)
        draw_text(f"High Score: {high_score}", font_medium, YELLOW, SCREEN_WIDTH//2, 220, True)
        draw_text("Press SPACE to Start", font_medium, GREEN, SCREEN_WIDTH//2, 300, True)
        # ... keep other text elements ...
        
        # Handle events frequently
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                    game_state = "playing"
                    reset_game()
        
        pygame.display.flip()
        video_clock.tick(30)  # Limit to 30 FPS for menu
        
def reset_game():
    global score, lives, level, all_sprites, enemies, player_bullets, enemy_bullets, powerups, player
    
    score = 0
    lives = 3
    level = 1
    
    # Clear all sprites
    all_sprites.empty()
    enemies.empty()
    player_bullets.empty()
    enemy_bullets.empty()
    powerups.empty()
    
    # Create new player and enemies
    player = Player()
    all_sprites.add(player)
    create_enemies()

def show_game_over():
    global game_state, high_score
    
    # Update high score
    if score > high_score:
        high_score = score
        with open("assets/highscore.txt", "w") as f:
            f.write(str(high_score))
    
    screen.fill(BLACK)
    draw_text("GAME OVER", font_large, RED, SCREEN_WIDTH // 2, 200, True)
    draw_text(f"Score: {score}", font_medium, WHITE, SCREEN_WIDTH // 2, 280, True)
    draw_text(f"High Score: {high_score}", font_medium, YELLOW, SCREEN_WIDTH // 2, 330, True)
    draw_text("Press SPACE to Play Again", font_medium, GREEN, SCREEN_WIDTH // 2, 400, True)
    draw_text("Press ESC to Quit", font_small, WHITE, SCREEN_WIDTH // 2, 450, True)
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                    game_state = "menu"
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

def show_level_complete():
    global game_state, level
    
    screen.fill(BLACK)
    draw_text(f"LEVEL {level} COMPLETE!", font_large, GREEN, SCREEN_WIDTH // 2, 250, True)
    draw_text(f"Score: {score}", font_medium, WHITE, SCREEN_WIDTH // 2, 320, True)
    draw_text("Press SPACE to Continue", font_medium, YELLOW, SCREEN_WIDTH // 2, 400, True)
    
    pygame.display.flip()
    
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                    level += 1
                    if level > 3:
                        game_state = "gameover"
                        show_game_over()
                    else:
                        game_state = "playing"
                        # Clear existing enemies and create new ones
                        all_sprites.empty()
                        player_bullets.empty()
                        enemy_bullets.empty()
                        powerups.empty()
                        all_sprites.add(player)
                        create_enemies()

# Main game loop
running = True
create_enemies()

while running:
    # Keep loop running at the right speed
    clock.tick(FPS)
    
    # Process input/events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and game_state == "playing":
                player.shoot()
            if event.key == pygame.K_ESCAPE:
                running = False
    
    # Update
    if game_state == "playing":
        all_sprites.update()
        
        # Check for player bullet hits on enemies
        hits = pygame.sprite.groupcollide(enemies, player_bullets, False, True)
        for enemy, bullets in hits.items():
            for bullet in bullets:
                enemy.hit()
        
        # Check for enemy bullet hits on player
        if not player.shield:
            hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
            for hit in hits:
                lives -= 1
                explosion = Explosion(player.rect.centerx, player.rect.centery)
                all_sprites.add(explosion)
                if explosion_sound:
                    explosion_sound.play()
                if lives <= 0:
                    game_state = "gameover"
                    if game_over_sound:
                        game_over_sound.play()
        
        # Check for powerup collisions
        hits = pygame.sprite.spritecollide(player, powerups, True)
        for hit in hits:
            player.activate_powerup(hit.type)
        
        # Check if player hit an enemy
        if not player.shield:
            hits = pygame.sprite.spritecollide(player, enemies, False)
            for hit in hits:
                lives -= 1
                explosion = Explosion(player.rect.centerx, player.rect.centery)
                all_sprites.add(explosion)
                if explosion_sound:
                    explosion_sound.play()
                hit.kill()
                if lives <= 0:
                    game_state = "gameover"
                    if game_over_sound:
                        game_over_sound.play()
        
        # Check if all enemies are defeated
        if len(enemies) == 0:
            game_state = "level_complete"
            if level_complete_sound:
                level_complete_sound.play()
    
    # Draw/render
    screen.fill(BLACK)
    
    # Draw star background
    for i in range(100):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        pygame.draw.circle(screen, WHITE, (x, y), 1)
    
    if game_state == "playing":
        all_sprites.draw(screen)
        player.draw_shield(screen)
        
        # Draw UI
        draw_text(f"Score: {score}", font_small, WHITE, 10, 10)
        draw_text(f"Lives: {lives}", font_small, WHITE, 10, 40)
        draw_text(f"Level: {level}", font_small, WHITE, 10, 70)
        
        # Draw powerup indicators
        if player.rapid_fire:
            time_left = max(0, (player.rapid_fire_end_time - pygame.time.get_ticks()) // 1000)
            draw_text(f"Rapid Fire: {time_left}s", font_small, YELLOW, SCREEN_WIDTH - 150, 10)
        if player.shield:
            time_left = max(0, (player.shield_end_time - pygame.time.get_ticks()) // 1000)
            draw_text(f"Shield: {time_left}s", font_small, BLUE, SCREEN_WIDTH - 150, 40)
    
    elif game_state == "menu":
        show_menu()
    elif game_state == "gameover":
        show_game_over()
    elif game_state == "level_complete":
        show_level_complete()
    
    # Flip the display
    pygame.display.flip()
    
    # Add this right before pygame.quit()
stop_video_thread = True
if video_thread.is_alive():
    video_thread.join(timeout=1)

if 'cap' in globals() and cap.isOpened():
    cap.release()
    
# ===== VIDEO CLEANUP =====
cap.release()
# ========================
pygame.quit()