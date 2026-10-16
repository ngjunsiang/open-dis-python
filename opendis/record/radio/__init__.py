"""Radio Communications family (IEEE 1278.1-2012 §7.7) — target-state PDUs.

Wire ground truth: submodules/open-dis-spec-xml/xml/RadioCommunicationsFamilyPdus.xml.
Transmitter, Signal, Receiver, and Intercom Signal/Control.

Python-side deltas from the XML (sample-review rulings): the XML's
RadioCommsHeader is flattened onto the PDUs (the composed PDU header
already owns the attribute name ``header``; legacy dis7.py made the same
call); the Transmitter keeps SINGLE Modulation Parameters and Antenna
Pattern records (the XML's objectlists are wrong there — the standard
allows one of each, §7.7.2/Annex C/§6.2.8) with byte-length counts, and
its VTP list decodes uid-66 records via the registry. The §6.2.8.2 Beam
Antenna Pattern record is generated here (header-less, Table 31 — the
Transmitter's ``antennaPatternType`` field types it); the Annex C
dispatch classes (GenericRadio, HAVE QUICK, SINCGARS, unknown
placeholders) live in the hand seam ``radio/annexc.py``. Signal
and Intercom Signal carry bit-counted byte payloads padded to 32 bits.
"""

from dataclasses import dataclass, field
from typing import ClassVar

from opendis.enum_registry import rich_or_int
from opendis.record.common import (
    EntityIdentifier,
    EntityType,
    EulerAngles,
    Vector3Float,
    WorldCoordinates,
)
from opendis.record.pdu import Pdu
from opendis.record.radio.annexc import (
    AntennaPatternRecord,
    BasicHaveQuickMP,
    CCTTSincgarsMP,
    GenericRadio,
    ModulationParametersRecord,
    SimpleIntercomRadio,
    UnknownAntennaPattern,
    UnknownRadio,
)
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, enum16, float32, uint8, uint16, uint32, uint64

__all__ = [
    "BeamAntennaPattern",
    "IntercomCommunicationsParameters",
    "IntercomControlPdu",
    "IntercomReferenceID",
    "IntercomSignalPdu",
    "ModulationType",
    "RadioCommunicationsFamilyPdu",
    "ReceiverPdu",
    "SignalPdu",
    "TransmitterPdu",
]


def _padTo32(byteCount: int) -> int:
    """Pad bytes needed to bring a datagram to a 32-bit boundary."""
    return (4 - byteCount % 4) % 4


