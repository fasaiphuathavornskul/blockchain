"""
Blockchain Practice from Hackernoon
Author: Fasai Phuathavornskul
"""
from time import time
import json
import hashlib

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
    previous_hash: <str??> (hexcode)
    """

    def __init__(self):
        self.blockchain = []
        self.transactions = []

        # Initialize genesis block TODO what proof and hash?
        gen_block = self.new_block(proof=100, previous_hash=1)
        self.blockchain.append(gen_block)

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
        proof = 1
        while not self.proof_valid(previous_proof, proof):
            proof += 1

        return proof

    @staticmethod
    def proof_valid(previous_proof, proof):
        guess_as_string = f'{previous_proof}{proof}'.encode() #TODO lookkup syntax multiply?
        guess = hashlib.sha256(guess_as_string).hexdigest()
        return guess[:4] == "0000"

    @property
    def last_block(self):
        return self.blockchain[-1]


"""
Setting up endpoints with Flask
"""

