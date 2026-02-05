import arcade


class MusicManager:
    def __init__(self):
        self.menu_music = arcade.load_sound("music/menu.ogg")
        self.menu_player = None

    def play_menu(self):
        if self.menu_player is None:
            self.menu_player = self.menu_music.play(
                volume=0.6,
                loop=True
            )

    def stop_menu(self):
        if self.menu_player:
            self.menu_player.pause()
            self.menu_player = None