@dataclass(slots=True)
class BeamAntennaPattern(AntennaPatternRecord):
    """§6.2.8.2 Beam Antenna Pattern record

    Used when the antenna pattern type field has a value of 1. Specifies the
    direction, pattern, and polarization of radiation from an antenna.

    Non-self-identifying (§6.2.8): Antenna Pattern records carry no record
    header of their own — the Transmitter PDU's ``antennaPatternType`` field
    types the record and its byte-length count bounds it on the wire (Table
    31: 320 bits total).
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "referenceSystem": 168,
    }

    beamDirection: EulerAngles = field(default_factory=EulerAngles)
    azimuthBeamwidth: float32 = 0.0
    elevationBeamwidth: float32 = 0.0
    referenceSystem: enum8 = 0  # [UID 168]
    ez: float32 = 0.0
    ex: float32 = 0.0
    phase: float32 = 0.0
    # Padding ruling: explicit attribute, out of __init__ (zero by default,
    # holds the wire value after parse so odd pads round-trip byte-exact).
    padding1: uint8 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)
    padding3: uint32 = field(init=False, default=0)

    def marshalledSize(self) -> int:
        return self.beamDirection.marshalledSize() + 4 + 4 + 1 + 1 + 2 + 4 + 4 + 4 + 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.beamDirection.serialize(outputStream)
        outputStream.write_float32(self.azimuthBeamwidth)
        outputStream.write_float32(self.elevationBeamwidth)
        outputStream.write_uint8(self.referenceSystem)
        outputStream.write_uint8(self.padding1)
        outputStream.write_uint16(self.padding2)
        outputStream.write_float32(self.ez)
        outputStream.write_float32(self.ex)
        outputStream.write_float32(self.phase)
        outputStream.write_uint32(self.padding3)

    def parse(self, inputStream: DataInputStream) -> None:
        self.beamDirection.parse(inputStream)
        self.azimuthBeamwidth = inputStream.read_float32()
        self.elevationBeamwidth = inputStream.read_float32()
        self.referenceSystem = rich_or_int(168, inputStream.read_uint8())
        self.padding1 = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint16()
        self.ez = inputStream.read_float32()
        self.ex = inputStream.read_float32()
        self.phase = inputStream.read_float32()
        self.padding3 = inputStream.read_uint32()

    @classmethod
    def parseFrom(cls, inputStream: DataInputStream) -> "BeamAntennaPattern":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class ModulationType:
    """Information about the type of modulation used for radio transmission.
    6.2.59.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "majorModulation": 155,
        "radioSystem": 163,
    }

    spreadSpectrum: uint16 = 0
    majorModulation: enum16 = 0  # [UID 155]
    detail: uint16 = 0  # [UID 156-162]
    radioSystem: enum16 = 0  # [UID 163]

    def marshalledSize(self) -> int:
        return 8

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.spreadSpectrum)
        outputStream.write_uint16(self.majorModulation)
        outputStream.write_uint16(self.detail)
        outputStream.write_uint16(self.radioSystem)

    def parse(self, inputStream: DataInputStream) -> None:
        self.spreadSpectrum = inputStream.read_uint16()
        self.majorModulation = rich_or_int(155, inputStream.read_uint16())
        self.detail = inputStream.read_uint16()
        self.radioSystem = rich_or_int(163, inputStream.read_uint16())


@dataclass(slots=True)
class RadioCommunicationsFamilyPdu(Pdu):
    """§7.7 Radio Communications family PDU

    Abstract superclass for radio communications PDUs.
    """

    protocolFamily: ClassVar[int] = 4  # [UID 5] Radio Communications


