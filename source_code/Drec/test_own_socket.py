import datetime
from source_code.Drec.scripts.Connection.CustomSocket import CustomSocket


def test_with_own_socket():
    socket = CustomSocket()
    socket.connect()
    buf = []
    start = datetime.datetime.now()
    while datetime.datetime.now() - start < datetime.timedelta(seconds=10):
        buf.append(socket.read_socket_buffer_for_port())

    print(buf)


if __name__ == '__main__':
    test_with_own_socket()