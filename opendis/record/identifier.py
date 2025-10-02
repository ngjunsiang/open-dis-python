"""Identifier classes for OpenDIS7.

This module defines classes used as identifiers in various DIS records and PDUs,
and their associated classes.
"""

from opendis.stream import DataInputStream, DataOutputStream
from opendis.types import (
    enum8,
    enum16,
    enum32,
    bf_enum,
    bf_int,
    bf_uint,
    float32,
    struct8,
    uint8,
    uint16,
    uint32,
)


class LiveSimulationAddress:
    """6.2.54 Live Simulation Address record
    
    A simulation's designation associated with all Live Entity IDs contained in
    Live Entity PDUs.
    """

    def __init__(self,
                 site: uint8 = 0,
                 application: uint8 = 0):
        self.site = site
        self.application = application

    def marshalledSize(self) -> int:
        return 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint8(self.site)
        outputStream.write_uint8(self.application)

    def parse(self, inputStream: DataInputStream) -> None:
        self.site = inputStream.read_uint8()
        self.application = inputStream.read_uint8()


class SimulationAddress:
    """6.2.80 Simulation Address record
    
    A simulation's designation associated with all object identifiers except
    those contained in Live Entity PDUs.
    """

    def __init__(self,
                 site: uint16 = 0,
                 application: uint16 = 0):
        self.site = site
        self.application = application

    def marshalledSize(self) -> int:
        return 4

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.site)
        outputStream.write_uint16(self.application)

    def parse(self, inputStream: DataInputStream) -> None:
        self.site = inputStream.read_uint16()
        self.application = inputStream.read_uint16()


class LiveEventIdentifier:
    """6.2.33 Event Identifier record
    
    Applies to the Live Entity PDU.
    """

    def __init__(self,
                 simulationAddress: SimulationAddress | None = None,
                 eventNumber: uint16 = 0):
        self.simulationAddress = simulationAddress or SimulationAddress()
        self.eventNumber = eventNumber

    def marshalledSize(self) -> int:
        return self.simulationAddress.marshalledSize() + 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.simulationAddress.serialize(outputStream)
        outputStream.write_uint16(self.eventNumber)

    def parse(self, inputStream: DataInputStream) -> None:
        self.simulationAddress.parse(inputStream)
        self.eventNumber = inputStream.read_uint16()


class EventIdentifier:
    """6.2.33 Event Identifier record
    
    Applies to all PDUs except the Live Entity (LE) PDU.
    """

    def __init__(self,
                 simulationAddress: SimulationAddress | None = None,
                 eventNumber: uint16 = 0):
        self.simulationAddress = simulationAddress or SimulationAddress()
        self.eventNumber = eventNumber

    def marshalledSize(self) -> int:
        return self.simulationAddress.marshalledSize() + 2

    def serialize(self, outputStream: DataOutputStream) -> None:
        self.simulationAddress.serialize(outputStream)
        outputStream.write_uint16(self.eventNumber)

    def parse(self, inputStream: DataInputStream) -> None:
        self.simulationAddress.parse(inputStream)
        self.eventNumber = inputStream.read_uint16()