@dataclass(slots=True)
class TransmitterPdu(RadioCommunicationsFamilyPdu):
    """§7.7.2 Transmitter PDU

    Communicates the state of a particular radio transmitter or simple
    intercom.
    """

    pduType: ClassVar[int] = 25  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "transmitState": 164,
        "inputSource": 165,
        "antennaPatternType": 167,
        "cryptoSystem": 166,
    }

    radioReferenceID: EntityIdentifier = field(default_factory=EntityIdentifier)
    radioNumber: uint16 = 0
    radioEntityType: EntityType = field(default_factory=EntityType)
    transmitState: enum8 = 0  # [UID 164]
    inputSource: enum8 = 0  # [UID 165]
    antennaLocation: WorldCoordinates = field(default_factory=WorldCoordinates)
    relativeAntennaLocation: Vector3Float = field(default_factory=Vector3Float)
    antennaPatternType: enum16 = 0  # [UID 167]
    frequency: uint64 = 0
    transmitFrequencyBandwidth: float32 = 0.0
    power: float32 = 0.0
    modulationType: ModulationType = field(default_factory=ModulationType)
    cryptoSystem: enum16 = 0  # [UID 166]
    cryptoKeyId: uint16 = 0
    modulationParameters: ModulationParametersRecord | None = None
    antennaPattern: AntennaPatternRecord | None = None
    variableTransmitterParameters: list = field(default_factory=list)
    padding1: uint8 = field(init=False, default=0)
    padding2: uint16 = field(init=False, default=0)

    @property
    def modulationParameterCount(self) -> uint8:
        """Length in bytes of the Modulation Parameters record (0 if
        absent)."""
        return (
            self.modulationParameters.marshalledSize()
            if self.modulationParameters is not None
            else 0
        )

    @property
    def antennaPatternCount(self) -> uint16:
        """Length in bytes of the Antenna Pattern record (0 if absent)."""
        return (
            self.antennaPattern.marshalledSize()
            if self.antennaPattern is not None
            else 0
        )

    @property
    def variableTransmitterParameterCount(self) -> uint16:
        """How many variable transmitter parameter records follow."""
        return len(self.variableTransmitterParameters)

    def _marshalledBodySize(self):
        size = (
            self.radioReferenceID.marshalledSize()
            + 2
            + self.radioEntityType.marshalledSize()
            + 1
            + 1
            + 2  # variableTransmitterParameterCount
            + self.antennaLocation.marshalledSize()
            + self.relativeAntennaLocation.marshalledSize()
            + 2
            + 2  # antennaPatternType + antennaPatternCount
            + 8
            + 4
            + 4
            + self.modulationType.marshalledSize()
            + 2
            + 2  # cryptoSystem + cryptoKeyId
            + 1
            + 1
            + 2
        )  # modulationParameterCount + pads
        if self.modulationParameters is not None:
            size += self.modulationParameters.marshalledSize()
        if self.antennaPattern is not None:
            size += self.antennaPattern.marshalledSize()
        size += sum(vtp.marshalledSize() for vtp in self.variableTransmitterParameters)
        return size

    def _serializeBody(self, outputStream: DataOutputStream):
        self.radioReferenceID.serialize(outputStream)
        outputStream.write_uint16(self.radioNumber)
        self.radioEntityType.serialize(outputStream)
        outputStream.write_uint8(self.transmitState)
        outputStream.write_uint8(self.inputSource)
        outputStream.write_uint16(self.variableTransmitterParameterCount)
        self.antennaLocation.serialize(outputStream)
        self.relativeAntennaLocation.serialize(outputStream)
        outputStream.write_uint16(self.antennaPatternType)
        outputStream.write_uint16(self.antennaPatternCount)
        outputStream.write_uint64(self.frequency)
        outputStream.write_float32(self.transmitFrequencyBandwidth)
        outputStream.write_float32(self.power)
        self.modulationType.serialize(outputStream)
        outputStream.write_uint16(self.cryptoSystem)
        outputStream.write_uint16(self.cryptoKeyId)
        outputStream.write_uint8(self.modulationParameterCount)
        outputStream.write_uint8(self.padding1)
        outputStream.write_uint16(self.padding2)
        if self.modulationParameters is not None:
            self.modulationParameters.serialize(outputStream)
        if self.antennaPattern is not None:
            self.antennaPattern.serialize(outputStream)
        for vtp in self.variableTransmitterParameters:
            vtp.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream):
        self.radioReferenceID = EntityIdentifier.parse(inputStream)
        self.radioNumber = inputStream.read_uint16()
        self.radioEntityType = EntityType.parse(inputStream)
        self.transmitState = rich_or_int(164, inputStream.read_uint8())
        self.inputSource = rich_or_int(165, inputStream.read_uint8())
        variableTransmitterParameterCount = inputStream.read_uint16()
        self.antennaLocation.parse(inputStream)
        self.relativeAntennaLocation.parse(inputStream)
        self.antennaPatternType = rich_or_int(167, inputStream.read_uint16())
        antennaPatternLength = inputStream.read_uint16()
        self.frequency = inputStream.read_uint64()
        self.transmitFrequencyBandwidth = inputStream.read_float32()
        self.power = inputStream.read_float32()
        self.modulationType = ModulationType()
        self.modulationType.parse(inputStream)
        self.cryptoSystem = rich_or_int(166, inputStream.read_uint16())
        self.cryptoKeyId = inputStream.read_uint16()
        modulationParametersLength = inputStream.read_uint8()
        self.padding1 = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint16()

        # generator: single-record MP/AP dispatch is beyond mechanical
        # generation (record boundaries depend on the radio system and
        # antenna pattern type)
        if modulationParametersLength > 0:
            radioSystem = int(self.modulationType.radioSystem)
            if radioSystem == 1:  # generic radio or simple intercom
                radio = (
                    SimpleIntercomRadio()
                    if int(self.modulationType.majorModulation) == 0
                    else GenericRadio()
                )
                radio.parse(inputStream)
            elif radioSystem in (2, 3, 4):  # HAVE QUICK I/II/IIA
                radio = BasicHaveQuickMP()
                radio.parse(inputStream)
            elif radioSystem == 6:  # CCTT SINCGARS
                radio = CCTTSincgarsMP()
                radio.parse(inputStream)
            else:
                radio = UnknownRadio()
                radio.parse(inputStream, bytelength=modulationParametersLength)
            self.modulationParameters = radio
        else:
            self.modulationParameters = None

        if antennaPatternLength > 0:
            if int(self.antennaPatternType) == 1:
                pattern = BeamAntennaPattern()
                pattern.parse(inputStream)
            else:
                pattern = UnknownAntennaPattern()
                pattern.parse(inputStream, bytelength=antennaPatternLength)
            self.antennaPattern = pattern
        else:
            self.antennaPattern = None

        self.variableTransmitterParameters = [
            parseStandardVariableRecord(inputStream)
            for _ in range(variableTransmitterParameterCount)
        ]


