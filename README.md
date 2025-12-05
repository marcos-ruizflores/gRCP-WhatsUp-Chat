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


En el caso de que se quiera ejecutar en máquinas diferentes dentro de una misma red para ver mejor el funcionamiento y la lógica del vector clock es necesario: 
1. ipconfig getifaddr en0 -> esto devuelve la IP de la máquina donde se ejecutara el servidor por lo tanto donde se ejecute se hace este comando y con la IP que devuelva.
2. En la otra máquina abrimos un cliente y sustituimos localhost por la IP dada con anterioridad.
3. Los clientes que se ejecuten en la máquina donde se esta ejecutando el servidor pueden seguir manteniendo localhost.
   



