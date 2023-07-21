import socket
import threading

list_users = []
list_sockets = []

def handle_client(client_socket, client_address):
    print(f"New connection from {client_address}")
    username = ""

    while True:
        data = ""
        while not data.endswith("\n"):
            data += client_socket.recv(1).decode()
            if not data:
                break

        if not data:
            if username != "":
                list_users.remove(username)
                list_sockets.remove(client_socket)
                break
        else:
            data = data.split()

            if data[0] == "HELLO-FROM":
                if not data[1]:
                    client_socket.sendall(("BAD-RQST-BODY\n").encode("utf-8"))
                elif len(list_users) > 63:
                    client_socket.sendall(("BUSY\n").encode("utf-8"))
                elif data[1] in list_users:
                    client_socket.sendall(("IN-USE\n").encode("utf-8"))
                else:
                    client_socket.sendall(("HELLO " + data[1] + "\n").encode("utf-8"))
                    username = data[1]
                    list_users.append(data[1])
                    list_sockets.append(client_socket)
                    print(list_users)
            elif data[0] == "LIST":
                users = ""
                for user in list_users:
                    users += user + ","

                if users.endswith(","):
                    users = users[:len(users)-1]

                client_socket.sendall(("LIST-OK " + users + "\n").encode("utf-8"))
            elif data[0] == "SEND":
                if not data[1]:
                    client_socket.sendall(("BAD-RQST-BODY\n").encode("utf-8"))
                elif data[1] not in list_users:
                    client_socket.sendall(("BAD-DEST-USER\n").encode("utf-8"))
                else:
                    message = ""
                    index = 2
                    while index < len(data):
                        message += data[index] + " "
                        index += 1

                    list_sockets[list_users.index(data[1])].sendall(("DELIVERY " + username + " " + message + "\n").encode("utf-8"))
                    client_socket.sendall(("SEND-OK\n").encode("utf-8"))
            else:
                client_socket.sendall(("BAD-RQST-HDR\n").encode("utf-8"))

    print(f"Closing connection with {client_address}")
    client_socket.close()

ip = "localhost"
port = 5678
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((ip, port))
server_socket.listen()

print(f"Server listening on {ip}:{port}")

while True:
    client_socket, client_address = server_socket.accept()

    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()