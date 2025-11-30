import grpc
import chat_pb2
import chat_pb2_grpc
import sys
import threading
import time
import curses
from collections import defaultdict
from datetime import datetime
import signal

nickname = sys.argv[2]
messages = []
lock = threading.Lock()
vector_clock = defaultdict(int)
connected_users = []
user_colors = {}
color_palette = [
    curses.COLOR_GREEN,
    curses.COLOR_CYAN,
    curses.COLOR_MAGENTA,
    curses.COLOR_YELLOW,
    curses.COLOR_BLUE,
    curses.COLOR_WHITE,
]


def get_color_for_user(user):
    if user not in user_colors:
        idx = len(user_colors) % len(color_palette)
        user_colors[user] = idx + 5  # start after predefined pairs
        curses.init_pair(user_colors[user], color_palette[idx], curses.COLOR_BLACK)
    return curses.color_pair(user_colors[user])


def poll_messages(stub):
    while True:
        resp = stub.getMessages(chat_pb2.ClientInfo(nickname=nickname))

        formatted = []
        merged_clock = defaultdict(int)
        for msg in resp.messages:
            for node, value in msg.vector_clock.items():
                merged_clock[node] = max(merged_clock[node], value)
            formatted.append(f"{msg.timestamp} {msg.nickname}: {msg.text}")

        with lock:
            messages.clear()
            messages.extend(formatted)
            for node, value in merged_clock.items():
                vector_clock[node] = max(vector_clock[node], value)
            connected_users[:] = list(resp.connected_users)
        time.sleep(1)


def curses_main(stdscr, stub):
    curses.curs_set(1)
    stdscr.nodelay(True)

    # añadimos los colores que queremos mirar de si cambiar para que quede más bonito
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    input_buffer = ""

    while True:
        stdscr.clear()

        # size de la pantalla
        h, w = stdscr.getmaxyx()
        sidebar_width = 20
        max_msgs = h - 3
        main_width = max(10, w - sidebar_width - 2)

        with lock:
            to_show = messages[-max_msgs:]
            users_snapshot = list(connected_users)

        for i, msg in enumerate(to_show):
            try:
                # formato de la string que mostramos "YYYY-MM-DD HH:MM:SS nombre: texto"
                parts = msg.split(" ", 3)
                if len(parts) >= 4 and parts[2].endswith(":"):
                    ts = f"{parts[0]} {parts[1]}"
                    user = parts[2][:-1]
                    text = parts[3] if len(parts) > 3 else ""
                elif len(parts) >= 3 and ":" in parts[2]:
                    ts = f"{parts[0]} {parts[1]}"
                    user, text = parts[2].split(": ", 1)
                else:
                    ts = ""
                    user = "?"
                    text = msg

                # Determinar color de la persona
                if user.startswith(nickname):
                    color_user = curses.color_pair(2)  # verde
                else:
                    color_user = get_color_for_user(user)

                if ts:
                    stdscr.addstr(i, 0, ts + " ", curses.color_pair(1))

                offset = len(ts) + 1 if ts else 0
                stdscr.addstr(i, offset, user + ": ", color_user)

                # mostramos el mensaje
                stdscr.addstr(i, offset + len(user) + 2, text)

            except Exception:
                stdscr.addstr(i, 0, msg)

        # Lista dinámica de usuarios conectados
        sidebar_x = main_width + 1
        stdscr.vline(0, sidebar_x - 1, "|", h - 1)
        stdscr.addstr(0, sidebar_x, "Conectados:", curses.color_pair(1))
        for idx, user in enumerate(users_snapshot, start=1):
            color = curses.color_pair(2) if user == nickname else get_color_for_user(user)
            stdscr.addstr(idx, sidebar_x, user, color)

        stdscr.addstr(h - 2, 0, f"{nickname} --> ", curses.color_pair(4))
        stdscr.addstr(h - 2, len(nickname) + 5, input_buffer)

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
                with lock:
                    vector_clock[nickname] += 1
                    payload_clock = dict(vector_clock)
                stub.sendMessage(
                    chat_pb2.Message(
                        nickname=nickname,
                        text=input_buffer,
                        timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        vector_clock=payload_clock,
                    )
                )
            input_buffer = ""


        elif ch in (263, 127):
            input_buffer = input_buffer[:-1]


        elif 32 <= ch <= 126:
            input_buffer += chr(ch)


def main():
    channel = grpc.insecure_channel(sys.argv[1] + ":50051")
    stub = chat_pb2_grpc.ChatServiceStub(channel)

    # Thread para recibir mensajes
    threading.Thread(target=poll_messages, args=(stub,), daemon=True).start()

    # Interfaz
    try:
        curses.wrapper(curses_main, stub)
    except KeyboardInterrupt:
        try:
            stub.disconnect(chat_pb2.ClientInfo(nickname=nickname))
        except Exception:
            pass


if __name__ == "__main__":
    main()
