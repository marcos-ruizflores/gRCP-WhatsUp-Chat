# RCP-WhatsUp-Chat
implementación de protocolo gRCP para crear un char de WhatsUp de un grupo donde varios clientes se conectarn y pueden interactuar con un servidor. 
Desarrollado en el IDE de PyCharm por los autores Marcos Ruiz-Flores Vicente y Marc Joan Sabater Riera. 

Pasos previos para poder ejecutar el entorno: 
 1. python3 -m venv venv
 2. source venv/bin/activate
 3. pip install grpcio grpcio-tools
 4. pip freeze > requeriments.txt
 5. python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. chat.proto

Ejemplos de ejecución: 
Terminal 1: python server.py
Terminal 2: python client.py localhost Marcos
Terminal 3: python client.py localhost Marc
Terminal 4: python client.py localhost Profesor




