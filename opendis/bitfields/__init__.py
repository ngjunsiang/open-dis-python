"""Bitfield view classes layered over raw integer wire fields.

Design: docs/design/dis7-representation.md §3.5. The wire field stays a
plain integer; these views decode/encode named sub-fields without
disturbing unknown or reserved bits.
"""

from opendis.bitfields.appearance import (
    AirPlatformAppearance,
    AirPlatformCapabilities,
    LandPlatformAppearance,
    LandPlatformCapabilities,
)
from opendis.bitfields.base import BitfieldView
from opendis.bitfields.minefield import MinefieldStateAppearance
from opendis.bitfields.simulation_management import StopFreezeFrozenBehavior
from opendis.bitfields.warfare import DEFireFlags

__all__ = [
    "AirPlatformAppearance",
    "AirPlatformCapabilities",
    "BitfieldView",
    "DEFireFlags",
    "LandPlatformAppearance",
    "LandPlatformCapabilities",
    "MinefieldStateAppearance",
    "StopFreezeFrozenBehavior",
]
