"""Entity Appearance (IEEE 1278.1-2012 §6.2.26) and Entity Capabilities
(§6.2.27) bitfield views.

Layouts transcribed from SISO-REF-010 v37 bitfield tables: all 13
appearance variants [UID 31-43] — one per entity kind, and per domain
for platforms — plus the six capability tables with REF-010 layouts
[UID 450-455]. One view class per entity kind/domain layout, all over
the same uint32 wire field. Kinds without a capability table
(life forms, environmental, cultural, supply, radio, expendable,
sensor/emitter) keep the raw integer.

# generator: layouts and bit positions are mechanical output of the
# SISO-REF-010 bitfield tables; the row-name to camelCase property
# sanitization ("Spot/Search Light #1 On" -> spotSearchLight1On) needs a
# name-mapping table in the generator.
"""

from typing import ClassVar

from opendis.bitfields.base import BitfieldView

__all__ = [
    "AirPlatformAppearance",
    "AirPlatformCapabilities",
    "CulturalFeatureAppearance",
    "EnvironmentalAppearance",
    "ExpendableAppearance",
    "LandPlatformAppearance",
    "LandPlatformCapabilities",
    "LifeFormsAppearance",
    "MunitionAppearance",
    "MunitionCapabilities",
    "RadioAppearance",
    "SensorEmitterAppearance",
    "SpacePlatformAppearance",
    "SpacePlatformCapabilities",
    "SubsurfacePlatformAppearance",
    "SubsurfacePlatformCapabilities",
    "SupplyAppearance",
    "SurfacePlatformAppearance",
    "SurfacePlatformCapabilities",
]


