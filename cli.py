import argparse
import requests

NODE = "http://127.0.0.1:5000"


def mine(miner):

    r = requests.get(f"{NODE}/mine?miner={miner}")

    print(r.json())


def chain():

    r = requests.get(f"{NODE}/chain")

    print(r.json())


def mempool():

    r = requests.get(f"{NODE}/mempool")

    print(r.json())


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("command")

    parser.add_argument("--miner")

    args = parser.parse_args()

    if args.command == "mine":
        mine(args.miner)

    elif args.command == "chain":
        chain()

    elif args.command == "mempool":
        mempool()


if __name__ == "__main__":
    main()