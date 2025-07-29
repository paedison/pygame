import dataclasses

import pygame


@dataclasses.dataclass
class Button:
    text: str
    position: dataclasses.field(default_factory=tuple)
    size: tuple = (120, 40)
    bg_color: tuple = (200, 200, 200)
    border_color: tuple = (50, 50, 50)
    text_color: tuple = (0, 0, 0)
    bold: bool = False

    def __post_init__(self):
        self.rect = pygame.Rect(self.position, self.size)
        self.font = pygame.font.SysFont("나눔고딕", 20, self.bold)

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)  # 테두리
        txt_surf = self.font.render(self.text, True, self.text_color)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        screen.blit(txt_surf, txt_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)


# 💡 카드 데이터 클래스
@dataclasses.dataclass
class Card:
    color: str
    shape: str
    count: int
    fill: str

    def __post_init__(self):
        self.filename = f'{self.color}_{self.shape}_{self.count}_{self.fill}'

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return (
                self.color == other.color and
                self.shape == other.shape and
                self.count == other.count and
                self.fill == other.fill
        )

    def __hash__(self):
        return hash((self.color, self.shape, self.count, self.fill))

    def __repr__(self):
        color_dict = {'red': 'RED', 'green': 'GRN', 'purple': 'PUR'}
        shape_dict = {'oval': '○', 'squiggle': '~', 'diamond': '◇'}
        fill_dict = {'solid': '■', 'striped': '▤', 'open': '□'}
        color = color_dict[self.color]
        shape = shape_dict[self.shape]
        fill = fill_dict[self.fill]
        return f'{color}{shape}{self.count}{fill}'
