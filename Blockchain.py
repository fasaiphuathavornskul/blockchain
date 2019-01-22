"""
Blockchain Practice from Hackernoon
Author: Fasai Phuathavornskul
"""
from time import time
import json
import hashlib
from urllib.parse import urlparse
import requests

class Blockchain:
    """
    A block looks like:
    index: <int>
    timestamp: <longint>
    transaction: <list>
        sender: <str>
        recipient: <str>
        amount: <double>
    proof: <int>
    previous_hash: <str>
    """

    def __init__(self):
        self.blockchain = []
        self.transactions = []
        self.nodes = set()

        # Initialize genesis block TODO what proof and hash? Does proof always have to be positive int?
        gen_block = self.new_block(proof=100, previous_hash=1)

    def register(self, address):
        # address is the url of node: http://000.000.0.0:xxxx
        parsed_url = urlparse(address) # dissects the address into different parts (scheme, netloc, query, path ...)
        self.nodes.add(parsed_url.netloc) # grabs just the IP address and port

    def new_transaction(self, sender, recipient, amount):
        self.transactions.append({
            "sender": sender,
            "recipient": recipient,
            "amount": amount
        })
        return self.last_block['index'] + 1 # TODO why?

    def new_block(self, proof, previous_hash=None):
        block = {
            "index": len(self.blockchain) + 1,
            "timestamp": time(),
            "transaction": self.transactions,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.last_block)
        }

        self.transactions = []
        self.blockchain.append(block)
        return block

    @staticmethod
    def hash(block):
        block_as_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_as_string).hexdigest()

    def proof_of_work(self, previous_proof):
        # find integer proof whose hash of f(proof, previous_proof) meets a specified condition
        proof = 0
        while not self.proof_valid(previous_proof, proof):
            proof += 1

        return proof

    @staticmethod
    def proof_valid(previous_proof, proof):
        guess_as_string = f'{previous_proof}{proof}'.encode()
        guess = hashlib.sha256(guess_as_string).hexdigest()
        return guess[:4] == "0000"

    @property
    def last_block(self):
        return self.blockchain[-1]

    # Consensus: resolve conflicts by replacing chain with longest valid chain among neighbors
    def resolve(self):
        neighbors = self.nodes
        new_chain = None

        max_length = len(self.blockchain)

        for nbr in neighbors:
            response = requests.get(f'http://{nbr}/chain')

            # check that response is valid
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # if response if valid, check if nbr's chain is longer and valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.blockchain = new_chain
            return True

        return False

    # Check if the chain is valid
    def valid_chain(self, chain):
        idx = 1
        last_block = chain[0]

        while idx < len(chain):
            # check that current block's "previous_hash" matches the hash of the previous block
            block = chain[idx]
            if block['previous_hash'] != self.hash(last_block): # is not vs. !=
                return False

            # check that proof is correct
            if not self.proof_valid(last_block['proof'], block['proof']):
                return False

            last_block = block
            idx += 1

        return True


"""
Setting up endpoints with Flask:
/transactions/new: add new transaction
/mine: create new block
/chain: return blockchain
/nodes/register: register a new node
/nodes/resolve: resolve conflicts among nodes
"""

from flask import Flask, jsonify, request
from uuid import uuid4

# Instantiate node
app = Flask(__name__)

# Generate globally unique address
node_id = str(uuid4()).replace('-', '') # node ID for when the network rewards node with coin

# Instantiate blockchain
blockchain = Blockchain()


@app.route('/nodes/register', methods=['POST'])
def register():
    values = request.get_json()
    nodes = values.get('nodes')

    if not nodes:
        return "No valid nodes present", 400

    for node in nodes:
        blockchain.register(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }

    return jsonify(response)


@app.route('/mine', methods=['GET'])
def mine():
    # calculate proof of work
    proof = blockchain.proof_of_work(blockchain.last_block['proof'])

    # reward miner by adding transaction giving 1 coin
    blockchain.new_transaction(
        sender="0",
        recipient=node_id, # our node
        amount=1
    )

    # add new block to the chain
    new_block = blockchain.new_block(proof, blockchain.hash(blockchain.last_block))

    response = {
        'message': "New Block Forged",
        'index': new_block['index'],
        'transactions': new_block['transaction'],
        'proof': new_block['proof'],
        'previous_hash': new_block['previous_hash']
    }

    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # check that all fields are there
    if not values:
        return 'No JSON. Check type of body', 400
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to block {index}'}
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.blockchain,
        'length': len(blockchain.blockchain)
    }

    return jsonify(response), 200 # JSON dumps with MIME headers for app


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.blockchain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.blockchain
        }

    return jsonify(response), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)



