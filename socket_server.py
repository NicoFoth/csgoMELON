import socket
import threading
import sqlite3
import config

PORT = config.SOCKET_PORT
SERVER = config.SOCKET_HOST
print(SERVER)
ADDR = (SERVER, PORT)
HEADER = 8
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def parse_old_elo(elo_list):
    elo_string = ""

    for elo in elo_list:
        elo_string += f"{elo}/"

    elo_string = elo_string[:-1]

    return elo_string

def parse_new_stats(msg):
    new_stats = {}

    player_list = msg.split("/")
    for player in player_list:
        player_split = player.split("$")
        new_stats[player_split[0]] = player_split[1]

    for key in new_stats:
        new_stats[key] = new_stats[key].split(":")
        value_list = []
        for value in new_stats[key]:
            value_list.append(value)
        value_list = [int(x) for x in value_list]
        new_stats[key] = value_list
    
    return new_stats


def handle_client(conn, addr):
    connected = True
    while connected:
        msg_length = conn.recv(HEADER)
        msg_length = int(msg_length)
        msg = conn.recv(msg_length).decode(FORMAT)

        print(msg)

        steam_id_list = msg.split("/")
        elo_list = retrieve_elo_from_database(steam_id_list) # ADD YOUR FUNCTION TO RETRIEVE THE ELO FROM THE DB

        elo_string = parse_old_elo(elo_list)

        conn.send(elo_string.encode(FORMAT))

        msg2_length = conn.recv(HEADER)
        msg2_length = int(msg2_length)
        msg2 = conn.recv(msg2_length).decode(FORMAT)

        new_stats = parse_new_stats(msg2)
        print(new_stats)

        store_info_in_database(new_stats) # ADD YOUR FUNCTION TO STORE THE NEW STATS IN THE DB

        connected = False


def start():
    server.listen()
    print("Server started...")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

start()
