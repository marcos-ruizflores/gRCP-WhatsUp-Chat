import grpc
import chat_pb2
import chat_pb2_grpc
import sys
import threading
import time

nickname = sys.argv[2]

def poll_messages(stub):
    last = 0
    while True:
        resp = stub.getMessages(chat_pb2.Empty())
        for line in resp.lines[last:]:
            print(line, end="")
        last = len(resp.lines)
        time.sleep(1)

def main():
    channel = grpc.insecure_channel(sys.argv[1] + ":50051")
    stub = chat_pb2_grpc.ChatServiceStub(channel)

    print(f"Welcome {nickname}!")

    # hilo para recibir mensajes
    threading.Thread(target=poll_messages, args=(stub,), daemon=True).start()

    # escribir mensajes
    while True:
        text = input()
        stub.sendMessage(chat_pb2.Message(nickname=nickname, text=text))

if __name__ == "__main__":
    main()
