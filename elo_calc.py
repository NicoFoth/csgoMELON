import math
import server
import socket_client
import time

# Calculates performance value
def calculate_p(stats):
    k = 1

    if stats[2] == 0:
        stats[2] = 1

    raw_p = (stats[0] + (stats[1]/2)) / stats[2]

    p = 1

    if raw_p > 1:
        raw_p -= 1
        p = raw_p * k
        p += 1

    elif raw_p < 1:
        raw_p = 1 - raw_p
        p = raw_p * k
        p = 1-p
    
    return p


# Calculates expectation value
# ra: Previous rating of player A, rb: Previous rating of player B
# ea: Expectation of player A, eb: Expectation of player B
def calculate_ev(ra, rb):

    ea = 1/(1+pow(10, ((rb-ra)/400)))
    eb = 1/(1+pow(10, ((ra-rb)/400)))

    return ea, eb


# Calculates new elo of the winning player
# ra: Previous rating of player A, rb: Previous rating of player B
# oa & ob: Outcome of the game - True if won, False if lost
# pa, pb: Perfomance coefficient of the players
def calc_elo_1v1(ra, rb, oa, ob, stats_a, stats_b):
    pa = calculate_p(stats_a)
    pb = calculate_p(stats_b)
    
    k = 20

    if oa == True:
        new_rating_a = ra + (k * ((1-calculate_ev(ra, rb)[0]) * pa))
    
    elif oa == False:
        new_rating_a = ra + (k * ((0-calculate_ev(ra, rb)[0]) * (1/pa)))

    if ob == True:
        new_rating_b = rb + (k * ((1-calculate_ev(ra, rb)[1]) * pb))

    if ob == False:
        new_rating_b = rb + (k * ((0-calculate_ev(ra, rb)[1]) * (1/pb)))

    return new_rating_a, new_rating_b

#oa = outcome_a
def calc_elo_team(rta, rtb, oa, ob, stats_ta, stats_tb):
    k = 20

    average_ra = sum(rta) / len(rta)
    average_rb = sum(rtb) / len(rtb)

    new_rta = []
    new_rtb = []

    for player_rating_index in range(len(rta)):

        p = calculate_p(stats_ta[player_rating_index])

        if oa == True:
            new_rating = rta[player_rating_index] + (k * p * ((1-calculate_ev(rta[player_rating_index], average_rb)[0])))
            new_rta.append(round(new_rating))

        if oa == False:
            new_rating = rta[player_rating_index] + (k * (1/p) * ((0-calculate_ev(rta[player_rating_index], average_rb)[0])))
            new_rta.append(round(new_rating))
        
        if oa == None:
            
            if (0.5-calculate_ev(rta[player_rating_index], average_rb)[0]) >= 0:
                if p >= 1:
                    new_rating = rta[player_rating_index] + k * p * (0.5-calculate_ev(rta[player_rating_index], average_rb)[0])
                else:
                    new_rating = rta[player_rating_index] + k * p * (0.5-calculate_ev(rta[player_rating_index], average_rb)[0])
            else:
                if p >= 1:
                    new_rating = rta[player_rating_index] + k * (1/p) * (0.5-calculate_ev(rta[player_rating_index], average_rb)[0])
                else:
                    new_rating = rta[player_rating_index] + k * (1/p) * (0.5-calculate_ev(rta[player_rating_index], average_rb)[0])
            new_rta.append(round(new_rating)) 

    for player_rating_index in range(len(rtb)):

        p = calculate_p(stats_tb[player_rating_index])

        if ob == True:
            new_rating = rtb[player_rating_index] + (k * p * ((1-calculate_ev(rtb[player_rating_index], average_ra)[0])))
            new_rtb.append(round(new_rating))

        if ob == False:
            new_rating = rtb[player_rating_index] + (k * (1/p) * ((0-calculate_ev(rtb[player_rating_index], average_ra)[0])))
            new_rtb.append(round(new_rating))

        if ob == None:
            
            if (0.5-calculate_ev(rtb[player_rating_index], average_ra)[0]) >= 0:
                if p >= 1:
                    new_rating = rtb[player_rating_index] + k * p * (0.5-calculate_ev(rtb[player_rating_index], average_ra)[0])
                else:
                    new_rating = rtb[player_rating_index] + k * p * (0.5-calculate_ev(rtb[player_rating_index], average_ra)[0])
            else:
                if p >= 1:
                    new_rating = rtb[player_rating_index] + k * (1/p) * (0.5-calculate_ev(rtb[player_rating_index], average_ra)[0])
                else:
                    new_rating = rtb[player_rating_index] + k * (1/p) * (0.5-calculate_ev(rtb[player_rating_index], average_ra)[0])

            new_rtb.append(round(new_rating)) 

    return new_rta, new_rtb


#sorts and filters gsi server dictionary and returns two lists, they contain each´s Team player name list in alphabetical order
def gsi_parse_player_list(payload):
    payload = sorted(payload.items())           #sort dictionary (names, alphabetical)

    players_t = []
    players_ct = []
    players = ""

    for player in payload:
        if player[1]["team"] == "T":            #checks player team
            players_t.append(player[0])         #appends player name to team list
        elif player[1]["team"] == "CT":
            players_ct.append(player[0])
        else:
            print("Player could not be asigned a Team or the payload is corrupted")

    for i in range(len(players_t)):             #adds players 
        players += players_t[i]
        players += "/"
    for j in range(len(players_ct)):
        players += players_ct[j]
        players += "/"

    players = players[:-1]                      #selects all chars from beginign to the one before the last one

    return players


