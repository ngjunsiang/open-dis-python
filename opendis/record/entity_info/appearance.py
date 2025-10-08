"""Classes for 6.2.26 Entity Appearance record

This record shall be defined as a 32-bit record (see [UID 31-43]).
"""

from opendis.record import base, bitfield
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import bf_enum

class LandPlatformAppearance(base.Record):
    """SISO-REF-010 17.11.1.1.1 Land Platform Appearance Record [UID 31]"""
    _struct = bitfield.bitfield(name="LandPlatformAppearance", fields=[
        ("paintScheme", bitfield.INTEGER, 1),
        ("mobilityKilled", bitfield.INTEGER, 1),
        ("firepowerKilled", bitfield.INTEGER, 1),
        ("damage", bitfield.INTEGER, 2),
        ("isSmokeEmanating", bitfield.INTEGER, 1),
        ("isEngineEmittingSmoke", bitfield.INTEGER, 1),
        ("trailingDustCloud", bitfield.INTEGER, 2),
        ("primaryHatch", bitfield.INTEGER, 3),
        ("headLightsOn", bitfield.INTEGER, 1),
        ("tailLightsOn", bitfield.INTEGER, 1),
        ("brakeLightsOn", bitfield.INTEGER, 1),
        ("isFlaming", bitfield.INTEGER, 1),
        ("operational", bitfield.INTEGER, 1),
        ("camouflageType", bitfield.INTEGER, 2),
        ("concealedPosition", bitfield.INTEGER, 1),
        ("isFrozen", bitfield.INTEGER, 1),
        ("powerPlantOn", bitfield.INTEGER, 1),
        ("state", bitfield.INTEGER, 1),
        ("tentExtended", bitfield.INTEGER, 1),
        ("rampExtended", bitfield.INTEGER, 1),
        ("blackoutLightsOn", bitfield.INTEGER, 1),
        ("blackoutBrakeLightsOn", bitfield.INTEGER, 1),
        ("spotLightOn", bitfield.INTEGER, 1),
        ("interiorLightsOn", bitfield.INTEGER, 1),
        ("occupantsSurrendered", bitfield.INTEGER, 1),
        ("cloaked", bitfield.INTEGER, 1),
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
    
    def marshalledSize(self) -> int:
          return 4
    
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
