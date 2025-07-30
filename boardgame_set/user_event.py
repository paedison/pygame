import pygame


class UserEvent:
    load_check_set = pygame.USEREVENT + 1  # 32867
    set_success = pygame.USEREVENT + 2  # 32868
    animation_done = pygame.USEREVENT + 3  # 32869
    game_over = pygame.USEREVENT + 4  # 32870
    replace_all_cards = pygame.USEREVENT + 5 # 32871
