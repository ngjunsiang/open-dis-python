"""Distributed Emissions Regeneration family (IEEE 1278.1-2012 §7.6)
— target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/DistributedEmissionsFamilyPdus.xml.
Electromagnetic Emission, Designator, Underwater Acoustic, IFF, and SEES
PDUs with their emitter-system / beam record trees. The beam and system
"data length" fields count 32-bit words (§7.6.2) and are always derived
(``marshalledSize() // 4``; zero means the section is "large").

The IFF PDU (type 28) implements the §7.6.5 layer mechanism: Layer 1 is
always present; layers 2-5 are length-driven optionals dispatched by
Layer Header layer number (Table 165), with the Layer 3/4 format picked
by the Layer 1 System Type field. The layer lists hold flat §6.2.43 IFF
Data records (the XML's IFFDataSpecification wrapper adds a count the
layer already carries). SystemIdentifier's Change/Options is 8 bits
(Table B.5, Table 118 total 48 bits — the XML's 16-bit binding made
every IFF PDU one byte long; upstream candidate).
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.record.common import (
    EntityIdentifier,
    EventIdentifier,
    Vector3Double,
    Vector3Float,
)
from opendis.record.pdu import Pdu
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import (
    enum8,
    enum16,
    enum32,
    float32,
    uint8,
    uint16,
    uint32,
    uint64,
    int32,
)

__all__ = [
    "APA",
    "AcousticEmitter",
    "BeamData",
    "BeamStatus",
    "DesignatorPdu",
    "DistributedEmissionsRegenerationFamilyPdu",
    "EEFundamentalParameterData",
    "ElectromagneticEmissionPdu",
    "ElectronicEmitter",
    "EmitterBeam",
    "EmitterSystem",
    "FundamentalOperationalData",
    "IFFData",
    "IFFFundamentalParameterData",
    "IFFPdu",
    "IFFPduLayer2Data",
    "IFFPduLayer3InterrogatorFormatData",
    "IFFPduLayer3TransponderFormatData",
    "IFFPduLayer4InterrogatorFormatData",
    "IFFPduLayer4TransponderFormatData",
    "IFFPduLayer5Data",
    "IdentificationFriendOrFoePdu",
    "JammingTechnique",
    "LayerHeader",
    "Mode5InterrogatorBasicData",
    "Mode5TransponderBasicData",
    "ModeSInterrogatorBasicData",
    "ModeSTransponderBasicData",
    "PropulsionSystemData",
    "SEESPdu",
    "ShaftRPM",
    "SupplementalEmissionEntityStatePdu",
    "SystemIdentifier",
    "TrackJamData",
    "UABeam",
    "UAEmitter",
    "UAFundamentalParameter",
    "UnderwaterAcousticPdu",
    "VectoringNozzleSystem",
]


@dataclass(slots=True)
class EEFundamentalParameterData:
    """§6.2.22 EE Fundamental Parameter Data record

    Contains electromagnetic emission regeneration parameters that are
    variable throught a scenario.

    Continuous wave emissions are represented by 0.0 in both pulse
    repetition frequency and pulse width.
    """

    frequency: float32 = 0.0  # Hz
    frequencyRange: float32 = 0.0  # Hz
    effectiveRadiatedPower: float32 = 0.0  # dBm
    pulseRepetitionFrequency: float32 = 0.0  # Hz
    pulseWidth: float32 = 0.0  # seconds

    def marshalledSize(self) -> int:
        return 20

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_float32(self.frequency)
        outputStream.write_float32(self.frequencyRange)
        outputStream.write_float32(self.effectiveRadiatedPower)
        outputStream.write_float32(self.pulseRepetitionFrequency)
        outputStream.write_float32(self.pulseWidth)

    def parse(self, inputStream: DataInputStream) -> None:
        self.frequency = inputStream.read_float32()
        self.frequencyRange = inputStream.read_float32()
        self.effectiveRadiatedPower = inputStream.read_float32()
        self.pulseRepetitionFrequency = inputStream.read_float32()
        self.pulseWidth = inputStream.read_float32()


@dataclass(slots=True)
class BeamData:
    """§6.2.11 Beam Data record

    Describes the scan volue of an emitter beam.
    """

    beamAzimuthCenter: float32 = 0.0
    beamAzimuthSweep: float32 = 0.0
    beamElevationCenter: float32 = 0.0
    beamElevationSweep: float32 = 0.0
    beamSweepSync: float32 = 0.0

    def marshalledSize(self) -> int:
        return 20

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_float32(self.beamAzimuthCenter)
        outputStream.write_float32(self.beamAzimuthSweep)
        outputStream.write_float32(self.beamElevationCenter)
        outputStream.write_float32(self.beamElevationSweep)
        outputStream.write_float32(self.beamSweepSync)

    def parse(self, inputStream: DataInputStream) -> None:
        self.beamAzimuthCenter = inputStream.read_float32()
        self.beamAzimuthSweep = inputStream.read_float32()
        self.beamElevationCenter = inputStream.read_float32()
        self.beamElevationSweep = inputStream.read_float32()
        self.beamSweepSync = inputStream.read_float32()


@dataclass(slots=True)
class BeamStatus:
    """§6.2.12 Beam Status record

    Information related to the status of a beam. This is contained in the
    beam status field of the electromagnitec emission PDU. The first bit
    determines whether the beam is active (0) or deactivated (1).

    One byte: the [UID 318] beam state in bit 0, seven reserved bits (kept
    so odd wire bytes round-trip byte-exact).
    """

    beamState: uint8 = 0  # [UID 318]

    def marshalledSize(self) -> int:
        return 1

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(int(self.beamState))

    def parse(self, inputStream: DataInputStream) -> None:
        self.beamState = inputStream.read_uint8()


@dataclass(slots=True)
class JammingTechnique:
    """Jamming technique. §6.2.49, uid 284."""

    kind: uint8 = 0
    category: uint8 = 0
    subCategory: uint8 = 0
    specific: uint8 = 0

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.kind)
        outputStream.write_uint8(self.category)
        outputStream.write_uint8(self.subCategory)
        outputStream.write_uint8(self.specific)

    def parse(self, inputStream: DataInputStream) -> None:
        self.kind = inputStream.read_uint8()
        self.category = inputStream.read_uint8()
        self.subCategory = inputStream.read_uint8()
        self.specific = inputStream.read_uint8()


@dataclass(frozen=True, slots=True)
class TrackJamData:
    """§6.2.90 Track/Jam Data record

    Track-Jam data.
    """

    entityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    emitterNumber: uint8 = 0
    beamNumber: uint8 = 0

    def marshalledSize(self) -> int:
        return self.entityID.marshalledSize() + 1 + 1

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.entityID.serialize(outputStream)
        outputStream.write_uint8(self.emitterNumber)
        outputStream.write_uint8(self.beamNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "TrackJamData":
        entityID = EntityIdentifier.parse(inputStream)
        emitterNumber = inputStream.read_uint8()
        beamNumber = inputStream.read_uint8()
        return cls(entityID, emitterNumber, beamNumber)


@dataclass(slots=True)
class EmitterSystem:
    """§6.2.23 Emitter System record

    This field shall specify information about a particular emitter system.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "emitterName": 75,
        "emitterFunction": 76,
    }

    emitterName: enum16 = 0  # [UID 75]
    emitterFunction: enum8 = 0  # [UID 76]
    emitterIDNumber: uint8 = 0

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.emitterName)
        outputStream.write_uint8(self.emitterFunction)
        outputStream.write_uint8(self.emitterIDNumber)

    def parse(self, inputStream: DataInputStream) -> None:
        self.emitterName = rich_or_int(75, inputStream.read_uint16())
        self.emitterFunction = rich_or_int(76, inputStream.read_uint8())
        self.emitterIDNumber = inputStream.read_uint8()


