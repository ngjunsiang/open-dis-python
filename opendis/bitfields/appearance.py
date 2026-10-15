"""Entity Appearance (IEEE 1278.1-2012 §6.2.26) and Entity Capabilities
(§6.2.27) bitfield views.

Layouts transcribed from SISO-REF-010 v37 bitfield tables: Land Platform
Appearance [UID 31], Air Platform Appearance [UID 32], Land Platform
Capabilities [UID 450], Air Platform Capabilities [UID 451]. One view
class per entity kind/domain layout, all over the same uint32 wire field.

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
    "LandPlatformAppearance",
    "LandPlatformCapabilities",
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
