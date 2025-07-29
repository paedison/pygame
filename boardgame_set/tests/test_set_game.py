from boardgame_set.old.code_6 import Card, is_set, generate_deck, find_possible_set


# 🃏 카드 생성 테스트
def test_card_creation():
    card = Card(color="red", shape="oval", count=1, fill="solid")
    assert card.color == "red"
    assert card.shape == "oval"
    assert card.count == 1
    assert card.fill == "solid"


# 🧠 세트 판단 함수 테스트
def test_valid_set():
    c1 = Card("red", "oval", 1, "solid")
    c2 = Card("red", "oval", 2, "solid")
    c3 = Card("red", "oval", 3, "solid")
    assert is_set(c1, c2, c3) is True


def test_invalid_set():
    c1 = Card("red", "oval", 1, "solid")
    c2 = Card("green", "oval", 2, "solid")
    c3 = Card("red", "oval", 3, "solid")
    assert is_set(c1, c2, c3) is False


# 🎴 덱 생성 테스트
def test_generate_deck():
    deck = generate_deck()
    assert len(deck) == 81  # SET 게임의 카드 수
    unique_cards = set(str(card) for card in deck)
    assert len(unique_cards) == 81  # 중복 없는 카드


# 🔍 가능한 세트 탐색 테스트
def test_find_possible_set_found():
    cards = [
        Card("red", "oval", 1, "solid"),
        Card("red", "oval", 2, "solid"),
        Card("red", "oval", 3, "solid"),
    ]
    result = find_possible_set(cards)
    assert result == (0, 1, 2)


def test_find_possible_set_not_found():
    cards = [
        Card("red", "oval", 1, "solid"),
        Card("red", "squiggle", 2, "striped"),
        Card("purple", "diamond", 3, "open"),
    ]
    result = find_possible_set(cards)
    assert result is None