@dataclass(slots=True)
class EmitterBeam:
    """Emitter beams focused emissions from an electromagnetic or active
    acoustic transmitter. The beam is defined by the main lobe of the
    antenna pattern.

    Emitter beam data section of the EE PDU (§7.6.2). ``beamDataLength``
    counts 32-bit words of the whole beam record (including the length
    field) and is derived; zero means the beam is "large" (§7.6.2).
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "beamFunction": 78,
        "highDensityTrackJam": 79,
    }

    beamNumber: uint8 = 0
    beamParameterIndex: uint16 = 0
    fundamentalParameterData: EEFundamentalParameterData = field(
        default_factory=EEFundamentalParameterData
    )
    beamData: BeamData = field(default_factory=BeamData)
    beamFunction: enum8 = 0  # [UID 78]
    highDensityTrackJam: enum8 = 0  # [UID 79]
    beamStatus: BeamStatus = field(default_factory=BeamStatus)
    jammingTechnique: JammingTechnique = field(default_factory=JammingTechnique)
    trackJamData: list[TrackJamData] = field(default_factory=list)

    @property
    def numberOfTargets(self) -> uint8:
        """numberOfTargets"""
        return len(self.trackJamData)

    def marshalledSize(self):
        return (
            1
            + 1
            + 2  # beamDataLength + beamNumber + parameter index
            + self.fundamentalParameterData.marshalledSize()
            + self.beamData.marshalledSize()
            + 1
            + 1
            + 1
            + self.beamStatus.marshalledSize()
            + self.jammingTechnique.marshalledSize()
            + sum(tj.marshalledSize() for tj in self.trackJamData)
        )

    def serialize(self, outputStream: DataOutputStream):
        outputStream.write_uint8(self.beamDataLength)
        outputStream.write_uint8(self.beamNumber)
        outputStream.write_uint16(self.beamParameterIndex)
        self.fundamentalParameterData.serialize(outputStream)
        self.beamData.serialize(outputStream)
        outputStream.write_uint8(self.beamFunction)
        outputStream.write_uint8(self.numberOfTargets)
        outputStream.write_uint8(self.highDensityTrackJam)
        self.beamStatus.serialize(outputStream)
        self.jammingTechnique.serialize(outputStream)
        for trackJam in self.trackJamData:
            trackJam.serialize(outputStream)

    def parse(self, inputStream: DataInputStream):
        inputStream.read_uint8()  # beamDataLength (derived on re-serialize)
        self.beamNumber = inputStream.read_uint8()
        self.beamParameterIndex = inputStream.read_uint16()
        self.fundamentalParameterData.parse(inputStream)
        self.beamData.parse(inputStream)
        self.beamFunction = rich_or_int(78, inputStream.read_uint8())
        numberOfTargets = inputStream.read_uint8()
        self.highDensityTrackJam = rich_or_int(79, inputStream.read_uint8())
        self.beamStatus = BeamStatus()
        self.beamStatus.parse(inputStream)
        self.jammingTechnique = JammingTechnique()
        self.jammingTechnique.parse(inputStream)
        self.trackJamData = [
            TrackJamData.parse(inputStream) for _ in range(numberOfTargets)
        ]

    @property
    def beamDataLength(self) -> uint8:
        """Beam data length in 32-bit words — derived."""
        return self.marshalledSize() // 4

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "EmitterBeam":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class ElectronicEmitter:
    """A device that is able to discharge detectable electromagnetic energy.
    Per-system data of the EE PDU (7.6.2).

    Per-emitter-system data section of the EE PDU (§7.6.2).
    ``systemDataLength`` counts 32-bit words and is derived.
    """

    emitterSystem: EmitterSystem = field(default_factory=EmitterSystem)
    location: Vector3Float = field(default_factory=Vector3Float)
    beams: list[EmitterBeam] = field(default_factory=list)
    # Padding ruling: explicit attribute, out of __init__ (zero by default,
    # holds the wire value after parse so odd pads round-trip byte-exact).
    padding: uint16 = field(init=False, default=0)

    @property
    def numberOfBeams(self) -> uint8:
        """the number of beams being described in the current PDU for the emitter
        system being described.
        """
        return len(self.beams)

    def marshalledSize(self):
        return (
            1
            + 1
            + 2
            + self.emitterSystem.marshalledSize()
            + self.location.marshalledSize()
            + sum(beam.marshalledSize() for beam in self.beams)
        )

    def serialize(self, outputStream: DataOutputStream):
        outputStream.write_uint8(self.systemDataLength)
        outputStream.write_uint8(self.numberOfBeams)
        outputStream.write_uint16(self.padding)
        self.emitterSystem.serialize(outputStream)
        self.location.serialize(outputStream)
        for beam in self.beams:
            beam.serialize(outputStream)

    def parse(self, inputStream: DataInputStream):
        inputStream.read_uint8()  # systemDataLength (derived on re-serialize)
        numberOfBeams = inputStream.read_uint8()
        self.padding = inputStream.read_uint16()
        self.emitterSystem = EmitterSystem()
        self.emitterSystem.parse(inputStream)
        self.location.parse(inputStream)
        self.beams = []
        for _ in range(numberOfBeams):
            beam = EmitterBeam()
            beam.parse(inputStream)
            self.beams.append(beam)

    @property
    def systemDataLength(self) -> uint8:
        """System data length in 32-bit words — derived."""
        return self.marshalledSize() // 4

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "ElectronicEmitter":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class DistributedEmissionsRegenerationFamilyPdu(Pdu):
    """§7.6 Distributed Emissions Regeneration family PDU

    Distributed Emission Regeneration protocol family. Abstract superclass
    for distributed emissions PDU.
    """

    protocolFamily: ClassVar[int] = 6  # [UID 5] Distributed Emissions Regeneration


@dataclass(slots=True)
class ElectromagneticEmissionPdu(DistributedEmissionsRegenerationFamilyPdu):
    """§7.6.2 Electromagnetic Emission PDU

    Communicate active electromagnetic emissions, including radar and radar-
    related electronic warfare (e.g., jamming). Exceptions include IFF
    interrogations and replies, navigation aids, voice, beacon and data
    radio communications, directed energy weapons, and laser ranging and
    designation systems, which are handled by other PDUs. §5.7.3.
    """

    pduType: ClassVar[int] = 23  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "stateUpdateIndicator": 77,
    }

    emittingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    eventID: EventIdentifier = field(default_factory=EventIdentifier)
    stateUpdateIndicator: enum8 = 0  # [UID 77]
    systems: list[ElectronicEmitter] = field(default_factory=list)
    paddingForEmissionsPdu: uint16 = field(init=False, default=0)

    @property
    def numberOfSystems(self) -> uint8:
        """This field shall specify the number of emission systems being described
        in the current PDU.
        """
        return len(self.systems)

    def _marshalledBodySize(self) -> int:
        return (
            self.emittingEntityID.marshalledSize()
            + self.eventID.marshalledSize()
            + 1
            + 1
            + 2
            + sum(item.marshalledSize() for item in self.systems)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.emittingEntityID.serialize(outputStream)
        self.eventID.serialize(outputStream)
        outputStream.write_uint8(self.stateUpdateIndicator)
        outputStream.write_uint8(self.numberOfSystems)
        outputStream.write_uint16(self.paddingForEmissionsPdu)
        for item in self.systems:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.emittingEntityID = EntityIdentifier.parse(inputStream)
        self.eventID = EventIdentifier.parse(inputStream)
        self.stateUpdateIndicator = rich_or_int(77, inputStream.read_uint8())
        numberOfSystems = inputStream.read_uint8()
        self.paddingForEmissionsPdu = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.systems = [
            ElectronicEmitter.parseFrom(inputStream) for _ in range(numberOfSystems)
        ]


@dataclass(slots=True)
class DesignatorPdu(DistributedEmissionsRegenerationFamilyPdu):
    """§7.6.3 Designator PDU

    Handles designating operations. See §5.7.4.
    """

    pduType: ClassVar[int] = 24  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "codeName": 80,
        "designatorCode": 81,
        "deadReckoningAlgorithm": 44,
    }

    designatingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    codeName: enum16 = 0  # [UID 80]
    designatedEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    designatorCode: enum16 = 0  # [UID 81]
    designatorPower: float32 = 0.0  # watts
    designatorWavelength: float32 = 0.0  # microns
    designatorSpotWrtDesignated: Vector3Float = field(default_factory=Vector3Float)
    designatorSpotLocation: Vector3Double = field(default_factory=Vector3Double)
    deadReckoningAlgorithm: enum8 = 0  # [UID 44]
    entityLinearAcceleration: Vector3Float = field(default_factory=Vector3Float)
    padding1: uint8 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (
            self.designatingEntityID.marshalledSize()
            + 2
            + self.designatedEntityID.marshalledSize()
            + 2
            + 4
            + 4
            + self.designatorSpotWrtDesignated.marshalledSize()
            + self.designatorSpotLocation.marshalledSize()
            + 1
            + 1
            + 2
            + self.entityLinearAcceleration.marshalledSize()
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.designatingEntityID.serialize(outputStream)
        outputStream.write_uint16(self.codeName)
        self.designatedEntityID.serialize(outputStream)
        outputStream.write_uint16(self.designatorCode)
        outputStream.write_float32(self.designatorPower)
        outputStream.write_float32(self.designatorWavelength)
        self.designatorSpotWrtDesignated.serialize(outputStream)
        self.designatorSpotLocation.serialize(outputStream)
        outputStream.write_uint8(self.deadReckoningAlgorithm)
        outputStream.write_uint8(self.padding1)
        outputStream.write_uint16(self.padding2)
        self.entityLinearAcceleration.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.designatingEntityID = EntityIdentifier.parse(inputStream)
        self.codeName = rich_or_int(80, inputStream.read_uint16())
        self.designatedEntityID = EntityIdentifier.parse(inputStream)
        self.designatorCode = rich_or_int(81, inputStream.read_uint16())
        self.designatorPower = inputStream.read_float32()
        self.designatorWavelength = inputStream.read_float32()
        self.designatorSpotWrtDesignated.parse(inputStream)
        self.designatorSpotLocation.parse(inputStream)
        self.deadReckoningAlgorithm = rich_or_int(44, inputStream.read_uint8())
        self.padding1 = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint16()
        self.entityLinearAcceleration.parse(inputStream)


@dataclass(slots=True)
class ShaftRPM:
    """§7.6.4 Shaft RPM record

    Current Shaft RPM, Ordered Shaft RPM for use by Underwater Acoustic (UA)
    PDU.
    """

    currentRPM: uint16 = 0
    orderedRPM: uint16 = 0
    RPMrateOfChange: int32 = 0

    def marshalledSize(self) -> int:
        return 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.currentRPM)
        outputStream.write_uint16(self.orderedRPM)
        outputStream.write_int32(self.RPMrateOfChange)

    def parse(self, inputStream: DataInputStream) -> None:
        self.currentRPM = inputStream.read_uint16()
        self.orderedRPM = inputStream.read_uint16()
        self.RPMrateOfChange = inputStream.read_int32()

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "ShaftRPM":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class APA:
    """§7.6.4 APA record

    Additional Passive Activity for use by Underwater Acoustic (UA) PDU.

    14-bit additional passive activity parameter index (plus 2 status bits)
    and a value, both held raw.
    """

    parameterIndex: uint16 = 0
    value: uint16 = 0

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.parameterIndex)
        outputStream.write_uint16(self.value)

    def parse(self, inputStream: DataInputStream) -> None:
        self.parameterIndex = inputStream.read_uint16()
        self.value = inputStream.read_uint16()

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "APA":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class AcousticEmitter:
    """§6.2.2 Acoustic Emitter System record

    Information about a specific UA emitter.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "acousticSystemName": 144,
        "acousticFunction": 145,
    }

    acousticSystemName: enum16 = 0  # [UID 144]
    acousticFunction: enum8 = 0  # [UID 145]
    acousticIDNumber: uint8 = 0

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.acousticSystemName)
        outputStream.write_uint8(self.acousticFunction)
        outputStream.write_uint8(self.acousticIDNumber)

    def parse(self, inputStream: DataInputStream) -> None:
        self.acousticSystemName = rich_or_int(144, inputStream.read_uint16())
        self.acousticFunction = rich_or_int(145, inputStream.read_uint8())
        self.acousticIDNumber = inputStream.read_uint8()


