"""Record classes for DIS 7, IEEE1278.1-2012 Annex C.

These classes implement Modulation Parameters (MP) and VTP specified in Annex C
of the DIS 7 standard, 1278.1-2012.
"""

from .record import NetId, Record
from .types import(
    enum8,
    enum16,
    enum32,
    int32,
    uint8,
    uint16,
    uint32,
)
from .DataInputStream import DataInputStream
from .DataOutputStream import DataOutputStream


# Symbolic names from Table 25—Symbolic names (DIS 7 Annex C)

SYMBOLIC_AGG_RESPONSE_DFLT = 10  # seconds
ALL_AGGS = 0xFFFF
ALL_APPLIC = 0xFFFF
ALL_BEAMS = 0xFF
ALL_EMITTERS = 0xFF
ALL_ENTITIES = 0xFFFF
ALL_OBJECTS = 0xFFFF
ALL_SITES = 0xFFFF
COLLISION_ELASTIC_TIMEOUT = 5  # seconds
COLLISION_THRSH = 0.1  # m/s
DE_AREA_AIMING_THRSH = 10  # degrees
DE_ENERGY_THRSH = 1.0  # percent
DE_PRECISION_AIMING_THRSH = 0.5  # meters
DRA_ORIENT_THRSH = 3  # degrees
DRA_POS_THRSH = 1  # meter
D_SPOT_NO_ENTITY = (None, None, None)  # NO_SITE, NO_APPLIC, NO_ENTITY
EE_AD_PULRAT_THRSH = 0.017  # rad/s
EE_AD_PULACC_THRSH = 0.017  # rad/s^2
EE_AZ_THRSH = 1  # degree
EE_EL_THRSH = 1  # degree
EE_ERP_THRSH = 1.0  # dBm
EE_FREQ_THRSH = 1  # Hz
EE_FRNG_THRSH = 1  # Hz
EE_FT_VEL_THRSH = 1.0  # m/s
EE_FT_ACC_THRSH = 1.0  # m/s^2
EE_FT_MWD_THRSH = 10000  # meters
EE_FT_KT_THRSH = 10  # seconds
EE_FT_ESP_THRSH = 10  # meters
EE_HIGH_DENSITY_THRSH = 10  # entities/beam
EE_PRF_THRSH = 1  # Hz
EE_PW_THRSH = 1  # microseconds
ENTITY_ID_UNKNOWN = (None, None, None)  # NO_SITE, NO_APPLIC, NO_ENTITY
EP_DIMENSION_THRSH = 1  # meter
EP_NO_SEQUENCE = 0xFFFF
EP_POS_THRSH = 1  # meter
EP_STATE_THRSH = None  # user defined
GD_GEOMETRY_CHANGE = 0.1  # percent (±10%)
GD_STATE_CHANGE = None  # user defined
HBT_DAMAGE_TIMEOUT_MPLIER = 2.4
HBT_ESPDU_KIND_CULTURAL_FEATURE = 5  # seconds (±10%)
HBT_ESPDU_KIND_ENVIRONMENTAL = 5  # seconds (±10%)
HBT_ESPDU_KIND_EXPENDABLE = 5  # seconds (±10%)
HBT_ESPDU_KIND_LIFE_FORM = 5  # seconds (±10%)
HBT_ESPDU_KIND_MUNITION = 5  # seconds (±10%)
HBT_ESPDU_KIND_RADIO = 5  # seconds (±10%)
HBT_ESPDU_KIND_SENSOR_EMITTER = 5  # seconds (±10%)
HBT_ESPDU_KIND_SUPPLY = 5  # seconds (±10%)
HBT_ESPDU_PLATFORM_AIR = 5  # seconds (±10%)
HBT_ESPDU_PLATFORM_LAND = 5  # seconds (±10%)
HBT_ESPDU_PLATFORM_SPACE = 5  # seconds (±10%)
HBT_ESPDU_PLATFORM_SUBSURFACE = 5  # seconds (±10%)
HBT_ESPDU_PLATFORM_SURFACE = 5  # seconds (±10%)
HBT_PDU_AGGREGATE_STATE = 30  # seconds (±10%)
HBT_PDU_APPEARANCE = 60  # seconds (±10%)
HBT_PDU_DE_FIRE = 0.5  # seconds (±10%)
HBT_PDU_DESIGNATOR = 5  # seconds (±10%)
HBT_PDU_EE = 5  # seconds (±10%)
HBT_PDU_ENTITY_DAMAGE = 10  # seconds (±10%)
HBT_PDU_ENVIRONMENTAL_PROCESS = 15  # seconds (±10%)
HBT_PDU_GRIDDED_DATA = 900  # seconds (15 min, ±10%)
HBT_PDU_IFF = 10  # seconds (±10%)
HBT_PDU_ISGROUPOF = 5  # seconds (±10%)
HBT_PDU_MINEFIELD_DATA = 5  # seconds (±10%)
HBT_PDU_MINEFIELD_STATE = 5  # seconds (±10%)
HBT_PDU_RECEIVER = 5  # seconds (±10%)
HBT_PDU_SEES = 180  # seconds (3 min, ±10%)
HBT_PDU_TRANSMITTER = 2  # seconds (±10%)
HBT_PDU_TSPI = 30  # seconds (±10%)
HBT_PDU_UA = 180  # seconds (3 min, ±10%)
HBT_STATIONARY = 60  # seconds (±10%)
HBT_TIMEOUT_MPLIER = 2.4
HQ_TOD_DIFF_THRSH = 0.02  # seconds (20 ms)
IFF_AZ_THRSH = 3  # degrees
IFF_CHG_LATENCY = 2  # seconds
IFF_EL_THRSH = 3  # degrees
IFF_IP_REPLY_TIMER = 30  # seconds
IFF_PDU_FINAL = 10  # seconds
IFF_PDU_RESUME = 10  # seconds
IO_UNTIL_FURTHER_NOTICE = 65535
MAX_PDU_SIZE_BITS = 65536  # bits
MAX_PDU_SIZE_OCTETS = 8192  # octets
MINEFIELD_CHANGE = 2.5  # seconds
MINEFIELD_RESPONSE_TIMER = 1  # second
MULTIPLES_PRESENT = 0
NO_AGG = 0
NO_APPLIC = 0
NO_BEAM = 0
NO_CATEGORY = 0
NO_EMITTER = 0
NO_ENTITY = 0
NO_FIRE_MISSION = 0
NO_KIND = 0
NO_OBJECT = 0
NO_PATTERN = 0
NO_REF_NUMBER = 0.0
NO_SITE = 0
NO_SPECIFIC = 0
NO_SPECIFIC_ENTITY = 0
NO_SUBCAT = 0
NO_VALUE = 0
NON_SYNC_THRSH = 60  # seconds
POWER_ENGINE_OFF = -100.0
POWER_IDLE = 0.0
POWER_MAX_AFTERBURNER = 100.0
POWER_MILITARY = 50.0
POWER_MIN_AFTERBURNER = 51.0
REPAR_REC_T1 = 5  # seconds
REPAR_SUP_T1 = 12  # seconds
REPAR_SUP_T2 = 12  # seconds
RESUP_REC_T1 = 5  # seconds
RESUP_REC_T2 = 55  # seconds
RESUP_SUP_T1 = 60  # seconds
RQST_ASSIGN_ID = 0xFFFE
SEES_NDA_THRSH = 2  # degrees (±2° in axis of deflection)
SEES_PS_THRSH = 0.1  # percent (±10% of max Power Setting)
SEES_RPM_THRSH = 0.05  # percent (±5% of max engine RPM)
SMALLEST_MTU_OCTETS = 1400  # octets (IPv4)
SM_REL_RETRY_CNT = 3
SM_REL_RETRY_DELAY = 2  # seconds
TARGET_ID_UNKNOWN = (None, None, None)  # NO_SITE, NO_APPLIC, NO_ENTITY
TIMESTAMP_AHEAD = 5  # seconds
TIMESTAMP_BEHIND = 5  # seconds
TI_TIMER1_DFLT = 2  # seconds
TI_TIMER2_DFLT = 12  # seconds
TO_AUTO_RESPONSE_TIMER = 5  # seconds
TO_MAN_RESPONSE_TIMER = 120  # seconds
TR_TIMER1_DFLT = 5  # seconds
TR_TIMER2_DFLT = 60  # seconds
TRANS_ORIENT_THRSH = 180  # degrees
TRANS_POS_THRSH = 500  # meters
UA_ORIENT_THRSH = 2  # degrees
UA_POS_THRSH = 10  # meters
UA_SRPM_ROC_THRSH = 0.1  # percent (±10% of max rate of change)
UA_SRPM_THRSH = 0.05  # percent (±5% of max shaft rate in RPM)


