import math


"""calculates the performance value given the kills assists and deaths of a player"""

def calculate_performance(stats):       #stats is of the form [kills,assists,deaths]

    k = 1   #a parameter that declares the weight the stats/raw_perfomance has on the performance of the player
            # k>1 stats become more obsolete; k<1 stats become more important
            #hint: use two different k values to weight poor and good perfomance differently from another

    #ensures every player has at least 1 death to prohibit division with 0
    if stats[2] == 0:
        stats[2] = 1

    raw_perfomance = (stats[0] + (stats[1]/2)) / stats[2]   #K/D ratio (assists count as 1/2 kills)

    performance = 1     #the performance value that is returned by the method at a later point, it is used to calculate the new elo

    #applies k value when the player performs good 
    if raw_perfomance > 1:
        raw_perfomance -= 1
        performance = raw_perfomance * k
        performance += 1

    #applies k value when the player performs poorly
    elif raw_perfomance < 1:
        raw_perfomance = 1 - raw_perfomance
        performance = raw_perfomance * k
        performance = 1-performance

    #defines the minimal and maximal performance that is achievable 
    if performance > 3:
        return 3
    elif performance < 0.3:
        return 0.3
    else:
        return performance


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
    pa = calculate_performance(stats_a)
    pb = calculate_performance(stats_b)
    
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

def calculate_elo_team(team_rating,team_stats,win,average_rating_opponend):
    k = 20
    new_team_rating = []
    for player_rating_index in range(len(team_rating)):

        p = calculate_performance(team_stats[player_rating_index])

        if win == True:
            new_rating = team_rating[player_rating_index] + (k * p * ((1-calculate_ev(team_rating[player_rating_index], average_rating_opponend)[0])))
            new_team_rating.append(round(new_rating))

        if win == False:
            new_rating = team_rating[player_rating_index] + (k * (1/p) * ((0-calculate_ev(team_rating[player_rating_index], average_rating_opponend)[0])))
            new_team_rating.append(round(new_rating))

        if win is None:
            
            if calculate_ev(team_rating[player_rating_index], average_rating_opponend)[0] <= 0.5:
                new_rating = team_rating[player_rating_index] + k * p * (0.5-calculate_ev(team_rating[player_rating_index], average_rating_opponend)[0])
            else:
                new_rating = team_rating[player_rating_index] + k * (1/p) * (0.5-calculate_ev(team_rating[player_rating_index], average_rating_opponend)[0])
            new_team_rating.append(round(new_rating)) 
    return new_team_rating



#oa = outcome_a
#example parameters calc_elo_match([1100],[900],True,False,[[9,0,4]],[[4,0,9]])
def calc_elo_match(rta, rtb, oa, ob, stats_ta, stats_tb):

    average_ra = sum(rta) / len(rta)
    average_rb = sum(rtb) / len(rtb)
    
    new_rta = calculate_elo_team(rta,stats_ta,oa,average_rb)
    new_rtb = calculate_elo_team(rtb,stats_tb,ob,average_ra)

    return new_rta, new_rtb