@dataclass(slots=True)
class UAFundamentalParameter:
    """§6.2.91 UA Fundamental Parameter Data record

    Regeneration parameters for active emission systems that are variable
    throughout a scenario.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "activeEmissionParameterIndex": 146,
        "scanPattern": 147,
    }

    activeEmissionParameterIndex: enum16 = 0  # [UID 146]
    scanPattern: enum16 = 0  # [UID 147]
    beamCenterAzimuthHorizontal: float32 = 0.0
    azimuthalBeamwidthHorizontal: float32 = 0.0
    beamCenterDepressionElevation: float32 = 0.0
    depressionElevationBeamWidth: float32 = 0.0

    def marshalledSize(self) -> int:
        return 20

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.activeEmissionParameterIndex)
        outputStream.write_uint16(self.scanPattern)
        outputStream.write_float32(self.beamCenterAzimuthHorizontal)
        outputStream.write_float32(self.azimuthalBeamwidthHorizontal)
        outputStream.write_float32(self.beamCenterDepressionElevation)
        outputStream.write_float32(self.depressionElevationBeamWidth)

    def parse(self, inputStream: DataInputStream) -> None:
        self.activeEmissionParameterIndex = rich_or_int(146, inputStream.read_uint16())
        self.scanPattern = rich_or_int(147, inputStream.read_uint16())
        self.beamCenterAzimuthHorizontal = inputStream.read_float32()
        self.azimuthalBeamwidthHorizontal = inputStream.read_float32()
        self.beamCenterDepressionElevation = inputStream.read_float32()
        self.depressionElevationBeamWidth = inputStream.read_float32()


@dataclass(slots=True)
class UABeam:
    """Information for one or more acoustic beams that the system has,
    including: length of the beam data,  beam identification number for each
    beam, and fundamental parametric data used to define the entity’s active
    emissions.  This field defines the active  emission  parameter  index,
    beam  scan  pattern,  orientation,  and beamwidth, which can vary
    dynamically during system operation.

    ``beamDataLength`` counts 32-bit words and is derived.
    """

    beamNumber: uint8 = 0
    fundamentalParameterData: UAFundamentalParameter = field(
        default_factory=UAFundamentalParameter
    )
    padding: uint16 = field(init=False, default=0)

    def marshalledSize(self):
        return 1 + 1 + 2 + self.fundamentalParameterData.marshalledSize()

    def serialize(self, outputStream: DataOutputStream):
        outputStream.write_uint8(self.beamDataLength)
        outputStream.write_uint8(self.beamNumber)
        outputStream.write_uint16(self.padding)
        self.fundamentalParameterData.serialize(outputStream)

    def parse(self, inputStream: DataInputStream):
        inputStream.read_uint8()  # beamDataLength (derived on re-serialize)
        self.beamNumber = inputStream.read_uint8()
        self.padding = inputStream.read_uint16()
        self.fundamentalParameterData.parse(inputStream)

    @property
    def beamDataLength(self) -> uint8:
        """Beam data length in 32-bit words — derived."""
        return self.marshalledSize() // 4

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "UABeam":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class UAEmitter:
    """Underwater Acoustic (UA) active emissions (intentional emissions) and
    passive signature (unintentional emissions) information.

    ``systemDataLength`` counts 32-bit words and is derived.
    """

    acousticEmitter: AcousticEmitter = field(default_factory=AcousticEmitter)
    location: Vector3Float = field(default_factory=Vector3Float)
    beams: list[UABeam] = field(default_factory=list)
    padding: uint16 = field(init=False, default=0)

    @property
    def numberOfBeams(self) -> uint8:
        """the number of beams being described in the current PDU for the emitter
        system being described.
        """
        return len(self.beams)

    def marshalledSize(self):
        return (
            1
            + 1
            + 2
            + self.acousticEmitter.marshalledSize()
            + self.location.marshalledSize()
            + sum(beam.marshalledSize() for beam in self.beams)
        )

    def serialize(self, outputStream: DataOutputStream):
        outputStream.write_uint8(self.systemDataLength)
        outputStream.write_uint8(self.numberOfBeams)
        outputStream.write_uint16(self.padding)
        self.acousticEmitter.serialize(outputStream)
        self.location.serialize(outputStream)
        for beam in self.beams:
            beam.serialize(outputStream)

    def parse(self, inputStream: DataInputStream):
        inputStream.read_uint8()  # systemDataLength (derived on re-serialize)
        numberOfBeams = inputStream.read_uint8()
        self.padding = inputStream.read_uint16()
        self.acousticEmitter = AcousticEmitter()
        self.acousticEmitter.parse(inputStream)
        self.location.parse(inputStream)
        self.beams = []
        for _ in range(numberOfBeams):
            beam = UABeam()
            beam.parse(inputStream)
            self.beams.append(beam)

    @property
    def systemDataLength(self) -> uint8:
        """System data length in 32-bit words — derived."""
        return self.marshalledSize() // 4

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "UAEmitter":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class UnderwaterAcousticPdu(DistributedEmissionsRegenerationFamilyPdu):
    """§7.6.4 Underwater Acoustic PDU

    Information about underwater acoustic emmissions. See §5.7.5.
    """

    pduType: ClassVar[int] = 29  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "stateChangeIndicator": 143,
        "passiveParameterIndex": 148,
    }

    emittingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    eventID: EventIdentifier = field(default_factory=EventIdentifier)
    stateChangeIndicator: enum8 = 0  # [UID 143]
    passiveParameterIndex: enum16 = 0  # [UID 148]
    propulsionPlantConfiguration: uint8 = 0
    shaftRPMs: list[ShaftRPM] = field(default_factory=list)
    apaData: list[APA] = field(default_factory=list)
    emitterSystems: list[UAEmitter] = field(default_factory=list)
    pad: uint8 = field(init=False, default=0)

    @property
    def numberOfShafts(self) -> uint8:
        """This field shall represent the number of shafts on a platform."""
        return len(self.shaftRPMs)

    @property
    def numberOfAPAs(self) -> uint8:
        """This field shall indicate the number of APAs described in the current UA
        PDU.
        """
        return len(self.apaData)

    @property
    def numberOfUAEmitterSystems(self) -> uint8:
        """This field shall specify the number of UA emitter systems being
        described in the current UA PDU.
        """
        return len(self.emitterSystems)

    def _marshalledBodySize(self) -> int:
        return (
            self.emittingEntityID.marshalledSize()
            + self.eventID.marshalledSize()
            + 1
            + 1
            + 2
            + 1
            + 1
            + 1
            + 1
            + sum(item.marshalledSize() for item in self.shaftRPMs)
            + sum(item.marshalledSize() for item in self.apaData)
            + sum(item.marshalledSize() for item in self.emitterSystems)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.emittingEntityID.serialize(outputStream)
        self.eventID.serialize(outputStream)
        outputStream.write_uint8(self.stateChangeIndicator)
        outputStream.write_uint8(self.pad)
        outputStream.write_uint16(self.passiveParameterIndex)
        outputStream.write_uint8(self.propulsionPlantConfiguration)
        outputStream.write_uint8(self.numberOfShafts)
        outputStream.write_uint8(self.numberOfAPAs)
        outputStream.write_uint8(self.numberOfUAEmitterSystems)
        for item in self.shaftRPMs:
            item.serialize(outputStream)
        for item in self.apaData:
            item.serialize(outputStream)
        for item in self.emitterSystems:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.emittingEntityID = EntityIdentifier.parse(inputStream)
        self.eventID = EventIdentifier.parse(inputStream)
        self.stateChangeIndicator = rich_or_int(143, inputStream.read_uint8())
        self.pad = inputStream.read_uint8()
        self.passiveParameterIndex = rich_or_int(148, inputStream.read_uint16())
        self.propulsionPlantConfiguration = inputStream.read_uint8()
        numberOfShafts = inputStream.read_uint8()
        numberOfAPAs = inputStream.read_uint8()
        numberOfUAEmitterSystems = inputStream.read_uint8()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.shaftRPMs = [
            ShaftRPM.parseFrom(inputStream) for _ in range(numberOfShafts)
        ]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.apaData = [APA.parseFrom(inputStream) for _ in range(numberOfAPAs)]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.emitterSystems = [
            UAEmitter.parseFrom(inputStream) for _ in range(numberOfUAEmitterSystems)
        ]


@dataclass(frozen=True, slots=True)
class SystemIdentifier:
    """§6.2.87 System Identifier record

    The ID of the IFF emitting system.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "systemType": 82,
        "systemName": 83,
        "systemMode": 84,
    }

    systemType: enum16 = 0  # [UID 82]
    systemName: enum16 = 0  # [UID 83]
    systemMode: enum8 = 0  # [UID 84]
    changeOptions: uint8 = (
        0  # 8-bit Change/Options (Table B.5); Table 118 totals the record at 48 bits — the §6.2.87 prose cites the 16-bit-looking §6.2.13 shape
    )

    def marshalledSize(self) -> int:
        return 6

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.systemType)
        outputStream.write_uint16(self.systemName)
        outputStream.write_uint8(self.systemMode)
        outputStream.write_uint8(int(self.changeOptions))

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "SystemIdentifier":
        systemType = rich_or_int(82, inputStream.read_uint16())
        systemName = rich_or_int(83, inputStream.read_uint16())
        systemMode = rich_or_int(84, inputStream.read_uint8())
        changeOptions = inputStream.read_uint8()
        return cls(systemType, systemName, systemMode, changeOptions)


