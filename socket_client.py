import socket

def start_client():
    host = "207.154.246.228"
    port = 5470
    

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host,port))
    return client_socket

def send_message(client_socket, msg):
    header = 8

    msg = msg.encode("utf-8")
    #print(msg)

    greeting = str(len(msg)).encode("utf-8")

    greeting += b" " * (header - len(greeting))
    #print(greeting)
    
    client_socket.send(greeting)

    client_socket.send(msg)

    print(client_socket.recv(1024).decode("utf-8"))
    
#socket = start_client()
# send_message(socket,"Kurt/Boby/Gary")
