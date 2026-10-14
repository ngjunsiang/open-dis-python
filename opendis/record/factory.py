"""PDU factory: dispatch table plus UnrecognizedPdu fallback.

Design: docs/design/dis7-representation.md §3.2. An unknown ``pduType``
byte produces an ``UnrecognizedPdu`` — fully parsed header plus the raw
payload as bytes — rather than an exception or a silent skip, so a DIS v8
or malformed datagram never kills a long-running listener. Truncated
datagrams parse as far as the bytes allow and never raise.

This is the target-state factory for the converted families; the legacy
``opendis.PduFactory`` keeps serving ``opendis.dis7`` classes unchanged
until the per-family conversion completes.
"""

import io
import logging
from os import PathLike

from opendis.record.distributed_emissions import (
    DesignatorPdu,
    ElectromagneticEmissionPdu,
    UnderwaterAcousticPdu,
)
from opendis.record.entity_information import EntityStatePdu
from opendis.record.information_operations import (
    InformationOperationsActionPdu,
    InformationOperationsReportPdu,
)
from opendis.record.minefield import (
    MinefieldDataPdu,
    MinefieldQueryPdu,
    MinefieldResponseNACKPdu,
    MinefieldStatePdu,
)
from opendis.record.entity_management import (
    AggregateStatePdu,
    IsGroupOfPdu,
    IsPartOfPdu,
    TransferOwnershipPdu,
)
from opendis.record.live_entity import (
    AppearancePdu,
    ArticulatedPartsPdu,
    LiveEntityDetonationPdu,
    LiveEntityFirePdu,
    TimeSpacePositionInformationPdu,
)
from opendis.record.logistics import (
    RepairCompletePdu,
    RepairResponsePdu,
    ResupplyCancelPdu,
    ResupplyOfferPdu,
    ResupplyReceivedPdu,
    ServiceRequestPdu,
)
from opendis.record.pdu import Pdu, UnrecognizedPdu
from opendis.record.radio import (
    IntercomControlPdu,
    IntercomSignalPdu,
    ReceiverPdu,
    SignalPdu,
    TransmitterPdu,
)
from opendis.record.simulation_management_with_reliability import (
    AcknowledgeReliablePdu,
    ActionRequestReliablePdu,
    ActionResponseReliablePdu,
    CommentReliablePdu,
    CreateEntityReliablePdu,
    DataQueryReliablePdu,
    DataReliablePdu,
    EventReportReliablePdu,
    RecordQueryReliablePdu,
    RecordReliablePdu,
    RemoveEntityReliablePdu,
    SetDataReliablePdu,
    SetRecordReliablePdu,
    StartResumeReliablePdu,
    StopFreezeReliablePdu,
)
from opendis.record.synthetic_environment import (
    ArealObjectStatePdu,
    EnvironmentalProcessPdu,
    LinearObjectStatePdu,
    PointObjectStatePdu,
)
from opendis.record.simulation_management import (
    AcknowledgePdu,
    ActionRequestPdu,
    ActionResponsePdu,
    CommentPdu,
    CreateEntityPdu,
    DataPdu,
    DataQueryPdu,
    EventReportPdu,
    RemoveEntityPdu,
    SetDataPdu,
    StartResumePdu,
    StopFreezePdu,
)
from opendis.record.warfare import (
    DetonationPdu,
    DirectedEnergyFirePdu,
    EntityDamageStatusPdu,
    FirePdu,
)
from opendis.stream import DataInputStream

__all__ = [
    "PDU_FAMILIES",
    "PduTypeDecoders",
    "createPdu",
    "createPduFromFilePath",
    "getPdu",
]

_logger = logging.getLogger(__name__)

# pduType [UID 4] -> concrete PDU class. Registration is explicit (a dict,
# per the design; __init_subclass__ registration is the idiomatic
# equivalent once the generator emits the full set).
PduTypeDecoders: dict[int, type[Pdu]] = {
    1: EntityStatePdu,
    2: FirePdu,
    3: DetonationPdu,
    5: ServiceRequestPdu,
    6: ResupplyOfferPdu,
    7: ResupplyReceivedPdu,
    8: ResupplyCancelPdu,
    9: RepairCompletePdu,
    10: RepairResponsePdu,
    11: CreateEntityPdu,
    12: RemoveEntityPdu,
    13: StartResumePdu,
    14: StopFreezePdu,
    15: AcknowledgePdu,
    16: ActionRequestPdu,
    17: ActionResponsePdu,
    18: DataQueryPdu,
    19: SetDataPdu,
    20: DataPdu,
    21: EventReportPdu,
    22: CommentPdu,
    23: ElectromagneticEmissionPdu,
    24: DesignatorPdu,
    29: UnderwaterAcousticPdu,
    33: AggregateStatePdu,
    34: IsGroupOfPdu,
    35: TransferOwnershipPdu,
    36: IsPartOfPdu,
    37: MinefieldStatePdu,
    38: MinefieldQueryPdu,
    39: MinefieldDataPdu,
    40: MinefieldResponseNACKPdu,
    41: EnvironmentalProcessPdu,
    43: PointObjectStatePdu,
    44: LinearObjectStatePdu,
    45: ArealObjectStatePdu,
    46: TimeSpacePositionInformationPdu,
    47: AppearancePdu,
    48: ArticulatedPartsPdu,
    49: LiveEntityFirePdu,
    50: LiveEntityDetonationPdu,
    51: CreateEntityReliablePdu,
    52: RemoveEntityReliablePdu,
    53: StartResumeReliablePdu,
    54: StopFreezeReliablePdu,
    55: AcknowledgeReliablePdu,
    56: ActionRequestReliablePdu,
    57: ActionResponseReliablePdu,
    58: DataQueryReliablePdu,
    59: SetDataReliablePdu,
    60: DataReliablePdu,
    61: EventReportReliablePdu,
    62: CommentReliablePdu,
    63: RecordReliablePdu,
    64: SetRecordReliablePdu,
    65: RecordQueryReliablePdu,
    25: TransmitterPdu,
    26: SignalPdu,
    27: ReceiverPdu,
    31: IntercomSignalPdu,
    32: IntercomControlPdu,
    68: DirectedEnergyFirePdu,
    69: EntityDamageStatusPdu,
    70: InformationOperationsActionPdu,
    71: InformationOperationsReportPdu,
}

