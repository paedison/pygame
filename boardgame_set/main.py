import random
from itertools import combinations

import pygame

from boardgame_set.user_event import UserEvent
from boardgame_set.inerface import Button, Card
from boardgame_set.logger import DebugLogger, GameLogger
from boardgame_set import constants as CONST  # noqa

user_event = UserEvent()
debug_logger = DebugLogger()
logger = GameLogger()

pygame.init()
FONT_1 = pygame.font.SysFont("나눔고딕", 20)


def generate_deck(for_test=False):
    colors = ['red', 'green', 'purple']
    shapes = ['oval', 'squiggle', 'diamond']
    counts = [1, 2, 3]
    fills = ['solid', 'striped', 'open']
    deck = [Card(c, s, n, f) for c in colors for s in shapes for n in counts for f in fills]

    if for_test:
        return random.sample(deck, 12)
    return deck


def get_card_image(filename=None):
    if filename is None:
        filename = '_empty_card'
    original = pygame.image.load(f'images/{filename}.png').convert_alpha()
    return pygame.transform.smoothscale(original, (CONST.CARD_WIDTH, CONST.CARD_HEIGHT))


# 📦 카드 렌더링용 Sprite
class CardSprite(pygame.sprite.Sprite):
    alpha = 255
    state = 'idle'
    next_card = None
    is_selected = False
    is_hinted = False

    def __init__(self, card: Card, position):
        super().__init__()
        self.card = card
        self.position = position
        self.image = get_card_image(self.card.filename)
        self.empty_image = get_card_image()
        self.rect = self.image.get_rect(topleft=self.position)

    def update(self):
        if self.state == 'fade_out':
            self.alpha -= 10
            if self.alpha <= 0:
                self.alpha = 0
                self.state = 'replacing'

        elif self.state == 'replacing':
            if self.next_card:
                self.card = self.next_card
                self.image = get_card_image(self.card.filename)
                self.next_card = None
            else:
                self.card = None
                self.image = self.empty_image
            self.alpha = 0
            self.state = 'fade_in'

        elif self.state == 'fade_in':
            self.alpha += 10
            if self.alpha >= 255:
                self.alpha = 255
                self.state = 'idle'
                if self.card is None:
                    self.state = 'removed'

        self.image.set_alpha(self.alpha)

    def start_fade_out(self, new_card=None):
        self.next_card = new_card
        self.state = "fade_out"
        pygame.time.set_timer(user_event.animation_done, 500)

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)
        if self.is_selected:
            pygame.draw.rect(screen, (0, 128, 0), self.rect.inflate(6, 6), 4)
        elif self.is_hinted:
            pygame.draw.rect(screen, (255, 0, 0), self.rect.inflate(6, 6), 4)
        else:
            pygame.draw.rect(screen, (240, 240, 240), self.rect.inflate(6, 6), 4)


