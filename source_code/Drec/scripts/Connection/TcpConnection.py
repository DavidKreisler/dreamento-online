class Connection:
    def __init__(self, src_host, src_port, dst_host, dst_port, first_seq: int = None):
        self.src_host = src_host
        self.src_port = src_port
        self.dst_host = dst_host
        self.dst_port = dst_port
        if not first_seq:
            self.expected_seq = None
        else:
            self.expected_seq = first_seq + 1
        self.packet_buffer = {}

    def get_id(self):
        return self.src_host, self.src_port, self.dst_host, self.dst_port

    def get_inv_id(self):
        return self.dst_host, self.dst_port, self.src_host, self.src_port

    def parse_payload(self, seq, payload, data_queue):
        # past or future packets
        if self.expected_seq is None:
            self.expected_seq = seq

        if seq < self.expected_seq or seq > self.expected_seq:
            self.packet_buffer[seq] = payload
            return None

        # current packets
        self.expected_seq += len(payload)
        data_queue.put(payload)

        # handle buffer
        while self.expected_seq in self.packet_buffer:
            buffered_payload = self.packet_buffer.pop(self.expected_seq)
            data_queue.put(buffered_payload)
            self.expected_seq += len(buffered_payload)


if __name__ == "__main__":
    pass

