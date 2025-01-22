import pygame
import time
import random

pygame.font.init()

WIDTH, HEIGHT = 1200, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Dodge")

try:
    BG = pygame.transform.scale(pygame.image.load("bg.jpeg"), (WIDTH, HEIGHT))
except pygame.error:
    BG = None  # You can add a solid color background here if needed

PLAYER_WIDTH = 35
PLAYER_HEIGHT = 60

PLAYER_VEL = 5
STAR_WIDTH = 10
STAR_HEIGHT = 20
STAR_VEL = 3

FONT = pygame.font.SysFont("comicsans", 30)


def draw(player, elapsed_time, stars, lives):
    WIN.blit(BG, (0, 0))

    time_text = FONT.render(f"Time: {round(elapsed_time)}s", 1, "white")
    WIN.blit(time_text, (10, 10))

    lives_text = FONT.render(f"Lives: {lives}", 1, "white")
    WIN.blit(lives_text, (WIDTH - 100, 10))

    pygame.draw.rect(WIN, "red", player)

    for star in stars:
        pygame.draw.rect(WIN, "white", star)

    pygame.display.update()


def ai_move(player, stars, danger_zone=180, horizontal_margin=0.2, packed_threshold=5):
    """
    AI to dodge stars by detecting obstacles within the danger zone.
    The AI attempts to dodge stars that are within a vertical 'danger zone'
    and uses a horizontal margin for precise dodging.
    If both sides are heavily packed with stars, the player will not move.
    """
    player_center_x = player.x + player.width // 2  # Center of the player

    # Count of stars in the danger zone on the left and right sides
    left_star_count = 0
    right_star_count = 0

    # Look at each star and determine if it's within the danger zone
    for star in stars:
        if 0 <= player.y - star.y <= danger_zone:
            if star.x < player_center_x:  # Star is on the left side
                left_star_count += 1
            elif star.x > player_center_x:  # Star is on the right side
                right_star_count += 1

    # If both sides are heavily packed, do not move
    if left_star_count >= packed_threshold and right_star_count >= packed_threshold:
        return  # No movement needed, exit the function

    # Variables to track if the AI should move left or right
    move_left = False
    move_right = False

    # Check for stars that require dodging
    for star in stars:
        if 0 <= player.y - star.y <= danger_zone:
            # If the star is horizontally aligned with the player, decide which way to dodge
            if star.x < player_center_x and (player_center_x - star.x) <= player.width * (1 + horizontal_margin):
                move_right = True  # Star is to the left, move right
            elif star.x > player_center_x and (star.x - player_center_x) <= player.width * (1 + horizontal_margin):
                move_left = True  # Star is to the right, move left

    # Move the player based on the closest threat
    if move_left and player.x - PLAYER_VEL >= 0:
        player.x -= PLAYER_VEL  # Move left
    elif move_right and player.x + PLAYER_VEL + player.width <= WIDTH:
        player.x += PLAYER_VEL  # Move right

    # Parameters to define zones (left, center, right)
    left_zone_end = WIDTH // 3
    right_zone_start = 2 * WIDTH // 3
    player_x_center = player.x + player.width // 2
    vertical_proximity_threshold = PLAYER_HEIGHT * 1.5  # Defines how far above the player stars will be detected

    # Track free space in the left, center, and right zones
    left_free_space = 0
    center_free_space = 0
    right_free_space = 0

    # Evaluate the free space in each zone
    for star in stars:
        if star.y < player.y:  # Consider stars that are above the player

            # Left zone evaluation
            if star.x < left_zone_end:
                left_free_space -= (player.y - star.y)  # Closer stars reduce free space
            # Center zone evaluation
            elif left_zone_end <= star.x < right_zone_start:
                center_free_space -= (player.y - star.y)
            # Right zone evaluation
            else:
                right_free_space -= (player.y - star.y)

    # Normalize free space (higher values are better)
    left_free_space += player.y * (left_zone_end / WIDTH)  # Weight the free space based on zone size
    center_free_space += player.y * ((right_zone_start - left_zone_end) / WIDTH)
    right_free_space += player.y * ((WIDTH - right_zone_start) / WIDTH)

    # AI decision-making based on the most free space
    if left_free_space > center_free_space and left_free_space > right_free_space:
        move_direction = "left"
    elif right_free_space > center_free_space:
        move_direction = "right"
    else:
        move_direction = " "

    # Dynamic velocity based on free space: faster if space is closing in
    dynamic_vel = PLAYER_VEL + 2 if min(left_free_space, center_free_space, right_free_space) < 200 else PLAYER_VEL

    # **Path Clearance Check**: Look ahead multiple steps to detect stars
    imminent_collision = False
    steps_ahead = 4 # Number of steps to check ahead
    future_positions = [player.x - dynamic_vel * step for step in range(1, steps_ahead + 1)] if move_direction == "left" else \
        [player.x + dynamic_vel * step for step in range(1, steps_ahead + 1)]

    # **Vertical Proximity Check**: Check for stars slightly above the player
    star_above = False
    for star in stars:
        if player.y - vertical_proximity_threshold < star.y < player.y:  # Star is slightly above the player
            if move_direction == "left" and player.x - dynamic_vel < star.x + STAR_WIDTH and star.x < player.x:
                star_above = True
            elif move_direction == "right" and player.x + dynamic_vel + PLAYER_WIDTH > star.x and star.x > player.x:
                star_above = True

    # If a star is slightly above, take extra caution
    if star_above:
        imminent_collision = True

    # **Real-time collision detection and continuous dodging**
    for future_pos in future_positions:
        for star in stars:
            if player.y < star.y < player.y + PLAYER_HEIGHT:  # Star is in the horizontal path
                if move_direction == "left" and future_pos < star.x + STAR_WIDTH and star.x < player.x:
                    imminent_collision = True
                elif move_direction == "right" and future_pos + PLAYER_WIDTH > star.x and star.x > player.x:
                    imminent_collision = True
                if imminent_collision:
                    break  # Stop further checks if a collision is detected

    # **Continuous Dodging**: If there’s a collision or a star slightly above, adjust position
    if imminent_collision:
        # If star is on the left, try moving right and vice versa
        if move_direction == "left":
            if player.x + dynamic_vel + player.width <= WIDTH:
                player.x += dynamic_vel  # Try moving right if space allows
            elif player.y - PLAYER_VEL >= 0:  # If no horizontal room, move vertically
                player.y -= PLAYER_VEL
        elif move_direction == "right":
            if player.x - dynamic_vel >= 0:
                player.x -= dynamic_vel  # Try moving left if space allows
            elif player.y - PLAYER_VEL >= 0:
                player.y -= PLAYER_VEL  # If no horizontal room, move vertically
    else:
        # No collision detected, continue with the original plan
        if move_direction == "left" and player.x - dynamic_vel >= 0:
            player.x -= dynamic_vel
        elif move_direction == "right" and player.x + dynamic_vel + player.width <= WIDTH:
            player.x += dynamic_vel
        elif move_direction == "center":
            # Move toward the center if it's the safest zone
            if player_x_center < WIDTH // 2 and player.x + dynamic_vel + player.width <= WIDTH:
                player.x += dynamic_vel
            elif player_x_center > WIDTH // 2 and player.x - dynamic_vel >= 0:
                player.x -= dynamic_vel


