"""Hand-maintained Annex C radio records — the modulation-parameters and
antenna-pattern seam the Transmitter PDU dispatches on (opendis/record/
radio/__init__.py is generated; these tagged-union members stay hand-
written until Annex C records are generated).

Retired here per the 2026-10-15 ruling: the legacy ``_struct`` classes
SpreadSpectrum and NetId. ``ModulationType`` is generated (the XML
declares it); ``netId`` fields hold the raw packed uint16 (mode bits 0–1,
frequency table bits 2–3 — Annex C Table C.5).
"""

from opendis.record import base
from opendis.record.common import EulerAngles
from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import enum8, uint8, uint16, uint32

__all__ = [
    "AntennaPatternRecord",
    "BasicHaveQuickMP",
    "BeamAntennaPattern",
    "CCTTSincgarsMP",
    "GenericRadio",
    "HighFidelityHAVEQUICKRadio",
    "ModulationParametersRecord",
    "SimpleIntercomRadio",
    "UnknownAntennaPattern",
    "UnknownRadio",
    "VariableTransmitterParametersRecord",
]


class AntennaPatternRecord(base.VariableRecord):
    """§6.2.8 Antenna Pattern record

    The total length of each record shall be a multiple of 64 bits.
    """


class ModulationParametersRecord(base.VariableRecord):
    """§6.2.58 Modulation Parameters record

    Base class for modulation parameters records, as defined in Annex C.
    The total length of each record shall be a multiple of 64 bits.
    """


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


class BeamAntennaPattern(AntennaPatternRecord):
    """§6.2.8.2 Beam Antenna Pattern record

    Used when the antenna pattern type field has a value of 1. Specifies the
    direction, pattern, and polarization of radiation from an antenna.
    """

    def __init__(
        self,
        beamDirection: "EulerAngles | None" = None,
        azimuthBeamwidth: float = 0.0,  # in radians
        elevationBeamwidth: float = 0.0,  # in radians
        referenceSystem: enum8 = 0,  # [UID 168]
        ez: float = 0.0,
        ex: float = 0.0,
        phase: float = 0.0,
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
        net_id: uint16 = 0,
        mwod_index: uint16 = 1,
        reserved16: uint16 = 0,
        reserved8_1: uint8 = 0,
        reserved8_2: uint8 = 0,
        time_of_day: uint32 = 0,
        padding: uint32 = 0,
    ):
        # net_id packs the Annex C Table C.5 fields: net number bits 4-13,
        # frequency table bits 2-3 [UID 299], mode bits 0-1 [UID 298]
        self.net_id = net_id
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
        outputStream.write_uint16(self.net_id)
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
        self.net_id = inputStream.read_uint16()
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


class VariableTransmitterParametersRecord(base.StandardVariableRecord):
    """§6.2.95 Variable Transmitter Parameters record

    One or more VTP records may be associated with a radio system, and the same
    VTP record may be associated with multiple radio systems.
    Specific VTP records applicable to a radio system are identified in the
    subclause that defines the radio system's unique requirements in Annex C.
    The total length of each record shall be a multiple of 64 bits.
    """


class HighFidelityHAVEQUICKRadio(VariableTransmitterParametersRecord):
    """Annex C C4.2.3, Table C.4 — High Fidelity HAVE QUICK Radio record"""

    recordType: uint32 = 3000

    def __init__(
        self,
        netId: uint16 = 0,
        todTransmitIndicator: enum8 = 0,
        todDelta: uint32 = 0,
        wod1: uint32 = 0,
        wod2: uint32 = 0,
        wod3: uint32 = 0,
        wod4: uint32 = 0,
        wod5: uint32 = 0,
        wod6: uint32 = 0,
    ):
        # netId packs the Annex C Table C.5 fields (mode bits 0-1 [UID 298],
        # frequency table bits 2-3 [UID 299], net number bits 4-13)
        self.padding1: uint16 = 0
        self.netId = netId
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
        outputStream.write_uint16(self.netId)
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
        self.netId = inputStream.read_uint16()
        self.todTransmitIndicator = inputStream.read_uint8()
        self.padding2 = inputStream.read_uint8()
        self.todDelta = inputStream.read_uint32()
        self.wod1 = inputStream.read_uint32()
        self.wod2 = inputStream.read_uint32()
        self.wod3 = inputStream.read_uint32()
        self.wod4 = inputStream.read_uint32()
        self.wod5 = inputStream.read_uint32()
        self.wod6 = inputStream.read_uint32()
