import manage


def initialisation():

    print("How would you like to store/retrieve the data?")
    print("Type 1 for .xlsx file, 2 for sockets or 3 for raw:")
    storage_type = int(input())

    print("Which gamemode do you want to play?")
    print("Type 1 for MM, 2 for Wingman or 3 for custom:")
    gamemode = int(input())
    custom_gamemode = []

    if gamemode == 3:
        print("How many players are playing on Team 1?")
        custom_gamemode.append(int(input()))
        print("How many players are playing on Team 2?")
        custom_gamemode.append(int(input()))

    print("Would you like to use SteamIDs or Usernames?")
    print("Type 1 for SteamID or 2 for Usernames:")
    player_reference = int(input())

    manage.exec_server(storage_type, gamemode, custom_gamemode, player_reference)