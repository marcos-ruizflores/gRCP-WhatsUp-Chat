import grpc
import chat_pb2
import chat_pb2_grpc
import sys
import threading
import time
import curses

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

    # Inicializar colores
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)   # Timestamp
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)   # Mensajes propios
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)    # Mensajes de otros
    curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Prompt

    input_buffer = ""

    while True:
        stdscr.clear()

        # Tamaño de pantalla
        h, w = stdscr.getmaxyx()
        max_msgs = h - 3

        # Obtener mensajes
        with lock:
            to_show = messages[-max_msgs:]

        # Dibujar cada mensaje
        for i, msg in enumerate(to_show):
            try:
                # Particionar mensaje: "12:41 Javier: hola"
                parts = msg.split(" ", 2)
                ts = parts[0]     # timestamp
                user = parts[1]   # "Javier:"
                text = parts[2] if len(parts) > 2 else ""

                # Determinar color del usuario
                if user.startswith(nickname):
                    color_user = curses.color_pair(2)  # verde
                else:
                    color_user = curses.color_pair(3)  # cyan

                # Imprimir timestamp (blanco)
                stdscr.addstr(i, 0, ts + " ", curses.color_pair(1))

                # Imprimir usuario en color
                stdscr.addstr(user + " ", color_user)

                # Imprimir texto del mensaje
                stdscr.addstr(text)

            except Exception:
                stdscr.addstr(i, 0, msg)

        # Dibujar prompt
        stdscr.addstr(h - 2, 0, f"{nickname} --> ", curses.color_pair(4))
        stdscr.addstr(input_buffer)

        stdscr.refresh()

        # Leer teclado
        try:
            ch = stdscr.getch()
        except:
            ch = -1

        if ch == -1:
            time.sleep(0.05)
            continue

        # ENTER
        if ch in (10, 13):
            if input_buffer.strip():
                stub.sendMessage(chat_pb2.Message(
                    nickname=nickname,
                    text=input_buffer
                ))
            input_buffer = ""

        # BACKSPACE
        elif ch in (263, 127):
            input_buffer = input_buffer[:-1]

        # Texto normal
        elif 32 <= ch <= 126:
            input_buffer += chr(ch)


def main():
    channel = grpc.insecure_channel(sys.argv[1] + ":50051")
    stub = chat_pb2_grpc.ChatServiceStub(channel)

    # Thread para recibir mensajes
    threading.Thread(target=poll_messages, args=(stub,), daemon=True).start()

    # Interfaz curses
    curses.wrapper(curses_main, stub)


if __name__ == "__main__":
    main()
