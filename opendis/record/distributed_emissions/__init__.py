"""Distributed Emissions Regeneration family (IEEE 1278.1-2012 §7.6)
— target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/DistributedEmissionsFamilyPdus.xml.
Electromagnetic Emission, Designator, and Underwater Acoustic PDUs with
their emitter-system / beam record trees. The beam and system "data
length" fields count 32-bit words (§7.6.2) and are always derived
(``marshalledSize() // 4``; zero means the section is "large").

Scope note: the IFF PDU (type 28) and SEE PDU (type 30) with their
Annex-B layer structures are NOT implemented in this pass — their
pduTypes stay unregistered, so datagrams degrade to the lossless
``UnrecognizedPdu`` fallback (see docs/design/sample-review.md).
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
from opendis.types import enum8, enum16, float32, uint8, uint16, int32

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
    "JammingTechnique",
    "ShaftRPM",
    "TrackJamData",
    "UABeam",
    "UAEmitter",
    "UAFundamentalParameter",
    "UnderwaterAcousticPdu",
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
