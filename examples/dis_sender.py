#!python

__author__ = "DMcG"
__date__ = "$Jun 23, 2015 10:27:29 AM$"

import socket
import time

from io import BytesIO

from opendis.stream import DataOutputStream
from opendis.record.common import EntityIdentifier, SimulationAddress
from opendis.record.entity_information import EntityStatePdu
from opendis.RangeCoordinates import *

UDP_PORT = 3001
DESTINATION_ADDRESS = "127.0.0.1"

gps = GPS()  # conversion helper


def build_espdu() -> EntityStatePdu:
    """The demo entity: site 17 / application 23 / entity 42, marking
    'Igor3d', located in Monterey, CA facing north."""
    pdu = EntityStatePdu()

    # identity records are frozen: construct them, never mutate them
    pdu.entityID = EntityIdentifier(SimulationAddress(site=17, application=23), 42)
    pdu.marking.string = "Igor3d"

    montereyLocation = gps.llarpy2ecef(
        deg2rad(36.6),  # latitude (radians)
        deg2rad(-121.9),  # longitude (radians)
        1,  # altitude (meters)
        0,  # roll (radians)
        0,  # pitch (radians)
        0,  # yaw (radians)
    )

    pdu.entityLocation.x = montereyLocation[0]
    pdu.entityLocation.y = montereyLocation[1]
    pdu.entityLocation.z = montereyLocation[2]
    pdu.entityOrientation.psi = montereyLocation[3]
    pdu.entityOrientation.theta = montereyLocation[4]
    pdu.entityOrientation.phi = montereyLocation[5]

    return pdu


def serialize(pdu: EntityStatePdu) -> bytes:
    """The PDU as a datagram-ready byte string."""
    memoryStream = BytesIO()
    pdu.serialize(DataOutputStream(memoryStream))
    return memoryStream.getvalue()


def send():
    pdu = build_espdu()
    print("Entity state pdu type is ", pdu.pduType)
    data = serialize(pdu)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udpSocket:
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            udpSocket.sendto(data, (DESTINATION_ADDRESS, UDP_PORT))
            print("Sent {}. {} bytes".format(pdu.__class__.__name__, len(data)))
            time.sleep(1)


if __name__ == "__main__":
    send()
