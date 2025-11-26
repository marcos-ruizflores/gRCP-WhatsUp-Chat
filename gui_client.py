import grpc
import chat_pb2
import chat_pb2_grpc
import sys
import threading
import time
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime


SERVER_IP = sys.argv[1]
nickname = sys.argv[2]


class ChatGUI:
    def __init__(self, stub):
        self.stub = stub

        # Root window
        self.root = tk.Tk()
        self.root.title(f"Chat - {nickname}")
        self.root.geometry("500x600")
        self.root.configure(bg="#2c2f33")

        # Chat window
        self.chat_box = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, bg="#23272a",
                                                  fg="white", font=("Arial", 12))
        self.chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_box.config(state=tk.DISABLED)

        # Input frame
        self.input_frame = tk.Frame(self.root, bg="#2c2f33")
        self.input_frame.pack(fill=tk.X)

        self.input_field = tk.Entry(self.input_frame, font=("Arial", 14))
        self.input_field.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

        self.send_button = tk.Button(self.input_frame, text="Enviar",
                                     command=self.send_message, bg="#7289da",
                                     fg="white", font=("Arial", 12))
        self.send_button.pack(side=tk.RIGHT, padx=10)

        # bind enter key
        self.root.bind("<Return>", lambda event: self.send_message())

        # Start polling thread
        self.last_count = 0
        threading.Thread(target=self.poll_messages, daemon=True).start()

    def send_message(self):
        text = self.input_field.get().strip()
        if text == "":
            return

        # Send to server
        self.stub.sendMessage(chat_pb2.Message(
            nickname=nickname,
            text=text
        ))

        self.input_field.delete(0, tk.END)

    def poll_messages(self):
        while True:
            try:
                resp = self.stub.getMessages(chat_pb2.Empty())
                new = resp.lines[self.last_count:]

                if new:
                    for line in new:
                        self.add_message(line.rstrip("\n"))

                self.last_count = len(resp.lines)
            except:
                pass

            time.sleep(1)

    def add_message(self, msg):
        self.chat_box.config(state=tk.NORMAL)

        # Formato actual del servidor: "Javier: Hola"
        if ": " in msg:
            user, text = msg.split(": ", 1)
            timestamp = ""
        else:
            self.chat_box.insert(tk.END, msg + "\n")
            self.chat_box.config(state=tk.DISABLED)
            self.chat_box.see(tk.END)
            return

        color = "lightgreen" if user == nickname else "cyan"

        # Insertar mensaje
        self.chat_box.insert(tk.END, f"{user}: ", color)
        self.chat_box.insert(tk.END, text + "\n")

        self.chat_box.tag_config("lightgreen", foreground="lightgreen")
        self.chat_box.tag_config("cyan", foreground="cyan")

        self.chat_box.config(state=tk.DISABLED)
        self.chat_box.see(tk.END)



    def run(self):
        self.root.mainloop()


def main():
    channel = grpc.insecure_channel(SERVER_IP + ":50051")
    stub = chat_pb2_grpc.ChatServiceStub(channel)

    gui = ChatGUI(stub)
    gui.run()


if __name__ == "__main__":
    main()
