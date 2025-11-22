# RCP-WhatsUp-Chat
implementación de protocolo gRCP para crear un char de WhatsUp de un grupo donde varios clientes se conectarn y pueden interactuar con un servidor. 


# setup del sistema

## instalación de paquetes y librerías
para poder ejecutar el código desde una nueva máquina, el usuario (tester) deberá instalar la libreria que permite usar gRPC en el lenguaje del programa. En nuestro caso es python

pip install grpcio grpcio-tools

o bien 

pip3 install grpcio grpcio-tools

## Generación del .proto compilado

Para compilar el archivo .proto y ser usado por los diferentes clientes y servidores, es necesario generar el archivo .proto, para ello se ejecutará el siguiente comando:

protoc --proto_path=protos --<lenguaje>_out=generated --grpc_out=generated protos/chat.proto

protoc --proto_path=gRPC --pytohn_out=generated --grpc_out=generated protos/chat.proto

python -m grpc_tools.protoc --proto_path=protos --python_out=. --grpc_python_out=. gRPC/chat.proto
