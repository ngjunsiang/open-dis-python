"""Radio Family PDU record types"""

__all__ = [
    "AntennaPatternRecord",
    "BasicHaveQuickMP",
    "BeamAntennaPattern",
    "CCTTSincgarsMP",
    "GenericRadio",
    "HighFidelityHAVEQUICKRadio",
    "ModulationParametersRecord",
    "ModulationType",
    "NetId",
    "SimpleIntercomRadio",
    "SpreadSpectrum",
    "UnknownAntennaPattern",
    "UnknownRadio",
    "VariableTransmitterParametersRecord",
]

from opendis.record import base, bitfield
from opendis.record.common import *
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import (
    enum8,
    enum16,
    enum32,
    bf_enum,
    bf_int,
    bf_uint,
    float32,
    float64,
    struct8,
    uint8,
    uint16,
    uint32,
)

# Interfaces


class AntennaPatternRecord(base.VariableRecord):
    """§6.2.8 Antenna Pattern record

    The total length of each record shall be a multiple of 64 bits.
    """


class ModulationParametersRecord(base.VariableRecord):
    """§6.2.58 Modulation Parameters record

    Base class for modulation parameters records, as defined in Annex C.
    The total length of each record shall be a multiple of 64 bits.
    """


# Placeholders


class UnknownRadio(ModulationParametersRecord):
    """Placeholder for unknown or unimplemented radio types."""

    def __init__(self, data: bytes = b""):
        self.data = data

    def marshalledSize(self) -> int:
        return len(self.data)

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_bytes(self.data)

    def parse(
        self, inputStream: DataInputStream, bytelength: int | None = None
    ) -> None:
        # Validate bytelength argument by calling base method
        super().parse(inputStream, bytelength)
        assert isinstance(bytelength, int)
        self.data = inputStream.read_bytes(bytelength)


class UnknownAntennaPattern(AntennaPatternRecord):
    """Placeholder for unknown or unimplemented antenna pattern types."""

    def __init__(self, data: bytes = b""):
        self.data = data

    def marshalledSize(self) -> int:
        return len(self.data)

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_bytes(self.data)

    def parse(
        self,  # pyright: ignore[reportIncompatibleMethodOverride]
        inputStream: DataInputStream,
        bytelength: int,
    ) -> None:
        # Validate bytelength argument by calling base method
        super().parse(inputStream, bytelength)
        # Read the remaining bytes in the record
        self.data = inputStream.read_bytes(bytelength - 6)


# Implementations


class BeamAntennaPattern(AntennaPatternRecord):
    """§6.2.8.2 Beam Antenna Pattern record

    Used when the antenna pattern type field has a value of 1. Specifies the
    direction, pattern, and polarization of radiation from an antenna.
    """

    def __init__(
        self,
        beamDirection: "EulerAngles | None" = None,
        azimuthBeamwidth: float32 = 0.0,  # in radians
        elevationBeamwidth: float32 = 0.0,  # in radians
        referenceSystem: enum8 = 0,  # [UID 168]
        ez: float32 = 0.0,
        ex: float32 = 0.0,
        phase: float32 = 0.0,
    ):  # in radians
        self.beamDirection = beamDirection or EulerAngles()
        """The rotation that transforms the reference coordinate sytem into the beam coordinate system. Either world coordinates or entity coordinates may be used as the reference coordinate system, as specified by the reference system field of the antenna pattern record."""
        self.azimuthBeamwidth = azimuthBeamwidth
        self.elevationBeamwidth = elevationBeamwidth
        self.referenceSystem = referenceSystem
        self.padding1: uint8 = 0
        self.padding2: uint16 = 0
        self.ez = ez
        """This field shall specify the magnitude of the Z-component (in beam coordinates) of the Electrical field at some arbitrary single point in the main beam and in the far field of the antenna."""
        self.ex = ex
        """This field shall specify the magnitude of the X-component (in beam coordinates) of the Electrical field at some arbitrary single point in the main beam and in the far field of the antenna."""
        self.phase = phase
        """This field shall specify the phase angle between EZ and EX in radians. If fully omni-directional antenna is modeled using beam pattern type one, the omni-directional antenna shall be represented by beam direction Euler angles psi, theta, and phi of zero, an azimuth beamwidth of 2PI, and an elevation beamwidth of PI"""
        self.padding3: uint32 = 0

    def marshalledSize(self) -> int:
        return 40

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
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

    def parse(self, inputStream: DataInputStream, bytelength: int | None = 40) -> None:
        # Validate bytelength argument by calling base method
        super().parse(inputStream, bytelength)
        self.beamDirection.parse(inputStream)
        self.azimuthBeamwidth = inputStream.read_float32()
        self.elevationBeamwidth = inputStream.read_float32()
        self.referenceSystem = inputStream.read_uint8()
        self.padding1 = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint16()
        self.ez = inputStream.read_float32()
        self.ex = inputStream.read_float32()
        self.phase = inputStream.read_float32()
        self.padding3 = inputStream.read_uint32()


