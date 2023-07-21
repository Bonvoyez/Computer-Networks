import socket
import threading

def receive_msg(s):
    while True:
        try:
            data = ""
            while not data.endswith("\n"):
                data += s.recv(1).decode()

            data = data.split()

            if len(data) >= 1:
                if data[0] == "DELIVERY":
                    data_idx = 2
                    message = ""

                    while len(data) > data_idx:
                        message += data[data_idx] + " "
                        data_idx += 1

                    print(data[1] + ": " + message)
                elif data[0] == "LIST-OK":
                    print("\nList of Users: \n" + data[1])
                elif data[0] == "SEND-OK":
                    print("MESSAGE SENT")
                elif data[0] == "BAD-DEST-USER":
                    print("There is no such user. Please choose an existing user.")
                
                print("\nSend message:")
        except OSError:
            print("Chat server disconnected...")
            return

def send_msg(s, t):       
    in_data = ""

    while in_data != "!quit":
        in_data = input("")

        if in_data == "!who":
            s.send(("LIST\n").encode())
        elif in_data != "!quit":
            if len(in_data) > 0 and in_data[0] == "@":
                in_data = in_data[1:]
                in_data = in_data.split()
        
                if len(in_data) <= 1:
                    print("Wrong format.")
                else:
                    username = in_data[0]
                            
                    message = ""
                    in_data_idx = 1
                    while len(in_data) > in_data_idx:
                        message += in_data[in_data_idx] + " "
                        in_data_idx += 1

                    message = ("SEND " + username + " " + message + "\n").encode("utf-8")
                    s.send(message)
                    print("MESSAGE SENT")
                    print("send message:")
            else:
                print("Wrong format.")
    
    s.close()

def login():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("143.47.184.219", 5378))

    username = input("Enter a username:\n")

    if username == "!quit":
        s.close()
    elif username.isalnum():
        message = ("HELLO-FROM " + username + "\n").encode("utf-8")
        s.send(message)

        data = ""
        while not data.endswith("\n"):
            data += s.recv(1).decode()

        data = data.split()

        if data[0] == "IN-USE":
            print("The name is in use. Please select different name.")
            login()
        elif data[0] == "HELLO":
            print("Hello " + data[1] + "! Welcome to the server.\n")
            print("Send Message:")

            t = threading.Thread(target=receive_msg, args=[s])
            t.start()
            send_msg(s, t)
        elif data[0] == "BUSY\n":
            print("Server busy. Please come back later.")
            login()
    else:
        print("Only numbers and alphabets allowed.")
        login()

login()