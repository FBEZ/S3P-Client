#!/usr/bin/env python3

# Usage: ethsend.py eth0 ff:ff:ff:ff:ff:ff 'Hello everybody!'
#        ethsend.py eth0 06:e5:f0:20:af:7a 'Hello 06:e5:f0:20:af:7a!'
#
# Note: CAP_NET_RAW capability is required to use SOCK_RAW

import fcntl
import socket
import struct
import sys
import settings
import S3P_commands

def send_frame(ifname, dstmac, eth_type, payload):
    # Open raw socket and bind it to network interface.
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    s.bind((ifname, 0))

    # Get source interface's MAC address.
    info = fcntl.ioctl(s.fileno(),
                       0x8927,
                       struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
    srcmac = ':'.join('%02x' % b for b in info[18:24])

    # Build Ethernet frame
    #payload_bytes = payload.encode('utf-8')
    payload_bytes=payload
    assert len(payload_bytes) <= 1500  # Ethernet MTU

    frame = human_mac_to_bytes(dstmac) + \
            human_mac_to_bytes(srcmac) + \
            eth_type + \
            payload_bytes

    # Send Ethernet frame
    return s.send(frame)

def human_mac_to_bytes(addr):
    return bytes.fromhex(addr.replace(':', ''))


def encode_s3p_frame(destination_address, command,argument):
    if(command not in S3P_commands.commands.keys()):
        raise ValueError("The command is not recognized")
    return destination_address + \
        settings.S3P_settings["s3p_address"] + \
        S3P_commands.commands[command] + \
        argument


def main():
  ifname = settings.ethernet_settings["ethernet_interface"]
  dstmac = settings.ethernet_settings["destination_mac"]
  destination_address = bytes([0x1,0x2,0x3,0x4])
  argument = bytes([0x0,0x1,0xFF,0xCA,0xfe])
  payload = encode_s3p_frame(destination_address,"WSH", argument)
  ethtype = settings.ethernet_settings["ethertype"] 
  send_frame(ifname, dstmac, ethtype, payload)

if __name__ == "__main__":
    main()
