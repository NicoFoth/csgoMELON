# 🍉csgoMELON🍉
CS:GO MELON (MELON for the ELO and because they're delicious) is a elo calculation tool for Counterstrike: Global Offensive.
It extracts the information of a privately hosted game using Valve's Gamestate Integration. You can store the data (currently only the elo but kills, deaths, etc. are coming...) in an excel file or transfer it via the featured socket client and server to another machine, where it can be stored.

## 🙋🏼‍♂️Introduction🙋🏼‍♂️
We looked for a way to retrieve data from our private CS:GO matches and calculate an elo value based on that. We thought it might be a good idea to start a leaderboard displaying the long-term performance of every player. I discovered the Gamestate Integration interface by Valve for Counterstrike and then researched if there are any repositories fulfilling our plans. We didn't find any, so instead we figured to code one ourselves.

## 🛰Technologies🛰
The program is fully coded in python using Valve's Gamestate Integration. The data is being stored in the excel file using openpyxl, which can be installed with pip. The socket server is built using only built-in python packages. The foundation of the Gamestate Integration part of the program is extracted out of [mdhedelung's CSGO-GSI](https://github.com/mdhedelund/CSGO-GSI) repo.

## 🕹Installing/Using🕹
Installing it is fairly easy, because there is no installation. Just download the repo, configure it and you're good to go. Configuring is done inside of the config.py file, where you can set your gamemode, storage type, etc. After you configured your csgoMELON instance, copy the gsi.cfg file into your Counterstrike: Global Offensive directory into csgo/cfg. The full path will probably be something along those lines: <br />C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\csgo\cfg<br />
After you've set everything up just execute manage.py and everything will work automatically.

## ⛔️Important notes⛔
The player using the GSI has to be an observer in your CS:GO match. That's just another name for a spectator. So if you're executing the csgoMELON you can't participate in the game. But you could join the lobby with a second account on a different machine and execute csgoMELON there.<br />
Also right now there is no way for the program to automatically add new players to the "database". You have to add all the players, who'll be playing beforehand using their steamID.
