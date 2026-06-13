"""
device_sim.py — Hardware device abstraction stub.

In production this will drive a real SPI display (ST7701S on RPi Zero 2W).
For now it wraps the Pygame simulator so the rest of the codebase can call
a single interface regardless of whether we're running on hardware or desktop.

NOT BUILT — placeholder showing the intended interface.
"""

from abc import ABC, abstractmethod
from PIL import Image


class DisplayBackend(ABC):
    """Abstract backend — Pygame simulator or real SPI hardware."""

    @abstractmethod
    def show(self, img: Image.Image) -> None:
        """Push a 360×360 PIL image to the display."""

    @abstractmethod
    def backlight(self, level: float) -> None:
        """Set backlight brightness 0.0–1.0."""

    @abstractmethod
    def read_touch(self) -> tuple[int, int] | None:
        """Return (x, y) of last touch event, or None."""


class PygameBackend(DisplayBackend):
    """Pygame window backend — used by the desktop simulator."""

    def __init__(self, window):
        self._win = window

    def show(self, img: Image.Image) -> None:
        import pygame
        from simulator.display.gravity_sim import pil_to_surface, apply_circular_clip, DISC_OFFSET
        surf    = pil_to_surface(img)
        clipped = apply_circular_clip(surf)
        self._win.blit(clipped, (DISC_OFFSET, DISC_OFFSET))
        pygame.display.flip()

    def backlight(self, level: float) -> None:
        pass  # Not applicable on desktop

    def read_touch(self) -> tuple[int, int] | None:
        import pygame
        for event in pygame.event.get(pygame.MOUSEBUTTONUP):
            return event.pos
        return None


class HardwareBackend(DisplayBackend):
    """
    SPI hardware backend — NOT BUILT.

    Future implementation will:
    - Open /dev/spidev0.0 at 40 MHz
    - Send ST7701S initialisation sequence
    - Convert PIL image to RGB565 bytes and blast to framebuffer
    - Drive backlight via GPIO PWM
    - Read FT6236 capacitive touch over I2C
    """

    def show(self, img: Image.Image) -> None:
        raise NotImplementedError("Hardware backend not yet implemented")

    def backlight(self, level: float) -> None:
        raise NotImplementedError

    def read_touch(self) -> tuple[int, int] | None:
        raise NotImplementedError
