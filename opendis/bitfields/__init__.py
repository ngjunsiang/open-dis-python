"""Bitfield view classes layered over raw integer wire fields.

Design: docs/design/dis7-representation.md §3.5. The wire field stays a
plain integer; these views decode/encode named sub-fields without
disturbing unknown or reserved bits.
"""

from opendis.bitfields.appearance import (
    AirPlatformAppearance,
    AirPlatformCapabilities,
    CulturalFeatureAppearance,
    EnvironmentalAppearance,
    ExpendableAppearance,
    LandPlatformAppearance,
    LandPlatformCapabilities,
    LifeFormsAppearance,
    MunitionAppearance,
    MunitionCapabilities,
    RadioAppearance,
    SensorEmitterAppearance,
    SpacePlatformAppearance,
    SpacePlatformCapabilities,
    SubsurfacePlatformAppearance,
    SubsurfacePlatformCapabilities,
    SupplyAppearance,
    SurfacePlatformAppearance,
    SurfacePlatformCapabilities,
)
from opendis.bitfields.base import BitfieldView
from opendis.bitfields.minefield import MinefieldStateAppearance
from opendis.bitfields.simulation_management import StopFreezeFrozenBehavior
from opendis.bitfields.warfare import DEFireFlags

__all__ = [
    "AirPlatformAppearance",
    "AirPlatformCapabilities",
    "BitfieldView",
    "CulturalFeatureAppearance",
    "DEFireFlags",
    "EnvironmentalAppearance",
    "ExpendableAppearance",
    "LandPlatformAppearance",
    "LandPlatformCapabilities",
    "LifeFormsAppearance",
    "MinefieldStateAppearance",
    "MunitionAppearance",
    "MunitionCapabilities",
    "RadioAppearance",
    "SensorEmitterAppearance",
    "SpacePlatformAppearance",
    "SpacePlatformCapabilities",
    "StopFreezeFrozenBehavior",
    "SubsurfacePlatformAppearance",
    "SubsurfacePlatformCapabilities",
    "SupplyAppearance",
    "SurfacePlatformAppearance",
    "SurfacePlatformCapabilities",
]
