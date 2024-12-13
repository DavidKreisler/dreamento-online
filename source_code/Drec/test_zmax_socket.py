import datetime

from source_code.Drec.scripts.Connection.ZmaxSocket import ZmaxSocket


def test_with_zmax_socket():
    socket = ZmaxSocket()
    socket.connect()
    buf = []
    start = datetime.datetime.now()
    while datetime.datetime.now() - start < datetime.timedelta(seconds=10):
        buf.append([socket.receive_oneLineBuffer()])

    print(buf)


if __name__ == '__main__':
    test_with_zmax_socket()


