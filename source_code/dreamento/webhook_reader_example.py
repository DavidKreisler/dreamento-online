from flask import Flask, request


store = []

app = Flask(__name__)


@app.route('/webhookcallback/sleepstate', methods=['POST'])
def sleepStateHook():
    state = request.values.get('state')
    epoch = request.values.get('epoch')

    store.append((epoch, state))

    print(f'state: {state}')
    print('epoch: ' + str(epoch))

    return "received"


@app.route('/webhookcallback/hello', methods=['POST'])
def helloHook():
    msg = request.values.get('hello')
    print(f'hello message sent. message: {msg}')

    return "received"


@app.route('/webhookcallback/finished', methods=['POST'])
def recordingFinished():
    with open('received_sleep_states.txt') as f:
        f.writelines(store)
    store = 0


if __name__ == '__main__':
    app.run()