def ask_user_to_play():
    """
    Display a message asking the user to press Y for yes or N for no.
    Return True if the user presses Y (wants to play), otherwise False.
    """
    asking = True
    while asking:
        WIN.fill((0, 0, 0))  # Fill the screen with black
        question_text = FONT.render("Do you want to play? Press Y for Yes or N to let AI play", 1, "white")
        WIN.blit(question_text,
                 (WIDTH / 2 - question_text.get_width() / 2, HEIGHT / 2 - question_text.get_height() / 2))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_y]:
                return True
            if keys[pygame.K_n]:
                return False


def main():
    run = True
    player_lives = 3  # Player starts with 3 lives
    restart_game = False

    # Ask the user if they want to play or watch AI play
    player_control = ask_user_to_play()

    while run:
        player = pygame.Rect(200, HEIGHT - PLAYER_HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT)
        clock = pygame.time.Clock()
        start_time = time.time()
        elapsed_time = 0

        star_add_increment = 2000
        star_count = 0

        stars = []
        hit = False

        while player_lives > 0 and not restart_game:
            star_count += clock.tick(60)
            elapsed_time = time.time() - start_time

            if star_count > star_add_increment:
                for _ in range(3):
                    star_x = random.randint(0, WIDTH - STAR_WIDTH)
                    star = pygame.Rect(star_x, -STAR_HEIGHT, STAR_WIDTH, STAR_HEIGHT)
                    stars.append(star)

                star_add_increment = max(200, star_add_increment - 50)
                star_count = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    restart_game = True  # To exit outer loop
                    break

            keys = pygame.key.get_pressed()

            # Check if player or AI controls the character
            if player_control:
                # Player controls
                if keys[pygame.K_LEFT] and player.x - PLAYER_VEL >= 0:
                    player.x -= PLAYER_VEL
                if keys[pygame.K_RIGHT] and player.x + PLAYER_VEL + player.width <= WIDTH:
                    player.x += PLAYER_VEL
            else:
                # AI controls the player
                ai_move(player, stars)

            for star in stars[:]:
                star.y += STAR_VEL
                if star.y > HEIGHT:
                    stars.remove(star)
                elif star.y + star.height >= player.y and star.colliderect(player):
                    stars.remove(star)
                    player_lives -= 1  # Lose a life
                    break

            if player_lives <= 0:
                lost_text = FONT.render("You Lost!", 1, "white")
                WIN.blit(lost_text, (WIDTH / 2 - lost_text.get_width() / 2, HEIGHT / 2 - lost_text.get_height() / 2))
                restart_text = FONT.render("Press R to Restart", 1, "white")
                WIN.blit(restart_text, (WIDTH / 2 - restart_text.get_width() / 2, HEIGHT / 2 + 50))
                pygame.display.update()

                # Wait for the player to press 'R' to restart
                wait_for_restart = True
                while wait_for_restart:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            run = False
                            wait_for_restart = False
                        keys = pygame.key.get_pressed()
                        if keys[pygame.K_r]:
                            restart_game = True  # Restart the game
                            wait_for_restart = False

                break

            draw(player, elapsed_time, stars, player_lives)

        if not run:  # Break from the outer loop if the game is closed
            break

        # Reset game variables if player chooses to restart
        if restart_game:
            player_lives = 3
            restart_game = False

            # Ask the user again if they want to play or let AI play
            player_control = ask_user_to_play()

    pygame.quit()


if __name__ == "__main__":
    main()