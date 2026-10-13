import os
import pygame

from settings import (
    PREFERENCES,
    save_preferences,
)


class UISoundManager:

    # =========================================================
    # INITIALIZE
    # =========================================================

    def __init__(self):

        self.sounds = {}

        self.enabled = True
        self.loaded = False

        self.current_hover = None
        self.hover_scope = None

        self.last_play_time = {}

        self.cooldowns = {
            "hover": 70,
            "click": 50,
            "back": 50,
            "success": 100,
            "error": 100,
        }

        # =====================================================
        # SOUND DIRECTORY
        # =====================================================

        project_root = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        self.sound_directory = os.path.join(
            project_root,
            "assets",
            "sound"
        )

        # =====================================================
        # SOUND PATHS
        # =====================================================

        self.paths = {

            "hover": [
                os.path.join(
                    self.sound_directory,
                    "button_hover.mp3"
                ),
                os.path.join(
                    self.sound_directory,
                    "button_hover.wav"
                ),
                os.path.join(
                    self.sound_directory,
                    "button_hover.ogg"
                ),

                # Fallback
                os.path.join(
                    self.sound_directory,
                    "button_click.mp3"
                ),
            ],

            "click": [
                os.path.join(
                    self.sound_directory,
                    "button_click.mp3"
                ),
                os.path.join(
                    self.sound_directory,
                    "button_click.wav"
                ),
                os.path.join(
                    self.sound_directory,
                    "button_click.ogg"
                ),
            ],

            "back": [
                os.path.join(
                    self.sound_directory,
                    "button_back.mp3"
                ),
                os.path.join(
                    self.sound_directory,
                    "button_back.wav"
                ),
                os.path.join(
                    self.sound_directory,
                    "button_back.ogg"
                ),

                # Fallback
                os.path.join(
                    self.sound_directory,
                    "button_click.mp3"
                ),
            ],

            "success": [
                os.path.join(
                    self.sound_directory,
                    "success.mp3"
                ),
                os.path.join(
                    self.sound_directory,
                    "success.wav"
                ),
                os.path.join(
                    self.sound_directory,
                    "success.ogg"
                ),

                # Fallback
                os.path.join(
                    self.sound_directory,
                    "button_click.mp3"
                ),
            ],

            "error": [
                os.path.join(
                    self.sound_directory,
                    "error.mp3"
                ),
                os.path.join(
                    self.sound_directory,
                    "error.wav"
                ),
                os.path.join(
                    self.sound_directory,
                    "error.ogg"
                ),

                # Fallback
                os.path.join(
                    self.sound_directory,
                    "button_click.mp3"
                ),
            ],
        }

        # =====================================================
        # BASE VOLUME
        # =====================================================
        #
        # These are the individual sound strengths.
        #
        # The actual volume becomes:
        #
        # base volume
        #     x
        # SFX volume
        #     x
        # Master volume
        #
        # Therefore:
        #
        # SFX 0% = completely silent
        #
        # =====================================================

        self.base_volumes = {

            "hover": 0.18,

            "click": 0.42,

            "back": 0.38,

            "success": 0.45,

            "error": 0.40,
        }


    # =========================================================
    # CLAMP
    # =========================================================

    @staticmethod
    def clamp_volume(value):

        try:

            value = float(value)

        except (
            TypeError,
            ValueError
        ):

            value = 1.0

        return max(
            0.0,
            min(
                1.0,
                value
            )
        )


    # =========================================================
    # FIND FIRST EXISTING SOUND
    # =========================================================

    def _first_existing(
        self,
        candidates
    ):

        for path in candidates:

            if os.path.isfile(path):

                return path

        return None


    # =========================================================
    # MASTER VOLUME
    # =========================================================

    def get_master_volume(self):

        return self.clamp_volume(
            PREFERENCES.get(
                "master_volume",
                1.0
            )
        )


    # =========================================================
    # SFX VOLUME
    # =========================================================

    def get_sfx_volume(self):

        return self.clamp_volume(
            PREFERENCES.get(
                "sfx_volume",
                1.0
            )
        )


    # =========================================================
    # FINAL SOUND VOLUME
    # =========================================================

    def get_sound_volume(
        self,
        name
    ):

        base_volume = self.base_volumes.get(
            name,
            0.4
        )

        master_volume = self.get_master_volume()

        sfx_volume = self.get_sfx_volume()

        final_volume = (
            base_volume
            * master_volume
            * sfx_volume
        )

        return self.clamp_volume(
            final_volume
        )


    # =========================================================
    # LOAD SOUNDS
    # =========================================================

    def load(self):

        if self.loaded:
            return

        # Mark as loaded so we don't repeatedly try loading
        # missing/broken sounds.
        self.loaded = True

        # -----------------------------------------------------
        # Check mixer
        # -----------------------------------------------------

        if pygame.mixer.get_init() is None:

            print(
                "UI sounds disabled: "
                "pygame mixer is not initialized."
            )

            self.enabled = False

            return

        # -----------------------------------------------------
        # Load every sound
        # -----------------------------------------------------

        for name, candidates in self.paths.items():

            path = self._first_existing(
                candidates
            )

            if path is None:

                print(
                    f"UI sound missing: {name}"
                )

                continue

            try:

                sound = pygame.mixer.Sound(
                    path
                )

                sound.set_volume(
                    self.get_sound_volume(
                        name
                    )
                )

                self.sounds[name] = sound

                print(
                    f"Loaded UI sound '{name}': "
                    f"{path}"
                )

            except pygame.error as error:

                print(
                    f"Unable to load UI sound "
                    f"'{name}': {error}"
                )


    # =========================================================
    # APPLY CURRENT VOLUME SETTINGS
    # =========================================================

    def apply_volume_settings(self):

        if not self.loaded:
            return

        if not self.sounds:
            return

        for name, sound in self.sounds.items():

            try:

                sound.set_volume(
                    self.get_sound_volume(
                        name
                    )
                )

            except pygame.error:

                pass


    # =========================================================
    # PLAY SOUND
    # =========================================================

    def play(
        self,
        name,
        force=False
    ):

        # -----------------------------------------------------
        # Sound system disabled
        # -----------------------------------------------------

        if not self.enabled:
            return

        # -----------------------------------------------------
        # Load sounds if necessary
        # -----------------------------------------------------

        if not self.loaded:

            self.load()

        sound = self.sounds.get(
            name
        )

        if sound is None:
            return

        # -----------------------------------------------------
        # LIVE VOLUME
        # -----------------------------------------------------
        #
        # This is important.
        #
        # If the player changes the volume slider while the
        # game is running, the new volume is used immediately.
        #
        # -----------------------------------------------------

        final_volume = self.get_sound_volume(
            name
        )

        sound.set_volume(
            final_volume
        )

        # -----------------------------------------------------
        # If volume is 0%, don't play the sound.
        # -----------------------------------------------------

        if final_volume <= 0.0:

            return

        # -----------------------------------------------------
        # Cooldown
        # -----------------------------------------------------

        now = pygame.time.get_ticks()

        last_time = self.last_play_time.get(
            name,
            -10000
        )

        cooldown = self.cooldowns.get(
            name,
            0
        )

        if (
            not force
            and now - last_time < cooldown
        ):

            return

        self.last_play_time[name] = now

        # -----------------------------------------------------
        # Play
        # -----------------------------------------------------

        try:

            sound.play()

        except pygame.error:

            pass


    # =========================================================
    # CLICK
    # =========================================================

    def click(self):

        self.play(
            "click"
        )


    # =========================================================
    # BACK
    # =========================================================

    def back(self):

        self.play(
            "back"
        )


    # =========================================================
    # SUCCESS
    # =========================================================

    def success(self):

        self.play(
            "success"
        )


    # =========================================================
    # ERROR
    # =========================================================

    def error(self):

        self.play(
            "error"
        )


    # =========================================================
    # HOVER
    # =========================================================

    def hover(
        self,
        button_id,
        scope=None
    ):

        # -----------------------------------------------------
        # New screen/scope
        # -----------------------------------------------------

        if (
            scope is not None
            and scope != self.hover_scope
        ):

            self.hover_scope = scope

            self.current_hover = None

        # -----------------------------------------------------
        # Same button
        # -----------------------------------------------------

        if button_id == self.current_hover:

            return

        self.current_hover = button_id

        # -----------------------------------------------------
        # Play hover sound
        # -----------------------------------------------------

        if button_id is not None:

            self.play(
                "hover"
            )


    # =========================================================
    # UPDATE HOVER
    # =========================================================

    def update_hover(
        self,
        buttons,
        mouse_position,
        scope=None
    ):

        hovered = None

        for name, rect in buttons.items():

            if rect.collidepoint(
                mouse_position
            ):

                hovered = name

                break

        # -----------------------------------------------------
        # Create unique hover ID
        # -----------------------------------------------------

        if (
            hovered is not None
            and scope
        ):

            hover_id = (
                f"{scope}_{hovered}"
            )

        else:

            hover_id = hovered

        self.hover(
            hover_id,
            scope
        )

        return hovered


    # =========================================================
    # RESET HOVER
    # =========================================================

    def reset_hover(
        self,
        scope=None
    ):

        self.current_hover = None

        self.hover_scope = scope


    # =========================================================
    # ENABLE / DISABLE
    # =========================================================

    def set_enabled(
        self,
        enabled
    ):

        self.enabled = bool(
            enabled
        )

        if not self.enabled:

            self.current_hover = None


    # =========================================================
    # SET SFX VOLUME
    # =========================================================

    def set_sfx_volume(
        self,
        volume,
        save=True
    ):

        volume = self.clamp_volume(
            volume
        )

        PREFERENCES[
            "sfx_volume"
        ] = volume

        # Apply immediately
        self.apply_volume_settings()

        # Save permanently
        if save:

            save_preferences(
                PREFERENCES
            )


    # =========================================================
    # SET MASTER VOLUME
    # =========================================================

    def set_master_volume(
        self,
        volume,
        save=True
    ):

        volume = self.clamp_volume(
            volume
        )

        PREFERENCES[
            "master_volume"
        ] = volume

        # Apply immediately
        self.apply_volume_settings()

        # Save permanently
        if save:

            save_preferences(
                PREFERENCES
            )


    # =========================================================
    # SET BOTH VOLUMES
    # =========================================================

    def set_volume(
        self,
        master=None,
        sfx=None,
        save=True
    ):

        if master is not None:

            PREFERENCES[
                "master_volume"
            ] = self.clamp_volume(
                master
            )

        if sfx is not None:

            PREFERENCES[
                "sfx_volume"
            ] = self.clamp_volume(
                sfx
            )

        # Apply immediately
        self.apply_volume_settings()

        # Save
        if save:

            save_preferences(
                PREFERENCES
            )


    # =========================================================
    # COMPATIBILITY
    # =========================================================

    def set_all_volume(
        self,
        volume
    ):

        self.set_sfx_volume(
            volume
        )


    # =========================================================
    # MUTE
    # =========================================================

    def mute(self):

        self.set_sfx_volume(
            0.0
        )


    # =========================================================
    # UNMUTE
    # =========================================================

    def unmute(
        self,
        volume=1.0
    ):

        self.set_sfx_volume(
            volume
        )


    # =========================================================
    # RELOAD SETTINGS
    # =========================================================

    def refresh(self):

        """
        Re-apply settings after another screen modifies
        PREFERENCES directly.
        """

        self.apply_volume_settings()


# =============================================================
# GLOBAL UI SOUND MANAGER
# =============================================================

ui_sounds = UISoundManager()