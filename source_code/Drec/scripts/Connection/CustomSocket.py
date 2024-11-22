import os
import socket
import struct
import ctypes
import time


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


class CustomSocket:
    def __init__(self, sock=None):
        if not is_admin():
            raise EnvironmentError('program has to be launched as admin')

        self.serverConnected = False
        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_IP)

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

    def read_socket_buffer_for_port(self, port=8000):
        time_start = time.time()
        # Receive a packet
        while True:
            if (time.time() - time_start) >= 5:
                print(f'it seems there is no data available at port {port}')
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
                tcp_header = packet[iph_length:iph_length + 20]
                tcph = struct.unpack('!HHLLBBHHH', tcp_header)

                source_port = tcph[0]
                dest_port = tcph[1]
                sequence = tcph[2]
                acknowledgment = tcph[3]
                doff_reserved = tcph[4]
                tcph_length = doff_reserved >> 4
                tcp_header_length = tcph_length * 4

                if (source_port == port) or (dest_port == port):
                    # Get data if available
                    data_offset = iph_length + tcp_header_length
                    data = packet[data_offset:]
                    if not data:
                        return ''
                    return data.decode()


if __name__ == '__main__':
    sock = CustomSocket()
    print(sock.serverConnected)
