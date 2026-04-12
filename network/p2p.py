import socket
import json
import threading


def encode_message(msg_type, data):
    return json.dumps({
        "type": msg_type,
        "data": data
    }).encode()


def broadcast_transaction(peers, tx):

    message = encode_message("transaction", tx.to_dict())

    for peer in peers:
        try:
            sock = socket.socket()
            sock.connect(peer)
            sock.send(message)
            sock.close()
        except Exception as e:
            print(f"Failed to broadcast TX to {peer}: {e}")


def broadcast_block(peers, block):

    block_dict = {
        "index": block.index,
        "prev_hash": block.prev_hash,
        "transactions": [tx.to_dict() for tx in block.transactions],
        "timestamp": block.timestamp,
        "difficulty": block.difficulty,
        "nonce": block.nonce,
        "hash": block.hash
    }

    message = encode_message("block", block_dict)

    for peer in peers:
        try:
            sock = socket.socket()
            sock.connect(peer)
            sock.send(message)
            sock.close()
        except Exception as e:
            print(f"Failed to broadcast block to {peer}: {e}")


def request_blocks(peer, start_index, end_index):
    """Send getblocks request to peer, return blocks list"""
    try:
        message = encode_message("getblocks", {
            "start_index": start_index,
            "end_index": end_index
        })

        sock = socket.socket()
        sock.connect(peer)
        sock.send(message)

        response_data = sock.recv(65536)
        sock.close()

        if response_data:
            response = json.loads(response_data.decode())
            if response.get("type") == "blocks":
                return response.get("data", [])
    except Exception as e:
        print(f"Failed to request blocks from {peer}: {e}")

    return []