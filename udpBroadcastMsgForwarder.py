# The MIT License (MIT)
# Copyright (c) 2020 Brad Drehmer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.

import os
import re
import socket
import struct

from subprocess import check_output

HDHR_NAME = 'HDHR'
DEVICE_DISCOVERY_PORT = 65001
wifi_ip = check_output(["hostname", "-I"]).decode("utf-8").split(" ")[0]
print(f'found WiFi IP: {wifi_ip}')
FWD_UDP_PORT = 65002
raw_network_scan = [
  re.findall('^[\w\?\.]+|(?<=\s)\([\d\.]+\)|(?<=at\s)[\w\:]+', i) for i in os.popen('arp -a')
]
network_scan = [dict(zip(['NAME', 'LAN_IP', 'MAC_ADDRESS'], i)) for i in raw_network_scan]
network_scan = [{**i, **{'LAN_IP':i['LAN_IP'][1:-1]}} for i in network_scan]
print(f'network_scan: {network_scan}')

hdhr_ip = None
for network_peer in network_scan:
    if network_peer['NAME'] == HDHR_NAME:
        hdhr_ip = network_peer['LAN_IP']
        print(f'found {HDHR_NAME} IP: {hdhr_ip}')
        break

if not hdhr_ip:
    print('could not find HDHR')
    exit()

MCAST_GRP = '224.1.1.1'   # multi-cast group (don't modify)
MCAST_PORT = DEVICE_DISCOVERY_PORT
IS_ALL_GROUPS = True

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
if IS_ALL_GROUPS:
    # on this port, receives ALL multicast groups
    sock.bind(('', MCAST_PORT))
else:
    # on this port, listen ONLY to MCAST_GRP
    sock.bind((MCAST_GRP, MCAST_PORT))
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

while True:
    data, requestor = sock.recvfrom(1024)
    print(f'got query from {requestor}')
    # forward query to HDHR
    hdhr_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    hdhr_sock.bind((wifi_ip, FWD_UDP_PORT))
    print('forwarding to HDHR')
    hdhr_sock.sendto(data, (hdhr_ip, DEVICE_DISCOVERY_PORT))
    hdhr_reply_data, (hdhr_addr, hdhr_port) = hdhr_sock.recvfrom(1024)
    print(f'HDHR reply from {hdhr_addr}:{hdhr_port}')
    print('forwarding HDHR reply to original requestor')
    sock.sendto(hdhr_reply_data, requestor)
    hdhr_sock.close()