# C.4 HAVE QUICK Radios

# C.4.2.2 Basic HAVE QUICK MP record

class BasicHaveQuickMP(Record):
    """Annex C 4.2.2, Table C.3 — Basic HAVE QUICK MP record"""

    def __init__(self,
                 net_id: NetId | None = None,
                 mwod_index: uint16 = 1,
                 reserved16: uint16 = 0,
                 reserved8_1: uint8 = 0,
                 reserved8_2: uint8 = 0,
                 time_of_day: uint32 = 0,
                 padding: uint32 = 0):
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
        self.net_id.serialize(outputStream)
        outputStream.write_uint16(self.mwod_index)
        outputStream.write_uint16(self.reserved16)
        outputStream.write_uint8(self.reserved8_1)
        outputStream.write_uint8(self.reserved8_2)
        outputStream.write_uint32(self.time_of_day)
        outputStream.write_uint32(self.padding)

    def parse(self, inputStream: DataInputStream) -> None:
        self.net_id.parse(inputStream)
        self.mwod_index = inputStream.read_uint16()
        self.reserved16 = inputStream.read_uint16()
        self.reserved8_1 = inputStream.read_uint8()
        self.reserved8_2 = inputStream.read_uint8()
        self.time_of_day = inputStream.read_uint32()
        self.padding = inputStream.read_uint32()


