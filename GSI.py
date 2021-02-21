import http.server

serverinfo = ("127.0.0.1", 6969)
server = http.server.HTTPServer(serverinfo)

server.listen()