class LandPlatformAppearance(BitfieldView):
    """Entity Appearance layout for land platforms [UID 31].

    Single-bit properties are bool; True means the enumerated value 1
    (e.g. ``paintScheme=True`` is camouflage [UID 378], ``state=True``
    is deactivated [UID 386]).
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("paintScheme", 0, 1, 378),
        ("mobilityKilled", 1, 1, None),
        ("firePowerKilled", 2, 1, None),
        ("damage", 3, 2, 379),
        ("isSmokeEmitting", 5, 1, None),
        ("isEngineEmittingSmoke", 6, 1, None),
        ("trailingDustCloud", 7, 2, 381),
        ("primaryHatch", 9, 3, 382),
        ("headLightsOn", 12, 1, None),
        ("tailLightsOn", 13, 1, None),
        ("brakeLightsOn", 14, 1, None),
        ("isFlaming", 15, 1, None),
        ("launcherOperational", 16, 1, 383),
        ("camouflageType", 17, 2, 384),
        ("concealedPosition", 19, 1, 385),
        ("radarDeployed", 20, 1, None),
        ("isFrozen", 21, 1, None),
        ("powerPlantOn", 22, 1, None),
        ("state", 23, 1, 386),
        ("tentExtended", 24, 1, None),
        ("rampExtended", 25, 1, None),
        ("blackoutLightsOn", 26, 1, None),
        ("blackoutBrakeLightsOn", 27, 1, None),
        ("spotSearchLight1On", 28, 1, None),
        ("interiorLightsForwardOn", 29, 1, None),
        ("occupantsSurrendered", 30, 1, None),
        ("maskedCloaked", 31, 1, None),
    )

    @property
    def paintScheme(self) -> bool:
        return self._getBit(0)

    @paintScheme.setter
    def paintScheme(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def mobilityKilled(self) -> bool:
        return self._getBit(1)

    @mobilityKilled.setter
    def mobilityKilled(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def firePowerKilled(self) -> bool:
        return self._getBit(2)

    @firePowerKilled.setter
    def firePowerKilled(self, on: bool) -> None:
        self._setBit(2, on)

    @property
    def damage(self) -> int:
        """[UID 379] Appearance-Damage."""
        return self._getBits(3, 2, 379)

    @damage.setter
    def damage(self, value: int) -> None:
        self._setBits(3, 2, value)

    @property
    def isSmokeEmitting(self) -> bool:
        return self._getBit(5)

    @isSmokeEmitting.setter
    def isSmokeEmitting(self, on: bool) -> None:
        self._setBit(5, on)

    @property
    def isEngineEmittingSmoke(self) -> bool:
        return self._getBit(6)

    @isEngineEmittingSmoke.setter
    def isEngineEmittingSmoke(self, on: bool) -> None:
        self._setBit(6, on)

    @property
    def trailingDustCloud(self) -> int:
        """[UID 381] Appearance-Trailing Effects."""
        return self._getBits(7, 2, 381)

    @trailingDustCloud.setter
    def trailingDustCloud(self, value: int) -> None:
        self._setBits(7, 2, value)

    @property
    def primaryHatch(self) -> int:
        """[UID 382] Appearance-Hatch."""
        return self._getBits(9, 3, 382)

    @primaryHatch.setter
    def primaryHatch(self, value: int) -> None:
        self._setBits(9, 3, value)

    @property
    def headLightsOn(self) -> bool:
        return self._getBit(12)

    @headLightsOn.setter
    def headLightsOn(self, on: bool) -> None:
        self._setBit(12, on)

    @property
    def tailLightsOn(self) -> bool:
        return self._getBit(13)

    @tailLightsOn.setter
    def tailLightsOn(self, on: bool) -> None:
        self._setBit(13, on)

    @property
    def brakeLightsOn(self) -> bool:
        return self._getBit(14)

    @brakeLightsOn.setter
    def brakeLightsOn(self, on: bool) -> None:
        self._setBit(14, on)

    @property
    def isFlaming(self) -> bool:
        return self._getBit(15)

    @isFlaming.setter
    def isFlaming(self, on: bool) -> None:
        self._setBit(15, on)

    @property
    def launcherOperational(self) -> bool:
        return self._getBit(16)

    @launcherOperational.setter
    def launcherOperational(self, on: bool) -> None:
        self._setBit(16, on)

    @property
    def camouflageType(self) -> int:
        """[UID 384] Appearance-Camouflage Type."""
        return self._getBits(17, 2, 384)

    @camouflageType.setter
    def camouflageType(self, value: int) -> None:
        self._setBits(17, 2, value)

    @property
    def concealedPosition(self) -> bool:
        return self._getBit(19)

    @concealedPosition.setter
    def concealedPosition(self, on: bool) -> None:
        self._setBit(19, on)

    @property
    def radarDeployed(self) -> bool:
        return self._getBit(20)

    @radarDeployed.setter
    def radarDeployed(self, on: bool) -> None:
        self._setBit(20, on)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def powerPlantOn(self) -> bool:
        return self._getBit(22)

    @powerPlantOn.setter
    def powerPlantOn(self, on: bool) -> None:
        self._setBit(22, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)

    @property
    def tentExtended(self) -> bool:
        return self._getBit(24)

    @tentExtended.setter
    def tentExtended(self, on: bool) -> None:
        self._setBit(24, on)

    @property
    def rampExtended(self) -> bool:
        return self._getBit(25)

    @rampExtended.setter
    def rampExtended(self, on: bool) -> None:
        self._setBit(25, on)

    @property
    def blackoutLightsOn(self) -> bool:
        return self._getBit(26)

    @blackoutLightsOn.setter
    def blackoutLightsOn(self, on: bool) -> None:
        self._setBit(26, on)

    @property
    def blackoutBrakeLightsOn(self) -> bool:
        return self._getBit(27)

    @blackoutBrakeLightsOn.setter
    def blackoutBrakeLightsOn(self, on: bool) -> None:
        self._setBit(27, on)

    @property
    def spotSearchLight1On(self) -> bool:
        return self._getBit(28)

    @spotSearchLight1On.setter
    def spotSearchLight1On(self, on: bool) -> None:
        self._setBit(28, on)

    @property
    def interiorLightsForwardOn(self) -> bool:
        return self._getBit(29)

    @interiorLightsForwardOn.setter
    def interiorLightsForwardOn(self, on: bool) -> None:
        self._setBit(29, on)

    @property
    def occupantsSurrendered(self) -> bool:
        return self._getBit(30)

    @occupantsSurrendered.setter
    def occupantsSurrendered(self, on: bool) -> None:
        self._setBit(30, on)

    @property
    def maskedCloaked(self) -> bool:
        return self._getBit(31)

    @maskedCloaked.setter
    def maskedCloaked(self, on: bool) -> None:
        self._setBit(31, on)


class AirPlatformAppearance(BitfieldView):
    """Entity Appearance layout for air platforms [UID 32]."""

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("paintScheme", 0, 1, 378),
        ("propulsionKilled", 1, 1, None),
        ("nvgMode", 2, 1, 400),
        ("damage", 3, 2, 379),
        ("isSmokeEmitting", 5, 1, None),
        ("isEngineEmittingSmoke", 6, 1, None),
        ("trailingEffects", 7, 2, 381),
        ("canopyTroopDoor", 9, 3, 387),
        ("landingLightsOn", 12, 1, None),
        ("navigationLightsOn", 13, 1, None),
        ("antiCollisionLightsOn", 14, 1, None),
        ("isFlaming", 15, 1, None),
        ("afterburnerOn", 16, 1, None),
        ("lowerAntiCollisionLightOn", 17, 1, None),
        ("upperAntiCollisionLightOn", 18, 1, None),
        ("antiCollisionLightDayNight", 19, 1, 397),
        ("isBlinking", 20, 1, None),
        ("isFrozen", 21, 1, None),
        ("powerPlantOn", 22, 1, None),
        ("state", 23, 1, 386),
        ("formationLightsOn", 24, 1, None),
        ("landingGearExtended", 25, 1, None),
        ("cargoDoorsOpened", 26, 1, None),
        ("navigationPositionBrightness", 27, 1, 398),
        ("spotSearchLight1On", 28, 1, None),
        ("interiorLightsOn", 29, 1, None),
        ("reverseThrustEngaged", 30, 1, None),
        ("weightOnWheels", 31, 1, None),
    )

    @property
    def paintScheme(self) -> bool:
        return self._getBit(0)

    @paintScheme.setter
    def paintScheme(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def propulsionKilled(self) -> bool:
        return self._getBit(1)

    @propulsionKilled.setter
    def propulsionKilled(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def nvgMode(self) -> bool:
        return self._getBit(2)

    @nvgMode.setter
    def nvgMode(self, on: bool) -> None:
        self._setBit(2, on)

    @property
    def damage(self) -> int:
        """[UID 379] Appearance-Damage."""
        return self._getBits(3, 2, 379)

    @damage.setter
    def damage(self, value: int) -> None:
        self._setBits(3, 2, value)

    @property
    def isSmokeEmitting(self) -> bool:
        return self._getBit(5)

    @isSmokeEmitting.setter
    def isSmokeEmitting(self, on: bool) -> None:
        self._setBit(5, on)

    @property
    def isEngineEmittingSmoke(self) -> bool:
        return self._getBit(6)

    @isEngineEmittingSmoke.setter
    def isEngineEmittingSmoke(self, on: bool) -> None:
        self._setBit(6, on)

    @property
    def trailingEffects(self) -> int:
        """[UID 381] Appearance-Trailing Effects."""
        return self._getBits(7, 2, 381)

    @trailingEffects.setter
    def trailingEffects(self, value: int) -> None:
        self._setBits(7, 2, value)

    @property
    def canopyTroopDoor(self) -> int:
        """[UID 387] Appearance-Canopy."""
        return self._getBits(9, 3, 387)

    @canopyTroopDoor.setter
    def canopyTroopDoor(self, value: int) -> None:
        self._setBits(9, 3, value)

    @property
    def landingLightsOn(self) -> bool:
        return self._getBit(12)

    @landingLightsOn.setter
    def landingLightsOn(self, on: bool) -> None:
        self._setBit(12, on)

    @property
    def navigationLightsOn(self) -> bool:
        return self._getBit(13)

    @navigationLightsOn.setter
    def navigationLightsOn(self, on: bool) -> None:
        self._setBit(13, on)

    @property
    def antiCollisionLightsOn(self) -> bool:
        return self._getBit(14)

    @antiCollisionLightsOn.setter
    def antiCollisionLightsOn(self, on: bool) -> None:
        self._setBit(14, on)

    @property
    def isFlaming(self) -> bool:
        return self._getBit(15)

    @isFlaming.setter
    def isFlaming(self, on: bool) -> None:
        self._setBit(15, on)

    @property
    def afterburnerOn(self) -> bool:
        return self._getBit(16)

    @afterburnerOn.setter
    def afterburnerOn(self, on: bool) -> None:
        self._setBit(16, on)

    @property
    def lowerAntiCollisionLightOn(self) -> bool:
        return self._getBit(17)

    @lowerAntiCollisionLightOn.setter
    def lowerAntiCollisionLightOn(self, on: bool) -> None:
        self._setBit(17, on)

    @property
    def upperAntiCollisionLightOn(self) -> bool:
        return self._getBit(18)

    @upperAntiCollisionLightOn.setter
    def upperAntiCollisionLightOn(self, on: bool) -> None:
        self._setBit(18, on)

    @property
    def antiCollisionLightDayNight(self) -> bool:
        return self._getBit(19)

    @antiCollisionLightDayNight.setter
    def antiCollisionLightDayNight(self, on: bool) -> None:
        self._setBit(19, on)

    @property
    def isBlinking(self) -> bool:
        return self._getBit(20)

    @isBlinking.setter
    def isBlinking(self, on: bool) -> None:
        self._setBit(20, on)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def powerPlantOn(self) -> bool:
        return self._getBit(22)

    @powerPlantOn.setter
    def powerPlantOn(self, on: bool) -> None:
        self._setBit(22, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)

    @property
    def formationLightsOn(self) -> bool:
        return self._getBit(24)

    @formationLightsOn.setter
    def formationLightsOn(self, on: bool) -> None:
        self._setBit(24, on)

    @property
    def landingGearExtended(self) -> bool:
        return self._getBit(25)

    @landingGearExtended.setter
    def landingGearExtended(self, on: bool) -> None:
        self._setBit(25, on)

    @property
    def cargoDoorsOpened(self) -> bool:
        return self._getBit(26)

    @cargoDoorsOpened.setter
    def cargoDoorsOpened(self, on: bool) -> None:
        self._setBit(26, on)

    @property
    def navigationPositionBrightness(self) -> bool:
        return self._getBit(27)

    @navigationPositionBrightness.setter
    def navigationPositionBrightness(self, on: bool) -> None:
        self._setBit(27, on)

    @property
    def spotSearchLight1On(self) -> bool:
        return self._getBit(28)

    @spotSearchLight1On.setter
    def spotSearchLight1On(self, on: bool) -> None:
        self._setBit(28, on)

    @property
    def interiorLightsOn(self) -> bool:
        return self._getBit(29)

    @interiorLightsOn.setter
    def interiorLightsOn(self, on: bool) -> None:
        self._setBit(29, on)

    @property
    def reverseThrustEngaged(self) -> bool:
        return self._getBit(30)

    @reverseThrustEngaged.setter
    def reverseThrustEngaged(self, on: bool) -> None:
        self._setBit(30, on)

    @property
    def weightOnWheels(self) -> bool:
        return self._getBit(31)

    @weightOnWheels.setter
    def weightOnWheels(self, on: bool) -> None:
        self._setBit(31, on)


class SurfacePlatformAppearance(BitfieldView):
    """SISO-REF-010 [UID 33] Surface Platform Appearance — 32-bit field.

    Bit 2 and Bits 9–11 and Bits 13–14 and Bits 19–20 and Bits 24–26 and Bits 30–31 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("paintScheme", 0, 1, 378),
        ("mobilityKilled", 1, 1, None),
        ("damage", 3, 2, 379),
        ("isSmokeEmanating", 5, 1, None),
        ("isEngineEmittingSmoke", 6, 1, None),
        ("wakeSize", 7, 2, 381),
        ("runningLightsOn", 12, 1, None),
        ("isFlaming", 15, 1, None),
        ("isAccommodationLadderLowered", 16, 1, None),
        ("isFenceRaised", 17, 1, None),
        ("isFlagRaised", 18, 1, None),
        ("isFrozen", 21, 1, None),
        ("powerPlantOn", 22, 1, None),
        ("state", 23, 1, 386),
        ("towedArraySonar", 27, 1, None),
        ("spotLightsOn", 28, 1, None),
        ("interiorLightsOn", 29, 1, None),
    )

    @property
    def paintScheme(self) -> bool:
        return self._getBit(0)

    @paintScheme.setter
    def paintScheme(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def mobilityKilled(self) -> bool:
        return self._getBit(1)

    @mobilityKilled.setter
    def mobilityKilled(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def damage(self) -> int:
        """[UID 379] Appearance-Damage."""
        return self._getBits(3, 2, 379)

    @damage.setter
    def damage(self, value: int) -> None:
        self._setBits(3, 2, value)

    @property
    def isSmokeEmanating(self) -> bool:
        return self._getBit(5)

    @isSmokeEmanating.setter
    def isSmokeEmanating(self, on: bool) -> None:
        self._setBit(5, on)

    @property
    def isEngineEmittingSmoke(self) -> bool:
        return self._getBit(6)

    @isEngineEmittingSmoke.setter
    def isEngineEmittingSmoke(self, on: bool) -> None:
        self._setBit(6, on)

    @property
    def wakeSize(self) -> int:
        """[UID 381] Appearance-Trailing Effects."""
        return self._getBits(7, 2, 381)

    @wakeSize.setter
    def wakeSize(self, value: int) -> None:
        self._setBits(7, 2, value)

    @property
    def runningLightsOn(self) -> bool:
        return self._getBit(12)

    @runningLightsOn.setter
    def runningLightsOn(self, on: bool) -> None:
        self._setBit(12, on)

    @property
    def isFlaming(self) -> bool:
        return self._getBit(15)

    @isFlaming.setter
    def isFlaming(self, on: bool) -> None:
        self._setBit(15, on)

    @property
    def isAccommodationLadderLowered(self) -> bool:
        return self._getBit(16)

    @isAccommodationLadderLowered.setter
    def isAccommodationLadderLowered(self, on: bool) -> None:
        self._setBit(16, on)

    @property
    def isFenceRaised(self) -> bool:
        return self._getBit(17)

    @isFenceRaised.setter
    def isFenceRaised(self, on: bool) -> None:
        self._setBit(17, on)

    @property
    def isFlagRaised(self) -> bool:
        return self._getBit(18)

    @isFlagRaised.setter
    def isFlagRaised(self, on: bool) -> None:
        self._setBit(18, on)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def powerPlantOn(self) -> bool:
        return self._getBit(22)

    @powerPlantOn.setter
    def powerPlantOn(self, on: bool) -> None:
        self._setBit(22, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)

    @property
    def towedArraySonar(self) -> bool:
        return self._getBit(27)

    @towedArraySonar.setter
    def towedArraySonar(self, on: bool) -> None:
        self._setBit(27, on)

    @property
    def spotLightsOn(self) -> bool:
        return self._getBit(28)

    @spotLightsOn.setter
    def spotLightsOn(self, on: bool) -> None:
        self._setBit(28, on)

    @property
    def interiorLightsOn(self) -> bool:
        return self._getBit(29)

    @interiorLightsOn.setter
    def interiorLightsOn(self, on: bool) -> None:
        self._setBit(29, on)


class SubsurfacePlatformAppearance(BitfieldView):
    """SISO-REF-010 [UID 34] Subsurface Platform Appearance — 32-bit field.

    Bit 2 and Bits 7–8 and Bits 13–14 and Bit 24 and Bits 28–31 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("paintScheme", 0, 1, 378),
        ("mobilityKilled", 1, 1, None),
        ("damage", 3, 2, 379),
        ("isSmokeEmanating", 5, 1, None),
        ("isEngineEmittingSmoke", 6, 1, None),
        ("hatch", 9, 3, 388),
        ("runningLightsOn", 12, 1, None),
        ("isFlaming", 15, 1, None),
        ("periscope", 16, 1, None),
        ("snorkel", 17, 1, None),
        ("radarMast", 18, 1, None),
        ("commsMast", 19, 1, None),
        ("esmMast", 20, 1, None),
        ("isFrozen", 21, 1, None),
        ("powerPlantOn", 22, 1, None),
        ("state", 23, 1, 386),
        ("torpedoTubes", 25, 1, None),
        ("missileHatches", 26, 1, None),
        ("towedArraySonar", 27, 1, None),
    )

    @property
    def paintScheme(self) -> bool:
        return self._getBit(0)

    @paintScheme.setter
    def paintScheme(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def mobilityKilled(self) -> bool:
        return self._getBit(1)

    @mobilityKilled.setter
    def mobilityKilled(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def damage(self) -> int:
        """[UID 379] Appearance-Damage."""
        return self._getBits(3, 2, 379)

    @damage.setter
    def damage(self, value: int) -> None:
        self._setBits(3, 2, value)

    @property
    def isSmokeEmanating(self) -> bool:
        return self._getBit(5)

    @isSmokeEmanating.setter
    def isSmokeEmanating(self, on: bool) -> None:
        self._setBit(5, on)

    @property
    def isEngineEmittingSmoke(self) -> bool:
        return self._getBit(6)

    @isEngineEmittingSmoke.setter
    def isEngineEmittingSmoke(self, on: bool) -> None:
        self._setBit(6, on)

    @property
    def hatch(self) -> int:
        """[UID 388] Appearance-Subsurface Hatch."""
        return self._getBits(9, 3, 388)

    @hatch.setter
    def hatch(self, value: int) -> None:
        self._setBits(9, 3, value)

    @property
    def runningLightsOn(self) -> bool:
        return self._getBit(12)

    @runningLightsOn.setter
    def runningLightsOn(self, on: bool) -> None:
        self._setBit(12, on)

    @property
    def isFlaming(self) -> bool:
        return self._getBit(15)

    @isFlaming.setter
    def isFlaming(self, on: bool) -> None:
        self._setBit(15, on)

    @property
    def periscope(self) -> bool:
        return self._getBit(16)

    @periscope.setter
    def periscope(self, on: bool) -> None:
        self._setBit(16, on)

    @property
    def snorkel(self) -> bool:
        return self._getBit(17)

    @snorkel.setter
    def snorkel(self, on: bool) -> None:
        self._setBit(17, on)

    @property
    def radarMast(self) -> bool:
        return self._getBit(18)

    @radarMast.setter
    def radarMast(self, on: bool) -> None:
        self._setBit(18, on)

    @property
    def commsMast(self) -> bool:
        return self._getBit(19)

    @commsMast.setter
    def commsMast(self, on: bool) -> None:
        self._setBit(19, on)

    @property
    def esmMast(self) -> bool:
        return self._getBit(20)

    @esmMast.setter
    def esmMast(self, on: bool) -> None:
        self._setBit(20, on)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def powerPlantOn(self) -> bool:
        return self._getBit(22)

    @powerPlantOn.setter
    def powerPlantOn(self, on: bool) -> None:
        self._setBit(22, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)

    @property
    def torpedoTubes(self) -> bool:
        return self._getBit(25)

    @torpedoTubes.setter
    def torpedoTubes(self, on: bool) -> None:
        self._setBit(25, on)

    @property
    def missileHatches(self) -> bool:
        return self._getBit(26)

    @missileHatches.setter
    def missileHatches(self, on: bool) -> None:
        self._setBit(26, on)

    @property
    def towedArraySonar(self) -> bool:
        return self._getBit(27)

    @towedArraySonar.setter
    def towedArraySonar(self, on: bool) -> None:
        self._setBit(27, on)


class SpacePlatformAppearance(BitfieldView):
    """SISO-REF-010 [UID 35] Space Platform Appearance — 32-bit field.

    Bit 2 and Bits 7–14 and Bits 16–20 and Bits 24–31 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("paintScheme", 0, 1, 378),
        ("mobilityKilled", 1, 1, None),
        ("damage", 3, 2, 379),
        ("isSmokeVaporEmanating", 5, 1, None),
        ("isEngineEmittingSmoke", 6, 1, None),
        ("isFlaming", 15, 1, None),
        ("isFrozen", 21, 1, None),
        ("powerPlantOn", 22, 1, None),
        ("state", 23, 1, 386),
    )

    @property
    def paintScheme(self) -> bool:
        return self._getBit(0)

    @paintScheme.setter
    def paintScheme(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def mobilityKilled(self) -> bool:
        return self._getBit(1)

    @mobilityKilled.setter
    def mobilityKilled(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def damage(self) -> int:
        """[UID 379] Appearance-Damage."""
        return self._getBits(3, 2, 379)

    @damage.setter
    def damage(self, value: int) -> None:
        self._setBits(3, 2, value)

    @property
    def isSmokeVaporEmanating(self) -> bool:
        return self._getBit(5)

    @isSmokeVaporEmanating.setter
    def isSmokeVaporEmanating(self, on: bool) -> None:
        self._setBit(5, on)

    @property
    def isEngineEmittingSmoke(self) -> bool:
        return self._getBit(6)

    @isEngineEmittingSmoke.setter
    def isEngineEmittingSmoke(self, on: bool) -> None:
        self._setBit(6, on)

    @property
    def isFlaming(self) -> bool:
        return self._getBit(15)

    @isFlaming.setter
    def isFlaming(self, on: bool) -> None:
        self._setBit(15, on)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def powerPlantOn(self) -> bool:
        return self._getBit(22)

    @powerPlantOn.setter
    def powerPlantOn(self, on: bool) -> None:
        self._setBit(22, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)


class MunitionAppearance(BitfieldView):
    """SISO-REF-010 [UID 36] Munition Appearance — 32-bit field.

    Bits 0–2 and Bits 9–14 and Bits 17–20 and Bits 26–30 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("damage", 3, 2, 379),
        ("isSmokeVaporEmanating", 5, 1, None),
        ("isEngineEmittingSmoke", 6, 1, None),
        ("vaporTrailSize", 7, 2, 381),
        ("isFlaming", 15, 1, None),
        ("launchFlashPresent", 16, 1, None),
        ("isFrozen", 21, 1, None),
        ("powerPlantOn", 22, 1, None),
        ("state", 23, 1, 386),
        ("coverShroudStatus", 24, 2, 426),
        ("maskedCloaked", 31, 1, None),
    )

    @property
    def damage(self) -> int:
        """[UID 379] Appearance-Damage."""
        return self._getBits(3, 2, 379)

    @damage.setter
    def damage(self, value: int) -> None:
        self._setBits(3, 2, value)

    @property
    def isSmokeVaporEmanating(self) -> bool:
        return self._getBit(5)

    @isSmokeVaporEmanating.setter
    def isSmokeVaporEmanating(self, on: bool) -> None:
        self._setBit(5, on)

    @property
    def isEngineEmittingSmoke(self) -> bool:
        return self._getBit(6)

    @isEngineEmittingSmoke.setter
    def isEngineEmittingSmoke(self, on: bool) -> None:
        self._setBit(6, on)

    @property
    def vaporTrailSize(self) -> int:
        """[UID 381] Appearance-Trailing Effects."""
        return self._getBits(7, 2, 381)

    @vaporTrailSize.setter
    def vaporTrailSize(self, value: int) -> None:
        self._setBits(7, 2, value)

    @property
    def isFlaming(self) -> bool:
        return self._getBit(15)

    @isFlaming.setter
    def isFlaming(self, on: bool) -> None:
        self._setBit(15, on)

    @property
    def launchFlashPresent(self) -> bool:
        return self._getBit(16)

    @launchFlashPresent.setter
    def launchFlashPresent(self, on: bool) -> None:
        self._setBit(16, on)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def powerPlantOn(self) -> bool:
        return self._getBit(22)

    @powerPlantOn.setter
    def powerPlantOn(self, on: bool) -> None:
        self._setBit(22, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)

    @property
    def coverShroudStatus(self) -> int:
        """[UID 426] Cover/Shroud Status."""
        return self._getBits(24, 2, 426)

    @coverShroudStatus.setter
    def coverShroudStatus(self, value: int) -> None:
        self._setBits(24, 2, value)

    @property
    def maskedCloaked(self) -> bool:
        return self._getBit(31)

    @maskedCloaked.setter
    def maskedCloaked(self, on: bool) -> None:
        self._setBit(31, on)


class LifeFormsAppearance(BitfieldView):
    """SISO-REF-010 [UID 37] Life Forms Appearance — 32-bit field.

    Bit 2 is reserved; it survives round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("paintScheme", 0, 1, 378),
        ("rocketMissileMunitionPresent", 1, 1, None),
        ("health", 3, 2, 390),
        ("complianceStatus", 5, 4, 391),
        ("clothingIRSignature", 9, 2, 802),
        ("signalSmokeInUse", 11, 1, None),
        ("flashLightsOn", 12, 1, None),
        ("signalMirrorInUse", 13, 1, None),
        ("irStrobeOn", 14, 1, None),
        ("irIlluminatorOn", 15, 1, None),
        ("lifeFormPosture", 16, 4, 392),
        ("isSmokingCigarette", 20, 1, None),
        ("isFrozen", 21, 1, None),
        ("mountedHoistedStatus", 22, 1, None),
        ("state", 23, 1, 386),
        ("weaponImplement1", 24, 2, 393),
        ("weaponImplement2", 26, 2, 393),
        ("camouflageType", 28, 2, 384),
        ("concealedStationary", 30, 1, 385),
        ("concealedMovement", 31, 1, 394),
    )

    @property
    def paintScheme(self) -> bool:
        return self._getBit(0)

    @paintScheme.setter
    def paintScheme(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def rocketMissileMunitionPresent(self) -> bool:
        return self._getBit(1)

    @rocketMissileMunitionPresent.setter
    def rocketMissileMunitionPresent(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def health(self) -> int:
        """[UID 390] Appearance-Life Form Health."""
        return self._getBits(3, 2, 390)

    @health.setter
    def health(self, value: int) -> None:
        self._setBits(3, 2, value)

    @property
    def complianceStatus(self) -> int:
        """[UID 391] Appearance-Life Form Compliance Status."""
        return self._getBits(5, 4, 391)

    @complianceStatus.setter
    def complianceStatus(self, value: int) -> None:
        self._setBits(5, 4, value)

    @property
    def clothingIRSignature(self) -> int:
        """[UID 802] Clothing IR Signature."""
        return self._getBits(9, 2, 802)

    @clothingIRSignature.setter
    def clothingIRSignature(self, value: int) -> None:
        self._setBits(9, 2, value)

    @property
    def signalSmokeInUse(self) -> bool:
        return self._getBit(11)

    @signalSmokeInUse.setter
    def signalSmokeInUse(self, on: bool) -> None:
        self._setBit(11, on)

    @property
    def flashLightsOn(self) -> bool:
        return self._getBit(12)

    @flashLightsOn.setter
    def flashLightsOn(self, on: bool) -> None:
        self._setBit(12, on)

    @property
    def signalMirrorInUse(self) -> bool:
        return self._getBit(13)

    @signalMirrorInUse.setter
    def signalMirrorInUse(self, on: bool) -> None:
        self._setBit(13, on)

    @property
    def irStrobeOn(self) -> bool:
        return self._getBit(14)

    @irStrobeOn.setter
    def irStrobeOn(self, on: bool) -> None:
        self._setBit(14, on)

    @property
    def irIlluminatorOn(self) -> bool:
        return self._getBit(15)

    @irIlluminatorOn.setter
    def irIlluminatorOn(self, on: bool) -> None:
        self._setBit(15, on)

    @property
    def lifeFormPosture(self) -> int:
        """[UID 392] Appearance-Life Form Posture."""
        return self._getBits(16, 4, 392)

    @lifeFormPosture.setter
    def lifeFormPosture(self, value: int) -> None:
        self._setBits(16, 4, value)

    @property
    def isSmokingCigarette(self) -> bool:
        return self._getBit(20)

    @isSmokingCigarette.setter
    def isSmokingCigarette(self, on: bool) -> None:
        self._setBit(20, on)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def mountedHoistedStatus(self) -> bool:
        return self._getBit(22)

    @mountedHoistedStatus.setter
    def mountedHoistedStatus(self, on: bool) -> None:
        self._setBit(22, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)

    @property
    def weaponImplement1(self) -> int:
        """[UID 393] Appearance-Life Form Weapon/Implement."""
        return self._getBits(24, 2, 393)

    @weaponImplement1.setter
    def weaponImplement1(self, value: int) -> None:
        self._setBits(24, 2, value)

    @property
    def weaponImplement2(self) -> int:
        """[UID 393] Appearance-Life Form Weapon/Implement."""
        return self._getBits(26, 2, 393)

    @weaponImplement2.setter
    def weaponImplement2(self, value: int) -> None:
        self._setBits(26, 2, value)

    @property
    def camouflageType(self) -> int:
        """[UID 384] Appearance-Camouflage Type."""
        return self._getBits(28, 2, 384)

    @camouflageType.setter
    def camouflageType(self, value: int) -> None:
        self._setBits(28, 2, value)

    @property
    def concealedStationary(self) -> bool:
        return self._getBit(30)

    @concealedStationary.setter
    def concealedStationary(self, on: bool) -> None:
        self._setBit(30, on)

    @property
    def concealedMovement(self) -> bool:
        return self._getBit(31)

    @concealedMovement.setter
    def concealedMovement(self, on: bool) -> None:
        self._setBit(31, on)


class EnvironmentalAppearance(BitfieldView):
    """SISO-REF-010 [UID 38] Environmental Appearance — 32-bit field.

    Bits 0–15 and Bit 20 and Bit 22 and Bits 24–30 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("density", 16, 4, 395),
        ("isFrozen", 21, 1, None),
        ("state", 23, 1, 386),
        ("maskedCloaked", 31, 1, None),
    )

    @property
    def density(self) -> int:
        """[UID 395] Appearance-Environmental Density."""
        return self._getBits(16, 4, 395)

    @density.setter
    def density(self, value: int) -> None:
        self._setBits(16, 4, value)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)

    @property
    def maskedCloaked(self) -> bool:
        return self._getBit(31)

    @maskedCloaked.setter
    def maskedCloaked(self, on: bool) -> None:
        self._setBit(31, on)


class CulturalFeatureAppearance(BitfieldView):
    """SISO-REF-010 [UID 39] Cultural Feature Appearance — 32-bit field.

    Bits 6–14 and Bits 16–20 and Bits 24–27 and Bit 30 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("damageArea", 0, 3, 889),
        ("damage", 3, 2, 379),
        ("isSmokeEmanating", 5, 1, None),
        ("isFlaming", 15, 1, None),
        ("isFrozen", 21, 1, None),
        ("internalHeatOn", 22, 1, None),
        ("state", 23, 1, 386),
        ("exteriorLightsOn", 28, 1, None),
        ("interiorLightsOn", 29, 1, None),
        ("maskedCloaked", 31, 1, None),
    )

    @property
    def damageArea(self) -> int:
        """[UID 889] Damage Area."""
        return self._getBits(0, 3, 889)

    @damageArea.setter
    def damageArea(self, value: int) -> None:
        self._setBits(0, 3, value)

    @property
    def damage(self) -> int:
        """[UID 379] Appearance-Damage."""
        return self._getBits(3, 2, 379)

    @damage.setter
    def damage(self, value: int) -> None:
        self._setBits(3, 2, value)

    @property
    def isSmokeEmanating(self) -> bool:
        return self._getBit(5)

    @isSmokeEmanating.setter
    def isSmokeEmanating(self, on: bool) -> None:
        self._setBit(5, on)

    @property
    def isFlaming(self) -> bool:
        return self._getBit(15)

    @isFlaming.setter
    def isFlaming(self, on: bool) -> None:
        self._setBit(15, on)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def internalHeatOn(self) -> bool:
        return self._getBit(22)

    @internalHeatOn.setter
    def internalHeatOn(self, on: bool) -> None:
        self._setBit(22, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)

    @property
    def exteriorLightsOn(self) -> bool:
        return self._getBit(28)

    @exteriorLightsOn.setter
    def exteriorLightsOn(self, on: bool) -> None:
        self._setBit(28, on)

    @property
    def interiorLightsOn(self) -> bool:
        return self._getBit(29)

    @interiorLightsOn.setter
    def interiorLightsOn(self, on: bool) -> None:
        self._setBit(29, on)

    @property
    def maskedCloaked(self) -> bool:
        return self._getBit(31)

    @maskedCloaked.setter
    def maskedCloaked(self, on: bool) -> None:
        self._setBit(31, on)


class SupplyAppearance(BitfieldView):
    """SISO-REF-010 [UID 40] Supply Appearance — 32-bit field.

    Bits 1–2 and Bits 5–6 and Bits 9–14 and Bits 16–20 and Bit 22 and Bits 26–30 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("paintScheme", 0, 1, 378),
        ("damage", 3, 2, 379),
        ("parachuteStatus", 7, 2, 401),
        ("isFlaming", 15, 1, None),
        ("isFrozen", 21, 1, None),
        ("state", 23, 1, 386),
        ("deployedStatus", 24, 2, 399),
        ("maskedCloaked", 31, 1, None),
    )

    @property
    def paintScheme(self) -> bool:
        return self._getBit(0)

    @paintScheme.setter
    def paintScheme(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def damage(self) -> int:
        """[UID 379] Appearance-Damage."""
        return self._getBits(3, 2, 379)

    @damage.setter
    def damage(self, value: int) -> None:
        self._setBits(3, 2, value)

    @property
    def parachuteStatus(self) -> int:
        """[UID 401] Parachute."""
        return self._getBits(7, 2, 401)

    @parachuteStatus.setter
    def parachuteStatus(self, value: int) -> None:
        self._setBits(7, 2, value)

    @property
    def isFlaming(self) -> bool:
        return self._getBit(15)

    @isFlaming.setter
    def isFlaming(self, on: bool) -> None:
        self._setBit(15, on)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)

    @property
    def deployedStatus(self) -> int:
        """[UID 399] Appearance-Supply Deployed."""
        return self._getBits(24, 2, 399)

    @deployedStatus.setter
    def deployedStatus(self, value: int) -> None:
        self._setBits(24, 2, value)

    @property
    def maskedCloaked(self) -> bool:
        return self._getBit(31)

    @maskedCloaked.setter
    def maskedCloaked(self, on: bool) -> None:
        self._setBit(31, on)


class RadioAppearance(BitfieldView):
    """SISO-REF-010 [UID 41] Radio Appearance — 32-bit field.

    Bits 0–20 and Bit 22 and Bits 24–31 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("isFrozen", 21, 1, None),
        ("state", 23, 1, 386),
    )

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)


class ExpendableAppearance(BitfieldView):
    """SISO-REF-010 [UID 42] Expendable Appearance — 32-bit field.

    Bits 0–2 and Bit 6 and Bits 12–14 and Bits 19–20 and Bits 26–30 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("damage", 3, 2, 379),
        ("isSmokeEmanating", 5, 1, None),
        ("parachuteStatus", 7, 2, 401),
        ("flareSmokeColor", 9, 3, 402),
        ("isFlaming", 15, 1, None),
        ("launchFlashPresent", 16, 1, None),
        ("flareSmokeStatus", 17, 2, 403),
        ("isFrozen", 21, 1, None),
        ("powerPlantOn", 22, 1, None),
        ("state", 23, 1, 386),
        ("spotChaffStatus", 24, 2, 404),
        ("maskedCloaked", 31, 1, None),
    )

    @property
    def damage(self) -> int:
        """[UID 379] Appearance-Damage."""
        return self._getBits(3, 2, 379)

    @damage.setter
    def damage(self, value: int) -> None:
        self._setBits(3, 2, value)

    @property
    def isSmokeEmanating(self) -> bool:
        return self._getBit(5)

    @isSmokeEmanating.setter
    def isSmokeEmanating(self, on: bool) -> None:
        self._setBit(5, on)

    @property
    def parachuteStatus(self) -> int:
        """[UID 401] Parachute."""
        return self._getBits(7, 2, 401)

    @parachuteStatus.setter
    def parachuteStatus(self, value: int) -> None:
        self._setBits(7, 2, value)

    @property
    def flareSmokeColor(self) -> int:
        """[UID 402] Flare/Smoke Color."""
        return self._getBits(9, 3, 402)

    @flareSmokeColor.setter
    def flareSmokeColor(self, value: int) -> None:
        self._setBits(9, 3, value)

    @property
    def isFlaming(self) -> bool:
        return self._getBit(15)

    @isFlaming.setter
    def isFlaming(self, on: bool) -> None:
        self._setBit(15, on)

    @property
    def launchFlashPresent(self) -> bool:
        return self._getBit(16)

    @launchFlashPresent.setter
    def launchFlashPresent(self, on: bool) -> None:
        self._setBit(16, on)

    @property
    def flareSmokeStatus(self) -> int:
        """[UID 403] Flare/Smoke Status."""
        return self._getBits(17, 2, 403)

    @flareSmokeStatus.setter
    def flareSmokeStatus(self, value: int) -> None:
        self._setBits(17, 2, value)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def powerPlantOn(self) -> bool:
        return self._getBit(22)

    @powerPlantOn.setter
    def powerPlantOn(self, on: bool) -> None:
        self._setBit(22, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)

    @property
    def spotChaffStatus(self) -> int:
        """[UID 404] Spot Chaff Status."""
        return self._getBits(24, 2, 404)

    @spotChaffStatus.setter
    def spotChaffStatus(self, value: int) -> None:
        self._setBits(24, 2, value)

    @property
    def maskedCloaked(self) -> bool:
        return self._getBit(31)

    @maskedCloaked.setter
    def maskedCloaked(self, on: bool) -> None:
        self._setBit(31, on)


class SensorEmitterAppearance(BitfieldView):
    """SISO-REF-010 [UID 43] Sensor/Emitter Appearance — 32-bit field.

    Bits 9–11 and Bits 13–14 and Bit 20 and Bit 25 and Bits 27–28 and Bits 30–31 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("paintScheme", 0, 1, 378),
        ("mobilityKilled", 1, 1, None),
        ("missionKilled", 2, 1, None),
        ("damage", 3, 2, 379),
        ("isSmokeEmanating", 5, 1, None),
        ("isEngineEmittingSmoke", 6, 1, None),
        ("trailingEffects", 7, 2, 381),
        ("lightsOn", 12, 1, None),
        ("isFlaming", 15, 1, None),
        ("antennaRaised", 16, 1, None),
        ("camouflageType", 17, 2, 384),
        ("concealedPosition", 19, 1, 385),
        ("isFrozen", 21, 1, None),
        ("powerPlantOn", 22, 1, None),
        ("state", 23, 1, 386),
        ("tentExtended", 24, 1, None),
        ("blackoutLightsOn", 26, 1, None),
        ("interiorLightsOn", 29, 1, None),
    )

    @property
    def paintScheme(self) -> bool:
        return self._getBit(0)

    @paintScheme.setter
    def paintScheme(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def mobilityKilled(self) -> bool:
        return self._getBit(1)

    @mobilityKilled.setter
    def mobilityKilled(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def missionKilled(self) -> bool:
        return self._getBit(2)

    @missionKilled.setter
    def missionKilled(self, on: bool) -> None:
        self._setBit(2, on)

    @property
    def damage(self) -> int:
        """[UID 379] Appearance-Damage."""
        return self._getBits(3, 2, 379)

    @damage.setter
    def damage(self, value: int) -> None:
        self._setBits(3, 2, value)

    @property
    def isSmokeEmanating(self) -> bool:
        return self._getBit(5)

    @isSmokeEmanating.setter
    def isSmokeEmanating(self, on: bool) -> None:
        self._setBit(5, on)

    @property
    def isEngineEmittingSmoke(self) -> bool:
        return self._getBit(6)

    @isEngineEmittingSmoke.setter
    def isEngineEmittingSmoke(self, on: bool) -> None:
        self._setBit(6, on)

    @property
    def trailingEffects(self) -> int:
        """[UID 381] Appearance-Trailing Effects."""
        return self._getBits(7, 2, 381)

    @trailingEffects.setter
    def trailingEffects(self, value: int) -> None:
        self._setBits(7, 2, value)

    @property
    def lightsOn(self) -> bool:
        return self._getBit(12)

    @lightsOn.setter
    def lightsOn(self, on: bool) -> None:
        self._setBit(12, on)

    @property
    def isFlaming(self) -> bool:
        return self._getBit(15)

    @isFlaming.setter
    def isFlaming(self, on: bool) -> None:
        self._setBit(15, on)

    @property
    def antennaRaised(self) -> bool:
        return self._getBit(16)

    @antennaRaised.setter
    def antennaRaised(self, on: bool) -> None:
        self._setBit(16, on)

    @property
    def camouflageType(self) -> int:
        """[UID 384] Appearance-Camouflage Type."""
        return self._getBits(17, 2, 384)

    @camouflageType.setter
    def camouflageType(self, value: int) -> None:
        self._setBits(17, 2, value)

    @property
    def concealedPosition(self) -> bool:
        return self._getBit(19)

    @concealedPosition.setter
    def concealedPosition(self, on: bool) -> None:
        self._setBit(19, on)

    @property
    def isFrozen(self) -> bool:
        return self._getBit(21)

    @isFrozen.setter
    def isFrozen(self, on: bool) -> None:
        self._setBit(21, on)

    @property
    def powerPlantOn(self) -> bool:
        return self._getBit(22)

    @powerPlantOn.setter
    def powerPlantOn(self, on: bool) -> None:
        self._setBit(22, on)

    @property
    def state(self) -> bool:
        return self._getBit(23)

    @state.setter
    def state(self, on: bool) -> None:
        self._setBit(23, on)

    @property
    def tentExtended(self) -> bool:
        return self._getBit(24)

    @tentExtended.setter
    def tentExtended(self, on: bool) -> None:
        self._setBit(24, on)

    @property
    def blackoutLightsOn(self) -> bool:
        return self._getBit(26)

    @blackoutLightsOn.setter
    def blackoutLightsOn(self, on: bool) -> None:
        self._setBit(26, on)

    @property
    def interiorLightsOn(self) -> bool:
        return self._getBit(29)

    @interiorLightsOn.setter
    def interiorLightsOn(self, on: bool) -> None:
        self._setBit(29, on)


class LandPlatformCapabilities(BitfieldView):
    """Entity Capabilities layout for land platforms [UID 450].

    Bits 4–5 are reserved and not exposed; they round-trip untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("ammunitionSupply", 0, 1, None),
        ("fuelSupply", 1, 1, None),
        ("recovery", 2, 1, None),
        ("repair", 3, 1, None),
        ("slingLoadable", 6, 1, None),
        ("iedPresenceIndicator", 7, 1, None),
        ("taskOrganizable", 8, 1, None),
    )

    @property
    def ammunitionSupply(self) -> bool:
        return self._getBit(0)

    @ammunitionSupply.setter
    def ammunitionSupply(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def fuelSupply(self) -> bool:
        return self._getBit(1)

    @fuelSupply.setter
    def fuelSupply(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def recovery(self) -> bool:
        return self._getBit(2)

    @recovery.setter
    def recovery(self, on: bool) -> None:
        self._setBit(2, on)

    @property
    def repair(self) -> bool:
        return self._getBit(3)

    @repair.setter
    def repair(self, on: bool) -> None:
        self._setBit(3, on)

    @property
    def slingLoadable(self) -> bool:
        return self._getBit(6)

    @slingLoadable.setter
    def slingLoadable(self, on: bool) -> None:
        self._setBit(6, on)

    @property
    def iedPresenceIndicator(self) -> bool:
        return self._getBit(7)

    @iedPresenceIndicator.setter
    def iedPresenceIndicator(self, on: bool) -> None:
        self._setBit(7, on)

    @property
    def taskOrganizable(self) -> bool:
        return self._getBit(8)

    @taskOrganizable.setter
    def taskOrganizable(self, on: bool) -> None:
        self._setBit(8, on)


class AirPlatformCapabilities(BitfieldView):
    """Entity Capabilities layout for air platforms [UID 451]."""

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("ammunitionSupply", 0, 1, None),
        ("fuelSupply", 1, 1, None),
        ("recovery", 2, 1, None),
        ("repair", 3, 1, None),
        ("adsB", 4, 1, None),
        ("slingLoadCarrier", 5, 1, None),
        ("slingLoadable", 6, 1, None),
        ("iedPresenceIndicator", 7, 1, None),
        ("taskOrganizable", 8, 1, None),
        ("laircm", 9, 1, None),
    )

    @property
    def ammunitionSupply(self) -> bool:
        return self._getBit(0)

    @ammunitionSupply.setter
    def ammunitionSupply(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def fuelSupply(self) -> bool:
        return self._getBit(1)

    @fuelSupply.setter
    def fuelSupply(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def recovery(self) -> bool:
        return self._getBit(2)

    @recovery.setter
    def recovery(self, on: bool) -> None:
        self._setBit(2, on)

    @property
    def repair(self) -> bool:
        return self._getBit(3)

    @repair.setter
    def repair(self, on: bool) -> None:
        self._setBit(3, on)

    @property
    def adsB(self) -> bool:
        return self._getBit(4)

    @adsB.setter
    def adsB(self, on: bool) -> None:
        self._setBit(4, on)

    @property
    def slingLoadCarrier(self) -> bool:
        return self._getBit(5)

    @slingLoadCarrier.setter
    def slingLoadCarrier(self, on: bool) -> None:
        self._setBit(5, on)

    @property
    def slingLoadable(self) -> bool:
        return self._getBit(6)

    @slingLoadable.setter
    def slingLoadable(self, on: bool) -> None:
        self._setBit(6, on)

    @property
    def iedPresenceIndicator(self) -> bool:
        return self._getBit(7)

    @iedPresenceIndicator.setter
    def iedPresenceIndicator(self, on: bool) -> None:
        self._setBit(7, on)

    @property
    def taskOrganizable(self) -> bool:
        return self._getBit(8)

    @taskOrganizable.setter
    def taskOrganizable(self, on: bool) -> None:
        self._setBit(8, on)

    @property
    def laircm(self) -> bool:
        return self._getBit(9)

    @laircm.setter
    def laircm(self, on: bool) -> None:
        self._setBit(9, on)


class SurfacePlatformCapabilities(BitfieldView):
    """SISO-REF-010 [UID 452] Surface Platform Capabilities — 32-bit field.

    Bits 4–5 and Bits 9–31 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("ammunitionSupply", 0, 1, None),
        ("fuelSupply", 1, 1, None),
        ("recovery", 2, 1, None),
        ("repair", 3, 1, None),
        ("slingLoadable", 6, 1, None),
        ("iedPresenceIndicator", 7, 1, None),
        ("taskOrganizable", 8, 1, None),
    )

    @property
    def ammunitionSupply(self) -> bool:
        return self._getBit(0)

    @ammunitionSupply.setter
    def ammunitionSupply(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def fuelSupply(self) -> bool:
        return self._getBit(1)

    @fuelSupply.setter
    def fuelSupply(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def recovery(self) -> bool:
        return self._getBit(2)

    @recovery.setter
    def recovery(self, on: bool) -> None:
        self._setBit(2, on)

    @property
    def repair(self) -> bool:
        return self._getBit(3)

    @repair.setter
    def repair(self, on: bool) -> None:
        self._setBit(3, on)

    @property
    def slingLoadable(self) -> bool:
        return self._getBit(6)

    @slingLoadable.setter
    def slingLoadable(self, on: bool) -> None:
        self._setBit(6, on)

    @property
    def iedPresenceIndicator(self) -> bool:
        return self._getBit(7)

    @iedPresenceIndicator.setter
    def iedPresenceIndicator(self, on: bool) -> None:
        self._setBit(7, on)

    @property
    def taskOrganizable(self) -> bool:
        return self._getBit(8)

    @taskOrganizable.setter
    def taskOrganizable(self, on: bool) -> None:
        self._setBit(8, on)


class SubsurfacePlatformCapabilities(BitfieldView):
    """SISO-REF-010 [UID 453] Subsurface Platform Capabilities — 32-bit field.

    Bits 4–5 and Bits 9–31 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("ammunitionSupply", 0, 1, None),
        ("fuelSupply", 1, 1, None),
        ("recovery", 2, 1, None),
        ("repair", 3, 1, None),
        ("slingLoadable", 6, 1, None),
        ("iedPresenceIndicator", 7, 1, None),
        ("taskOrganizable", 8, 1, None),
    )

    @property
    def ammunitionSupply(self) -> bool:
        return self._getBit(0)

    @ammunitionSupply.setter
    def ammunitionSupply(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def fuelSupply(self) -> bool:
        return self._getBit(1)

    @fuelSupply.setter
    def fuelSupply(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def recovery(self) -> bool:
        return self._getBit(2)

    @recovery.setter
    def recovery(self, on: bool) -> None:
        self._setBit(2, on)

    @property
    def repair(self) -> bool:
        return self._getBit(3)

    @repair.setter
    def repair(self, on: bool) -> None:
        self._setBit(3, on)

    @property
    def slingLoadable(self) -> bool:
        return self._getBit(6)

    @slingLoadable.setter
    def slingLoadable(self, on: bool) -> None:
        self._setBit(6, on)

    @property
    def iedPresenceIndicator(self) -> bool:
        return self._getBit(7)

    @iedPresenceIndicator.setter
    def iedPresenceIndicator(self, on: bool) -> None:
        self._setBit(7, on)

    @property
    def taskOrganizable(self) -> bool:
        return self._getBit(8)

    @taskOrganizable.setter
    def taskOrganizable(self, on: bool) -> None:
        self._setBit(8, on)


class SpacePlatformCapabilities(BitfieldView):
    """SISO-REF-010 [UID 454] Space Platform Capabilities — 32-bit field.

    Bits 4–31 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("ammunitionSupply", 0, 1, None),
        ("fuelSupply", 1, 1, None),
        ("recovery", 2, 1, None),
        ("repair", 3, 1, None),
    )

    @property
    def ammunitionSupply(self) -> bool:
        return self._getBit(0)

    @ammunitionSupply.setter
    def ammunitionSupply(self, on: bool) -> None:
        self._setBit(0, on)

    @property
    def fuelSupply(self) -> bool:
        return self._getBit(1)

    @fuelSupply.setter
    def fuelSupply(self, on: bool) -> None:
        self._setBit(1, on)

    @property
    def recovery(self) -> bool:
        return self._getBit(2)

    @recovery.setter
    def recovery(self, on: bool) -> None:
        self._setBit(2, on)

    @property
    def repair(self) -> bool:
        return self._getBit(3)

    @repair.setter
    def repair(self, on: bool) -> None:
        self._setBit(3, on)


class MunitionCapabilities(BitfieldView):
    """SISO-REF-010 [UID 455] Munition Capabilities — 32-bit field.

    Bits 0–6 and Bits 8–31 are reserved; they survive round-trips untouched.
    """

    _WIDTH: ClassVar[int] = 32
    _FIELDS: ClassVar[tuple[tuple[str, int, int, int | None], ...]] = (
        ("iedPresenceIndicator", 7, 1, None),
    )

    @property
    def iedPresenceIndicator(self) -> bool:
        return self._getBit(7)

    @iedPresenceIndicator.setter
    def iedPresenceIndicator(self, on: bool) -> None:
        self._setBit(7, on)