@dataclass(slots=True)
class FundamentalOperationalData:
    """§6.2.39 Fundamental Operational Data record

    Basic operational data for IFF.
    """

    systemStatus: uint8 = 0
    dataField1: uint8 = 0
    informationLayers: uint8 = 0
    dataField2: uint8 = 0
    parameter1: uint16 = 0
    parameter2: uint16 = 0
    parameter3: uint16 = 0
    parameter4: uint16 = 0
    parameter5: uint16 = 0
    parameter6: uint16 = 0

    def marshalledSize(self) -> int:
        return 16

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.systemStatus)
        outputStream.write_uint8(self.dataField1)
        outputStream.write_uint8(self.informationLayers)
        outputStream.write_uint8(self.dataField2)
        outputStream.write_uint16(self.parameter1)
        outputStream.write_uint16(self.parameter2)
        outputStream.write_uint16(self.parameter3)
        outputStream.write_uint16(self.parameter4)
        outputStream.write_uint16(self.parameter5)
        outputStream.write_uint16(self.parameter6)

    def parse(self, inputStream: DataInputStream) -> None:
        self.systemStatus = inputStream.read_uint8()
        self.dataField1 = inputStream.read_uint8()
        self.informationLayers = inputStream.read_uint8()
        self.dataField2 = inputStream.read_uint8()
        self.parameter1 = inputStream.read_uint16()
        self.parameter2 = inputStream.read_uint16()
        self.parameter3 = inputStream.read_uint16()
        self.parameter4 = inputStream.read_uint16()
        self.parameter5 = inputStream.read_uint16()
        self.parameter6 = inputStream.read_uint16()


@dataclass(slots=True)
class LayerHeader:
    """§6.2.51 Layer Header record

    The identification of the additional information layer number, layer-
    specific information, and the length of the layer.
    """

    layerNumber: uint8 = 0
    layerSpecificInformation: uint8 = 0
    length: uint16 = 0

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.layerNumber)
        outputStream.write_uint8(self.layerSpecificInformation)
        outputStream.write_uint16(self.length)

    def parse(self, inputStream: DataInputStream) -> None:
        self.layerNumber = inputStream.read_uint8()
        self.layerSpecificInformation = inputStream.read_uint8()
        self.length = inputStream.read_uint16()


