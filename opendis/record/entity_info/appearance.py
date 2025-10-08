"""Classes for 6.2.26 Entity Appearance record

This record shall be defined as a 32-bit record (see [UID 31-43]).
"""

from opendis.record import base, bitfield
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import bf_enum

class AppearanceRecord(base.Record):
     """6.2.26 Entity Appearance Record
     
     A 32-bit record (see [UID 31-43]).
     """

     def marshalledSize(self) -> int:
          return 4


class UnknownAppearance(AppearanceRecord):
    """Placeholder for unknown appearance records."""
    def __init__(self, data: bytes = b'\0' * 4):
        self.data = data

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_bytes(self.data)

    def parse(self, inputStream: DataInputStream) -> None:
        _ = inputStream.read_bytes(self.marshalledSize())


class LandPlatformAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.1.1 Land Platform Appearance Record [UID 31]"""
    _struct = bitfield.bitfield(name="LandPlatformAppearance", fields=[
        ("paintScheme", bitfield.INTEGER, 1), # bit 0
        ("mobilityKilled", bitfield.INTEGER, 1),  # bit 1
        ("firepowerKilled", bitfield.INTEGER, 1),  # bit 2
        ("damage", bitfield.INTEGER, 2),  # bits 3-4
        ("isSmokeEmanating", bitfield.INTEGER, 1),  # bit 5
        ("isEngineEmittingSmoke", bitfield.INTEGER, 1),  # bit 6
        ("trailingDustCloud", bitfield.INTEGER, 2),  # bits 7-8
        ("primaryHatch", bitfield.INTEGER, 3),  # bits 9-11
        ("headLightsOn", bitfield.INTEGER, 1),  # bit 12
        ("tailLightsOn", bitfield.INTEGER, 1),  # bit 13
        ("brakeLightsOn", bitfield.INTEGER, 1),  # bit 14
        ("isFlaming", bitfield.INTEGER, 1),  # bit 15
        ("operational", bitfield.INTEGER, 1),  # bit 16
        ("camouflageType", bitfield.INTEGER, 2),  # bits 17-18
        ("concealedPosition", bitfield.INTEGER, 1),  # bit 19
        ("unused", bitfield.INTEGER, 1),  # bit 20
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("powerPlantOn", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("tentExtended", bitfield.INTEGER, 1),  # bit 24
        ("rampExtended", bitfield.INTEGER, 1),  # bit 25
        ("blackoutLightsOn", bitfield.INTEGER, 1),  # bit 26
        ("blackoutBrakeLightsOn", bitfield.INTEGER, 1),  # bit 27
        ("spotLightOn", bitfield.INTEGER, 1),  # bit 28
        ("interiorLightsOn", bitfield.INTEGER, 1),  # bit 29
        ("occupantsSurrendered", bitfield.INTEGER, 1),  # bit 30
        ("cloaked", bitfield.INTEGER, 1),  # bit 31
    ])

    def __init__(self,
                 paintScheme: bool = False,
                 mobilityKilled: bool = False,
                 firepowerKilled: bool = False,
                 damage: bf_enum = 0,
                 isSmokeEmanating: bool = False,
                 isEngineEmittingSmoke: bool = False,
                 trailingDustCloud: bf_enum = 0,
                 primaryHatch: bf_enum = 0,
                 headLightsOn: bool = False,
                 tailLightsOn: bool = False,
                 brakeLightsOn: bool = False,
                 isFlaming: bool = False,
                 operational: bool = True,
                 camouflageType: bf_enum = 0,
                 concealedPosition: bool = False,
                 isFrozen: bool = False,
                 powerPlantOn: bool = True,
                 state: bool = False,
                 tentExtended: bool = False,
                 rampExtended: bool = False,
                 blackoutLightsOn: bool = False,
                 blackoutBrakeLightsOn: bool = False,
                 spotLightOn: bool = False,
                 interiorLightsOn: bool = False,
                 occupantsSurrendered: bool = False,
                 cloaked: bool = False):
            self.paintScheme = paintScheme
            self.mobilityKilled = mobilityKilled
            self.firepowerKilled = firepowerKilled
            self.damage = damage
            self.isSmokeEmanating = isSmokeEmanating
            self.isEngineEmittingSmoke = isEngineEmittingSmoke
            self.trailingDustCloud = trailingDustCloud
            self.primaryHatch = primaryHatch
            self.headLightsOn = headLightsOn
            self.tailLightsOn = tailLightsOn
            self.brakeLightsOn = brakeLightsOn
            self.isFlaming = isFlaming
            self.operational = operational
            self.camouflageType = camouflageType
            self.concealedPosition = concealedPosition
            self.unused = 0
            self.isFrozen = isFrozen
            self.powerPlantOn = powerPlantOn
            self.state = state
            self.tentExtended = tentExtended
            self.rampExtended = rampExtended
            self.blackoutLightsOn = blackoutLightsOn
            self.blackoutBrakeLightsOn = blackoutBrakeLightsOn
            self.spotLightOn = spotLightOn
            self.interiorLightsOn = interiorLightsOn
            self.occupantsSurrendered = occupantsSurrendered
            self.cloaked = cloaked

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.paintScheme,
            self.mobilityKilled,
            self.firepowerKilled,
            self.damage,
            self.isSmokeEmanating,
            self.isEngineEmittingSmoke,
            self.trailingDustCloud,
            self.primaryHatch,
            self.headLightsOn,
            self.tailLightsOn,
            self.brakeLightsOn,
            self.isFlaming,
            self.operational,
            self.camouflageType,
            self.concealedPosition,
            self.unused,
            self.isFrozen,
            self.powerPlantOn,
            self.state,
            self.tentExtended,
            self.rampExtended,
            self.blackoutLightsOn,
            self.blackoutBrakeLightsOn,
            self.spotLightOn,
            self.interiorLightsOn,
            self.occupantsSurrendered,
            self.cloaked,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.paintScheme = record_bitfield.paintScheme
        self.mobilityKilled = record_bitfield.mobilityKilled
        self.firepowerKilled = record_bitfield.firepowerKilled
        self.damage = record_bitfield.damage
        self.isSmokeEmanating = record_bitfield.isSmokeEmanating
        self.isEngineEmittingSmoke = record_bitfield.isEngineEmittingSmoke
        self.trailingDustCloud = record_bitfield.trailingDustCloud
        self.primaryHatch = record_bitfield.primaryHatch
        self.headLightsOn = record_bitfield.headLightsOn
        self.tailLightsOn = record_bitfield.tailLightsOn
        self.brakeLightsOn = record_bitfield.brakeLightsOn
        self.isFlaming = record_bitfield.isFlaming
        self.operational = record_bitfield.operational
        self.camouflageType = record_bitfield.camouflageType
        self.concealedPosition = record_bitfield.concealedPosition
        self.unused = record_bitfield.unused
        self.isFrozen = record_bitfield.isFrozen
        self.powerPlantOn = record_bitfield.powerPlantOn
        self.state = record_bitfield.state
        self.tentExtended = record_bitfield.tentExtended
        self.rampExtended = record_bitfield.rampExtended
        self.blackoutLightsOn = record_bitfield.blackoutLightsOn
        self.blackoutBrakeLightsOn = record_bitfield.blackoutBrakeLightsOn
        self.spotLightOn = record_bitfield.spotLightOn
        self.interiorLightsOn = record_bitfield.interiorLightsOn
        self.occupantsSurrendered = record_bitfield.occupantsSurrendered
        self.cloaked = record_bitfield.cloaked


class AirPlatformAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.1.2 Air Platform Appearance Record [UID 32]"""
    _struct = bitfield.bitfield(name="AirPlatformAppearance", fields=[
        ("paintScheme", bitfield.INTEGER, 1),  # bit 0
        ("propulsionKilled", bitfield.INTEGER, 1),  # bit 1
        ("nvgMode", bitfield.INTEGER, 1),  # bit 2
        ("damage", bitfield.INTEGER, 2),  # bits 3-4
        ("isSmokeEmanating", bitfield.INTEGER, 1),  # bit 5
        ("isEngineEmittingSmoke", bitfield.INTEGER, 1),  # bit 6
        ("trailingEffects", bitfield.INTEGER, 2),  # bits 7-8
        ("canopyDoor", bitfield.INTEGER, 3),  # bits 9-11
        ("landingLightsOn", bitfield.INTEGER, 1),  # bit 12
        ("navigationLightsOn", bitfield.INTEGER, 1),  # bit 13
        ("antiCollisionLightsOn", bitfield.INTEGER, 1),  # bit 14
        ("isFlaming", bitfield.INTEGER, 1),  # bit 15
        ("afterburnerOn", bitfield.INTEGER, 1),  # bit 16
        ("lowerAntiCollisionLightOn", bitfield.INTEGER, 1),  # bit 17
        ("upperAntiCollisionLightOn", bitfield.INTEGER, 1),  # bit 18
        ("antiCollisionLightDayOrNight", bitfield.INTEGER, 1),  # bit 19
        ("isBlinking", bitfield.INTEGER, 1),  # bit 20
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("powerPlantOn", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("formationLightsOn", bitfield.INTEGER, 1),  # bit 24
        ("landingGearExtended", bitfield.INTEGER, 1),  # bit 25
        ("cargoDoorsOpened", bitfield.INTEGER, 1),  # bit 26
        ("navigationLightBrightness", bitfield.INTEGER, 1),  # bit 27
        ("spotLightOn", bitfield.INTEGER, 1),  # bit 28
        ("interiorLightsOn", bitfield.INTEGER, 1),  # bit 29
        ("reverseThrustEngaged", bitfield.INTEGER, 1),  # bit 30
        ("weightOnWheels", bitfield.INTEGER, 1),  # bit 31
    ])

    def __init__(self,
                 paintScheme: bool = False,
                 propulsionKilled: bool = False,
                 nvgMode: bool = False,
                 damage: bf_enum = 0,
                 isSmokeEmanating: bool = False,
                 isEngineEmittingSmoke: bool = False,
                 trailingEffects: bf_enum = 0,
                 canopyDoor: bf_enum = 0,
                 landingLightsOn: bool = False,
                 navigationLightsOn: bool = False,
                 antiCollisionLightsOn: bool = False,
                 isFlaming: bool = False,
                 afterburnerOn: bool = True,
                 lowerAntiCollisionLightOn: bool = False,
                 upperAntiCollisionLightOn: bool = False,
                 antiCollisionLightDayOrNight: bool = False,
                 isBlinking: bool = False,
                 isFrozen: bool = False,
                 powerPlantOn: bool = True,
                 state: bool = False,
                 formationLightsOn: bool = False,
                 landingGearExtended: bool = False,
                 cargoDoorsOpened: bool = False,
                 navigationLightBrightness: bool = False,
                 spotLightOn: bool = False,
                 interiorLightsOn: bool = False,
                 reverseThrustEngaged: bool = False,
                 weightOnWheels: bool = False):
            self.paintScheme = paintScheme
            self.propulsionKilled = propulsionKilled
            self.nvgMode = nvgMode
            self.damage = damage
            self.isSmokeEmanating = isSmokeEmanating
            self.isEngineEmittingSmoke = isEngineEmittingSmoke
            self.trailingEffects = trailingEffects
            self.canopyDoor = canopyDoor
            self.landingLightsOn = landingLightsOn
            self.navigationLightsOn = navigationLightsOn
            self.antiCollisionLightsOn = antiCollisionLightsOn
            self.isFlaming = isFlaming
            self.afterburnerOn = afterburnerOn
            self.lowerAntiCollisionLightOn = lowerAntiCollisionLightOn
            self.upperAntiCollisionLightOn = upperAntiCollisionLightOn
            self.antiCollisionLightDayOrNight = antiCollisionLightDayOrNight
            self.isFrozen = isFrozen
            self.isBlinking = isBlinking
            self.powerPlantOn = powerPlantOn
            self.state = state
            self.formationLightsOn = formationLightsOn
            self.landingGearExtended = landingGearExtended
            self.cargoDoorsOpened = cargoDoorsOpened
            self.navigationLightBrightness = navigationLightBrightness
            self.spotLightOn = spotLightOn
            self.interiorLightsOn = interiorLightsOn
            self.reverseThrustEngaged = reverseThrustEngaged
            self.weightOnWheels = weightOnWheels

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.paintScheme,
            self.propulsionKilled,
            self.nvgMode,
            self.damage,
            self.isSmokeEmanating,
            self.isEngineEmittingSmoke,
            self.trailingEffects,
            self.canopyDoor,
            self.landingLightsOn,
            self.navigationLightsOn,
            self.antiCollisionLightsOn,
            self.isFlaming,
            self.afterburnerOn,
            self.lowerAntiCollisionLightOn,
            self.upperAntiCollisionLightOn,
            self.antiCollisionLightDayOrNight,
            self.isFrozen,
            self.isBlinking,
            self.powerPlantOn,
            self.state,
            self.formationLightsOn,
            self.landingGearExtended,
            self.cargoDoorsOpened,
            self.navigationLightBrightness,
            self.spotLightOn,
            self.interiorLightsOn,
            self.reverseThrustEngaged,
            self.weightOnWheels,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.paintScheme = record_bitfield.paintScheme
        self.propulsionKilled = record_bitfield.propulsionKilled
        self.nvgMode = record_bitfield.nvgMode
        self.damage = record_bitfield.damage
        self.isSmokeEmanating = record_bitfield.isSmokeEmanating
        self.isEngineEmittingSmoke = record_bitfield.isEngineEmittingSmoke
        self.trailingEffects = record_bitfield.trailingEffects
        self.canopyDoor = record_bitfield.canopyDoor
        self.landingLightsOn = record_bitfield.landingLightsOn
        self.navigationLightsOn = record_bitfield.navigationLightsOn
        self.antiCollisionLightsOn = record_bitfield.antiCollisionLightsOn
        self.isFlaming = record_bitfield.isFlaming
        self.afterburnerOn = record_bitfield.afterburnerOn
        self.lowerAntiCollisionLightOn = record_bitfield.lowerAntiCollisionLightOn
        self.upperAntiCollisionLightOn = record_bitfield.upperAntiCollisionLightOn
        self.antiCollisionLightDayOrNight = record_bitfield.antiCollisionLightDayOrNight
        self.isFrozen = record_bitfield.isFrozen
        self.isBlinking = record_bitfield.isBlinking
        self.powerPlantOn = record_bitfield.powerPlantOn
        self.state = record_bitfield.state
        self.formationLightsOn = record_bitfield.formationLightsOn
        self.landingGearExtended = record_bitfield.landingGearExtended
        self.cargoDoorsOpened = record_bitfield.cargoDoorsOpened
        self.navigationLightBrightness = record_bitfield.navigationLightBrightness
        self.spotLightOn = record_bitfield.spotLightOn
        self.interiorLightsOn = record_bitfield.interiorLightsOn
        self.reverseThrustEngaged = record_bitfield.reverseThrustEngaged
        self.weightOnWheels = record_bitfield.weightOnWheels


class SurfacePlatformAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.1.3 Land Platform Appearance Record [UID 33]"""
    _struct = bitfield.bitfield(name="SurfacePlatformAppearance", fields=[
        ("paintScheme", bitfield.INTEGER, 1), # bit 0
        ("mobilityKilled", bitfield.INTEGER, 1),  # bit 1
        ("unused1", bitfield.INTEGER, 1),  # bit 2
        ("damage", bitfield.INTEGER, 2),  # bits 3-4
        ("isSmokeEmanating", bitfield.INTEGER, 1),  # bit 5
        ("isEngineEmittingSmoke", bitfield.INTEGER, 1),  # bit 6
        ("wakeSize", bitfield.INTEGER, 2),  # bits 7-8
        ("unused2", bitfield.INTEGER, 3),  # bits 9-11
        ("runningLightsOn", bitfield.INTEGER, 1),  # bit 12
        ("unused3", bitfield.INTEGER, 2),  # bits 13-14
        ("isFlaming", bitfield.INTEGER, 1),  # bit 15
        ("isAccomodationLadderLowered", bitfield.INTEGER, 1),  # bit 16
        ("isFenceRaised", bitfield.INTEGER, 2),  # bit 17
        ("isFlagRaised", bitfield.INTEGER, 2),  # bit 18
        ("unused4", bitfield.INTEGER, 2),  # bits 19-20
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("powerPlantOn", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("unused5", bitfield.INTEGER, 3),  # bits 24-26
        ("towedArraySonar", bitfield.INTEGER, 1),  # bit 27
        ("spotLightOn", bitfield.INTEGER, 1),  # bit 28
        ("interiorLightsOn", bitfield.INTEGER, 1),  # bit 29
        ("unused6", bitfield.INTEGER, 2),  # bits 30-31
    ])

    def __init__(self,
                 paintScheme: bool = False,
                 mobilityKilled: bool = False,
                 damage: bf_enum = 0,
                 isSmokeEmanating: bool = False,
                 isEngineEmittingSmoke: bool = False,
                 wakeSize: bf_enum = 0,
                 runningLightsOn: bf_enum = 0,
                 isFlaming: bool = False,
                 isAccomodationLadderLowered: bool = True,
                 isFenceRaised: bool = False,
                 isFlagRaised: bool = False,
                 isFrozen: bool = False,
                 powerPlantOn: bool = True,
                 state: bool = False,
                 towedArraySonar: bool = False,
                 spotLightOn: bool = False,
                 interiorLightsOn: bool = False):
            self.paintScheme = paintScheme
            self.mobilityKilled = mobilityKilled
            self.unused1 = 0
            self.damage = damage
            self.isSmokeEmanating = isSmokeEmanating
            self.isEngineEmittingSmoke = isEngineEmittingSmoke
            self.wakeSize = wakeSize
            self.unused2 = 0
            self.runningLightsOn = runningLightsOn
            self.unused3 = 0
            self.isFlaming = isFlaming
            self.isAccomodationLadderLowered = isAccomodationLadderLowered
            self.isFenceRaised = isFenceRaised
            self.isFlagRaised = isFlagRaised
            self.unused4 = 0
            self.isFrozen = isFrozen
            self.powerPlantOn = powerPlantOn
            self.state = state
            self.unused5 = 0
            self.towedArraySonar = towedArraySonar
            self.spotLightOn = spotLightOn
            self.interiorLightsOn = interiorLightsOn
            self.unused6 = 0

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.paintScheme,
            self.mobilityKilled,
            self.unused1,
            self.damage,
            self.isSmokeEmanating,
            self.isEngineEmittingSmoke,
            self.wakeSize,
            self.unused2,
            self.runningLightsOn,
            self.unused3,
            self.isFlaming,
            self.isAccomodationLadderLowered,
            self.isFenceRaised,
            self.isFlagRaised,
            self.unused4,
            self.isFrozen,
            self.powerPlantOn,
            self.state,
            self.unused5,
            self.towedArraySonar,
            self.spotLightOn,
            self.interiorLightsOn,
            self.unused6,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.paintScheme = record_bitfield.paintScheme
        self.mobilityKilled = record_bitfield.mobilityKilled
        self.unused1 = record_bitfield.unused1
        self.damage = record_bitfield.damage
        self.isSmokeEmanating = record_bitfield.isSmokeEmanating
        self.isEngineEmittingSmoke = record_bitfield.isEngineEmittingSmoke
        self.wakeSize = record_bitfield.wakeSize
        self.unused2 = record_bitfield.unused2
        self.runningLightsOn = record_bitfield.runningLightsOn
        self.unused3 = record_bitfield.unused3
        self.isFlaming = record_bitfield.isFlaming
        self.isAccomodationLadderLowered = record_bitfield.isAccomodationLadderLowered
        self.isFenceRaised = record_bitfield.isFenceRaised
        self.isFlagRaised = record_bitfield.isFlagRaised
        self.unused4 = record_bitfield.unused4
        self.isFrozen = record_bitfield.isFrozen
        self.powerPlantOn = record_bitfield.powerPlantOn
        self.state = record_bitfield.state
        self.unused5 = record_bitfield.unused5
        self.towedArraySonar = record_bitfield.towedArraySonar
        self.spotLightOn = record_bitfield.spotLightOn
        self.interiorLightsOn = record_bitfield.interiorLightsOn
        self.unused6 = record_bitfield.unused6


class SubsurfacePlatformAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.1.4 Subsurface Platform Appearance Record [UID 34]"""
    _struct = bitfield.bitfield(name="SubsurfacePlatformAppearance", fields=[
        ("paintScheme", bitfield.INTEGER, 1), # bit 0
        ("mobilityKilled", bitfield.INTEGER, 1),  # bit 1
        ("unused1", bitfield.INTEGER, 1),  # bit 2
        ("damage", bitfield.INTEGER, 2),  # bits 3-4
        ("isSmokeEmanating", bitfield.INTEGER, 1),  # bit 5
        ("isEngineEmittingSmoke", bitfield.INTEGER, 1),  # bit 6
        ("unused2", bitfield.INTEGER, 2),  # bits 7-8
        ("hatchState", bitfield.INTEGER, 3),  # bits 9-11
        ("runningLightsOn", bitfield.INTEGER, 1),  # bit 12
        ("unused3", bitfield.INTEGER, 2),  # bits 13-14
        ("isFlaming", bitfield.INTEGER, 1),  # bit 15
        ("periscope", bitfield.INTEGER, 1),  # bit 16
        ("snorkel", bitfield.INTEGER, 1),  # bit 17
        ("radarMast", bitfield.INTEGER, 1),  # bit 18
        ("commsMast", bitfield.INTEGER, 1),  # bit 19
        ("esmMast", bitfield.INTEGER, 1),  # bit 20
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("powerPlantOn", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("unused4", bitfield.INTEGER, 1),  # bit 24
        ("torpedoTubesOpen", bitfield.INTEGER, 1),  # bit 25
        ("missileHatchesOpen", bitfield.INTEGER, 1),  # bit 26
        ("towedArraySonar", bitfield.INTEGER, 1),  # bit 27
        ("unused5", bitfield.INTEGER, 4),  # bits 28-31
    ])

    def __init__(self,
                 paintScheme: bool = False,
                 mobilityKilled: bool = False,
                 damage: bf_enum = 0,
                 isSmokeEmanating: bool = False,
                 isEngineEmittingSmoke: bool = False,
                 hatchState: bf_enum = 0,
                 runningLightsOn: bool = False,
                 isFlaming: bool = False,
                 periscope: bool = False,
                 snorkel: bool = False,
                 radarMast: bool = False,
                 commsMast: bool = False,
                 esmMast: bool = False,
                 isFrozen: bool = False,
                 powerPlantOn: bool = True,
                 state: bool = False,
                 torpedoTubesOpen: bool = False,
                 missileHatchesOpen: bool = False,
                 towedArraySonar: bool = False):
        self.paintScheme = paintScheme
        self.mobilityKilled = mobilityKilled
        self.unused1 = 0
        self.damage = damage
        self.isSmokeEmanating = isSmokeEmanating
        self.isEngineEmittingSmoke = isEngineEmittingSmoke
        self.unused2 = 0
        self.hatchState = hatchState
        self.runningLightsOn = runningLightsOn
        self.unused3 = 0
        self.isFlaming = isFlaming
        self.periscope = periscope
        self.snorkel = snorkel
        self.radarMast = radarMast
        self.commsMast = commsMast
        self.esmMast = esmMast
        self.isFrozen = isFrozen
        self.powerPlantOn = powerPlantOn
        self.state = state
        self.unused4 = 0
        self.torpedoTubesOpen = torpedoTubesOpen
        self.missileHatchesOpen = missileHatchesOpen
        self.towedArraySonar = towedArraySonar
        self.unused5 = 0

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.paintScheme,
            self.mobilityKilled,
            self.unused1,
            self.damage,
            self.isSmokeEmanating,
            self.isEngineEmittingSmoke,
            self.unused2,
            self.hatchState,
            self.runningLightsOn,
            self.unused3,
            self.isFlaming,
            self.periscope,
            self.snorkel,
            self.radarMast,
            self.commsMast,
            self.esmMast,
            self.isFrozen,
            self.powerPlantOn,
            self.state,
            self.unused4,
            self.torpedoTubesOpen,
            self.missileHatchesOpen,
            self.towedArraySonar,
            self.unused5,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.paintScheme = record_bitfield.paintScheme
        self.mobilityKilled = record_bitfield.mobilityKilled
        self.unused1 = record_bitfield.unused1
        self.damage = record_bitfield.damage
        self.isSmokeEmanating = record_bitfield.isSmokeEmanating
        self.isEngineEmittingSmoke = record_bitfield.isEngineEmittingSmoke
        self.unused2 = record_bitfield.unused2
        self.hatchState = record_bitfield.hatchState
        self.runningLightsOn = record_bitfield.runningLightsOn
        self.unused3 = record_bitfield.unused3
        self.isFlaming = record_bitfield.isFlaming
        self.periscope = record_bitfield.periscope
        self.snorkel = record_bitfield.snorkel
        self.radarMast = record_bitfield.radarMast
        self.commsMast = record_bitfield.commsMast
        self.esmMast = record_bitfield.esmMast
        self.isFrozen = record_bitfield.isFrozen
        self.powerPlantOn = record_bitfield.powerPlantOn
        self.state = record_bitfield.state
        self.unused4 = record_bitfield.unused4
        self.torpedoTubesOpen = record_bitfield.torpedoTubesOpen
        self.missileHatchesOpen = record_bitfield.missileHatchesOpen
        self.towedArraySonar = record_bitfield.towedArraySonar
        self.unused5 = record_bitfield.unused5


class SpacePlatformAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.1.5 Space Platform Appearance Record [UID 35]"""
    _struct = bitfield.bitfield(name="SpacePlatformAppearance", fields=[
        ("paintScheme", bitfield.INTEGER, 1), # bit 0
        ("mobilityKilled", bitfield.INTEGER, 1),  # bit 1
        ("unused1", bitfield.INTEGER, 1),  # bit 2
        ("damage", bitfield.INTEGER, 2),  # bits 3-4
        ("isSmokeEmanating", bitfield.INTEGER, 1),  # bit 5
        ("isEngineEmittingSmoke", bitfield.INTEGER, 1),  # bit 6
        ("unused2", bitfield.INTEGER, 8),  # bits 7-14
        ("isFlaming", bitfield.INTEGER, 1),  # bit 15
        ("unused3", bitfield.INTEGER, 5),  # bits 16-20
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("powerPlantOn", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("unused4", bitfield.INTEGER, 8),  # bits 24-31
    ])

    def __init__(self,
                 paintScheme: bool = False,
                 mobilityKilled: bool = False,
                 damage: bf_enum = 0,
                 isSmokeEmanating: bool = False,
                 isEngineEmittingSmoke: bool = False,
                 isFlaming: bool = False,
                 isFrozen: bool = False,
                 powerPlantOn: bool = True,
                 state: bool = False):
            self.paintScheme = paintScheme
            self.mobilityKilled = mobilityKilled
            self.unused1 = 0
            self.damage = damage
            self.isSmokeEmanating = isSmokeEmanating
            self.isEngineEmittingSmoke = isEngineEmittingSmoke
            self.unused2 = 0
            self.isFlaming = isFlaming
            self.unused3 = 0
            self.isFrozen = isFrozen
            self.powerPlantOn = powerPlantOn
            self.state = state
            self.unused4 = 0

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.paintScheme,
            self.mobilityKilled,
            self.unused1,
            self.damage,
            self.isSmokeEmanating,
            self.isEngineEmittingSmoke,
            self.unused2,
            self.isFlaming,
            self.unused3,
            self.isFrozen,
            self.powerPlantOn,
            self.state,
            self.unused4,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.paintScheme = record_bitfield.paintScheme
        self.mobilityKilled = record_bitfield.mobilityKilled
        self.unused1 = record_bitfield.unused1
        self.damage = record_bitfield.damage
        self.isSmokeEmanating = record_bitfield.isSmokeEmanating
        self.isEngineEmittingSmoke = record_bitfield.isEngineEmittingSmoke
        self.unused2 = record_bitfield.unused2
        self.isFlaming = record_bitfield.isFlaming
        self.unused3 = record_bitfield.unused3
        self.isFrozen = record_bitfield.isFrozen
        self.powerPlantOn = record_bitfield.powerPlantOn
        self.state = record_bitfield.state
        self.unused4 = record_bitfield.unused4


class MunitionAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.2 Munition Appearance Record [UID 36]"""
    _struct = bitfield.bitfield(name="MunitionAppearance", fields=[
        ("unused", bitfield.INTEGER, 3),  # bits 0-2
        ("damage", bitfield.INTEGER, 2),  # bits 3-4
        ("sSmokeEmanating", bitfield.INTEGER, 1),  # bit 5
        ("isEngineEmittingSmoke", bitfield.INTEGER, 1),  # bit 6
        ("vaporTrailSize", bitfield.INTEGER, 2),  # bits 7-8
        ("unused1", bitfield.INTEGER, 6),  # bits 9-14
        ("isFlaming", bitfield.INTEGER, 1),  # bit 15
        ("launchFlashPresent", bitfield.INTEGER, 1),  # bit 16
        ("unused2", bitfield.INTEGER, 4),  # bits 17-20
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("powerPlantOn", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("coverShroudStatus", bitfield.INTEGER, 2),  # bits 24-25
        ("unused3", bitfield.INTEGER, 6),  # bits 26-31
    ])

    def __init__(self,
                 damage: bf_enum = 0,
                 isSmokeEmanating: bool = False,
                 isEngineEmittingSmoke: bool = False,
                 vaporTrailSize: bf_enum = 0,
                 isFlaming: bool = False,
                 launchFlashPresent: bool = False,
                 isFrozen: bool = False,
                 powerPlantOn: bool = True,
                 state: bool = False,
                 coverShroudStatus: bf_enum = 0):
        self.damage = damage
        self.isSmokeEmanating = isSmokeEmanating
        self.isEngineEmittingSmoke = isEngineEmittingSmoke
        self.vaporTrailSize = vaporTrailSize
        self.unused1 = 0
        self.isFlaming = isFlaming
        self.launchFlashPresent = launchFlashPresent
        self.unused2 = 0
        self.isFrozen = isFrozen
        self.powerPlantOn = powerPlantOn
        self.state = state
        self.coverShroudStatus = coverShroudStatus
        self.unused3 = 0

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.unused,
            self.damage,
            self.isSmokeEmanating,
            self.isEngineEmittingSmoke,
            self.vaporTrailSize,
            self.unused1,
            self.isFlaming,
            self.launchFlashPresent,
            self.unused2,
            self.isFrozen,
            self.powerPlantOn,
            self.state,
            self.coverShroudStatus,
            self.unused3,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.unused = record_bitfield.unused
        self.damage = record_bitfield.damage
        self.isSmokeEmanating = record_bitfield.isSmokeEmanating
        self.isEngineEmittingSmoke = record_bitfield.isEngineEmittingSmoke
        self.vaporTrailSize = record_bitfield.vaporTrailSize
        self.unused1 = record_bitfield.unused1
        self.isFlaming = record_bitfield.isFlaming
        self.launchFlashPresent = record_bitfield.launchFlashPresent
        self.unused2 = record_bitfield.unused2
        self.isFrozen = record_bitfield.isFrozen
        self.powerPlantOn = record_bitfield.powerPlantOn
        self.state = record_bitfield.state
        self.coverShroudStatus = record_bitfield.coverShroudStatus
        self.unused3 = record_bitfield.unused3


class HumanLifeFormAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.3.1 Human Life Form Appearance Record [UID 37]"""
    _struct = bitfield.bitfield(name="LifeFormAppearance", fields=[
        ("paintScheme", bitfield.INTEGER, 1),  # bit 0
        ("unused1", bitfield.INTEGER, 2),  # bits 1-2
        ("health", bitfield.INTEGER, 2),  # bits 3-4
        ("complianceStatus", bitfield.INTEGER, 4),  # bits 5-8
        ("clothingIRSignature", bitfield.INTEGER, 2),  # bits 9-10
        ("signalSmokeInUse", bitfield.INTEGER, 1),  # bit 11
        ("flashLightsOn", bitfield.INTEGER, 1),  # bit 12
        ("signalMirrorInUse", bitfield.INTEGER, 1),  # bit 13
        ("irStrobeOn", bitfield.INTEGER, 1),  # bit 14
        ("irIlluminatorOn", bitfield.INTEGER, 1),  # bit 15
        ("ifeFormPosture", bitfield.INTEGER, 4),  # bits 16-19
        ("isSmokingCigarette", bitfield.INTEGER, 1),  # bit 20
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("mountedStatus", bitfield.INTEGER, 2),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("primaryWeaponPosition", bitfield.INTEGER, 2),  # bits 24-25
        ("secondaryWeaponPosition", bitfield.INTEGER, 2),  # bits 26-
        ("camouflageType", bitfield.INTEGER, 2),  # bits 28-29
        ("concealedStationary", bitfield.INTEGER, 1),  # bit 30
        ("concealedMoving", bitfield.INTEGER, 1),  # bit 31
    ])


    def __init__(self,
                 paintScheme: bool = False,
                 health: bf_enum = 0,
                 complianceStatus: bf_enum = 0,
                 clothingIRSignature: bf_enum = 0,
                 signalSmokeInUse: bool = False,
                 flashLightsOn: bool = False,
                 signalMirrorInUse: bool = False,
                 irStrobeOn: bool = False,
                 irIlluminatorOn: bool = False,
                 lifeFormPosture: bf_enum = 0,
                 isSmokingCigarette: bool = False,
                 isFrozen: bool = False,
                 mountedStatus: bf_enum = 0,
                 state: bool = False,
                 primaryWeaponPosition: bf_enum = 0,
                 secondaryWeaponPosition: bf_enum = 0,
                 camouflageType: bf_enum = 0,
                 concealedStationary: bool = False,
                 concealedMoving: bool = False):
        self.paintScheme = paintScheme
        self.unused1 = 0
        self.health = health
        self.complianceStatus = complianceStatus
        self.clothingIRSignature = clothingIRSignature
        self.signalSmokeInUse = signalSmokeInUse
        self.flashLightsOn = flashLightsOn
        self.signalMirrorInUse = signalMirrorInUse
        self.irStrobeOn = irStrobeOn
        self.irIlluminatorOn = irIlluminatorOn
        self.lifeFormPosture = lifeFormPosture
        self.isSmokingCigarette = isSmokingCigarette
        self.isFrozen = isFrozen
        self.mountedStatus = mountedStatus
        self.state = state
        self.primaryWeaponPosition = primaryWeaponPosition
        self.secondaryWeaponPosition = secondaryWeaponPosition
        self.camouflageType = camouflageType
        self.concealedStationary = concealedStationary
        self.concealedMoving = concealedMoving

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.paintScheme,
            self.unused1,
            self.health,
            self.complianceStatus,
            self.clothingIRSignature,
            self.signalSmokeInUse,
            self.flashLightsOn,
            self.signalMirrorInUse,
            self.irStrobeOn,
            self.irIlluminatorOn,
            self.lifeFormPosture,
            self.isSmokingCigarette,
            self.isFrozen,
            self.mountedStatus,
            self.state,
            self.primaryWeaponPosition,
            self.secondaryWeaponPosition,
            self.camouflageType,
            self.concealedStationary,
            self.concealedMoving,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.paintScheme = record_bitfield.paintScheme
        self.unused1 = record_bitfield.unused1
        self.health = record_bitfield.health
        self.complianceStatus = record_bitfield.complianceStatus
        self.clothingIRSignature = record_bitfield.clothingIRSignature
        self.signalSmokeInUse = record_bitfield.signalSmokeInUse
        self.flashLightsOn = record_bitfield.flashLightsOn
        self.signalMirrorInUse = record_bitfield.signalMirrorInUse
        self.irStrobeOn = record_bitfield.irStrobeOn
        self.irIlluminatorOn = record_bitfield.irIlluminatorOn
        self.lifeFormPosture = record_bitfield.lifeFormPosture
        self.isSmokingCigarette = record_bitfield.isSmokingCigarette
        self.isFrozen = record_bitfield.isFrozen
        self.mountedStatus = record_bitfield.mountedStatus
        self.state = record_bitfield.state
        self.primaryWeaponPosition = record_bitfield.primaryWeaponPosition
        self.secondaryWeaponPosition = record_bitfield.secondaryWeaponPosition
        self.camouflageType = record_bitfield.camouflageType
        self.concealedStationary = record_bitfield.concealedStationary
        self.concealedMoving = record_bitfield.concealedMoving


class EnvironmentalAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.4 Environmental Appearance Record [UID 38]"""
    _struct = bitfield.bitfield(name="EnvironmentalAppearance", fields=[
        ("unused1", bitfield.INTEGER, 16),  # bits 0-15
        ("density", bitfield.INTEGER, 4),  # bits 16-19
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("unused2", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("unused3", bitfield.INTEGER, 7),  # bits 24-30
        ("masked", bitfield.INTEGER, 1),  # bit 31
    ])

    def __init__(self,
                 density: bf_enum = 0,
                 isFrozen: bool = False,
                 state: bool = False,
                 masked: bool = False):
        self.unused1 = 0
        self.density = density
        self.isFrozen = isFrozen
        self.unused2 = 0
        self.state = state
        self.unused3 = 0
        self.masked = masked

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.unused1,
            self.density,
            self.isFrozen,
            self.unused2,
            self.state,
            self.unused3,
            self.masked,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.unused1 = record_bitfield.unused1
        self.density = record_bitfield.density
        self.isFrozen = record_bitfield.isFrozen
        self.unused2 = record_bitfield.unused2
        self.state = record_bitfield.state
        self.unused3 = record_bitfield.unused3
        self.masked = record_bitfield.masked


class CulturalFeatureAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.5 Cultural Feature Appearance Record [UID 39]"""
    _struct = bitfield.bitfield(name="CulturalFeatureAppearance", fields=[
        ("damageArea", bitfield.INTEGER, 3),  # bits 0-2
        ("damage", bitfield.INTEGER, 2),  # bits 3-4
        ("isSmokeEmanating", bitfield.INTEGER, 1),  # bit 5
        ("unused1", bitfield.INTEGER, 9),  # bits 6-14
        ("isFlaming", bitfield.INTEGER, 1),  # bit 15
        ("unused2", bitfield.INTEGER, 5),  # bits 16-20
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("internalHeatOn", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("unused3", bitfield.INTEGER, 4),  # bits 24-27
        ("exteriorLightsOn", bitfield.INTEGER, 1),  # bit 28
        ("interiorLightsOn", bitfield.INTEGER, 1),  # bit 29
        ("unused4", bitfield.INTEGER, 1),  # bit 30
        ("masked", bitfield.INTEGER, 1),  # bit 31
    ])

    def __init__(self,
                 damageArea: bf_enum = 0,
                 damage: bf_enum = 0,
                 isSmokeEmanating: bool = False,
                 isFlaming: bool = False,
                 isFrozen: bool = False,
                 internalHeatOn: bool = False,
                 state: bool = False,
                 exteriorLightsOn: bool = False,
                 interiorLightsOn: bool = False,
                 masked: bool = False):
            self.damageArea = damageArea
            self.damage = damage
            self.isSmokeEmanating = isSmokeEmanating
            self.unused1 = 0
            self.isFlaming = isFlaming
            self.unused2 = 0
            self.isFrozen = isFrozen
            self.internalHeatOn = internalHeatOn
            self.state = state
            self.unused3 = 0
            self.exteriorLightsOn = exteriorLightsOn
            self.interiorLightsOn = interiorLightsOn
            self.unused4 = 0
            self.masked = masked

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.damageArea,
            self.damage,
            self.isSmokeEmanating,
            self.unused1,
            self.isFlaming,
            self.unused2,
            self.isFrozen,
            self.internalHeatOn,
            self.state,
            self.unused3,
            self.exteriorLightsOn,
            self.interiorLightsOn,
            self.unused4,
            self.masked,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.damageArea = record_bitfield.damageArea
        self.damage = record_bitfield.damage
        self.isSmokeEmanating = record_bitfield.isSmokeEmanating
        self.unused1 = record_bitfield.unused1
        self.isFlaming = record_bitfield.isFlaming
        self.unused2 = record_bitfield.unused2
        self.isFrozen = record_bitfield.isFrozen
        self.internalHeatOn = record_bitfield.internalHeatOn
        self.state = record_bitfield.state
        self.unused3 = record_bitfield.unused3
        self.exteriorLightsOn = record_bitfield.exteriorLightsOn
        self.interiorLightsOn = record_bitfield.interiorLightsOn
        self.unused4 = record_bitfield.unused4
        self.masked = record_bitfield.masked


class SupplyAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.6 Supply Appearance Record [UID 40]"""
    _struct = bitfield.bitfield(name="SupplyAppearance", fields=[
        ("paintScheme", bitfield.INTEGER, 1),  # bit 0
        ("unused1", bitfield.INTEGER, 2),  # bits 1-2
        ("damage", bitfield.INTEGER, 2),  # bits 3-4
        ("unused2", bitfield.INTEGER, 2),  # bits 5-6
        ("parachuteStatus", bitfield.INTEGER, 2),  # bits 7-8
        ("unused3", bitfield.INTEGER, 6),  # bits 9-14
        ("isFlaming", bitfield.INTEGER, 1),  # bit 15
        ("unused4", bitfield.INTEGER, 5),  # bits 16-20
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("unused5", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("deployedStatus", bitfield.INTEGER, 2),  # bits 24-25
        ("unused6", bitfield.INTEGER, 5),  # bits 26-30
        ("masked", bitfield.INTEGER, 1),  # bit 31
    ])

    def __init__(self,
                 paintScheme: bool = False,
                 damage: bf_enum = 0,
                 parachuteStatus: bf_enum = 0,
                 isFlaming: bool = False,
                 isFrozen: bool = False,
                 state: bool = False,
                 deployedStatus: bf_enum = 0,
                 masked: bool = False):
            self.paintScheme = paintScheme
            self.unused1 = 0
            self.damage = damage
            self.unused2 = 0
            self.parachuteStatus = parachuteStatus
            self.unused3 = 0
            self.isFlaming = isFlaming
            self.unused4 = 0
            self.isFrozen = isFrozen
            self.unused5 = 0
            self.state = state
            self.deployedStatus = deployedStatus
            self.unused6 = 0
            self.masked = masked

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.paintScheme,
            self.unused1,
            self.damage,
            self.unused2,
            self.parachuteStatus,
            self.unused3,
            self.isFlaming,
            self.unused4,
            self.isFrozen,
            self.unused5,
            self.state,
            self.deployedStatus,
            self.unused6,
            self.masked,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.paintScheme = record_bitfield.paintScheme
        self.unused1 = record_bitfield.unused1
        self.damage = record_bitfield.damage
        self.unused2 = record_bitfield.unused2
        self.parachuteStatus = record_bitfield.parachuteStatus
        self.unused3 = record_bitfield.unused3
        self.isFlaming = record_bitfield.isFlaming
        self.unused4 = record_bitfield.unused4
        self.isFrozen = record_bitfield.isFrozen
        self.unused5 = record_bitfield.unused5
        self.state = record_bitfield.state
        self.deployedStatus = record_bitfield.deployedStatus
        self.unused6 = record_bitfield.unused6
        self.masked = record_bitfield.masked


class RadioAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.7 Radio Appearance Record [UID 41]"""
    _struct = bitfield.bitfield(name="RadioAppearance", fields=[
        ("unused1", bitfield.INTEGER, 21),  # bits 0-20
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("unused2", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("unused3", bitfield.INTEGER, 8),  # bits 24-31
    ])

    def __init__(self,
                 isFrozen: bool = False,
                 state: bool = False):
            self.unused1 = 0
            self.isFrozen = isFrozen
            self.unused2 = 0
            self.state = state
            self.unused3 = 0

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.unused1,
            self.isFrozen,
            self.unused2,
            self.state,
            self.unused3,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.unused1 = record_bitfield.unused1
        self.isFrozen = record_bitfield.isFrozen
        self.unused2 = record_bitfield.unused2
        self.state = record_bitfield.state
        self.unused3 = record_bitfield.unused3


class ExpendableAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.8 Expendable Appearance Record [UID 42]"""
    _struct = bitfield.bitfield(name="ExpendableAppearance", fields=[
        ("unused1", bitfield.INTEGER, 3),  # bits 0-2
        ("damage", bitfield.INTEGER, 2),  # bits 3-4
        ("isSmokeEmanating", bitfield.INTEGER, 1),  # bit 5
        ("parachuteStatus", bitfield.INTEGER, 2),  # bits 7-8
        ("flareOrSmokeColor", bitfield.INTEGER, 3),  # bits 9-11
        ("isFlaming", bitfield.INTEGER, 1),  # bit 15
        ("launchFlashPresent", bitfield.INTEGER, 1),  # bit 16
        ("flareOrSmokeStatus", bitfield.INTEGER, 2),  # bits 17-18
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("powerPlantOn", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("spotChaffStatus", bitfield.INTEGER, 2),  # bits 24-25
        ("unused2", bitfield.INTEGER, 6),  # bits 26-30
        ("masked", bitfield.INTEGER, 1),  # bit 31
    ])

    def __init__(self,
                 damage: bf_enum = 0,
                 isSmokeEmanating: bool = False,
                 parachuteStatus: bf_enum = 0,
                 flareOrSmokeColor: bf_enum = 0,
                 isFlaming: bool = False,
                 launchFlashPresent: bool = False,
                 flareOrSmokeStatus: bf_enum = 0,
                 isFrozen: bool = False,
                 powerPlantOn: bool = True,
                 state: bool = False,
                 spotChaffStatus: bf_enum = 0,
                 masked: bool = False):
            self.unused1 = 0
            self.damage = damage
            self.isSmokeEmanating = isSmokeEmanating
            self.parachuteStatus = parachuteStatus
            self.flareOrSmokeColor = flareOrSmokeColor
            self.isFlaming = isFlaming
            self.launchFlashPresent = launchFlashPresent
            self.flareOrSmokeStatus = flareOrSmokeStatus
            self.isFrozen = isFrozen
            self.powerPlantOn = powerPlantOn
            self.state = state
            self.spotChaffStatus = spotChaffStatus
            self.unused2 = 0
            self.masked = masked

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.unused1,
            self.damage,
            self.isSmokeEmanating,
            self.parachuteStatus,
            self.flareOrSmokeColor,
            self.isFlaming,
            self.launchFlashPresent,
            self.flareOrSmokeStatus,
            self.isFrozen,
            self.powerPlantOn,
            self.state,
            self.spotChaffStatus,
            self.unused2,
            self.masked,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.unused1 = record_bitfield.unused1
        self.damage = record_bitfield.damage
        self.isSmokeEmanating = record_bitfield.isSmokeEmanating
        self.parachuteStatus = record_bitfield.parachuteStatus
        self.flareOrSmokeColor = record_bitfield.flareOrSmokeColor
        self.isFlaming = record_bitfield.isFlaming
        self.launchFlashPresent = record_bitfield.launchFlashPresent
        self.flareOrSmokeStatus = record_bitfield.flareOrSmokeStatus
        self.isFrozen = record_bitfield.isFrozen
        self.powerPlantOn = record_bitfield.powerPlantOn
        self.state = record_bitfield.state
        self.spotChaffStatus = record_bitfield.spotChaffStatus
        self.unused2 = record_bitfield.unused2
        self.masked = record_bitfield.masked


class SensorEmitterAppearance(AppearanceRecord):
    """SISO-REF-010 17.11.1.9 Sensor Emitter Appearance Record [UID 43]"""
    _struct = bitfield.bitfield(name="SensorEmitterAppearance", fields=[
        ("paintScheme", bitfield.INTEGER, 1),  # bit 0
        ("mobilityKilled", bitfield.INTEGER, 1),  # bit 1
        ("missionKilled", bitfield.INTEGER, 1),  # bit 2
        ("damage", bitfield.INTEGER, 2),  # bits 3-4
        ("isSmokeEmanating", bitfield.INTEGER, 1),  # bit 5
        ("isEngineEmittingSmoke", bitfield.INTEGER, 1),  # bit 6
        ("trailingEffects", bitfield.INTEGER, 2),  # bits 7-8
        ("unused1", bitfield.INTEGER, 3),  # bits 9-11
        ("lightsOn", bitfield.INTEGER, 1),  # bit 12
        ("unused2", bitfield.INTEGER, 2),  # bits 13-14
        ("isFlaming", bitfield.INTEGER, 1),  # bit 15
        ("antennaRaised", bitfield.INTEGER, 1),  # bit 16
        ("camouflageType", bitfield.INTEGER, 2),  # bits 17-18
        ("concealedPosition", bitfield.INTEGER, 1),  # bit 19
        ("unused3", bitfield.INTEGER, 1),  # bit 20
        ("isFrozen", bitfield.INTEGER, 1),  # bit 21
        ("powerPlantOn", bitfield.INTEGER, 1),  # bit 22
        ("state", bitfield.INTEGER, 1),  # bit 23
        ("tentExtended", bitfield.INTEGER, 1),  # bit 24
        ("unused4", bitfield.INTEGER, 1),  # bit 25
        ("blackoutLightsOn", bitfield.INTEGER, 1),  # bit 26
        ("unused5", bitfield.INTEGER, 2),  # bits 27-28
        ("interiorLightsOn", bitfield.INTEGER, 1),  # bit 29
        ("unused6", bitfield.INTEGER, 2),  # bits 30-31
    ])

    def __init__(self,
                 paintScheme: bool = False,
                 mobilityKilled: bool = False,
                 missionKilled: bool = False,
                 damage: bf_enum = 0,
                 isSmokeEmanating: bool = False,
                 isEngineEmittingSmoke: bool = False,
                 trailingEffects: bf_enum = 0,
                 lightsOn: bool = False,
                 isFlaming: bool = False,
                 antennaRaised: bool = False,
                 camouflageType: bf_enum = 0,
                 concealedPosition: bool = False,
                 isFrozen: bool = False,
                 powerPlantOn: bool = True,
                 state: bool = False,
                 tentExtended: bool = False,
                 blackoutLightsOn: bool = False,
                 interiorLightsOn: bool = False):
            self.paintScheme = paintScheme
            self.mobilityKilled = mobilityKilled
            self.missionKilled = missionKilled
            self.damage = damage
            self.isSmokeEmanating = isSmokeEmanating
            self.isEngineEmittingSmoke = isEngineEmittingSmoke
            self.trailingEffects = trailingEffects
            self.unused1 = 0
            self.lightsOn = lightsOn
            self.unused2 = 0
            self.isFlaming = isFlaming
            self.antennaRaised = antennaRaised
            self.camouflageType = camouflageType
            self.concealedPosition = concealedPosition
            self.unused3 = 0
            self.isFrozen = isFrozen
            self.powerPlantOn = powerPlantOn
            self.state = state
            self.tentExtended = tentExtended
            self.unused4 = 0
            self.blackoutLightsOn = blackoutLightsOn
            self.unused5 = 0
            self.interiorLightsOn = interiorLightsOn
            self.unused6 = 0

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.paintScheme,
            self.mobilityKilled,
            self.missionKilled,
            self.damage,
            self.isSmokeEmanating,
            self.isEngineEmittingSmoke,
            self.trailingEffects,
            self.unused1,
            self.lightsOn,
            self.unused2,
            self.isFlaming,
            self.antennaRaised,
            self.camouflageType,
            self.concealedPosition,
            self.unused3,
            self.isFrozen,
            self.powerPlantOn,
            self.state,
            self.tentExtended,
            self.unused4,
            self.blackoutLightsOn,
            self.unused5,
            self.interiorLightsOn,
            self.unused6,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.paintScheme = record_bitfield.paintScheme
        self.mobilityKilled = record_bitfield.mobilityKilled
        self.missionKilled = record_bitfield.missionKilled
        self.damage = record_bitfield.damage
        self.isSmokeEmanating = record_bitfield.isSmokeEmanating
        self.isEngineEmittingSmoke = record_bitfield.isEngineEmittingSmoke
        self.trailingEffects = record_bitfield.trailingEffects
        self.unused1 = record_bitfield.unused1
        self.lightsOn = record_bitfield.lightsOn
        self.unused2 = record_bitfield.unused2
        self.isFlaming = record_bitfield.isFlaming
        self.antennaRaised = record_bitfield.antennaRaised
        self.camouflageType = record_bitfield.camouflageType
        self.concealedPosition = record_bitfield.concealedPosition
        self.unused3 = record_bitfield.unused3
        self.isFrozen = record_bitfield.isFrozen
        self.powerPlantOn = record_bitfield.powerPlantOn
        self.state = record_bitfield.state
        self.tentExtended = record_bitfield.tentExtended
        self.unused4 = record_bitfield.unused4
        self.blackoutLightsOn = record_bitfield.blackoutLightsOn
        self.unused5 = record_bitfield.unused5
        self.interiorLightsOn = record_bitfield.interiorLightsOn
        self.unused6 = record_bitfield.unused6