#sorts and filters gsi server dictionary and returns two lists, they contain K/A/D in the alphabetical order of the player´s name 
def gsi_parse_stats(payload):
    payload = sorted(payload.items())           #sort dictionary (names, alphabetical)
    
    team_t_stats = []
    team_ct_stats = []

    for player in payload:
        p = []                                  #empty player list
        if player[1]["team"] == "T":            #checks player team
            p.append(int(player[1]["kills"]))   #appends stats to player list
            p.append(int(player[1]["assists"]))
            p.append(int(player[1]["deaths"]))
            team_t_stats.append(p)              #appends player to team list
        elif player[1]["team"] == "CT":
            p.append(int(player[1]["kills"]))
            p.append(int(player[1]["assists"]))
            p.append(int(player[1]["deaths"]))
            team_ct_stats.append(p)
        else:
            print("Player could not be asigned a Team or the payload is corrupted")
        
    return team_t_stats, team_ct_stats

#takes a touple of the form ([[t_elo_1,t_elo_2,...],[ct_elo_1,ct_elo_2,...]]) and a string of the form "t_name_1/t_name_2.../ct_name_n" 
#returns single string with player name and corosponding new elo "t_name_1:t_new_elo_1|...|ct_name_n:ct_new_elo_n"
def parse_payload_to_send(elo_list, player_dictionary): #elo_list[team(0 = t, 1 = ct)][player][0]
        output_string = ""
        player_dictionary = sorted(player_dictionary.items())
        
        i = 0
        for player in player_dictionary:
            if player[1]["team"] == "T":
                output_string += str(player[0]) + "$" + str(elo_list[0][i]) + ":" + str(player[1]["kills"]) + ":" + str(player[1]["assists"]) + ":" + str(player[1]["deaths"]) + "/"
                i += 1
        i = 0
        for player in player_dictionary:
            if player[1]["team"] == "CT":
                output_string += str(player[0]) + "$" + str(elo_list[1][i]) + ":" + str(player[1]["kills"]) + ":" + str(player[1]["assists"]) + ":" + str(player[1]["deaths"]) + "/"
                i += 1

        return output_string[:-1]

def elo_str_to_elo_list(all_player_elo_str, player_dictionary):
    player_dictionary = sorted(player_dictionary.items())
    all_player_elo_list = all_player_elo_str.split("/")
    out_player_elo_list = [[],[]]
    count_ts = 0
    count_cts = 0
    i = 0
    
    for player in player_dictionary:
        if player[1]["team"] == "T":            #checks player team
            count_ts += 1                       #appends player name to team list
        elif player[1]["team"] == "CT":
            count_cts += 1


    for _ in range(count_ts):
        out_player_elo_list[0].append(int(all_player_elo_list[i]))
        i += 1
    
    for _ in range(count_cts):
        out_player_elo_list[1].append(int(all_player_elo_list[i]))
        i += 1

    return out_player_elo_list


"""Starting Servers"""
gsi_server_instance = server.GSIServer(("localhost",3000),"tau")
gsi_server_instance.start_server()
socket = socket_client.start_client()
t_index = 0 #dont change 
ct_index = 1 #dont change 
max_team_wins = 9 #maximal amount of rounds a team can win before the match ends/ standart = 16; wingman = 9

"""Cheks if the round has ended in a T win (True, False), CT win (False, True), or draw (None, None)"""
game_ended = (False, False)
while game_ended[0] == False and game_ended[1] == False: 
    
    game_ended = server.scan_for_win(gsi_server_instance, max_team_wins)
gsi_server_output = server.output(gsi_server_instance)

players_in_match_str = gsi_parse_player_list(gsi_server_output) 
#of the form "Neekotin/dqniel/Horizon/FamerHamer"

#hint: variable names that contain "str" in them are usualy messages recieved from or ment to be send to the socket server 

"""Sends request to server to send the players elo"""
current_elo_str = socket_client.send_message(socket, players_in_match_str)
#of the form "1505/1153/1539/1549"
current_elo_list = elo_str_to_elo_list(current_elo_str, gsi_server_output) 
#of the form [[1505, 1153], [1539, 1549]] 

"""Filters the players stats out of the gsi dictionary"""
all_player_KAD = gsi_parse_stats(gsi_server_output)
#of the form ([[22, 2, 16], [9, 4, 17]], [[18, 0, 16], [20, 4, 21]]) ([t1_stats,t2_stats],[ct1_stats,ct2_stats]) t1_stats = [kills,assists,deaths]

print("Player Stats: " + str(all_player_KAD))
print("Player Elo(old): " + str(current_elo_list))


"""calculating the new elo"""
new_elo = calc_elo_team(current_elo_list[t_index], current_elo_list[ct_index], game_ended[t_index], game_ended[ct_index], all_player_KAD[t_index], all_player_KAD[ct_index])
print("Player Elo(new): " + str(new_elo))

"""Parsing new elo to a string and sending it to the socket server"""
updated_elo_str = parse_payload_to_send(new_elo,gsi_server_output)
socket_client.send_message(socket, updated_elo_str)

# test_new_elo = ([1513, 1560], [1480, 1489])
# socket_client.send_message(socket, "Neekotin$1671:0:0:0")
#all_player_KAD = gsi_parse_stats(server.output(gsi_server_instance)) # takes snapshot of current round KAD
# print(calc_elo_1v1(1500, 1500, False, True, [20, 0, 40], [40, 0, 20]))