class SpreadSpectrum(base.Record):
    """§6.2.59 Modulation Type record, Table 90

    Modulation used for radio transmission is characterized in a generic
    fashion by the Spread Spectrum, Major Modulation, and Detail fields.

    Each independent type of spread spectrum technique shall be represented by
    a single element of this array.
    If a particular spread spectrum technique is in use, the corresponding array
    element shall be set to one; otherwise it shall be set to zero.
    All unused array elements shall be set to zero.

    In Python, the presence or absence of each technique is indicated by a bool.
    """

    _struct = bitfield.bitfield(
        name="SpreadSpectrum",
        fields=[
            ("frequencyHopping", bitfield.INTEGER, 1),
            ("pseudoNoise", bitfield.INTEGER, 1),
            ("timeHopping", bitfield.INTEGER, 1),
            ("padding", bitfield.INTEGER, 13),
        ],
    )

    def __init__(
        self,
        frequencyHopping: bool = False,
        pseudoNoise: bool = False,
        timeHopping: bool = False,
        padding: bf_uint = 0,
    ):
        self.frequencyHopping = frequencyHopping
        self.pseudoNoise = pseudoNoise
        self.timeHopping = timeHopping
        self.padding = padding

    def marshalledSize(self) -> int:
        return self._struct.marshalledSize()

    def serialize(self, outputStream: DataOutputStream) -> None:
        # Bitfield expects int input
        self._struct(
            int(self.frequencyHopping),
            int(self.pseudoNoise),
            int(self.timeHopping),
            self.padding,
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.frequencyHopping = bool(record_bitfield.frequencyHopping)
        self.pseudoNoise = bool(record_bitfield.pseudoNoise)
        self.timeHopping = bool(record_bitfield.timeHopping)


class ModulationType(base.Record):
    """§6.2.59 Modulation Type Record

    Information about the type of modulation used for radio transmission.
    """

    def __init__(
        self,
        spreadSpectrum: SpreadSpectrum | None = None,  # See RPR Enumerations
        majorModulation: enum16 = 0,  # [UID 155]
        detail: enum16 = 0,  # [UID 156-162]
        radioSystem: enum16 = 0,
    ):  # [UID 163]
        self.spreadSpectrum = spreadSpectrum or SpreadSpectrum()
        """This field shall indicate the spread spectrum technique or combination of spread spectrum techniques in use. Bit field. 0=freq hopping, 1=psuedo noise, time hopping=2, remaining bits unused"""
        self.majorModulation = majorModulation
        self.detail = detail
        self.radioSystem = radioSystem

    def marshalledSize(self) -> int:
        size = 0
        size += self.spreadSpectrum.marshalledSize()
        size += 2  # majorModulation
        size += 2  # detail
        size += 2  # radioSystem
        return size

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.spreadSpectrum.serialize(outputStream)
        outputStream.write_uint16(self.majorModulation)
        outputStream.write_uint16(self.detail)
        outputStream.write_uint16(self.radioSystem)

    def parse(self, inputStream: DataInputStream) -> None:
        self.spreadSpectrum.parse(inputStream)
        self.majorModulation = inputStream.read_uint16()
        self.detail = inputStream.read_uint16()
        self.radioSystem = inputStream.read_uint16()


class VariableTransmitterParametersRecord(base.StandardVariableRecord):
    """§6.2.95 Variable Transmitter Parameters record

    One or more VTP records may be associated with a radio system, and the same
    VTP record may be associated with multiple radio systems.
    Specific VTP records applicable to a radio system are identified in the
    subclause that defines the radio system's unique requirements in Annex C.
    The total length of each record shall be a multiple of 64 bits.
    """


class NetId(base.Record):
    """Annex C, Table C.5

    Represents an Operational Net in the format of NXX.XYY, where:
    N = Mode
    XXX = Net Number
    YY = Frequency Table
    """

    _struct = bitfield.bitfield(
        name="NetId",
        fields=[
            ("netNumber", bitfield.INTEGER, 10),
            ("frequencyTable", bitfield.INTEGER, 2),
            ("mode", bitfield.INTEGER, 2),
            ("padding", bitfield.INTEGER, 2),
        ],
    )

    def __init__(
        self,
        netNumber: bf_uint = 0,
        frequencyTable: bf_enum = 0,  # [UID 299]
        mode: bf_enum = 0,  # [UID 298]
        padding: bf_uint = 0,
    ):
        # Net number ranging from 0 to 999 decimal
        self.netNumber = netNumber
        self.frequencyTable = frequencyTable
        self.mode = mode
        self.padding = padding

    def marshalledSize(self) -> int:
        return self._struct.marshalledSize()

    def serialize(self, outputStream: DataOutputStream) -> None:
        self._struct(
            self.netNumber, self.frequencyTable, self.mode, self.padding
        ).serialize(outputStream)

    def parse(self, inputStream: DataInputStream) -> None:
        record_bitfield = self._struct.parse(inputStream)
        self.netNumber = record_bitfield.netNumber
        self.frequencyTable = record_bitfield.frequencyTable
        self.mode = record_bitfield.mode
        self.padding = record_bitfield.padding


class GenericRadio(ModulationParametersRecord):
    """Annex C.2 Generic Radio record

    There are no other specific Transmitter, Signal, or Receiver PDU
    requirements unique to a generic radio.
    """

    def marshalledSize(self) -> int:
        return 0

    def serialize(self, outputStream: DataOutputStream) -> None:
        pass

    def parse(
        self, inputStream: DataInputStream, bytelength: int | None = None
    ) -> None:
        pass


class SimpleIntercomRadio(ModulationParametersRecord):
    """Annex C.3 Simple Intercom Radio

    A Simple Intercom shall be identified by both the Transmitter PDU
    Modulation Type record—Radio System field indicating a system type of
    Generic Radio or Simple Intercom (1) and by the Modulation Type
    record—Major Modulation field set to No Statement (0).

    This class has specific field requirements for the TransmitterPdu.
    """

    def marshalledSize(self) -> int:
        return 0

    def serialize(self, outputStream: DataOutputStream) -> None:
        pass

    def parse(
        self, inputStream: DataInputStream, bytelength: int | None = None
    ) -> None:
        pass


# C.4 HAVE QUICK Radios


class BasicHaveQuickMP(ModulationParametersRecord):
    """Annex C 4.2.2, Table C.3 — Basic HAVE QUICK MP record"""

    def __init__(
        self,
        net_id: NetId | None = None,
        mwod_index: uint16 = 1,
        reserved16: uint16 = 0,
        reserved8_1: uint8 = 0,
        reserved8_2: uint8 = 0,
        time_of_day: uint32 = 0,
        padding: uint32 = 0,
    ):
        self.net_id = net_id or NetId()
        self.mwod_index = mwod_index
        self.reserved16 = reserved16
        self.reserved8_1 = reserved8_1
        self.reserved8_2 = reserved8_2
        self.time_of_day = time_of_day
        self.padding = padding

    def marshalledSize(self) -> int:
        return 16  # bytes

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        self.net_id.serialize(outputStream)
        outputStream.write_uint16(self.mwod_index)
        outputStream.write_uint16(self.reserved16)
        outputStream.write_uint8(self.reserved8_1)
        outputStream.write_uint8(self.reserved8_2)
        outputStream.write_uint32(self.time_of_day)
        outputStream.write_uint32(self.padding)

    def parse(
        self, inputStream: DataInputStream, bytelength: int | None = None
    ) -> None:
        # Validate bytelength argument by calling base method
        super().parse(inputStream, bytelength)
        self.net_id.parse(inputStream)
        self.mwod_index = inputStream.read_uint16()
        self.reserved16 = inputStream.read_uint16()
        self.reserved8_1 = inputStream.read_uint8()
        self.reserved8_2 = inputStream.read_uint8()
        self.time_of_day = inputStream.read_uint32()
        self.padding = inputStream.read_uint32()


class CCTTSincgarsMP(ModulationParametersRecord):
    """Annex C 6.2.3, Table C.7 — CCTT SINCGARS MP record"""

    def __init__(
        self,
        fh_net_id: uint16 = 0,
        hop_set_id: uint16 = 0,
        lockout_set_id: uint16 = 0,
        start_of_message: enum8 = 0,
        clear_channel: enum8 = 0,
        fh_sync_time_offset: uint32 = 0,
        transmission_security_key: uint16 = 0,
    ):
        self.fh_net_id = fh_net_id
        self.hop_set_id = hop_set_id
        self.lockout_set_id = lockout_set_id
        self.start_of_message = start_of_message
        self.clear_channel = clear_channel
        self.fh_sync_time_offset = fh_sync_time_offset
        self.transmission_security_key = transmission_security_key
        self.padding: uint16 = 0

    def marshalledSize(self) -> int:
        return 16  # bytes

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_uint16(self.fh_net_id)
        outputStream.write_uint16(self.hop_set_id)
        outputStream.write_uint16(self.lockout_set_id)
        outputStream.write_uint8(self.start_of_message)
        outputStream.write_uint8(self.clear_channel)
        outputStream.write_uint32(self.fh_sync_time_offset)
        outputStream.write_uint16(self.transmission_security_key)
        outputStream.write_uint16(self.padding)

    def parse(
        self, inputStream: DataInputStream, bytelength: int | None = None
    ) -> None:
        # Validate bytelength argument by calling base method
        super().parse(inputStream, bytelength)
        self.fh_net_id = inputStream.read_uint16()
        self.hop_set_id = inputStream.read_uint16()
        self.lockout_set_id = inputStream.read_uint16()
        self.start_of_message = inputStream.read_uint8()
        self.clear_channel = inputStream.read_uint8()
        self.fh_sync_time_offset = inputStream.read_uint32()
        self.transmission_security_key = inputStream.read_uint16()
        self.padding = inputStream.read_uint16()


class HighFidelityHAVEQUICKRadio(VariableTransmitterParametersRecord):
    """Annex C C4.2.3, Table C.4 — High Fidelity HAVE QUICK Radio record"""

    recordType: enum32 = 3000

    def __init__(
        self,
        netId: NetId | None = None,
        todTransmitIndicator: enum8 = 0,
        todDelta: uint32 = 0,
        wod1: uint32 = 0,
        wod2: uint32 = 0,
        wod3: uint32 = 0,
        wod4: uint32 = 0,
        wod5: uint32 = 0,
        wod6: uint32 = 0,
    ):
        self.padding1: uint16 = 0
        self.netId = netId or NetId()
        self.todTransmitIndicator = todTransmitIndicator
        self.padding2: uint8 = 0
        self.todDelta = todDelta
        self.wod1 = wod1
        self.wod2 = wod2
        self.wod3 = wod3
        self.wod4 = wod4
        self.wod5 = wod5
        self.wod6 = wod6

    def marshalledSize(self) -> int:
        return 40

    def serialize(self, outputStream: DataOutputStream) -> None:
        super().serialize(outputStream)
        outputStream.write_uint32(self.recordType)
        outputStream.write_uint16(self.recordLength)
        outputStream.write_uint16(self.padding1)
        self.netId.serialize(outputStream)
        outputStream.write_uint8(self.todTransmitIndicator)
        outputStream.write_uint8(self.padding2)
        outputStream.write_uint32(self.todDelta)
        outputStream.write_uint32(self.wod1)
        outputStream.write_uint32(self.wod2)
        outputStream.write_uint32(self.wod3)
        outputStream.write_uint32(self.wod4)
        outputStream.write_uint32(self.wod5)
        outputStream.write_uint32(self.wod6)

    def parse(self, inputStream: DataInputStream, bytelength: int) -> None:
        # Validate bytelength argument by calling base method
        super().parse(inputStream, bytelength)
        self.padding1 = inputStream.read_uint16()
        self.netId.parse(inputStream)
        self.todTransmitIndicator = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint8()
        self.todDelta = inputStream.read_uint32()
        self.wod1 = inputStream.read_uint32()
        self.wod2 = inputStream.read_uint32()
        self.wod3 = inputStream.read_uint32()
        self.wod4 = inputStream.read_uint32()
        self.wod5 = inputStream.read_uint32()
        self.wod6 = inputStream.read_uint32()


# ---------------------------------------------------------------------------
# dis7-ng target-state PDUs (dataclass style, composed PduHeader).
# Wire ground truth: xml-fixed/RadioCommunicationsFamilyPdus.xml; §7.7.
# The Annex C modulation/antenna record classes above (PR #80 layer) are
# reused for the Transmitter's dispatch — transitional until the generator
# emits dataclass forms.
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field  # noqa: E402
from typing import ClassVar  # noqa: E402

from opendis.enum_registry import rich_or_int  # noqa: E402
from opendis.record.common import (  # noqa: E402
    EntityIdentifier,
    EntityType,
    Vector3Float,
    WorldCoordinates,
)
from opendis.record.pdu import Pdu  # noqa: E402
from opendis.types import uint64  # noqa: E402


def _padTo32(byteCount: int) -> int:
    """Pad bytes needed to bring a datagram to a 32-bit boundary."""
    return (4 - byteCount % 4) % 4


@dataclass(slots=True)
class RadioCommunicationsFamilyPdu(Pdu):
    """§7.7 marker for the Radio Communications family."""

    protocolFamily: ClassVar[int] = 4  # [UID 5]


# generator: the XML's RadioCommsHeader is flattened onto the PDU (the
# composed PDU header already owns the attribute name ``header``); legacy
# dis7.py made the same flattening call.
@dataclass(slots=True)
class TransmitterPdu(RadioCommunicationsFamilyPdu):
    """§7.7.2 Transmitter PDU

    Detailed state of one radio transmitter or simple intercom. The
    Modulation Parameters record and Antenna Pattern record are SINGLE
    records (not lists — the XML's objectlists are wrong there; the
    standard allows one of each, §7.7.2/Annex C/§6.2.8), followed by the
    variable transmitter parameter records (uid-66 SV format). All three
    counts are derived.
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

    # XML order after the modulation-parameter count is pad-u8 + pad-u16
    # (legacy dis7.py wrote u16 + u8 — same 4 bytes, different layout;
    # zeros either way).
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

    def _marshalledBodySize(self) -> int:
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

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
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

    def _parseBody(self, inputStream: DataInputStream) -> None:
        from opendis.record import parseStandardVariableRecord

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

    Conveys the audio or digital data carried by a simulated radio
    transmission. ``dataLength`` is IN BITS and derived from the byte
    payload (bit counts not divisible by 8 are unsupported, same ruling
    as VariableDatum); the datagram is padded to a 32-bit boundary by the
    packer.
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
        """Length of the data field IN BITS — derived, never stored."""
        return len(self.data) * 8

    def _marshalledBodySize(self) -> int:
        prefix = self.radioReferenceID.marshalledSize() + 2 + 2 + 2 + 4 + 2 + 2
        return prefix + len(self.data) + _padTo32(12 + prefix + len(self.data))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.radioReferenceID.serialize(outputStream)
        outputStream.write_uint16(self.radioNumber)
        outputStream.write_uint16(self.encodingScheme)
        outputStream.write_uint16(self.tdlType)
        outputStream.write_uint32(self.sampleRate)
        outputStream.write_uint16(self.dataLength)
        outputStream.write_uint16(self.samples)
        outputStream.write_bytes(self.data)
        padding = _padTo32(self._marshalledBodySize())
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
        padding = _padTo32(12 + 20 + len(self.data))
        if padding:
            inputStream.read_bytes(padding)


@dataclass(slots=True)
class ReceiverPdu(RadioCommunicationsFamilyPdu):
    """§7.7.4 Receiver PDU

    Communicates the state of a particular radio receiver, primarily for
    network monitors, data loggers, and after-action review. Total PDU
    size is 36 bytes.
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
            + 2  # radioNumber + receiverState + padding1
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


@dataclass(slots=True)
class IntercomReferenceID:
    """§6.2.47 Intercom Reference Identifier record

    Unique designation of an attached or unattached intercom: site,
    application, and reference number. Not an EntityIdentifier — the
    reference number may address an unattached intercom."""

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
        return cls(
            inputStream.read_uint16(),
            inputStream.read_uint16(),
            inputStream.read_uint16(),
        )


@dataclass(slots=True)
class IntercomSignalPdu(RadioCommunicationsFamilyPdu):
    """§7.7.6 Intercom Signal PDU

    Conveys the audio or digital data used to communicate between
    simulated intercom devices. ``dataLength`` is IN BITS and derived;
    the datagram is padded to a 32-bit boundary by the packer (the
    xml-fixed set sized this list — legacy byte-counted a bits field).
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
        """Length of the data field IN BITS — derived, never stored."""
        return len(self.data) * 8

    def _marshalledBodySize(self) -> int:
        prefix = self.intercomReferenceID.marshalledSize() + 2 + 2 + 2 + 4 + 2
        return prefix + len(self.data) + _padTo32(12 + prefix + len(self.data))

    def _serializeBody(self, outputStream: DataOutputStream) -> None:
        self.intercomReferenceID.serialize(outputStream)
        outputStream.write_uint16(self.intercomNumber)
        outputStream.write_uint16(self.encodingScheme)
        outputStream.write_uint16(self.tdlType)
        outputStream.write_uint32(self.sampleRate)
        outputStream.write_uint16(self.dataLength)
        outputStream.write_uint16(self.samples)
        outputStream.write_bytes(self.data)
        padding = _padTo32(self._marshalledBodySize())
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
        padding = _padTo32(12 + 20 + len(self.data))
        if padding:
            inputStream.read_bytes(padding)


@dataclass(slots=True)
class IntercomCommunicationsParameters:
    """§6.2.46 Intercom Communications Parameter record

    A record type, a record length, and record-specific fields (held as
    raw bytes; ``recordLength`` counts the record-specific bytes,
    following the xml-fixed reading)."""

    FIELD_ENUM_UID: ClassVar[dict[str, int]] = {
        "recordType": 185,
    }

    recordType: enum16 = 0  # [UID 185]
    recordLength: uint16 = 0
    recordSpecificField: bytes = b""

    def marshalledSize(self) -> int:
        return 4 + len(self.recordSpecificField)

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.recordType)
        outputStream.write_uint16(self.recordLength)
        outputStream.write_bytes(self.recordSpecificField)

    def parse(self, inputStream: DataInputStream) -> None:
        self.recordType = rich_or_int(185, inputStream.read_uint16())
        self.recordLength = inputStream.read_uint16()
        self.recordSpecificField = inputStream.read_bytes(self.recordLength)


@dataclass(slots=True)
class IntercomControlPdu(RadioCommunicationsFamilyPdu):
    """§7.7.7 Intercom Control PDU

    Communicates the state of a particular intercom device, requests an
    action of another intercom device, or responds to an action request.
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
        """How many intercom communications parameter records follow."""
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
            + sum(p.marshalledSize() for p in self.intercomParameters)
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
        for parameter in self.intercomParameters:
            parameter.serialize(outputStream)

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
        self.intercomParameters = [
            self._parseIntercomParameter(inputStream)
            for _ in range(intercomParametersLength)
        ]

    @staticmethod
    def _parseIntercomParameter(
        inputStream: DataInputStream,
    ) -> IntercomCommunicationsParameters:
        parameter = IntercomCommunicationsParameters()
        parameter.parse(inputStream)
        return parameter
