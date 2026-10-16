#!python

__author__ = "mcgredo"
__date__ = "$Jun 25, 2015 12:10:26 PM$"

import socket
import time
from typing import cast

from opendis.record.entity_information import EntityStatePdu
from opendis.RangeCoordinates import *
from opendis.record.factory import createPdu

UDP_PORT = 3001

gps = GPS()


def describe_datagram(data: bytes) -> str:
    """Parse one datagram via the factory and render a human-readable
    report; ESPDUs get the full geodetic decode, anything else a
    one-line summary."""
    pdu = createPdu(data)

    if pdu.pduType == 1:  # Entity State [UID 4]
        pdu = cast(EntityStatePdu, pdu)  # for static checkers
        loc = (
            pdu.entityLocation.x,
            pdu.entityLocation.y,
            pdu.entityLocation.z,
            pdu.entityOrientation.psi,
            pdu.entityOrientation.theta,
            pdu.entityOrientation.phi,
        )

        body = gps.ecef2llarpy(*loc)

        return (
            "Received {}\n".format(pdu.__class__.__name__)
            + " Id        : {}\n".format(pdu.entityID.entityNumber)
            + " Latitude  : {:.2f} degrees\n".format(rad2deg(body[0]))
            + " Longitude : {:.2f} degrees\n".format(rad2deg(body[1]))
            + " Altitude  : {:.0f} meters\n".format(body[2])
            + " Yaw       : {:.2f} degrees\n".format(rad2deg(body[3]))
            + " Pitch     : {:.2f} degrees\n".format(rad2deg(body[4]))
            + " Roll      : {:.2f} degrees\n".format(rad2deg(body[5]))
        )

    return "Received {}, {} bytes".format(pdu.__class__.__name__, len(data))


def recv(udpSocket: socket.socket):
    print("Reading from socket...")
    data = udpSocket.recv(1024)  # buffer size in bytes
    print(describe_datagram(data), flush=True)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udpSocket:
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udpSocket.bind(("", UDP_PORT))
        print("Listening for DIS on UDP socket {}".format(UDP_PORT))
        while True:
            recv(udpSocket)
            time.sleep(0.5)


if __name__ == "__main__":
    main()
