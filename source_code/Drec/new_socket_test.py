from scripts.Connection.TcpSniffSocket import TcpSniffSocket


if __name__ == '__main__':
    sock = TcpSniffSocket()
    sock.connect()
    while True:
        print(sock.read_one_line())
