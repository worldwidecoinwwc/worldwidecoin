import socket
import threading
import json


class P2PNode:

    def __init__(self, host, port, blockchain):

        self.host = host
        self.port = port
        self.blockchain = blockchain
        self.peers = []

    # --------------------------------

    def start_server(self):

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server.bind((self.host, self.port))
        server.listen()

        print(f"P2P listening on {self.host}:{self.port}")

        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=self.handle_peer, args=(conn,))
            thread.daemon = True
            thread.start()

    # --------------------------------

    def handle_peer(self, conn):

        try:
            data = conn.recv(4096)

            if not data:
                return

            message = json.loads(data.decode())

            msg_type = message.get("type")

            if msg_type == "transaction":

                tx = message["data"]
                print("Received transaction from peer")

                self.blockchain.mempool.append(tx)

            elif msg_type == "block":

                block = message["data"]
                print("Received block from peer")

                # simple prototype: just print
                # real implementation would validate + append

        except Exception as e:
            print("Peer error:", e)

        finally:
            conn.close()

    # --------------------------------

    def connect_peer(self, host, port):

        peer = (host, port)

        if peer not in self.peers:
            self.peers.append(peer)

        print("Connected peer:", peer)

    # --------------------------------

    def broadcast_transaction(self, tx):

        message = json.dumps({
            "type": "transaction",
            "data": tx
        })

        for peer in self.peers:

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(peer)
                s.send(message.encode())
                s.close()

            except:
                pass

    # --------------------------------

    def broadcast_block(self, block):

        message = json.dumps({
            "type": "block",
            "data": block
        })

        for peer in self.peers:

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(peer)
                s.send(message.encode())
                s.close()

            except:
                pass