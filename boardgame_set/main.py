import random
from itertools import combinations
from datetime import datetime

import pygame

from boardgame_set.user_event import UserEvent
from boardgame_set.inerface import Button, Card
from boardgame_set.logger import DebugLogger, GameLogger

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 800
BACKGROUND_COLOR = (255, 255, 255)

user_event = UserEvent()
debug_logger = DebugLogger()
logger = GameLogger()

pygame.init()
FONT_1 = pygame.font.SysFont("나눔고딕", 20)


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
        self.image = self.get_card_image()
        self.rect = self.image.get_rect(topleft=self.position)

    def get_card_image(self, filename: str | None = None):
        if not filename:
            filename = self.card.filename
        original = pygame.image.load(f'images/{filename}.png').convert_alpha()
        return pygame.transform.smoothscale(original, (100, 150))

    def update(self):
        if self.state == 'fade_out':
            self.alpha -= 10
            if self.alpha <= 0:
                self.alpha = 0
                self.state = 'replacing'

        elif self.state == 'replacing':
            if self.next_card:
                self.card = self.next_card
                self.image = self.get_card_image()
                self.next_card = None
            else:
                self.card = None
                self.image = self.get_card_image('_empty_card')
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

    def __init__(self):

        # self.deck = self.generate_deck()
        self.deck = self.generate_test_deck()
        self.deck_depleted = False
        self.sprites: list[CardSprite | None] = self.create_initial_sprites()
        self.selected_idx = []
        self.matched_sets = []

        empty = pygame.image.load(f'images/_empty_card.png').convert_alpha()
        self.empty_image = pygame.transform.smoothscale(empty, (100, 150))

        self.last_click_time = 0
        self.click_delay = 300  # 밀리초 단위 (0.3초)

        self.hint_sets = self.find_all_sets()
        self.hint_index = 0

    def get_score(self):
        return len(self.matched_sets) * 3

    def generate_test_deck(self):
        deck = self.generate_deck()
        return random.sample(deck, 12)

    @staticmethod
    def generate_deck():
        colors = ['red', 'green', 'purple']
        shapes = ['oval', 'squiggle', 'diamond']
        counts = [1, 2, 3]
        fills = ['solid', 'striped', 'open']
        return [Card(c, s, n, f) for c in colors for s in shapes for n in counts for f in fills]

    def create_initial_sprites(self):
        created = []
        chosen = random.sample(self.deck, 12)
        for idx, card in enumerate(chosen):
            pos = self.get_position(idx)
            sprite = CardSprite(card, pos)
            created.append(sprite)
            self.deck.remove(card)
        return created

    @staticmethod
    def get_position(idx):
        x = 50 + (idx % 4) * 140
        y = 80 + (idx // 4) * 180
        return x, y

    def find_all_sets(self):
        valid_indices = [i for i, s in enumerate(self.sprites) if s and s.card is not None]
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
            if sprite and sprite.rect.collidepoint(pos):
                if sprite.is_selected:
                    sprite.is_selected = False
                    self.selected_idx.remove(idx)
                elif len(self.selected_idx) <= 3:
                    sprite.is_selected = True
                    self.selected_idx.append(idx)
                break

        if len(self.selected_idx) == 3:
            pygame.time.set_timer(user_event.load_check_set, 100)
            pygame.time.set_timer(user_event.animation_done, 600)

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
            if sprite:
                selected.append(sprite.card)

        if self.is_set(*selected):
            self.matched_sets.append(selected)
            msg = '세트 성공!'
            pygame.time.set_timer(user_event.set_success, 500)
            pygame.time.set_timer(user_event.animation_done, 500)
        else:
            msg = '세트 실패!'
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
        print(self.hint_sets)
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

    def replace_all_cards(self):
        self.deck += [s.card for s in self.sprites if s and s.card not in self.deck]
        new_cards = random.sample(self.deck, len(self.sprites))  # 중복 없이 새 카드 뽑기
        for i, sprite in enumerate(self.sprites):
            new_card = new_cards[i]
            self.deck.remove(new_card)
            sprite.start_fade_out(new_card)  # replace_all_cards

    def draw(self, screen):
        for idx, sprite in enumerate(self.sprites):
            if sprite is None:
                screen.blit(self.empty_image, self.get_position(idx))
            else:
                sprite.update()
                if sprite.state == 'removed':
                    self.sprites[idx] = None
                sprite.draw(screen)

        now = pygame.time.get_ticks()
        if self.message_text and now - self.message_time < self.message_duration:
            msg_surf = FONT_1.render(self.message_text, True, (0, 0, 0))
            screen.blit(msg_surf, (screen.get_width() // 2 - msg_surf.get_width() // 2, 700))


# 🕹️ 메인 게임 클래스
class SetGame:
    restart_btn = Button("다시 시작(R)", (WINDOW_WIDTH - 160, WINDOW_HEIGHT - 50))
    hint_btn = Button("힌트 보기(H)", (WINDOW_WIDTH - 300, WINDOW_HEIGHT - 50))
    restart_btn_in_dialog: Button
    quit_button_in_dialog: Button

    font = pygame.font.SysFont('나눔고딕', 20)

    clock = pygame.time.Clock()
    start_ticks = pygame.time.get_ticks()
    end_ticks = 0
    running = True
    animating = False
    in_restart_dialog = False

    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('SET 게임 (Pygame 버전)')
        self.board = GameBoard()
        self.event_handler = GameEventHandler(self)

    def show_restart_dialog(self):
        # 배경 어둡게 처리
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA).convert_alpha()
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # 메시지 박스
        box_width, box_height = 480, 250
        box_x = (self.screen.get_width() - box_width) // 2
        box_y = (self.screen.get_height() - box_height) // 2
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, box_width, box_height))

        # 글꼴 설정
        font = pygame.font.SysFont('나눔고딕', 20)

        # 점수 및 시간 계산
        play_time = int((self.end_ticks - self.start_ticks) / 1000)
        minutes = play_time // 60
        seconds = play_time % 60
        time_text = f'{minutes}분 {seconds}초'

        score = self.board.get_score()
        score_msg = font.render(f'점수: {score}', True, (0, 0, 0))
        time_msg = font.render(f'플레이 시간: {time_text}', True, (0, 0, 0))
        restart_msg = font.render('게임이 끝났습니다. 다시 시작할까요?', True, (0, 0, 0))

        self.screen.blit(score_msg, (box_x + 80, box_y + 40))
        self.screen.blit(time_msg, (box_x + 80, box_y + 70))
        self.screen.blit(restart_msg, (box_x + 80, box_y + 100))

        # 버튼 생성
        self.restart_btn_in_dialog = Button(
            '다시 시작', (box_x + 80, box_y + 160), bg_color=(0, 125, 0), text_color=(255, 255, 255), bold=True)
        self.quit_button_in_dialog = Button(
            '종료', (box_x + 280, box_y + 160), bg_color=(125, 0, 0), text_color=(255, 255, 255), bold=True)

        self.restart_btn_in_dialog.draw(self.screen)
        self.quit_button_in_dialog.draw(self.screen)

        pygame.display.update()

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

        elapsed_seconds = (pygame.time.get_ticks() - self.start_ticks) // 1000
        time_text = FONT_1.render(f'시간: {elapsed_seconds}초', True, (0, 0, 0))
        self.screen.blit(time_text, (20, WINDOW_HEIGHT - 70))

        score_text = FONT_1.render(f"점수: {len(self.board.matched_sets) * 3}", True, (0, 0, 0))
        self.screen.blit(score_text, (20, WINDOW_HEIGHT - 40))

        self.restart_btn.draw(self.screen)
        self.hint_btn.draw(self.screen)
        self.draw_log()

    def update_screen(self):
        self.screen.fill(BACKGROUND_COLOR)

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

    def handle(self, event):
        if self.game.in_restart_dialog:
            self.handle_restart_dialog(event)
        else:
            self.handle_main_event(event)

    def handle_game_quit(self, _):
        self.game.running = False
        logger.add('게임이 정상 종료되었습니다.', 'END')

    def handle_mouse_button_up(self, event):
        _game, _board = self.game, self.game.board
        if _game.hint_btn.is_clicked(event.pos):
            _board.handle_hint()
        elif _game.restart_btn.is_clicked(event.pos):
            self.game.board = GameBoard()  # _board와 같이 수정하면 안됨  # noqa
            _game.start_ticks = pygame.time.get_ticks()
        else:
            _board.handle_click(event.pos)

    def handle_key_up(self, event):
        _game, _board = self.game, self.game.board
        if event.key == pygame.K_h:
            _board.handle_hint()
            _game.in_restart_dialog = _board.deck_depleted
            if _game.in_restart_dialog:
                _game.end_ticks = pygame.time.get_ticks()
        elif event.key == pygame.K_r:
            self.game.board = GameBoard()  # _board와 같이 수정하면 안됨  # noqa
            _game.start_ticks = pygame.time.get_ticks()
        elif event.key == pygame.K_ESCAPE:
            _game.running = False

    def handle_event_load_check_set(self, _):
        _game, _board = self.game, self.game.board
        _board.check_set()
        pygame.time.set_timer(user_event.load_check_set, 0)  # 타이머 종료

    def handle_restart_dialog(self, event):
        _game, _board = self.game, self.game.board
        if event.type == pygame.MOUSEBUTTONUP:
            if _game.restart_btn_in_dialog.is_clicked(event.pos):
                self.start_new_game()
                _game.in_restart_dialog = False
            elif _game.quit_button_in_dialog.is_clicked(event.pos):
                _game.running = False
            _game.show_restart_dialog()

    def start_new_game(self):
        self.game.board = GameBoard()  # _board와 같이 수정하면 안됨  # noqa
        _game, _board = self.game, self.game.board
        _game.start_ticks = pygame.time.get_ticks()
        _game.in_restart_dialog = _board.deck_depleted = False
        logger.clear()

    def handle_event_set_success(self, _):
        _game, _board = self.game, self.game.board
        debug_logger.log("SET_SUCCESS_INVOKED", deck_size=len(_board.deck))

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
                _game.in_restart_dialog = True

        pygame.time.set_timer(user_event.set_success, 0)  # 타이머 종료
        debug_logger.log("PRE_SET_SUCCESS", selected_idx=_board.selected_idx)
        _board.selected_idx.clear()  # 교체된 후에는 초기화
        debug_logger.log("POST_SET_SUCCESS", selected_idx=_board.selected_idx)

    def handle_event_animation_done(self, _):
        _game, _board = self.game, self.game.board
        pygame.display.update()
        _game.animating = False
        _board.hint_index = 0
        _board.hint_sets = _board.find_all_sets()
        pygame.time.set_timer(user_event.animation_done, 0)

    def handle_game_over(self, _):
        _game, _board = self.game, self.game.board
        msg = '게임 종료! 다시 시작하려면 버튼을 눌러주세요'
        _board.show_message(msg, duration=3)
        logger.add(msg, 'END')
        _game.running = False  # 메인 루프 종료 트리거

    def handle_event_confirm_restart(self, event):
        _game, _board = self.game, self.game.board
        if event.type == pygame.MOUSEBUTTONUP:
            if _game.restart_btn_in_dialog.is_clicked(event.pos):
                self.start_new_game()
                _game.in_restart_dialog = False
            elif _game.quit_button_in_dialog.is_clicked(event.pos):
                _game.running = False
            _game.show_restart_dialog()

    def handle_main_event(self, event):
        _game, _board = self.game, self.game.board
        handlers = {
            pygame.QUIT: self.handle_game_quit,
            pygame.MOUSEBUTTONUP: self.handle_mouse_button_up,
            pygame.KEYUP: self.handle_key_up,
            user_event.load_check_set: self.handle_event_load_check_set,
            user_event.set_success: self.handle_event_set_success,
            user_event.animation_done: self.handle_event_animation_done,
            user_event.game_over: self.handle_game_over,
        }
        if _game.in_restart_dialog:
            self.handle_event_confirm_restart(event)
        else:
            if handler := handlers.get(event.type):
                handler(event)  # noqa


# 🚀 실행
if __name__ == "__main__":
    game = SetGame()
    game.run()
    pygame.quit()
