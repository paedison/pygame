import tkinter as tk
from unittest.mock import patch

import pytest
from PIL import Image

from boardgame_set.old.code_6 import SetGameGUI


@pytest.fixture
def app():
    root = tk.Tk()
    # root.withdraw()  # 테스트 중 창 숨기기

    gui = SetGameGUI(root)
    yield gui
    root.destroy()


def test_canvas_card_draws(app):
    # 초기 12장 카드가 그려졌는지 확인
    assert len(app.card_buttons) == 12

    for canvas, frame, card in app.card_buttons:
        items = canvas.find_all()
        assert isinstance(canvas, tk.Canvas)
        assert len(items) >= 2  # 이미지 + 오버레이 사각형


def test_canvas_click_event(app):
    # 클릭 시뮬레이션: 첫 번째 카드 선택
    canvas, _, _ = app.card_buttons[0]

    item_ids = canvas.find_all()
    assert item_ids, "Canvas에 아이템이 없습니다!"

    coords = canvas.bbox(item_ids[0])  # 첫 번째 아이템 bbox
    x = (coords[0] + coords[2]) // 2
    y = (coords[1] + coords[3]) // 2

    canvas.event_generate('<Button-1>', x=x, y=y)
    canvas.update()
    app.root.update()

    assert len(app.selected_indices) == 1


def test_overlay_visibility_on_select(app):
    # 카드 클릭 후 오버레이가 보이는지 확인
    canvas, _, _ = app.card_buttons[0]
    rect_id = canvas.find_all()[-1]  # 마지막이 overlay rectangle
    state_before = canvas.itemcget(rect_id, 'state')

    coords = canvas.bbox(canvas.find_all()[0])  # 첫 번째 아이템 bbox
    x = canvas.winfo_rootx() + (coords[0] + coords[2]) // 2
    y = canvas.winfo_rooty() + (coords[1] + coords[3]) // 2

    canvas.event_generate('<Button-1>', x=x, y=y)
    canvas.update()
    app.root.update()
    state_after = canvas.itemcget(rect_id, 'state')

    assert state_before == 'hidden'
    assert state_after == 'normal'


@patch("PIL.Image.open")
def test_card_image_load(mock_open, app):
    # 이미지 로딩 대체: 로컬 이미지가 없어도 테스트 가능
    mock_open.return_value = Image.new("RGB", (100, 150))
    app.rebuild_board()
    for canvas, _, _ in app.card_buttons:
        items = canvas.find_all()
        assert len(items) >= 2


def test_card_click_simulation(app):
    # 특정 이미지 영역 클릭 시 이벤트 처리 확인 (좌표 기반)
    canvas, _, _ = app.card_buttons[0]
    target_id = canvas.find_all()[0]
    bbox = canvas.bbox(target_id)
    x = (bbox[0] + bbox[2]) // 2
    y = (bbox[1] + bbox[3]) // 2

    # 클릭 이벤트 시뮬레이션
    event = tk.Event()
    event.x = x
    event.y = y
    canvas.event_generate("<Button-1>", x=x, y=y)

    # 선택 카드에 등록되었는지 확인
    assert len(app.selected_indices) >= 1


# def test_button_click_triggers_selection(app):
#     # 버튼 클릭 시 선택 리스트에 추가되는지 테스트
#     initial_len = len(app.selected_indices)
#     btn = app.card_buttons[0]
#     btn.invoke()  # 버튼 클릭 시뮬레이션
#     assert len(app.selected_indices) == initial_len + 1
#
#
# def test_set_check_and_reset(app):
#     # 세 카드 선택 후 자동으로 reset되는지 확인
#     for btn in app.card_buttons[:3]:
#         btn.invoke()
#     assert len(app.selected_indices) == 0  # 세트 판별 후 초기화됨
#
#
# def test_rebuild_board_changes_cards(app):
#     old_labels = [btn['text'] for btn in app.card_buttons]
#     app.rebuild_board()
#     new_labels = [btn['text'] for btn in app.card_buttons]
#     assert old_labels != new_labels  # 카드 내용이 변경됨


# def test_timer_update(app):
#     # 시간 업데이트 기능이 1초 후에도 변경되는지 확인
#     original_time = app.time_label['text']
#     app.root.after(1000, app.update_timer)
#     app.root.update_idletasks()
#     app.root.after(1000, app.root.quit)
#     app.root.mainloop()
#     updated_time = app.time_label['text']
#     assert original_time != updated_time
