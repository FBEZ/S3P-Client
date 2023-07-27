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
import time

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


def encode_s3p_frame(destination_address, command,arguments):
  """Ecodes the frame for s3p protocol 

  Args:
      destination_address (int): s3p address 
      command (string): Command name
      arguments (array of int): additional arguments

  Raises:
      ValueError: if the command is not recognized

  Returns:
      bytes array: payload to be used in an ethernet frame
  """
  if(command not in S3P_commands.commands.keys()):
        raise ValueError("The command is not recognized")
  argument = bytes([])
  for k in arguments:
        #print(k)
        #print(k.to_bytes(4,'big'))
        argument = argument + k.to_bytes(4,'big')
        
  return int(destination_address,16).to_bytes(4,"big") + \
        settings.S3P_settings["s3p_address"] + \
        int(S3P_commands.commands[command]).to_bytes(3,'big') + \
        len(arguments).to_bytes(1,'big') + \
        argument


def get_arguments_from_command(command):
  """Returns the arguments from the command, if required

  Args:
      command (string): command
  """
  args = []
  if(command == 'STO'):
     time_t = time.time()
     time_s = int(time_t)
     time_us = round(1e6*(time_t%1))
     args.append(time_s)
     args.append(time_us)

  return args

def main():
  ifname = settings.ethernet_settings["ethernet_interface"]
  dstmac = settings.ethernet_settings["destination_mac"]
  ethtype = settings.ethernet_settings["ethertype"]

  f=open("command_list.txt","r")
  for k in f.readlines():
      
      if(len(k.split())<2):
        raise ValueError("Too few arguments")
      command = k.split()[0]
      destination_address = k.split()[1]

      if(len(k.split())>2):
        arguments = k.split()[2:] # all other arguments except the first
      else:
        arguments = get_arguments_from_command(command)
      #print(arguments)
      
      payload = encode_s3p_frame(destination_address,command, arguments)
      #print(payload)
      print("\nSending command "+command+" to "+destination_address + " with arguments ")
      print(arguments)
      send_frame(ifname, dstmac, ethtype, payload)
      print("Sent! ***********")
      time.sleep(1)

if __name__ == "__main__":
    main()
