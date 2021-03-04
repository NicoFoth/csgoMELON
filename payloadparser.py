import gamestate
import time

class PayloadParser:

    def parse_payload(self, payload, gamestate):
        
        for item in payload: #parsing allplayers (three indexes)
            if item == "allplayers":
                # print(payload)
                index = 0
                for player in payload[item]: #cycles thrue each player and every stat that he has (name,match_stats etc.)
                    for stat in payload[item][player]:
                        
                        setattr(getattr(gamestate.allplayers , "p"+ str(index)), stat , payload[item][player][stat])
                    setattr(getattr(gamestate.allplayers , "p"+ str(index)), "steamid" , player)
                    index += 1

            for i in payload[item]: #parsing "normal" items (two indexes)
                try:
                    setattr(getattr(gamestate, item), i, payload[item][i])
                except:
                    pass
