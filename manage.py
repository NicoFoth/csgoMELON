from parsers import gsi_parse_player_list, gsi_parse_stats, elo_str_to_elo_list, parse_payload_to_send
from elo_calc import calc_elo_team
import server
import socket_client


def retrieve_current_elo_xlsx():
    pass

def retrieve_current_elo_socket(socket, players_in_match_str):
    """Sends request to server to send the players elo"""
    current_elo_str = socket_client.send_message(socket, players_in_match_str)
    #of the form "1505/1153/1539/1549"

def retrieve_current_elo_raw():
    pass

def send_current_elo_xlsx():
    pass

def send_current_elo_socket(socket, updated_elo_str):
    socket_client.send_message(socket, updated_elo_str)

def send_current_elo_raw():
    pass


def exec_server(storage_type, gamemode, custom_gamemode, player_reference):

    """Starting Servers"""
    gsi_server_instance = server.GSIServer(("localhost",3000),"tau")
    gsi_server_instance.start_server()
    

    t_index = 0 #dont change
    ct_index = 1 #dont change
    max_team_wins = None
    if gamemode == 1:
        max_team_wins = 16
    elif gamemode == 2:
        max_team_wins = 9

    """Cheks if the round has ended in a T win (True, False), CT win (False, True), or draw (None, None)"""
    game_ended = (False, False)
    while game_ended[0] == False and game_ended[1] == False:
        
        game_ended = server.scan_for_win(gsi_server_instance, max_team_wins)
    
    gsi_server_output = server.output(gsi_server_instance)

    players_in_match_str = gsi_parse_player_list(gsi_server_output)
    # "Player1/Player2/Player3/Player4/Player5"

    # hint: variable names that contain "str" in them are usualy messages recieved from or ment to be send to the socket server 

    socket = None
    current_elo_str = ""
    if storage_type == 1:
        current_elo_str = retrieve_current_elo_xlsx()

    elif storage_type == 2:
        socket = socket_client.start_client()
        current_elo_str = retrieve_current_elo_socket(socket, players_in_match_str)
    
    elif storage_type == 3:
        current_elo_str = retrieve_current_elo_raw()

    current_elo_list = elo_str_to_elo_list(current_elo_str, gsi_server_output)
    #of the form [[1505, 1153], [1539, 1549]]

    """Filters the players stats out of the gsi dictionary"""
    all_player_KAD = gsi_parse_stats(gsi_server_output)
    #of the form ([[22, 2, 16], [9, 4, 17]], [[18, 0, 16], [20, 4, 21]]) ([t1_stats,t2_stats],[ct1_stats,ct2_stats]) t1_stats = [kills,assists,deaths]


    """calculating the new elo"""
    new_elo = calc_elo_team(current_elo_list[t_index], current_elo_list[ct_index], game_ended[t_index], game_ended[ct_index], all_player_KAD[t_index], all_player_KAD[ct_index])


    """Parsing new elo to a string and sending it to the socket server"""
    updated_elo_str = parse_payload_to_send(new_elo,gsi_server_output)


    current_elo_str = ""
    if storage_type == 1:
        current_elo_str = send_current_elo_xlsx()

    elif storage_type == 2:
        current_elo_str = send_current_elo_socket(socket, updated_elo_str)
    
    elif storage_type == 3:
        current_elo_str = send_current_elo_raw()

