#sorts and filters gsi server dictionary and returns two lists, they contain each´s Team player name list in alphabetical order
def gsi_parse_player_list(payload):
    payload = sorted(payload.items())           #sort dictionary (names, alphabetical)

    players_t = []
    players_ct = []
    players = ""

    for player in payload:
        if player[1]["team"] == "T":            #checks player team
            players_t.append(player[1]["steamid"])         #appends player name to team list
        elif player[1]["team"] == "CT":
            players_ct.append(player[1]["steamid"])
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
                output_string += str(player[1]["steamid"]) + "$" + str(elo_list[0][i]) + ":" + str(player[1]["kills"]) + ":" + str(player[1]["assists"]) + ":" + str(player[1]["deaths"]) + "/"
                i += 1
        i = 0
        for player in player_dictionary:
            if player[1]["team"] == "CT":
                output_string += str(player[1]["steamid"]) + "$" + str(elo_list[1][i]) + ":" + str(player[1]["kills"]) + ":" + str(player[1]["assists"]) + ":" + str(player[1]["deaths"]) + "/"
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