@dataclass(frozen=True, slots=True)
class IFFFundamentalParameterData:
    """§6.2.44 IFF Fundamental Parameter Data record

    Fundamental IFF atc data.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "applicableModes": 339,
    }

    erp: float32 = 0.0
    frequency: float32 = 0.0
    pgrf: float32 = 0.0
    pulseWidth: float32 = 0.0
    burstLength: uint32 = 0
    applicableModes: enum8 = 0  # [UID 339]
    systemSpecificData: bytes = b"\x00" * 3

    def marshalledSize(self) -> int:
        return 24

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_float32(self.erp)
        outputStream.write_float32(self.frequency)
        outputStream.write_float32(self.pgrf)
        outputStream.write_float32(self.pulseWidth)
        outputStream.write_uint32(self.burstLength)
        outputStream.write_uint8(self.applicableModes)
        outputStream.write_bytes(self.systemSpecificData[:3].ljust(3, b"\x00"))

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "IFFFundamentalParameterData":
        erp = inputStream.read_float32()
        frequency = inputStream.read_float32()
        pgrf = inputStream.read_float32()
        pulseWidth = inputStream.read_float32()
        burstLength = inputStream.read_uint32()
        applicableModes = rich_or_int(339, inputStream.read_uint8())
        systemSpecificData = inputStream.read_bytes(3)
        return cls(
            erp,
            frequency,
            pgrf,
            pulseWidth,
            burstLength,
            applicableModes,
            systemSpecificData,
        )


@dataclass(slots=True)
class IFFData:
    """§6.2.43 IFF Data record

    repeating element (IFF Data record) in the IFF Data Specification
    record,.

    Generic §6.2.43 Standard-Variable-format record:
    ``recordSpecificFields`` carries the K data octets plus the trailing
    32-bit alignment pad (Table 169) exactly as received, and
    ``recordLength`` (= 6 + K + P) stays caller-settable wire state. Typed
    decodes of the B.2.1.1 record types ride the registry separately.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "recordType": 66,
    }

    recordType: enum32 = 0  # [UID 66]
    recordLength: uint16 = 0
    recordSpecificFields: bytes = b""

    def marshalledSize(self):
        return 6 + len(self.recordSpecificFields)

    def serialize(self, outputStream: DataOutputStream):
        outputStream.write_uint32(self.recordType)
        outputStream.write_uint16(self.recordLength)
        outputStream.write_bytes(self.recordSpecificFields)

    def parse(self, inputStream: DataInputStream):
        self.recordType = rich_or_int(66, inputStream.read_uint32())
        self.recordLength = inputStream.read_uint16()
        self.recordSpecificFields = inputStream.read_bytes(self.recordLength - 6)

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "IFFData":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class Mode5InterrogatorBasicData:
    """B.2.26. Mode 5 interrogator basic data."""

    mode5InterrogatorStatus: uint8 = 0
    mode5MessageFormatsPresent: uint32 = 0
    entityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    padding: uint8 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)
    padding3: uint16 = field(init=False, default=0)

    def marshalledSize(self) -> int:
        return 1 + 1 + 2 + 4 + self.entityID.marshalledSize() + 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.mode5InterrogatorStatus)
        outputStream.write_uint8(self.padding)
        outputStream.write_uint16(self.padding2)
        outputStream.write_uint32(self.mode5MessageFormatsPresent)
        self.entityID.serialize(outputStream)
        outputStream.write_uint16(self.padding3)

    def parse(self, inputStream: DataInputStream) -> None:
        self.mode5InterrogatorStatus = inputStream.read_uint8()
        self.padding = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint16()
        self.mode5MessageFormatsPresent = inputStream.read_uint32()
        self.entityID = EntityIdentifier.parse(inputStream)
        self.padding3 = inputStream.read_uint16()


@dataclass(slots=True)
class Mode5TransponderBasicData:
    """B.2.29. Mode 5 transponder basic data."""

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "navigationSource": 359,
    }

    mode5Status: uint16 = 0
    personalIdentificationNumber: uint16 = 0
    mode5MessageFormatsPresent: uint32 = 0
    enhancedMode1: uint16 = 0
    nationalOrigin: uint16 = 0
    supplementalData: uint8 = 0
    navigationSource: enum8 = 0  # [UID 359]
    figureOfMerit: uint8 = 0
    padding: uint8 = field(init=False, default=0)

    def marshalledSize(self) -> int:
        return 16

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.mode5Status)
        outputStream.write_uint16(self.personalIdentificationNumber)
        outputStream.write_uint32(self.mode5MessageFormatsPresent)
        outputStream.write_uint16(self.enhancedMode1)
        outputStream.write_uint16(self.nationalOrigin)
        outputStream.write_uint8(self.supplementalData)
        outputStream.write_uint8(self.navigationSource)
        outputStream.write_uint8(self.figureOfMerit)
        outputStream.write_uint8(self.padding)

    def parse(self, inputStream: DataInputStream) -> None:
        self.mode5Status = inputStream.read_uint16()
        self.personalIdentificationNumber = inputStream.read_uint16()
        self.mode5MessageFormatsPresent = inputStream.read_uint32()
        self.enhancedMode1 = inputStream.read_uint16()
        self.nationalOrigin = inputStream.read_uint16()
        self.supplementalData = inputStream.read_uint8()
        self.navigationSource = rich_or_int(359, inputStream.read_uint8())
        self.figureOfMerit = inputStream.read_uint8()
        self.padding = inputStream.read_uint8()


@dataclass(slots=True)
class ModeSInterrogatorBasicData:
    """B.2.37. Mode S interrogator basic data."""

    modeSInterrogatorStatus: uint8 = 0
    modeSLevelsPresent: uint8 = 0
    padding: uint8 = field(init=False, default=0)
    padding2: uint8 = field(init=False, default=0)
    padding3: uint32 = field(init=False, default=0)
    padding4: uint32 = field(init=False, default=0)
    padding5: uint32 = field(init=False, default=0)
    padding6: uint32 = field(init=False, default=0)
    padding7: uint32 = field(init=False, default=0)

    def marshalledSize(self) -> int:
        return 24

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.modeSInterrogatorStatus)
        outputStream.write_uint8(self.padding)
        outputStream.write_uint8(self.modeSLevelsPresent)
        outputStream.write_uint8(self.padding2)
        outputStream.write_uint32(self.padding3)
        outputStream.write_uint32(self.padding4)
        outputStream.write_uint32(self.padding5)
        outputStream.write_uint32(self.padding6)
        outputStream.write_uint32(self.padding7)

    def parse(self, inputStream: DataInputStream) -> None:
        self.modeSInterrogatorStatus = inputStream.read_uint8()
        self.padding = inputStream.read_uint8()
        self.modeSLevelsPresent = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint8()
        self.padding3 = inputStream.read_uint32()
        self.padding4 = inputStream.read_uint32()
        self.padding5 = inputStream.read_uint32()
        self.padding6 = inputStream.read_uint32()
        self.padding7 = inputStream.read_uint32()


@dataclass(slots=True)
class ModeSTransponderBasicData:
    """B.2.41. Mode S transponder basic data."""

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "aircraftPresentDomain": 356,
        "aircraftIdentificationType": 357,
        "capabilityReport": 358,
    }

    modeSTransponderStatus: uint16 = 0
    modeSLevelsPresent: uint8 = 0
    aircraftPresentDomain: enum8 = 0  # [UID 356]
    aircraftIdentification: uint64 = 0
    aircraftAddress: uint32 = 0
    aircraftIdentificationType: enum8 = 0  # [UID 357]
    dapSource: uint8 = 0
    modeSAltitude: uint16 = 0
    capabilityReport: enum8 = 0  # [UID 358]
    padding: uint8 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)

    def marshalledSize(self) -> int:
        return 24

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.modeSTransponderStatus)
        outputStream.write_uint8(self.modeSLevelsPresent)
        outputStream.write_uint8(self.aircraftPresentDomain)
        outputStream.write_uint64(self.aircraftIdentification)
        outputStream.write_uint32(self.aircraftAddress)
        outputStream.write_uint8(self.aircraftIdentificationType)
        outputStream.write_uint8(self.dapSource)
        outputStream.write_uint16(self.modeSAltitude)
        outputStream.write_uint8(self.capabilityReport)
        outputStream.write_uint8(self.padding)
        outputStream.write_uint16(self.padding2)

    def parse(self, inputStream: DataInputStream) -> None:
        self.modeSTransponderStatus = inputStream.read_uint16()
        self.modeSLevelsPresent = inputStream.read_uint8()
        self.aircraftPresentDomain = rich_or_int(356, inputStream.read_uint8())
        self.aircraftIdentification = inputStream.read_uint64()
        self.aircraftAddress = inputStream.read_uint32()
        self.aircraftIdentificationType = rich_or_int(357, inputStream.read_uint8())
        self.dapSource = inputStream.read_uint8()
        self.modeSAltitude = inputStream.read_uint16()
        self.capabilityReport = rich_or_int(358, inputStream.read_uint8())
        self.padding = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint16()


