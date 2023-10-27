import socket
import asyncio
import random
import json
import sys
import tkinter as tk
from tkinter import ttk

class Client:

    def __init__(self, client, address):
        self.address = address
        self.answer = None
        self.guesses = []
        self.client = client
        AddrToClient[address] = client

    def append(self, guess):
        self.guesses.append(guess)

    def gen_word(self):
        self.answer = random.choice(answers)
        self.guesses = []

    def close(self):
        AddrToClient.pop(self.address)
        self.client.close()

class Message:

    def __init__(self):
        self.json_size = None
        self.header = None
        self.content_size = None
        self.content = None
        self.encoded_content = None
        self.type = None

    async def read(self, client, loop):
        self.json_size = int.from_bytes(await loop.sock_recv(client, 2), "big")
        self.header = json.loads((await loop.sock_recv(client, self.json_size)).decode("utf-8"))
        self.content_size = self.header['content_size']
        self.type = self.header['response_type']
        if self.content_size != 0:
            self.encoded_content = await loop.sock_recv(client, self.content_size)
            self.content = self.encoded_content.decode("utf-8")
        else:
            self.content = ""
            self.encoded_content = self.content.encode("utf-8")

    def write(self, type, content):
        self.type = type
        self.content = content
        self.encoded_content = self.content.encode("utf-8")
        self.content_size = len(self.encoded_content)
        self.header = json.dumps({'content_size': self.content_size, 'response_type': type}, ensure_ascii=False).encode("utf-8")
        self.json_size = len(self.header)

    async def send(self, client, loop):
        await loop.sock_sendall(client, self.json_size.to_bytes(2, "big"))
        await loop.sock_sendall(client, self.header)
        await loop.sock_sendall(client, self.encoded_content)


async def handle_guess(client, guess):
    ans = client.answer
    msg = Message()
    guess = guess.lower()
    print(guess)
    if (len(ans) != 5) or not (guess.isalpha()) or not (guess in words):
        msg.write("invalid_guess", str(len(client.guesses)))
        return msg
    client.append(guess)
    mask = ["0"] * 5
    cnt_ans, cnt_guess = dict(), dict()
    for i in range(5):
        cnt_ans[ans[i]] = cnt_ans.get(ans[i], 0) + 1
    for i in range(5):
        if ans[i] == guess[i]:
            mask[i] = "1"
            cnt_guess[guess[i]] = cnt_guess.get(guess[i], 0) + 1
    for i in range(5):
        if not mask[i] == "1":
            if cnt_guess.get(guess[i], 0) < cnt_ans.get(guess[i], 0):
                mask[i] = "2"
            cnt_guess[guess[i]] = cnt_guess.get(guess[i], 0) + 1
    mask = "".join(mask) + str(len(client.guesses))
    msg.write("valid_guess", mask)
    return msg


async def start_game(client):
    client.gen_word()
    print(client.answer)
    msg = Message()
    msg.write("conn_acc", "")
    return msg

async def end_game(client):
    client.close()

async def show_ans(client):
    msg = Message()
    msg.write("lost", client.answer)
    return msg


async def run_server():

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    HOST = "172.15.5.172"
    PORT = 8000

    server.bind((HOST, PORT))

    loop = asyncio.get_event_loop()

    while True:

        server.listen(0)
        client, addr = await loop.sock_accept(server)
        client = Client(client, addr)
        loop.create_task(handle_client(client))

async def handle_client(client):

    loop = asyncio.get_event_loop()
    end = False

    while True:

        msg = Message()
        await msg.read(client.client, loop)

        if msg.type == 'start': response = await start_game(client)
        elif msg.type == 'guess': response = await handle_guess(client, msg.content)
        elif msg.type == 'lost': response = await show_ans(client)
        elif msg.type == 'end':
            await end_game(client)
            end = True
        else:
            print("Error!")
            sys.exit(1)
        if end:
            print(f"Connection with {client.address} closed!")
            break
        print(response.content)
        await response.send(client.client, loop)


AddrToClient = {}

word_file = open("wordlist.txt")
words = word_file.read().splitlines()

answer_file = open("answerlist.txt")
answers = answer_file.read().splitlines()


asyncio.run(run_server())