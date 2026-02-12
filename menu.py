import arcade
from main import GameWindow  # в main.py должен быть GameView(arcade.View)
from audio import music
from save import init_db
from export import export_to_word

SCREEN_TITLE = "Miami Gun"

class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.timer = 0
        self.blink = True


    def on_show_view(self):
        arcade.set_background_color((20, 0, 40))
        music.play_menu()
    def on_draw(self):
        self.clear()
        w, h = self.window.get_size()

        arcade.draw_text(
            "NEW GAME  [N]",
            w // 2,
            h // 2,
            arcade.color.HOT_PINK,
            22,
            anchor_x="center"
        )

        arcade.draw_text(
            "EXPORT STATS [M]",
            w // 2,
            h // 2 - 40,
            arcade.color.HOT_PINK,
            22,
            anchor_x="center"
        )

        arcade.draw_text(
            "MIAMI GUN",
            w // 2,
            h - 160,
            arcade.color.ORANGE,
            52,
            anchor_x="center"
        )

        if self.blink:
            arcade.draw_text(
                "START GAME  [ENTER]",
                w // 2,
                h // 2 + 40,
                arcade.color.HOT_PINK,
                28,
                anchor_x="center"
            )

        arcade.draw_text(
            "EXIT  [ESC]",
            w // 2,
            h // 2 - 80,
            arcade.color.HOT_PINK,
            22,
            anchor_x="center"
        )

    def on_update(self, delta_time: float):
        self.timer += delta_time
        if self.timer >= 0.45:
            self.timer = 0
            self.blink = not self.blink

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            self.window.show_view(GameWindow())

        elif key == arcade.key.N:
            # NEW GAME — сброс прогресса
            game = GameWindow()
            game.level = 1
            game.total_kills = 0
            game.setup()
            self.window.show_view(game)

        elif key == arcade.key.ESCAPE:
            arcade.close_window()
        elif key == arcade.key.M:
            export_to_word()

def main():
    init_db()
    window = arcade.Window(title=SCREEN_TITLE, fullscreen=True)
    window.show_view(MenuView())
    arcade.run()


if __name__ == "__main__":
    main()