@dataclass(slots=True)
class IFFPduLayer2Data:
    """§7.6.5.3 IFF PDU Layer 2 Emissions Data

    Layer 2 emissions data.
    """

    layerHeader: LayerHeader = field(default_factory=LayerHeader)
    beamData: BeamData = field(default_factory=BeamData)
    secondaryOpParameter1: uint8 = 0
    secondaryOpParameter2: uint8 = 0
    IFFFundamentalParameterDataRecord: list[IFFFundamentalParameterData] = field(
        default_factory=list
    )

    @property
    def numberOfIFFFundamentalParameterDataRecords(self) -> uint16:
        """Number of IFF Fundamental Parameter Data Records (N), Table 168."""
        return len(self.IFFFundamentalParameterDataRecord)

    def marshalledSize(self) -> int:
        return (
            self.layerHeader.marshalledSize()
            + self.beamData.marshalledSize()
            + 1
            + 1
            + 2
            + sum(
                item.marshalledSize() for item in self.IFFFundamentalParameterDataRecord
            )
        )

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.layerHeader.serialize(outputStream)
        self.beamData.serialize(outputStream)
        outputStream.write_uint8(self.secondaryOpParameter1)
        outputStream.write_uint8(self.secondaryOpParameter2)
        outputStream.write_uint16(self.numberOfIFFFundamentalParameterDataRecords)
        for item in self.IFFFundamentalParameterDataRecord:
            item.serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        self.layerHeader.parse(inputStream)
        self.beamData.parse(inputStream)
        self.secondaryOpParameter1 = inputStream.read_uint8()
        self.secondaryOpParameter2 = inputStream.read_uint8()
        numberOfIFFFundamentalParameterDataRecords = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.IFFFundamentalParameterDataRecord = [
            IFFFundamentalParameterData.parse(inputStream)
            for _ in range(numberOfIFFFundamentalParameterDataRecords)
        ]

    @classmethod
    def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer2Data":
        """Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included)."""
        layer = cls()
        layer.layerHeader = LayerHeader(layerNumber, layerSpecificInformation, length)
        layer.beamData.parse(inputStream)
        layer.secondaryOpParameter1 = inputStream.read_uint8()
        layer.secondaryOpParameter2 = inputStream.read_uint8()
        numberOfIFFFundamentalParameterDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFFundamentalParameterData.parse(inputStream)
            for _ in range(numberOfIFFFundamentalParameterDataRecords)
        ]
        return layer


@dataclass(slots=True)
class IFFPduLayer3TransponderFormatData:
    """§7.6.5.4.3 IFF PDU Layer 3 Mode 5 Transponder Format

    Layer 3 Mode 5 transponder format.
    """

    layerHeader: LayerHeader = field(default_factory=LayerHeader)
    siteNumber: uint16 = 0
    applicationNumber: uint16 = 0
    mode5TransponderBasicData: Mode5TransponderBasicData = field(
        default_factory=Mode5TransponderBasicData
    )
    IFFFundamentalParameterDataRecord: list[IFFData] = field(default_factory=list)
    padding: uint16 = field(init=False, default=0)

    @property
    def numberOfIFFDataRecords(self) -> uint16:
        """Number of IFF Data Records (N), Table 170."""
        return len(self.IFFFundamentalParameterDataRecord)

    def marshalledSize(self) -> int:
        return (
            self.layerHeader.marshalledSize()
            + 2
            + 2
            + self.mode5TransponderBasicData.marshalledSize()
            + 2
            + 2
            + sum(
                item.marshalledSize() for item in self.IFFFundamentalParameterDataRecord
            )
        )

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.layerHeader.serialize(outputStream)
        outputStream.write_uint16(self.siteNumber)
        outputStream.write_uint16(self.applicationNumber)
        self.mode5TransponderBasicData.serialize(outputStream)
        outputStream.write_uint16(self.padding)
        outputStream.write_uint16(self.numberOfIFFDataRecords)
        for item in self.IFFFundamentalParameterDataRecord:
            item.serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        self.layerHeader.parse(inputStream)
        self.siteNumber = inputStream.read_uint16()
        self.applicationNumber = inputStream.read_uint16()
        self.mode5TransponderBasicData.parse(inputStream)
        self.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]

    @classmethod
    def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer3TransponderFormatData":
        """Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included)."""
        layer = cls()
        layer.layerHeader = LayerHeader(layerNumber, layerSpecificInformation, length)
        layer.siteNumber = inputStream.read_uint16()
        layer.applicationNumber = inputStream.read_uint16()
        mode5TransponderBasicData = Mode5TransponderBasicData()
        mode5TransponderBasicData.parse(inputStream)
        layer.mode5TransponderBasicData = mode5TransponderBasicData
        layer.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]
        return layer


@dataclass(slots=True)
class IFFPduLayer3InterrogatorFormatData:
    """§7.6.5.4.2 IFF PDU Layer 3 Mode 5 Interrogator Format

    Layer 3 Mode 5 interrogator format.
    """

    layerHeader: LayerHeader = field(default_factory=LayerHeader)
    siteNumber: uint16 = 0
    applicationNumber: uint16 = 0
    mode5InterrogatorBasicData: Mode5InterrogatorBasicData = field(
        default_factory=Mode5InterrogatorBasicData
    )
    IFFFundamentalParameterDataRecord: list[IFFData] = field(default_factory=list)
    padding: uint16 = field(init=False, default=0)

    @property
    def numberOfIFFDataRecords(self) -> uint16:
        """Number of IFF Data Records (N), Table 169."""
        return len(self.IFFFundamentalParameterDataRecord)

    def marshalledSize(self) -> int:
        return (
            self.layerHeader.marshalledSize()
            + 2
            + 2
            + self.mode5InterrogatorBasicData.marshalledSize()
            + 2
            + 2
            + sum(
                item.marshalledSize() for item in self.IFFFundamentalParameterDataRecord
            )
        )

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.layerHeader.serialize(outputStream)
        outputStream.write_uint16(self.siteNumber)
        outputStream.write_uint16(self.applicationNumber)
        self.mode5InterrogatorBasicData.serialize(outputStream)
        outputStream.write_uint16(self.padding)
        outputStream.write_uint16(self.numberOfIFFDataRecords)
        for item in self.IFFFundamentalParameterDataRecord:
            item.serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        self.layerHeader.parse(inputStream)
        self.siteNumber = inputStream.read_uint16()
        self.applicationNumber = inputStream.read_uint16()
        self.mode5InterrogatorBasicData.parse(inputStream)
        self.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]

    @classmethod
    def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer3InterrogatorFormatData":
        """Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included)."""
        layer = cls()
        layer.layerHeader = LayerHeader(layerNumber, layerSpecificInformation, length)
        layer.siteNumber = inputStream.read_uint16()
        layer.applicationNumber = inputStream.read_uint16()
        mode5InterrogatorBasicData = Mode5InterrogatorBasicData()
        mode5InterrogatorBasicData.parse(inputStream)
        layer.mode5InterrogatorBasicData = mode5InterrogatorBasicData
        layer.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]
        return layer


@dataclass(slots=True)
class IFFPduLayer4InterrogatorFormatData:
    """§7.6.5.5.2 IFF PDU Layer 4 Mode S Interrogator Format

    Layer 4 Mode S interrogator format.
    """

    layerHeader: LayerHeader = field(default_factory=LayerHeader)
    siteNumber: uint16 = 0
    applicationNumber: uint16 = 0
    modeSInterrogatorBasicData: ModeSInterrogatorBasicData = field(
        default_factory=ModeSInterrogatorBasicData
    )
    IFFFundamentalParameterDataRecord: list[IFFData] = field(default_factory=list)
    padding: uint16 = field(init=False, default=0)

    @property
    def numberOfIFFDataRecords(self) -> uint16:
        """Number of IFF Data Records (N), Table 171."""
        return len(self.IFFFundamentalParameterDataRecord)

    def marshalledSize(self) -> int:
        return (
            self.layerHeader.marshalledSize()
            + 2
            + 2
            + self.modeSInterrogatorBasicData.marshalledSize()
            + 2
            + 2
            + sum(
                item.marshalledSize() for item in self.IFFFundamentalParameterDataRecord
            )
        )

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.layerHeader.serialize(outputStream)
        outputStream.write_uint16(self.siteNumber)
        outputStream.write_uint16(self.applicationNumber)
        self.modeSInterrogatorBasicData.serialize(outputStream)
        outputStream.write_uint16(self.padding)
        outputStream.write_uint16(self.numberOfIFFDataRecords)
        for item in self.IFFFundamentalParameterDataRecord:
            item.serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        self.layerHeader.parse(inputStream)
        self.siteNumber = inputStream.read_uint16()
        self.applicationNumber = inputStream.read_uint16()
        self.modeSInterrogatorBasicData.parse(inputStream)
        self.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]

    @classmethod
    def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer4InterrogatorFormatData":
        """Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included)."""
        layer = cls()
        layer.layerHeader = LayerHeader(layerNumber, layerSpecificInformation, length)
        layer.siteNumber = inputStream.read_uint16()
        layer.applicationNumber = inputStream.read_uint16()
        modeSInterrogatorBasicData = ModeSInterrogatorBasicData()
        modeSInterrogatorBasicData.parse(inputStream)
        layer.modeSInterrogatorBasicData = modeSInterrogatorBasicData
        layer.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]
        return layer


