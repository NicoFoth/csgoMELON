import socket
import config

def start_client():
    host = config.SOCKET_HOST
    port = config.SOCKET_PORT
    

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host,port))
    return client_socket

def send_message(client_socket, msg):
    header = 8

    msg = msg.encode("utf-8")

    greeting = str(len(msg)).encode("utf-8")

    greeting += b" " * (header - len(greeting))

    client_socket.send(greeting)
    client_socket.send(msg)
    return client_socket.recv(1024).decode("utf-8")