# pduType [UID 4] -> protocol family [UID 5] — family metadata for
# middleware that should not have to import PDU classes.
PDU_FAMILIES: dict[int, int] = {
    1: EntityStatePdu.protocolFamily,
    2: FirePdu.protocolFamily,
    3: DetonationPdu.protocolFamily,
    5: ServiceRequestPdu.protocolFamily,
    6: ResupplyOfferPdu.protocolFamily,
    7: ResupplyReceivedPdu.protocolFamily,
    8: ResupplyCancelPdu.protocolFamily,
    9: RepairCompletePdu.protocolFamily,
    10: RepairResponsePdu.protocolFamily,
    11: CreateEntityPdu.protocolFamily,
    12: RemoveEntityPdu.protocolFamily,
    13: StartResumePdu.protocolFamily,
    14: StopFreezePdu.protocolFamily,
    15: AcknowledgePdu.protocolFamily,
    16: ActionRequestPdu.protocolFamily,
    17: ActionResponsePdu.protocolFamily,
    18: DataQueryPdu.protocolFamily,
    19: SetDataPdu.protocolFamily,
    20: DataPdu.protocolFamily,
    21: EventReportPdu.protocolFamily,
    22: CommentPdu.protocolFamily,
    23: ElectromagneticEmissionPdu.protocolFamily,
    24: DesignatorPdu.protocolFamily,
    29: UnderwaterAcousticPdu.protocolFamily,
    33: AggregateStatePdu.protocolFamily,
    34: IsGroupOfPdu.protocolFamily,
    35: TransferOwnershipPdu.protocolFamily,
    36: IsPartOfPdu.protocolFamily,
    37: MinefieldStatePdu.protocolFamily,
    38: MinefieldQueryPdu.protocolFamily,
    39: MinefieldDataPdu.protocolFamily,
    40: MinefieldResponseNACKPdu.protocolFamily,
    41: EnvironmentalProcessPdu.protocolFamily,
    43: PointObjectStatePdu.protocolFamily,
    44: LinearObjectStatePdu.protocolFamily,
    45: ArealObjectStatePdu.protocolFamily,
    46: TimeSpacePositionInformationPdu.protocolFamily,
    47: AppearancePdu.protocolFamily,
    48: ArticulatedPartsPdu.protocolFamily,
    49: LiveEntityFirePdu.protocolFamily,
    50: LiveEntityDetonationPdu.protocolFamily,
    51: CreateEntityReliablePdu.protocolFamily,
    52: RemoveEntityReliablePdu.protocolFamily,
    53: StartResumeReliablePdu.protocolFamily,
    54: StopFreezeReliablePdu.protocolFamily,
    55: AcknowledgeReliablePdu.protocolFamily,
    56: ActionRequestReliablePdu.protocolFamily,
    57: ActionResponseReliablePdu.protocolFamily,
    58: DataQueryReliablePdu.protocolFamily,
    59: SetDataReliablePdu.protocolFamily,
    60: DataReliablePdu.protocolFamily,
    61: EventReportReliablePdu.protocolFamily,
    62: CommentReliablePdu.protocolFamily,
    63: RecordReliablePdu.protocolFamily,
    64: SetRecordReliablePdu.protocolFamily,
    65: RecordQueryReliablePdu.protocolFamily,
    25: TransmitterPdu.protocolFamily,
    26: SignalPdu.protocolFamily,
    27: ReceiverPdu.protocolFamily,
    31: IntercomSignalPdu.protocolFamily,
    32: IntercomControlPdu.protocolFamily,
    68: DirectedEnergyFirePdu.protocolFamily,
    69: EntityDamageStatusPdu.protocolFamily,
    70: InformationOperationsActionPdu.protocolFamily,
    71: InformationOperationsReportPdu.protocolFamily,
}


def getPdu(inputStream: DataInputStream) -> Pdu:
    """Parse one PDU starting at the stream's current position; unknown
    types and truncated datagrams degrade (UnrecognizedPdu / partial
    parse), never raise."""
    return createPdu(inputStream.stream.read())


def createPdu(data: bytes) -> Pdu:
    """Create a PDU of the correct type from a buffer of binary DIS data."""
    pduType = data[2] if len(data) > 2 else 0
    decoder = PduTypeDecoders.get(pduType)
    if decoder is None or len(data) < 12:
        return UnrecognizedPdu(rawHeader=data[:12], rawPayload=data[12:])
    pdu = decoder()
    try:
        pdu.parse(DataInputStream(io.BytesIO(data)))
    except Exception:
        # Tolerance rule: never raise mid-PDU; the parse that fit wins.
        _logger.warning("truncated or malformed PDU of type %s", pduType,
                        exc_info=True)
    return pdu


def createPduFromFilePath(filePath: PathLike) -> Pdu:
    """Utility written for unit tests, but could have other uses too."""
    with io.open(filePath, "rb") as f:
        return createPdu(f.read())