class HighFidelityHaveQuickVTP(Record):
    """Annex C 4.2.3, Table C.4 — High-Fidelity HAVE QUICK VTP record"""
    recordType: enum32 = 3000
    recordLength: uint16 = 40

    def __init__(self,
                 net_id: NetId | None = None,
                 tod_transmit_indicator: enum8 = 0,
                 padding1: uint8 = 0,
                 tod_delta: int32 = 0,
                 wod1: uint32 = 0,
                 wod2: uint32 = 0,
                 wod3: uint32 = 0,
                 wod4: uint32 = 0,
                 wod5: uint32 = 0,
                 wod6: uint32 = 0):
        self.net_id = net_id or NetId()
        self.tod_transmit_indicator = tod_transmit_indicator
        self.padding1 = padding1
        self.tod_delta = tod_delta
        self.wod1 = wod1
        self.wod2 = wod2
        self.wod3 = wod3
        self.wod4 = wod4
        self.wod5 = wod5
        self.wod6 = wod6

    def marshalledSize(self) -> int:
        return self.recordLength

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint32(self.recordType)
        outputStream.write_uint16(self.recordLength)
        self.net_id.serialize(outputStream)
        outputStream.write_uint8(self.tod_transmit_indicator)
        outputStream.write_uint8(self.padding1)
        outputStream.write_int32(self.tod_delta)
        outputStream.write_uint32(self.wod1)
        outputStream.write_uint32(self.wod2)
        outputStream.write_uint32(self.wod3)
        outputStream.write_uint32(self.wod4)
        outputStream.write_uint32(self.wod5)
        outputStream.write_uint32(self.wod6)

    def parse(self, inputStream: DataInputStream) -> None:
        assert self.recordType == inputStream.read_uint32()
        assert self.recordLength == inputStream.read_uint16()
        self.net_id.parse(inputStream)
        self.tod_transmit_indicator = inputStream.read_uint8()
        self.padding1 = inputStream.read_uint8()
        self.tod_delta = inputStream.read_int32()
        self.wod1 = inputStream.read_uint32()
        self.wod2 = inputStream.read_uint32()
        self.wod3 = inputStream.read_uint32()
        self.wod4 = inputStream.read_uint32()
        self.wod5 = inputStream.read_uint32()
        self.wod6 = inputStream.read_uint32()


class CCTTSincgarsMP(Record):
    """Annex C 6.2.3, Table C.7 — CCTT SINCGARS MP record"""

    def __init__(self,
                 fh_net_id: uint16 = 0,
                 hop_set_id: uint16 = 0,
                 lockout_set_id: uint16 = 0,
                 start_of_message: enum8 = 0,
                 clear_channel: enum8 = 0,
                 fh_sync_time_offset: uint32 = 0,
                 transmission_security_key: uint16 = 0,
                 padding: uint16 = 0):
        self.fh_net_id = fh_net_id
        self.hop_set_id = hop_set_id
        self.lockout_set_id = lockout_set_id
        self.start_of_message = start_of_message
        self.clear_channel = clear_channel
        self.fh_sync_time_offset = fh_sync_time_offset
        self.transmission_security_key = transmission_security_key
        self.padding = padding

    def marshalledSize(self) -> int:
        return 16  # bytes

    def serialize(self, outputStream: DataOutputStream) -> None:
        outputStream.write_uint16(self.fh_net_id)
        outputStream.write_uint16(self.hop_set_id)
        outputStream.write_uint16(self.lockout_set_id)
        outputStream.write_uint8(self.start_of_message)
        outputStream.write_uint8(self.clear_channel)
        outputStream.write_uint32(self.fh_sync_time_offset)
        outputStream.write_uint16(self.transmission_security_key)
        outputStream.write_uint16(self.padding)

    def parse(self, inputStream: DataInputStream) -> None:
        self.fh_net_id = inputStream.read_uint16()
        self.hop_set_id = inputStream.read_uint16()
        self.lockout_set_id = inputStream.read_uint16()
        self.start_of_message = inputStream.read_uint8()
        self.clear_channel = inputStream.read_uint8()
        self.fh_sync_time_offset = inputStream.read_uint32()
        self.transmission_security_key = inputStream.read_uint16()
        self.padding = inputStream.read_uint16()