@dataclass(slots=True)
class SignalPdu(RadioCommunicationsFamilyPdu):
    """§7.7.3 Signal PDU

    Conveys the audio or digital data carried by the simulated radio or
    intercom transmission.
    """

    pduType: ClassVar[int] = 26  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "tdlType": 178,
    }

    radioReferenceID: EntityIdentifier = field(default_factory=EntityIdentifier)
    radioNumber: uint16 = 0
    encodingScheme: uint16 = 0
    tdlType: enum16 = 0  # [UID 178]
    sampleRate: uint32 = 0
    samples: uint16 = 0
    data: bytes = b""

    @property
    def dataLength(self) -> uint16:
        """length of data in bits."""
        return len(self.data) * 8

    def _unpaddedBodySize(self) -> int:
        return (
            self.radioReferenceID.marshalledSize()
            + 2
            + 2
            + 2
            + 4
            + 2
            + 2
            + len(self.data)
        )

    def _marshalledBodySize(self) -> int:
        return self._unpaddedBodySize() + _padTo32(12 + self._unpaddedBodySize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.radioReferenceID.serialize(outputStream)
        outputStream.write_uint16(self.radioNumber)
        outputStream.write_uint16(self.encodingScheme)
        outputStream.write_uint16(self.tdlType)
        outputStream.write_uint32(self.sampleRate)
        outputStream.write_uint16(self.dataLength)
        outputStream.write_uint16(self.samples)
        outputStream.write_bytes(self.data)
        padding = _padTo32(12 + self._unpaddedBodySize())
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.radioReferenceID = EntityIdentifier.parse(inputStream)
        self.radioNumber = inputStream.read_uint16()
        self.encodingScheme = inputStream.read_uint16()
        self.tdlType = rich_or_int(178, inputStream.read_uint16())
        self.sampleRate = inputStream.read_uint32()
        dataLength = inputStream.read_uint16()
        self.samples = inputStream.read_uint16()
        self.data = inputStream.read_bytes(dataLength // 8)
        padding = _padTo32(12 + self._unpaddedBodySize())
        if padding:
            inputStream.read_bytes(padding)


@dataclass(slots=True)
class ReceiverPdu(RadioCommunicationsFamilyPdu):
    """§7.7.4 Receiver PDU

    Communicates the state of a particular radio receiver. Its primary
    application is in communicating state information to radio network
    monitors, data loggers, and similar applications for use in debugging,
    supervision, and after-action review.
    """

    pduType: ClassVar[int] = 27  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "receiverState": 179,
    }

    radioReferenceID: EntityIdentifier = field(default_factory=EntityIdentifier)
    radioNumber: uint16 = 0
    receiverState: enum16 = 0  # [UID 179]
    receivedPower: float32 = 0.0
    transmitterEntityId: EntityIdentifier = field(default_factory=EntityIdentifier)
    transmitterRadioId: uint16 = 0
    padding1: uint16 = field(init=False, default=0)

    def _marshalledBodySize(self) -> int:
        return (
            self.radioReferenceID.marshalledSize()
            + 2
            + 2
            + 2
            + 4
            + self.transmitterEntityId.marshalledSize()
            + 2
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.radioReferenceID.serialize(outputStream)
        outputStream.write_uint16(self.radioNumber)
        outputStream.write_uint16(self.receiverState)
        outputStream.write_uint16(self.padding1)
        outputStream.write_float32(self.receivedPower)
        self.transmitterEntityId.serialize(outputStream)
        outputStream.write_uint16(self.transmitterRadioId)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.radioReferenceID = EntityIdentifier.parse(inputStream)
        self.radioNumber = inputStream.read_uint16()
        self.receiverState = rich_or_int(179, inputStream.read_uint16())
        self.padding1 = inputStream.read_uint16()
        self.receivedPower = inputStream.read_float32()
        self.transmitterEntityId = EntityIdentifier.parse(inputStream)
        self.transmitterRadioId = inputStream.read_uint16()


@dataclass(frozen=True, slots=True)
class IntercomReferenceID:
    """§6.2.47 Intercom Reference Identifier record

    unique reference ID for this intercom; reference-ID portion of the
    Intercom Identifier record,.
    """

    siteNumber: uint16 = 0
    applicationNumber: uint16 = 0
    referenceNumber: uint16 = 0

    def marshalledSize(self) -> int:
        return 6

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.siteNumber)
        outputStream.write_uint16(self.applicationNumber)
        outputStream.write_uint16(self.referenceNumber)

    @classmethod
    def parse(cls, inputStream: DataInputStream) -> "IntercomReferenceID":
        siteNumber = inputStream.read_uint16()
        applicationNumber = inputStream.read_uint16()
        referenceNumber = inputStream.read_uint16()
        return cls(siteNumber, applicationNumber, referenceNumber)


@dataclass(slots=True)
class IntercomSignalPdu(RadioCommunicationsFamilyPdu):
    """§7.7.6 Intercom Signal PDU

    Conveys the audio or digital data that is used to communicate between
    simulated intercom devices.
    """

    pduType: ClassVar[int] = 31  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "tdlType": 178,
    }

    intercomReferenceID: IntercomReferenceID = field(
        default_factory=IntercomReferenceID
    )
    intercomNumber: uint16 = 0
    encodingScheme: uint16 = 0
    tdlType: enum16 = 0  # [UID 178]
    sampleRate: uint32 = 0
    samples: uint16 = 0
    data: bytes = b""

    @property
    def dataLength(self) -> uint16:
        """data length."""
        return len(self.data) * 8

    def _unpaddedBodySize(self) -> int:
        return (
            self.intercomReferenceID.marshalledSize()
            + 2
            + 2
            + 2
            + 4
            + 2
            + 2
            + len(self.data)
        )

    def _marshalledBodySize(self) -> int:
        return self._unpaddedBodySize() + _padTo32(12 + self._unpaddedBodySize())

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.intercomReferenceID.serialize(outputStream)
        outputStream.write_uint16(self.intercomNumber)
        outputStream.write_uint16(self.encodingScheme)
        outputStream.write_uint16(self.tdlType)
        outputStream.write_uint32(self.sampleRate)
        outputStream.write_uint16(self.dataLength)
        outputStream.write_uint16(self.samples)
        outputStream.write_bytes(self.data)
        padding = _padTo32(12 + self._unpaddedBodySize())
        if padding:
            outputStream.write_bytes(b"\x00" * padding)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.intercomReferenceID = IntercomReferenceID.parse(inputStream)
        self.intercomNumber = inputStream.read_uint16()
        self.encodingScheme = inputStream.read_uint16()
        self.tdlType = rich_or_int(178, inputStream.read_uint16())
        self.sampleRate = inputStream.read_uint32()
        dataLength = inputStream.read_uint16()
        self.samples = inputStream.read_uint16()
        self.data = inputStream.read_bytes(dataLength // 8)
        padding = _padTo32(12 + self._unpaddedBodySize())
        if padding:
            inputStream.read_bytes(padding)


@dataclass(slots=True)
class IntercomCommunicationsParameters:
    """§6.2.46 Intercom Communications Parameter record

    Intercom communications parameters.
    """

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "recordType": 185,
    }

    recordType: enum16 = 0  # [UID 185]
    recordLength: uint16 = 0
    recordSpecificField: bytes = b""

    def marshalledSize(self):
        return 4 + len(self.recordSpecificField)

    def serialize(self, outputStream: DataOutputStream):
        outputStream.write_uint16(self.recordType)
        outputStream.write_uint16(self.recordLength)
        outputStream.write_bytes(self.recordSpecificField)

    def parse(self, inputStream: DataInputStream):
        self.recordType = rich_or_int(185, inputStream.read_uint16())
        self.recordLength = inputStream.read_uint16()
        self.recordSpecificField = inputStream.read_bytes(self.recordLength)

    @classmethod
    def parseFrom(
        cls, inputStream: DataInputStream
    ) -> "IntercomCommunicationsParameters":
        """Construct a new record from the stream (list-parse helper; the
        mutating ``parse`` above satisfies the Record protocol)."""
        item = cls()
        item.parse(inputStream)
        return item


