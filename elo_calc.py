import math


"""calculates the performance value given the kills assists and deaths of a player"""

def calculate_performance(stats):       #stats is of the form [kills,assists,deaths]

    w = 1   #a parameter that declares the weight the stats/raw_perfomance has on the performance of the player
            # w > 1 stats become more obsolete; w < 1 stats become more important
            #hint: use two different w values to weight poor and good perfomance differently from another

    #ensures every player has at least 1 death to prohibit division with 0
    if stats[2] == 0:
        stats[2] = 1

    raw_perfomance = (stats[0] + (stats[1]/2)) / stats[2]   #K/D ratio (assists count as 1/2 kills)

    performance = 1     #the performance value that is returned by the method at a later point, it is used to calculate the new elo

    #applies w value when the player performs good 
    if raw_perfomance > 1:
        raw_perfomance -= 1
        performance = raw_perfomance * w 
        performance += 1

    #applies w value when the player performs poorly
    elif raw_perfomance < 1:
        raw_perfomance = 1 - raw_perfomance
        performance = raw_perfomance * w 
        performance = 1-performance

    #defines the minimal and maximal performance that is achievable 
    if performance > 3:
        return 3
    elif performance < 0.3:
        return 0.3
    else:
        return performance


"""calculates the win expectatio of each player/team in the matchup given the ratings of the palyers/teams"""

def calculate_ev(rating_a, rating_b):

    win_excpectation_a = 1/(1+pow(10, ((rating_b-rating_a)/400)))
    win_excpectation_b = 1/(1+pow(10, ((rating_a-rating_b)/400)))

    return win_excpectation_a, win_excpectation_b


""" calculates and returns the new elo of two players in a 1v1 situation """

def calc_elo_1v1(old_rating_a, old_rating_b, win_a, win_b, stats_a, stats_b):
    performance_a = calculate_performance(stats_a)
    performance_b = calculate_performance(stats_b)
    
    k = 20  #base value of the elo added/subtracted

    #checks match outcome for player A and applies the correct elo formula
    if win_a == True:
        new_rating_a = old_rating_a + (k * ((1-calculate_ev(old_rating_a, old_rating_b)[0]) * performance_a))
    
    elif win_a == False:
        new_rating_a = old_rating_a + (k * ((0-calculate_ev(old_rating_a, old_rating_b)[0]) * (1/performance_a)))

    #checks match outcome for player B and applies the correct elo formula
    if win_b == True:
        new_rating_b = old_rating_b + (k * ((1-calculate_ev(old_rating_a, old_rating_b)[1]) * performance_b))

    elif win_b == False:
        new_rating_b = old_rating_b + (k * ((0-calculate_ev(old_rating_a, old_rating_b)[1]) * (1/performance_b)))

    return new_rating_a, new_rating_b


""" calculates and returns the new elo of a team """

def calculate_elo_team(team_rating,team_stats,win,average_rating_opponend):

    k = 20  #base value of the elo added/subtracted
    
    new_team_rating = []


    if win == True:
        for player_rating_index in range(len(team_rating)):
            p = calculate_performance(team_stats[player_rating_index])
            new_rating = team_rating[player_rating_index] + (k * p * ((1-calculate_ev(team_rating[player_rating_index], average_rating_opponend)[0])))
            new_team_rating.append(round(new_rating))

    if win == False:
        for player_rating_index in range(len(team_rating)):
            p = calculate_performance(team_stats[player_rating_index])
            new_rating = team_rating[player_rating_index] + (k * (1/p) * ((0-calculate_ev(team_rating[player_rating_index], average_rating_opponend)[0])))
            new_team_rating.append(round(new_rating))

    if win is None:
        for player_rating_index in range(len(team_rating)):

            p = calculate_performance(team_stats[player_rating_index])
            
            if calculate_ev(team_rating[player_rating_index], average_rating_opponend)[0] <= 0.5:
                new_rating = team_rating[player_rating_index] + k * p * (0.5-calculate_ev(team_rating[player_rating_index], average_rating_opponend)[0])
            else:
                new_rating = team_rating[player_rating_index] + k * (1/p) * (0.5-calculate_ev(team_rating[player_rating_index], average_rating_opponend)[0])
            new_team_rating.append(round(new_rating)) 
    return new_team_rating

""" calculates the elo of two teams """

#example parameters print(calc_elo_match([1100],[900],None,None,[[9,0,4]],[[4,0,9]]))
def calc_elo_match(rating_team_a, rating_team_b, win_a, win_b, stats_ta, stats_tb):

    average_ra = sum(rating_team_a) / len(rating_team_a)
    average_rb = sum(rating_team_b) / len(rating_team_b)
    
    new_rating_team_a = calculate_elo_team(rating_team_a,stats_ta,win_a,average_rb)
    new_rating_team_b = calculate_elo_team(rating_team_b,stats_tb,win_b,average_ra)

    return new_rating_team_a, new_rating_team_b
