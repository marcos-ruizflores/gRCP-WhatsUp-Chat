# gRPC group chat

Terminal group chat built on gRPC, where several clients connect to a central server
and talk in real time. Message ordering across clients is handled with **vector
clocks**, so causally related messages always show up in the right order even when
clients run on different machines.

Built with Marc Joan Sabater Riera as a distributed systems project.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![gRPC](https://img.shields.io/badge/gRPC-244c5a?logo=grpc&logoColor=white)
![Protocol Buffers](https://img.shields.io/badge/Protobuf-4285F4?logo=google&logoColor=white)

## Features

- gRPC service defined in `chat.proto` (`sendMessage`, `getMessages`, `disconnect`)
- Vector clock attached to every message, with happens-before ordering on the server
- Terminal UI with `curses`: per-user colors, timestamps and a live list of connected users
- Optional Tkinter GUI client (`gui_client.py`)
- Chat history persisted to a log file and replayed to clients that join later

## Running it

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# generate the gRPC stubs
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto
```

Then start the server and a few clients, each in its own terminal:

```bash
python server.py
python client.py localhost Marcos
python client.py localhost Marc
python client.py localhost Guest
```

### Across machines on the same network

The vector clock logic is easier to see with clients on different machines:

1. On the server machine, get its local IP (`ipconfig getifaddr en0` on macOS).
2. On the other machines, run the client with that IP instead of `localhost`.
3. Clients on the server machine itself can keep using `localhost`.