@dataclass(slots=True)
class IFFPduLayer4TransponderFormatData:
    """§7.6.5.5.3 IFF PDU Layer 4 Mode S Transponder Format

    Layer 4 Mode S transponder format.
    """

    layerHeader: LayerHeader = field(default_factory=LayerHeader)
    siteNumber: uint16 = 0
    applicationNumber: uint16 = 0
    modeSTransponderBasicData: ModeSTransponderBasicData = field(
        default_factory=ModeSTransponderBasicData
    )
    IFFFundamentalParameterDataRecord: list[IFFData] = field(default_factory=list)
    padding: uint16 = field(init=False, default=0)

    @property
    def numberOfIFFDataRecords(self) -> uint16:
        """Number of IFF Data Records (N), Table 172."""
        return len(self.IFFFundamentalParameterDataRecord)

    def marshalledSize(self) -> int:
        return (
            self.layerHeader.marshalledSize()
            + 2
            + 2
            + self.modeSTransponderBasicData.marshalledSize()
            + 2
            + 2
            + sum(
                item.marshalledSize() for item in self.IFFFundamentalParameterDataRecord
            )
        )

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.layerHeader.serialize(outputStream)
        outputStream.write_uint16(self.siteNumber)
        outputStream.write_uint16(self.applicationNumber)
        self.modeSTransponderBasicData.serialize(outputStream)
        outputStream.write_uint16(self.padding)
        outputStream.write_uint16(self.numberOfIFFDataRecords)
        for item in self.IFFFundamentalParameterDataRecord:
            item.serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        self.layerHeader.parse(inputStream)
        self.siteNumber = inputStream.read_uint16()
        self.applicationNumber = inputStream.read_uint16()
        self.modeSTransponderBasicData.parse(inputStream)
        self.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]

    @classmethod
    def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer4TransponderFormatData":
        """Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included)."""
        layer = cls()
        layer.layerHeader = LayerHeader(layerNumber, layerSpecificInformation, length)
        layer.siteNumber = inputStream.read_uint16()
        layer.applicationNumber = inputStream.read_uint16()
        modeSTransponderBasicData = ModeSTransponderBasicData()
        modeSTransponderBasicData.parse(inputStream)
        layer.modeSTransponderBasicData = modeSTransponderBasicData
        layer.padding = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]
        return layer


