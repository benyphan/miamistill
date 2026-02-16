import arcade
from resources import resource_path

class MusicManager:
    def __init__(self):
        # Загружаем музыку один раз
        self.menu_music = arcade.load_sound(resource_path("music/menu.ogg"))
        self.game_music = arcade.load_sound(resource_path("music/game.ogg"))

        self.player = None
        self.current = None  # "menu" или "game"

    def _play(self, sound, track_name, volume=0.6):
        # Если уже играет этот трек — ничего не делаем
        if self.current == track_name:
            return

        # Остановить предыдущий
        if self.player:
            self.player.pause()

        # Запустить новый
        self.player = sound.play(volume=volume, loop=True)
        self.current = track_name

    # --- публичные методы ---
    def play_menu(self):
        self._play(self.menu_music, "menu")

    def play_game(self):
        self._play(self.game_music, "game")

    def stop(self):
        if self.player:
            self.player.pause()
            self.player = None
            self.current = None