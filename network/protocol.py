import json


def encode_message(msg_type, data):

    return json.dumps({
        "type": msg_type,
        "data": data
    }).encode()


def decode_message(message):

    return json.loads(message.decode())