@dataclass(slots=True)
class IntercomControlPdu(RadioCommunicationsFamilyPdu):
    """§7.7.7 Intercom Control PDU

    Communicates the state of a particular intercom device, request an
    action of another intercom device, or respond to an action request.
    """

    pduType: ClassVar[int] = 32  # [UID 4]

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "controlType": 180,
        "transmitLineState": 183,
        "command": 182,
    }

    controlType: enum8 = 0  # [UID 180]
    communicationsChannelType: uint8 = 0
    sourceEntityID: EntityIdentifier = field(default_factory=EntityIdentifier)
    sourceIntercomNumber: uint16 = 0
    sourceLineID: uint8 = 0
    transmitPriority: uint8 = 0
    transmitLineState: enum8 = 0  # [UID 183]
    command: enum8 = 0  # [UID 182]
    masterIntercomReferenceID: EntityIdentifier = field(
        default_factory=EntityIdentifier
    )
    masterIntercomNumber: uint16 = 0
    masterChannelID: uint16 = 0
    intercomParameters: list[IntercomCommunicationsParameters] = field(
        default_factory=list
    )

    @property
    def intercomParametersLength(self) -> uint32:
        """number of intercom parameters."""
        return len(self.intercomParameters)

    def _marshalledBodySize(self) -> int:
        return (
            1
            + 1
            + self.sourceEntityID.marshalledSize()
            + 2
            + 1
            + 1
            + 1
            + 1
            + self.masterIntercomReferenceID.marshalledSize()
            + 2
            + 2
            + 4
            + sum(item.marshalledSize() for item in self.intercomParameters)
        )

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.controlType)
        outputStream.write_uint8(self.communicationsChannelType)
        self.sourceEntityID.serialize(outputStream)
        outputStream.write_uint16(self.sourceIntercomNumber)
        outputStream.write_uint8(self.sourceLineID)
        outputStream.write_uint8(self.transmitPriority)
        outputStream.write_uint8(self.transmitLineState)
        outputStream.write_uint8(self.command)
        self.masterIntercomReferenceID.serialize(outputStream)
        outputStream.write_uint16(self.masterIntercomNumber)
        outputStream.write_uint16(self.masterChannelID)
        outputStream.write_uint32(self.intercomParametersLength)
        for item in self.intercomParameters:
            item.serialize(outputStream)

    def _parseBody(self, inputStream: DataInputStream) -> None:
        self.controlType = rich_or_int(180, inputStream.read_uint8())
        self.communicationsChannelType = inputStream.read_uint8()
        self.sourceEntityID = EntityIdentifier.parse(inputStream)
        self.sourceIntercomNumber = inputStream.read_uint16()
        self.sourceLineID = inputStream.read_uint8()
        self.transmitPriority = inputStream.read_uint8()
        self.transmitLineState = rich_or_int(183, inputStream.read_uint8())
        self.command = rich_or_int(182, inputStream.read_uint8())
        self.masterIntercomReferenceID = EntityIdentifier.parse(inputStream)
        self.masterIntercomNumber = inputStream.read_uint16()
        self.masterChannelID = inputStream.read_uint16()
        intercomParametersLength = inputStream.read_uint32()
        # Never append to a pre-existing list (instance-reuse corruption,
        # PR #49): the list is replaced wholesale.
        self.intercomParameters = [
            IntercomCommunicationsParameters.parseFrom(inputStream)
            for _ in range(intercomParametersLength)
        ]
