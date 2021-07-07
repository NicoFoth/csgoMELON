import manage


def initialisation():

    storage_type = inputs(
        "How would you like to store/retrieve the data?",
        "Type 1 for .xlsx file or 2 for sockets:",
    )

    gamemode = inputs(
        "Which gamemode do you want to play?",
        "Type 1 for MM, 2 for Wingman or 3 for custom:",
    )

    custom_gamemode = []

    if gamemode == 3:
        print("How many players are playing on Team 1?")
        custom_gamemode.append(int(input()))
        print("How many players are playing on Team 2?")
        custom_gamemode.append(int(input()))

    player_reference = inputs(
        "Would you like to use SteamIDs or Usernames?",
        "Type 1 for SteamID or 2 for Usernames:",
    )

    manage.exec_server(storage_type, gamemode, custom_gamemode, player_reference)

def inputs(arg0, arg1):
    print(arg0)
    print(arg1)
    return int(input())