@dataclass(slots=True)
class IFFPduLayer5Data:
    """§7.6.5.6 IFF PDU Layer 5 Data Communications

    Layer 5 data communications.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "dataCategory": 369,
    }

    layerHeader: LayerHeader = field(default_factory=LayerHeader)
    siteNumber: uint16 = 0
    applicationNumber: uint16 = 0
    applicableLayers: uint8 = 0
    dataCategory: enum8 = 0  # [UID 369]
    IFFFundamentalParameterDataRecord: list[IFFData] = field(default_factory=list)
    padding: uint16 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)

    @property
    def numberOfIFFDataRecords(self) -> uint16:
        """Number of IFF Data Records (N), Table 173."""
        return len(self.IFFFundamentalParameterDataRecord)

    def marshalledSize(self) -> int:
        return (
            self.layerHeader.marshalledSize()
            + 2
            + 2
            + 2
            + 1
            + 1
            + 2
            + 2
            + sum(
                item.marshalledSize() for item in self.IFFFundamentalParameterDataRecord
            )
        )

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.layerHeader.serialize(outputStream)
        outputStream.write_uint16(self.siteNumber)
        outputStream.write_uint16(self.applicationNumber)
        outputStream.write_uint16(self.padding)
        outputStream.write_uint8(self.applicableLayers)
        outputStream.write_uint8(self.dataCategory)
        outputStream.write_uint16(self.padding2)
        outputStream.write_uint16(self.numberOfIFFDataRecords)
        for item in self.IFFFundamentalParameterDataRecord:
            item.serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        self.layerHeader.parse(inputStream)
        self.siteNumber = inputStream.read_uint16()
        self.applicationNumber = inputStream.read_uint16()
        self.padding = inputStream.read_uint16()
        self.applicableLayers = inputStream.read_uint8()
        self.dataCategory = rich_or_int(369, inputStream.read_uint8())
        self.padding2 = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]

    @classmethod
    def parseLayer(
        cls,
        inputStream: DataInputStream,
        layerNumber: int,
        layerSpecificInformation: int,
        length: int,
    ) -> "IFFPduLayer5Data":
        """Construct the layer from its payload; the dispatching
        PDU has already read the four Layer Header bytes
        (layerNumber included)."""
        layer = cls()
        layer.layerHeader = LayerHeader(layerNumber, layerSpecificInformation, length)
        layer.siteNumber = inputStream.read_uint16()
        layer.applicationNumber = inputStream.read_uint16()
        layer.padding = inputStream.read_uint16()
        layer.applicableLayers = inputStream.read_uint8()
        layer.dataCategory = rich_or_int(369, inputStream.read_uint8())
        layer.padding2 = inputStream.read_uint16()
        numberOfIFFDataRecords = inputStream.read_uint16()
        layer.IFFFundamentalParameterDataRecord = [
            IFFData.parseFrom(inputStream) for _ in range(numberOfIFFDataRecords)
        ]
        return layer


@dataclass(slots=True)
class IdentificationFriendOrFoePdu(DistributedEmissionsRegenerationFamilyPdu):
    """§7.6.5 Identification Friend or Foe (IFF) PDU

    Information about military and civilian interrogators, transponders, and
    specific other electronic systems. See §5.7.6. Canonical descriptive
    name; IFFPdu is an alias.

    Layer 1 is always present; layers 2-5 are optional, presence declared by
    the Layer 1 Fundamental Operational Data Information Layers bits
    (§6.2.39 c, §6.2.45 a/Table 74 — bit N = Layer N; in the spec XML since
    v0.12.0) and each self-framed by a Layer Header whose Length includes
    the header (Table 165) — parse reads while wire length remains. Layers 3
    and 4 each have interrogator and transponder formats, picked by the
    Layer 1 System Type [UID 82] plus the Combined Interrogator/Transponder
    Change/Options indicator (Table B.5 bit 4, B.5.13/.14).
    """

    pduType: ClassVar[int] = 28  # [UID 4]

    emittingEntityId: EntityIdentifier = field(default_factory=EntityIdentifier)
    eventID: EventIdentifier = field(default_factory=EventIdentifier)
    location: Vector3Float = field(default_factory=Vector3Float)
    systemID: SystemIdentifier = field(default_factory=SystemIdentifier)
    systemDesignator: uint8 = 0
    systemSpecificData: uint8 = 0
    fundamentalParameters: FundamentalOperationalData = field(
        default_factory=FundamentalOperationalData
    )
    iFFPduLayer2Data: IFFPduLayer2Data | None = None
    iFFPduLayer3Data: (
        IFFPduLayer3InterrogatorFormatData | IFFPduLayer3TransponderFormatData | None
    ) = None
    iFFPduLayer4Data: (
        IFFPduLayer4InterrogatorFormatData | IFFPduLayer4TransponderFormatData | None
    ) = None
    iFFPduLayer5Data: IFFPduLayer5Data | None = None

    def _layersInOrder(self) -> list:
        """Present layers in numeric wire order (2, 3, 4, 5; one format
        per layer — Table 165 allows no duplicate layer numbers)."""
        return [
            layer
            for layer in (
                self.iFFPduLayer2Data,
                self.iFFPduLayer3Data,
                self.iFFPduLayer4Data,
                self.iFFPduLayer5Data,
            )
            if layer is not None
        ]

    def _layerIsInterrogator(self, layerNumber: int) -> bool:
        """Layer 3/4 format dispatch ([UID 82] + the CIT indicator).

        Interrogator sides: Mark XIIA Interrogator (6) and Mode 5
        Interrogator (7, Layer 3) or Mode S Interrogator (8, Layer 4); the
        Combined Interrogator/Transponders (12, 13) read their
        Change/Options Transponder/Interrogator Indicator (Table B.5 bit 4,
        B.5.13/.14) — Interrogator (1) sides with the interrogator format;
        everything else is the transponder format, the true complement
        (Layers 3/4 are Conditionally Required for any capable system type,
        B.5.1.1 b).
        """
        systemType = int(self.systemID.systemType)
        if systemType in (6, 7 if layerNumber == 3 else 8):
            return True
        if systemType in (12, 13):
            return bool((int(self.systemID.changeOptions) >> 4) & 1)
        return False

    def _marshalledBodySize(self):
        size = (
            self.emittingEntityId.marshalledSize()
            + self.eventID.marshalledSize()
            + self.location.marshalledSize()
            + self.systemID.marshalledSize()
            + 1
            + 1
            + self.fundamentalParameters.marshalledSize()
        )
        size += sum(layer.marshalledSize() for layer in self._layersInOrder())
        return size

    def _serializeBody(self, outputStream: DataOutputStream):
        self.emittingEntityId.serialize(outputStream)
        self.eventID.serialize(outputStream)
        self.location.serialize(outputStream)
        self.systemID.serialize(outputStream)
        outputStream.write_uint8(self.systemDesignator)
        outputStream.write_uint8(self.systemSpecificData)
        self.fundamentalParameters.serialize(outputStream)
        for layer in self._layersInOrder():
            layer.layerHeader.length = layer.marshalledSize()
            layer.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream):
        self.emittingEntityId = EntityIdentifier.parse(inputStream)
        self.eventID = EventIdentifier.parse(inputStream)
        self.location.parse(inputStream)
        self.systemID = SystemIdentifier.parse(inputStream)
        self.systemDesignator = inputStream.read_uint8()
        self.systemSpecificData = inputStream.read_uint8()
        self.fundamentalParameters.parse(inputStream)
        # generator: layers 2-5 presence is FLAG-declared — the Layer 1
        # Fundamental Operational Data Information Layers bits, one per layer
        # (6.2.39 c, 6.2.45 a/Table 74; declared in the XML since v0.12.0) —
        # and each layer self-frames with a Layer Header whose Length includes
        # the header (Table 165), so the loop reads while wire length remains.
        # Format dispatch: _layerIsInterrogator (System Type [UID 82] plus the
        # Combined Interrogator/Transponder Change/Options indicator, Table B.5
        # bit 4); parseLayer takes the header fields the dispatch consumed
        remaining = self.header._wireLength - 12 - 48
        while remaining >= 4:
            layerNumber = inputStream.read_uint8()
            layerSpecificInformation = inputStream.read_uint8()
            length = inputStream.read_uint16()
            if layerNumber == 2:
                self.iFFPduLayer2Data = IFFPduLayer2Data.parseLayer(
                    inputStream, layerNumber, layerSpecificInformation, length
                )
            elif layerNumber == 3:
                if self._layerIsInterrogator(3):
                    self.iFFPduLayer3Data = (
                        IFFPduLayer3InterrogatorFormatData.parseLayer(
                            inputStream, layerNumber, layerSpecificInformation, length
                        )
                    )
                else:
                    self.iFFPduLayer3Data = (
                        IFFPduLayer3TransponderFormatData.parseLayer(
                            inputStream, layerNumber, layerSpecificInformation, length
                        )
                    )
            elif layerNumber == 4:
                if self._layerIsInterrogator(4):
                    self.iFFPduLayer4Data = (
                        IFFPduLayer4InterrogatorFormatData.parseLayer(
                            inputStream, layerNumber, layerSpecificInformation, length
                        )
                    )
                else:
                    self.iFFPduLayer4Data = (
                        IFFPduLayer4TransponderFormatData.parseLayer(
                            inputStream, layerNumber, layerSpecificInformation, length
                        )
                    )
            elif layerNumber == 5:
                self.iFFPduLayer5Data = IFFPduLayer5Data.parseLayer(
                    inputStream, layerNumber, layerSpecificInformation, length
                )
            else:
                break  # layers 6-7 are not defined; stop before misparsing
            remaining -= length


# generator: aliasFor elements — one class plus a name assignment;
# descriptive name canonical, abbreviation aliased
IFFPdu = IdentificationFriendOrFoePdu


@dataclass(slots=True)
class PropulsionSystemData:
    """§6.2.68 Propulsion System Data record

    contains information describing the propulsion systems of the entity.
    This information shall be provided for each active propulsion system
    defined.
    """

    powerSetting: float32 = 0.0
    engineRpm: float32 = 0.0

    def marshalledSize(self) -> int:
        return 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_float32(self.powerSetting)
        outputStream.write_float32(self.engineRpm)

    def parse(self, inputStream: DataInputStream) -> None:
        self.powerSetting = inputStream.read_float32()
        self.engineRpm = inputStream.read_float32()

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "PropulsionSystemData":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class VectoringNozzleSystem:
    """§6.2.97 Vectoring Nozzle System Data record

    Operational data for describing the vectoring nozzle systems.
    """

    horizontalDeflectionAngle: float32 = 0.0
    verticalDeflectionAngle: float32 = 0.0

    def marshalledSize(self) -> int:
        return 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_float32(self.horizontalDeflectionAngle)
        outputStream.write_float32(self.verticalDeflectionAngle)

    def parse(self, inputStream: DataInputStream) -> None:
        self.horizontalDeflectionAngle = inputStream.read_float32()
        self.verticalDeflectionAngle = inputStream.read_float32()

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "VectoringNozzleSystem":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class SupplementalEmissionEntityStatePdu(DistributedEmissionsRegenerationFamilyPdu):
    """§7.6.6 Supplemental Emission/Entity State (SEES) PDU

    Certain supplemental information on an entity’s physical state and
    emissions. See §5.7.7. Canonical descriptive name; SEESPdu is an alias.

    Signature representation indexes are handles into the receiving
    application's signature tables, not physical values (§5.7.7).
    """

    pduType: ClassVar[int] = 30  # [UID 4]

    originatingEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    infraredSignatureRepresentationIndex: uint16 = 0
    acousticSignatureRepresentationIndex: uint16 = 0
    radarCrossSectionSignatureRepresentationIndex: uint16 = 0
    propulsionSystemData: list[PropulsionSystemData] = field(default_factory=list)
    vectoringSystemData: list[VectoringNozzleSystem] = field(default_factory=list)

    @property
    def numberOfPropulsionSystems(self) -> uint16:
        """how many propulsion systems."""
        return len(self.propulsionSystemData)

    @property
    def numberOfVectoringNozzleSystems(self) -> uint16:
        """how many vectoring nozzle systems."""
        return len(self.vectoringSystemData)

    def _marshalledBodySize(self) -> int:
        return (
            self.originatingEntityID.marshalledSize()
            + 2
            + 2
            + 2
            + 2
            + 2
            + sum(item.marshalledSize() for item in self.propulsionSystemData)
            + sum(item.marshalledSize() for item in self.vectoringSystemData)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.originatingEntityID.serialize(outputStream)
        outputStream.write_uint16(self.infraredSignatureRepresentationIndex)
        outputStream.write_uint16(self.acousticSignatureRepresentationIndex)
        outputStream.write_uint16(self.radarCrossSectionSignatureRepresentationIndex)
        outputStream.write_uint16(self.numberOfPropulsionSystems)
        outputStream.write_uint16(self.numberOfVectoringNozzleSystems)
        for item in self.propulsionSystemData:
            item.serialize(outputStream)
        for item in self.vectoringSystemData:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.originatingEntityID = EntityIdentifier.parse(inputStream)
        self.infraredSignatureRepresentationIndex = inputStream.read_uint16()
        self.acousticSignatureRepresentationIndex = inputStream.read_uint16()
        self.radarCrossSectionSignatureRepresentationIndex = inputStream.read_uint16()
        numberOfPropulsionSystems = inputStream.read_uint16()
        numberOfVectoringNozzleSystems = inputStream.read_uint16()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.propulsionSystemData = [
            PropulsionSystemData.parseFrom(inputStream)
            for _ in range(numberOfPropulsionSystems)
        ]
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.vectoringSystemData = [
            VectoringNozzleSystem.parseFrom(inputStream)
            for _ in range(numberOfVectoringNozzleSystems)
        ]


SEESPdu = SupplementalEmissionEntityStatePdu
