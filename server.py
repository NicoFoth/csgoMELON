from http.server import BaseHTTPRequestHandler, HTTPServer
from operator import attrgetter
from threading import Thread
import json
import time

import logger
import gamestate
import payloadparser

class GSIServer(HTTPServer):
    def __init__(self, server_address, auth_token):
        super(GSIServer, self).__init__(server_address, RequestHandler)

        self.auth_token = auth_token
        self.gamestate = gamestate.GameState()
        self.parser = payloadparser.PayloadParser()
        # self.setup_log_file()

        self.running = False

    # def setup_log_file(self):
    #     self.log_file = logger.LogFile(time.asctime())

    def start_server(self):
        try:
            thread = Thread(target=self.serve_forever)
            thread.start()
            first_time = True
            while self.running == False:
                if first_time == True:
                    print("CS:GO GSI Server starting..")
                first_time = False
        except:
            print("Could not start server.")

    def get_info(self, target, *argv):
        try:
            #print(target)
            if len(argv) == 0:
                state = attrgetter(f"{target}")(self.gamestate)
            elif len(argv) == 1:
                state = attrgetter(f"{target}.{argv[0]}")(self.gamestate)
            elif len(argv) == 2:
                state = attrgetter(f"{target}.{argv[0]}")(self.gamestate)[f"{argv[1]}"]
            else:
                print("Too many arguments.")
                return False
            if "object" in str(state):
                return vars(state)
            else:
                return state
        except Exception as E:
            #print(E)
            return False
    
    def stop_server(self):
        self.running = False
        print("sad")
        

class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = self.rfile.read(length).decode("utf-8")

        payload = json.loads(body)

        #self.server.log_file.log_event(time.asctime(), payload)

        if not self.authenticate_payload(payload):
            print("auth_token does not match.")
            return False
        else:
            self.server.running = True
        
        
        self.server.parser.parse_payload(payload, self.server.gamestate)

    def authenticate_payload(self, payload):
        if "auth" in payload and "token" in payload["auth"]:
            return payload["auth"]["token"] == self.server.auth_token
        else:
            return False

def scan_for_win(server, max_team_wins): #outputs 
    while True:
        t_wins = server.get_info("map","team_t","score")
        ct_wins = server.get_info("map","team_ct","score")
        if t_wins == max_team_wins:
            return True , False
        elif ct_wins == max_team_wins:
            return False , True
        elif ct_wins == max_team_wins-1 and t_wins == max_team_wins-1:
            return None , None
        else:
            return False , False
        

def output(server): #outputs the match stats as dictionary and in console
    output = {}
    for i in range(12):
            if getattr(getattr(server.gamestate.allplayers, "p" + str(i) ) , "name") != None:

                name = getattr(getattr(server.gamestate.allplayers, "p" + str(i) ) , "name")
                stats = getattr(getattr(server.gamestate.allplayers, "p" + str(i) ) , "match_stats")
                stats.pop("score")
                stats.pop("mvps")
                stats["team"] = getattr(getattr(server.gamestate.allplayers, "p" + str(i) ) , "team")
                stats["steamid"] = getattr(getattr(server.gamestate.allplayers, "p" + str(i) ) , "steamid")
                output[name] = stats

                print("---------------------------------------------------------------")
                print(name, end=": ")
                print(stats)
            else:
                pass
    return output

