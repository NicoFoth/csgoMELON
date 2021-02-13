import server
import time

server = server.GSIServer(("127.0.0.1", 3000), "S8RL9Z6Y22TYQK45JB4V8PHRJJMD9DS9")

server.start_server()

print(server.get_info("map"))
print(server.get_info("matchstats"))