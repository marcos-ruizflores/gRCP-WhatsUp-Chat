import grpc
from concurrent import futures
import time
import ast
import chat_pb2
import chat_pb2_grpc
from datetime import datetime
import threading

CHAT_FILE = "chatlog.txt"


class ChatService(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        self.messages = []
        self.lock = threading.Lock()
        self.server_clock = 0
        self.server_id = "server"
        self.connected = {}
        self._load_chatlog()

    @staticmethod
    def _happens_before(clock_a, clock_b):
        """Return True if clock_a happens-before clock_b."""
        keys = set(clock_a.keys()) | set(clock_b.keys())
        less = False
        for key in keys:
            a = clock_a.get(key, 0)
            b = clock_b.get(key, 0)
            if a > b:
                return False
            if a < b:
                less = True
        return less

    # ordena los mensajes por vector clock
    def _ordered_messages_locked(self):

        remaining = list(self.messages)
        ordered = []

        while remaining:
            ready_indexes = []
            for idx, (msg, _) in enumerate(remaining):
                if not any(
                        self._happens_before(other_msg.vector_clock, msg.vector_clock)
                        for j, (other_msg, _) in enumerate(remaining)
                        if j != idx
                ):
                    ready_indexes.append((idx, remaining[idx][1]))

            if not ready_indexes:
                ready_indexes = list(enumerate([rec for _, rec in remaining]))

            ready_indexes.sort(key=lambda pair: (pair[1], pair[0]))
            chosen_idx = ready_indexes[0][0]
            ordered.append(remaining.pop(chosen_idx)[0])

        return ordered

    def sendMessage(self, request, context):
        ts = request.timestamp or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        incoming_clock = dict(request.vector_clock)
        if request.nickname not in incoming_clock:
            incoming_clock[request.nickname] = 1

        self.server_clock += 1
        incoming_clock[self.server_id] = self.server_clock

        message = chat_pb2.Message(
            nickname=request.nickname,
            text=request.text,
            timestamp=ts,
            vector_clock=incoming_clock,
            ephemeral=request.ephemeral,
        )

        with self.lock:
            self.messages.append((message, time.time()))

        if not request.ephemeral:
            line = f"{ts} {request.nickname}: {request.text} | vc={incoming_clock}\n"
            with open(CHAT_FILE, "a") as f:
                f.write(line)

        return chat_pb2.SendResponse(ok=True)

    def getMessages(self, request, context):
        now = time.time()
        with self.lock:
            if request.nickname:
                self.connected[request.nickname] = now
            stale_cutoff = now - 30
            self.connected = {
                user: ts for user, ts in self.connected.items() if ts >= stale_cutoff
            }
            ordered_messages = self._ordered_messages_locked()
            connected_users = sorted(self.connected.keys())
        return chat_pb2.MessageList(messages=ordered_messages, connected_users=connected_users)

    def disconnect(self, request, context):
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        with self.lock:
            self.connected.pop(request.nickname, None)
            self.server_clock += 1
            vc = {self.server_id: self.server_clock, request.nickname: 1}
            msg = chat_pb2.Message(
                nickname=request.nickname,
                text="se ha desconectado",
                timestamp=ts,
                vector_clock=vc,
                ephemeral=True,
            )
            self.messages.append((msg, time.time()))
        return chat_pb2.Empty()

    def _load_chatlog(self):
        """Load existing chat log into memory to serve history."""
        try:
            with open(CHAT_FILE, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            return

        loaded = []
        for idx, line in enumerate(lines):
            parsed = self._parse_log_line(line.strip())
            if parsed is None:
                continue
            msg = chat_pb2.Message(
                nickname=parsed["nickname"],
                text=parsed["text"],
                timestamp=parsed["timestamp"],
                vector_clock=parsed["vector_clock"],
                ephemeral=False,
            )
            loaded.append((msg, idx))

        with self.lock:
            self.messages.extend(loaded)
            self.server_clock = max(self.server_clock, len(self.messages))

    def _parse_log_line(self, raw):
        """Best-effort parser for prior log formats."""
        if not raw:
            return None

        vc = {}
        body = raw
        if "| vc=" in raw:
            body, vc_part = raw.rsplit("| vc=", 1)
            try:
                vc = ast.literal_eval(vc_part.strip())
            except Exception:
                vc = {}

        body = body.strip()
        ts = ""
        nickname = ""
        text = body

        parts = body.split(" ", 2)
        if len(parts) == 3 and ":" in parts[2]:
            ts = f"{parts[0]} {parts[1]}"
            rest = parts[2]
        else:
            if len(parts) >= 2 and ":" in parts[1]:
                ts = parts[0]
                rest = " ".join(parts[1:])
            else:
                rest = body

        if ": " in rest:
            nickname, text = rest.split(": ", 1)
        else:
            nickname = "unknown"

        # If vector clock missing, seed with server clock to keep order stable.
        if not vc:
            vc = {self.server_id: len(self.messages) + 1}

        return {"timestamp": ts, "nickname": nickname, "text": text, "vector_clock": vc}


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Server running on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
