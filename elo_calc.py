import math

# Calculates performance value
def calculate_p(stats):
    k = 0.5

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
            new_rta.append(new_rating)

        if oa == False:
            new_rating = rta[player_rating_index] + (k * (1/p) * ((0-calculate_ev(rta[player_rating_index], average_rb)[0])))
            new_rta.append(new_rating)
        
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

            new_rta.append(new_rating) 

    for player_rating_index in range(len(rtb)):

        p = calculate_p(stats_tb[player_rating_index])

        if ob == True:
            new_rating = rtb[player_rating_index] + (k * p * ((1-calculate_ev(rtb[player_rating_index], average_ra)[0])))
            new_rtb.append(new_rating)

        if ob == False:
            new_rating = rtb[player_rating_index] + (k * (1/p) * ((0-calculate_ev(rtb[player_rating_index], average_ra)[0])))
            new_rtb.append(new_rating)

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

            new_rtb.append(new_rating) 

    return new_rta, new_rtb



print(calc_elo_team([1500, 1500], [1500, 1500], True, None, [[20, 0, 20], [20, 0, 20]], [[31, 7, 19], [26, 6, 19], [23, 3, 24], [11, 4, 19]]))

# print(calc_elo_1v1(1500, 1500, False, True, [20, 0, 40], [40, 0, 20]))