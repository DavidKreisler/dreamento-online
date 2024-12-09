import os
import socket
import struct
import ctypes
import time

from scripts.Utils.TCP_Packet import TCP_Packet


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


class CustomSocket:
    def __init__(self, sock=None, port=8000):
        if not is_admin():
            raise EnvironmentError('program has to be launched as admin')

        self.serverConnected = False
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)

        self.port = port

        self.packet_buffer = {}
        self.last_seq_number = None
        self.expected_seq_number = None
        self.ordered_data = b''

    def sendString(self, msg):
        print('sending is not allowed in this class. It solely reads the transmition on a socket.')

    def connect(self, host='127.0.0.1', port=0):
        try:
            self.sock.bind((host, port))
            self.serverConnected = True

            # Include IP headers
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

            # Enable promiscuous mode
            if os.name == "nt":
                self.sock.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

        except socket.error as e:
            print(e)
            self.serverConnected = False

    def send(self, msg):
        raise NotImplementedError('sending is not possible with a socket.SOCK_RAW')

    def read_socket_buffer_for_port(self):
        time_start = time.time()
        # Receive a packet
        while True:
            if (time.time() - time_start) >= 5:
                print(f'it seems there is no data available at port {self.port}')
                return ''

            packet, addr = self.sock.recvfrom(65565)

            # Extract IP header
            ip_header = packet[0:20]
            iph = struct.unpack('!BBHHHBBH4s4s', ip_header)

            version_ihl = iph[0]
            version = version_ihl >> 4
            ihl = version_ihl & 0xF
            iph_length = ihl * 4

            ttl = iph[5]
            protocol = iph[6]
            s_addr = socket.inet_ntoa(iph[8])
            d_addr = socket.inet_ntoa(iph[9])

            # Extract TCP header if protocol is TCP
            if protocol == 6:
                tcp_packet = TCP_Packet(packet, iph_length)
                if tcp_packet.source_port == self.port:
                    ret = self._handle_tcp_packet(tcp_packet)
                    return ret

    def _process_payload(self, payload):
        ret = payload.decode()
        return ret

    def _handle_tcp_packet(self, packet: TCP_Packet):
        if not packet.data:
            return ''

        # SEQ handling
        if self.expected_seq_number is None:
            # Initialize expected sequence number
            self.expected_seq_number = packet.sequence + len(packet.data)
            ret = self._process_payload(packet.data)
            return ret

        elif packet.sequence == self.expected_seq_number:
            # Process in-order packet
            accumulated_data = self._process_payload(packet.data)
            self.expected_seq_number += len(packet.data)

            # Check for subsequent buffered packets
            while self.expected_seq_number in self.packet_buffer:
                buffered_payload = self.packet_buffer.pop(self.expected_seq_number)
                accumulated_data.append(self._process_payload(buffered_payload))
                self.expected_seq_number += len(buffered_payload)

            return accumulated_data

        elif packet.sequence > self.expected_seq_number:
            # Buffer out-of-order packet
            self.packet_buffer[packet.sequence] = packet.data
            return ''

        else:
            print('past packet!')
            print(self.expected_seq_number, packet.sequence)
            return ''



if __name__ == '__main__':
    sock = CustomSocket()
    sock.connect('127.0.0.1', 8000)
    while True:
        data = sock.read_socket_buffer_for_port()
        print(data)