# 🎯 게임 보드 클래스
class GameBoard:
    message_text = ''
    message_time = pygame.time.get_ticks()
    message_duration = 500

    hint_index = 0
    last_click_time = 0
    click_delay = 300  # 밀리초 단위 (0.3초)
    failure_count = 0

    def __init__(self):
        self.deck = generate_deck()
        # self.deck = generate_deck(for_test=True)
        self.deck_depleted = False

        self.sprites: list[CardSprite | None] = self.create_initial_sprites()
        self.hint_sets = self.find_all_sets()
        self.selected_idx = []
        self.matched_sets = []

    def get_score(self):
        return len(self.matched_sets) * 3

    def create_initial_sprites(self):
        created = []
        chosen = random.sample(self.deck, 12)
        for idx, card in enumerate(chosen):
            position = self.get_sprite_position(idx)
            sprite = CardSprite(card, position)
            created.append(sprite)
            self.deck.remove(card)
        return created

    @staticmethod
    def get_sprite_position(idx):
        x_margin = (CONST.WINDOW_WIDTH - CONST.CARD_WIDTH * 4 - CONST.CARD_PADDING * 3) // 2
        x = x_margin + (idx % 4) * (CONST.CARD_WIDTH + CONST.CARD_PADDING)
        y = 40 + (idx // 4) * (CONST.CARD_HEIGHT + CONST.CARD_PADDING)
        return x, y

    def find_all_sets(self):
        valid_indices = [i for i, s in enumerate(self.sprites) if s and s.card]
        return [
            combo for combo in combinations(valid_indices, 3)
            if self.is_set(*(self.sprites[i].card for i in combo))
        ]

    @staticmethod
    def is_set(c1: Card, c2: Card, c3: Card):
        for attr in ['color', 'shape', 'count', 'fill']:
            vals = {getattr(c, attr) for c in [c1, c2, c3]}
            if len(vals) == 2:
                return False
        return True

    def handle_click(self, pos):
        for idx, sprite in enumerate(self.sprites):
            if sprite.card and sprite.rect.collidepoint(pos):
                if sprite.is_selected:
                    sprite.is_selected = False
                    self.selected_idx.remove(idx)
                elif len(self.selected_idx) <= 3:
                    sprite.is_selected = True
                    self.selected_idx.append(idx)
                break

        if len(self.selected_idx) == 3:
            pygame.time.set_timer(user_event.load_check_set, 100)
        pygame.time.set_timer(user_event.animation_done, 500)

    def show_message(self, text, duration=0.5):
        self.message_text = text
        self.message_time = pygame.time.get_ticks()
        self.message_duration = int(duration * 1000)

    def check_set(self):
        selected = []
        for i in self.selected_idx:
            sprite = self.sprites[i]
            sprite.is_selected = False
            sprite.is_hinted = False
            if sprite and sprite.card:
                selected.append(sprite.card)

        if self.is_set(*selected):
            msg = '세트 성공!'
            self.matched_sets.append(selected)
            pygame.time.set_timer(user_event.set_success, 500)
            pygame.time.set_timer(user_event.animation_done, 500)
        else:
            msg = '세트 실패!'
            self.failure_count += 1
            self.selected_idx.clear()

        self.show_message(msg)
        logger.add(msg, 'SET_CHECK', selected)

        if not self.hint_sets and not self.deck:
            msg = '더 이상 매칭할 세트가 없습니다. 다시 시작할까요?'
            duration = 3
            self.deck_depleted = True

            self.show_message(msg, duration)
            logger.add(msg, 'SET_CHECK', selected)
            self.selected_idx.clear()

    def handle_hint(self):
        for sprite in self.sprites:
            if sprite:
                sprite.is_hinted = False
                sprite.is_selected = False

        duration = 0.5
        if self.hint_sets:
            msg = '세트가 존재합니다!'
            for i in self.hint_sets[self.hint_index]:
                if sprite := self.sprites[i]:
                    sprite.is_hinted = True
            self.hint_index += 1

            if self.hint_index >= len(self.hint_sets):
                self.hint_index = 0
        else:
            if self.deck:
                msg = '세트가 없어 카드를 모두 교체합니다!'
                self.replace_all_cards()
            else:
                msg = '덱이 모두 소진되었습니다. 다시 시작할까요?'
                duration = 3
                self.deck_depleted = True

        self.show_message(msg, duration)
        logger.add(msg, 'HINT')
        self.selected_idx.clear()
        pygame.time.set_timer(user_event.animation_done, 500)

    def replace_all_cards(self):
        self.deck += [s.card for s in self.sprites if s and s.card not in self.deck]
        new_cards = random.sample(self.deck, len(self.sprites))  # 중복 없이 새 카드 뽑기
        for i, sprite in enumerate(self.sprites):
            new_card = new_cards[i]
            self.deck.remove(new_card)
            sprite.start_fade_out(new_card)  # 전체 카드 교체

    def draw(self, screen):
        for idx, sprite in enumerate(self.sprites):
            sprite.update()
            sprite.draw(screen)

        now = pygame.time.get_ticks()
        if self.message_text and now - self.message_time < self.message_duration:
            msg_surf = FONT_1.render(self.message_text, True, (0, 0, 0))
            screen.blit(msg_surf, (screen.get_width() // 2 - msg_surf.get_width() // 2, 700))


# 🕹️ 메인 게임 클래스
class SetGame:
    clock = pygame.time.Clock()
    start_ticks = pygame.time.get_ticks()

    end_ticks = 0
    running = True
    animating = False
    in_restart_dialog = False

    def __init__(self):
        self.screen = pygame.display.set_mode((CONST.WINDOW_WIDTH, CONST.WINDOW_HEIGHT))
        pygame.display.set_caption('SET 게임 (Pygame 버전)')

        self.board = GameBoard()
        self.event_handler = GameEventHandler(self)

        self.box_x = (self.screen.get_width() - CONST.MESSAGE_BOX_WIDTH) // 2
        self.box_y = (self.screen.get_height() - CONST.MESSAGE_BOX_HEIGHT) // 2

        self.restart_btn = Button("다시 시작(R)", (CONST.WINDOW_WIDTH - 160, CONST.WINDOW_HEIGHT - 50))
        self.hint_btn = Button("힌트 보기(H)", (CONST.WINDOW_WIDTH - 300, CONST.WINDOW_HEIGHT - 50))

        self.restart_btn_in_dialog = Button(
            '다시 시작', (self.box_x + 80, self.box_y + 160),
            bg_color=(0, 125, 0), text_color=CONST.C_WHITE, bold=True
        )
        self.quit_btn_in_dialog = Button(
            '종료', (self.box_x + 280, self.box_y + 160),
            bg_color=(125, 0, 0), text_color=CONST.C_WHITE, bold=True
        )

    def show_restart_dialog(self):
        # 배경 어둡게 처리
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA).convert_alpha()
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # 메시지 박스
        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            (self.box_x, self.box_y, CONST.MESSAGE_BOX_WIDTH, CONST.MESSAGE_BOX_HEIGHT)
        )

        x_position = self.box_x + 80
        y_position = self.box_y + 40

        # 시간 및 성공/실패 횟수 표시
        time_text = self.get_play_time_text(self.end_ticks)
        time_msg, success_msg, fail_msg = self.get_game_score_message(time_text)
        restart_msg = FONT_1.render('게임이 끝났습니다. 다시 시작할까요?', True, (0, 0, 0))

        self.screen.blit(time_msg, (x_position, y_position))
        self.screen.blit(success_msg, (x_position, y_position + 30))
        self.screen.blit(fail_msg, (x_position, y_position + 60))
        self.screen.blit(restart_msg, (x_position, y_position + 90))

        # 버튼 생성
        self.restart_btn_in_dialog.draw(self.screen)
        self.quit_btn_in_dialog.draw(self.screen)

        pygame.display.update()

    def get_play_time_text(self, target_ticks):
        play_time = (target_ticks - self.start_ticks) // 1000
        minutes = play_time // 60
        seconds = play_time % 60
        return f'{minutes}:{seconds:02}'

    def get_game_score_message(self, time_text: str):
        time_msg = FONT_1.render(f'시간 {time_text}', True, (0, 0, 0))
        success_msg = FONT_1.render(f'성공 {len(self.board.matched_sets)}', True, (0, 0, 0))
        fail_msg = FONT_1.render(f'실패 {self.board.failure_count}', True, (0, 0, 0))
        return time_msg, success_msg, fail_msg

    def button_is_clicked(self, button: str, event):
        if hasattr(self, button):
            return getattr(self, button).is_clicked(event.pos)

    def handle_restart_button(self):
        self.board = GameBoard()
        self.start_ticks = pygame.time.get_ticks()
        self.in_restart_dialog = self.board.deck_depleted = False
        logger.clear()

    def handle_mouse_click(self, event):
        self.animating = True
        self.board.handle_click(event.pos)

    def handle_hint(self):
        self.board.handle_hint()
        self.in_restart_dialog = self.board.deck_depleted
        if self.in_restart_dialog:
            self.end_ticks = pygame.time.get_ticks()

    def handle_set_success(self):
        _board = self.board
        if _board.deck:
            # 덱에 카드가 있다면 교체
            for i in _board.selected_idx:
                sprite = _board.sprites[i]
                new_card = random.choice(_board.deck)
                _board.deck.remove(new_card)
                sprite.start_fade_out(new_card)  # 세트 성공시 새 카드가 있는 경우
        else:
            # 덱에 카드가 없으면 해당 카드 제거
            debug_logger.log("PRE_CARD_REMOVE", sprites=_board.sprites)
            for i in _board.selected_idx:
                sprite = _board.sprites[i]
                sprite.start_fade_out()  # 세트 성공시 새 카드가 없는 경우
            debug_logger.log("POST_CARD_REMOVE", sprites=_board.sprites)

            if not _board.find_all_sets():
                self.in_restart_dialog = True

        pygame.time.set_timer(user_event.set_success, 0)  # 타이머 종료
        _board.hint_sets = _board.find_all_sets()
        _board.selected_idx.clear()  # 교체된 후에는 초기화

    def draw_log(self):
        font = pygame.font.SysFont('나눔고딕', 18)
        recent_logs = logger.log[-5:]
        color_map = logger.color_map
        for i, (ts, msg) in enumerate(recent_logs):
            color = (80, 80, 80)
            for tag in color_map:
                if msg.startswith(f'[{tag}]'):
                    color = color_map[tag]
            text = font.render(f'▶ {msg}', True, color)
            self.screen.blit(text, (20, 600 + i * 20))  # 위치는 조정 가능
        logger.save_to_file()

    def render(self):
        self.board.draw(self.screen)

        x_position = 20
        y_position = CONST.WINDOW_HEIGHT - 40

        # 시간 및 성공/실패 횟수 표시
        time_text = self.get_play_time_text(pygame.time.get_ticks())
        time_msg, success_msg, fail_msg = self.get_game_score_message(time_text)

        self.screen.blit(time_msg, (x_position, y_position - 60))
        self.screen.blit(success_msg, (x_position, y_position - 30))
        self.screen.blit(fail_msg, (x_position, y_position))

        self.restart_btn.draw(self.screen)
        self.hint_btn.draw(self.screen)
        self.draw_log()

    def update_screen(self):
        self.screen.fill(CONST.BACKGROUND_COLOR)

        if self.in_restart_dialog:
            self.show_restart_dialog()
        else:
            self.render()

        pygame.display.update()
        pygame.display.flip()

    def run(self):
        logger.add('게임이 시작되었습니다.', 'START')
        while self.running:
            for event in pygame.event.get():
                self.event_handler.handle(event)

            self.update_screen()
            self.clock.tick(60)


class GameEventHandler:
    def __init__(self, set_game: SetGame):
        self.game = set_game
        self.handlers = {
            pygame.QUIT:                    self.on_event_game_quit,            # 256
            pygame.MOUSEBUTTONUP:           self.on_event_mouse_button_up,      # 1026
            pygame.KEYUP:                   self.on_event_key_up,               # 769
            user_event.load_check_set:      self.on_event_load_check_set,       # 32867
            user_event.set_success:         self.on_event_set_success,          # 32868
            user_event.animation_done:      self.on_event_animation_done,       # 32869
            user_event.game_over:           self.on_event_game_over,            # 32870
            user_event.replace_all_cards:   self.on_event_replace_all_cards,    # 32870
        }

    def handle(self, event):
        if self.game.in_restart_dialog:
            self.on_event_restart_dialog(event)
        elif handler := self.handlers.get(event.type):
            handler(event)  # noqa

    def on_event_restart_dialog(self, event):
        _game = self.game
        if event.type == pygame.MOUSEBUTTONUP:
            if _game.button_is_clicked('restart_btn_in_dialog', event):
                _game.handle_restart_button()
            elif _game.button_is_clicked('quit_btn_in_dialog', event):
                _game.running = False
            _game.show_restart_dialog()

    def on_event_game_quit(self, _):
        self.game.running = False
        logger.add('게임이 정상 종료되었습니다.', 'END')

    def on_event_mouse_button_up(self, event):
        _game = self.game
        if _game.button_is_clicked('restart_btn', event):
            _game.handle_restart_button()
        elif _game.button_is_clicked('hint_btn', event):
            _game.handle_hint()
        else:
            _game.handle_mouse_click(event)

    def on_event_key_up(self, event):
        _game = self.game

        if _game.animating:
            debug_logger.log("KEY_IGNORED", reason="Animating in progress", key=event.key)
            return  # 애니메이션 중에는 키 입력 무시

        if event.key == pygame.K_h:
            _game.handle_hint()
        elif event.key == pygame.K_r:
            _game.handle_restart_button()
        elif event.key == pygame.K_ESCAPE:
            _game.running = False

    def on_event_load_check_set(self, _):
        self.game.board.check_set()
        pygame.time.set_timer(user_event.load_check_set, 0)  # 타이머 종료

    def on_event_set_success(self, _):
        debug_logger.log("SET_SUCCESS_INVOKED", deck_size=len(self.game.board.deck))
        self.game.handle_set_success()

    def on_event_animation_done(self, _):
        _game, _board = self.game, self.game.board
        pygame.display.update()
        _game.animating = False
        _board.hint_index = 0
        _board.hint_sets = _board.find_all_sets()
        pygame.time.set_timer(user_event.animation_done, 0)

    def on_event_game_over(self, _):
        _game, _board = self.game, self.game.board
        msg = '게임 종료! 다시 시작하려면 버튼을 눌러주세요'
        _board.show_message(msg, duration=3)
        logger.add(msg, 'END')
        _game.running = False  # 메인 루프 종료 트리거

    def on_event_replace_all_cards(self, _):
        _game, _board = self.game, self.game.board
        _game.animating = True
        _board.replace_all_cards()
        pygame.time.set_timer(user_event.replace_all_cards, 0)


# 🚀 실행
if __name__ == "__main__":
    game = SetGame()
    game.run()
    pygame.quit()
