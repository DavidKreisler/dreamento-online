import struct


class TCP_Packet:
    def __init__(self, tcp_packet, iph_length):
        tcp_header = tcp_packet[iph_length: iph_length + 20]
        tcph = struct.unpack('!HHLLBBHHH', tcp_header)

        self.source_port = tcph[0]
        self.dest_port = tcph[1]
        self.sequence = tcph[2]
        self.acknowledgment = tcph[3]
        self.doff_reserved = tcph[4]
        self.tcph_length = self.doff_reserved >> 4
        self.tcp_header_length = self.tcph_length * 4

        data_offset = iph_length + self.tcp_header_length
        self.data = tcp_packet[data_offset:]
