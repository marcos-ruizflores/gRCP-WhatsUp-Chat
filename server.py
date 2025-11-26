import grpc
from concurrent import futures
import time
import chat_pb2
import chat_pb2_grpc
from datetime import datetime

CHAT_FILE = "chatlog.txt"

class ChatService(chat_pb2_grpc.ChatServiceServicer):
    from datetime import datetime

    def sendMessage(self, request, context):
        ts = datetime.now().strftime("%H:%M")
        line = f"{ts} {request.nickname}: {request.text}\n"

        with open(CHAT_FILE, "a") as f:
            f.write(line)

        return chat_pb2.SendResponse(ok=True)

    def getMessages(self, request, context):
        try:
            with open(CHAT_FILE, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []
        return chat_pb2.MessageList(lines=lines)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Server running on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
