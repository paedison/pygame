import pygame


class UserEvent:
    load_check_set = pygame.USEREVENT + 1
    set_success = pygame.USEREVENT + 2
    animation_done = pygame.USEREVENT + 3
    game_over = pygame.USEREVENT + 4
