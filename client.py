import grpc
import chat_pb2
import chat_pb2_grpc
import curses
import threading
import time
import sys

nickname = sys.argv[2]

messages = []
lock = threading.Lock()

def poll_messages(stub):
    last = 0
    while True:
        resp = stub.getMessages(chat_pb2.Empty())
        new = resp.lines[last:]

        if new:
            with lock:
                for line in new:
                    messages.append(line.rstrip("\n"))
        last = len(resp.lines)
        time.sleep(1)

def curses_main(stdscr, stub):
    curses.curs_set(1)
    stdscr.nodelay(True)

    input_buffer = ""

    while True:
        stdscr.clear()

        h, w = stdscr.getmaxyx()
        max_msgs = h - 3
        with lock:
            to_show = messages[-max_msgs:]

        for i, msg in enumerate(to_show):
            stdscr.addstr(i, 0, msg)

        stdscr.addstr(h - 2, 0, f"{nickname} --> {input_buffer}")

        # Refresh
        stdscr.refresh()
        try:
            ch = stdscr.getch()
        except:
            ch = -1

        if ch == -1:
            time.sleep(0.05)
            continue

        if ch in (10, 13):
            if input_buffer.strip():
                stub.sendMessage(chat_pb2.Message(
                    nickname=nickname,
                    text=input_buffer
                ))
            input_buffer = ""
        elif ch in (263, 127):
            input_buffer = input_buffer[:-1]
        elif 32 <= ch <= 126:
            input_buffer += chr(ch)

def main():
    channel = grpc.insecure_channel(sys.argv[1] + ":50051")
    stub = chat_pb2_grpc.ChatServiceStub(channel)
    threading.Thread(target=poll_messages, args=(stub,), daemon=True).start()
    curses.wrapper(curses_main, stub)

if __name__ == "__main__":
    main()
