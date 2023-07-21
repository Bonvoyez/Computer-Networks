import socket
import threading
import time

users = []
user_seq = []
user_msg = []

def error_correction(s):
    recv_count = 0
    bits_storage = [[]]
    data = s.recv(1024).decode("ISO-8859-1")
    data = str(''.join(format(ord(c), '08b') for c in data))
    data = data[:-8]
    data_len = len(data)
    while recv_count < 30:
        data = s.recv(1024).decode("ISO-8859-1")
        data = str(''.join(format(ord(c), '08b') for c in data))
        data = data[:-8]
        if data_len != len(data):
            recv_count = 0
            break
        for i in range(data_len):
            bits_storage.append([])
            bits_storage[i].append(data[i])
        recv_count += 1
    
    zero_count = 0
    one_count = 0
    data = ""
    for i in range(data_len):
        for j in range(recv_count - 1):
            if bits_storage[i][j] == "0":
                zero_count += 1
            elif bits_storage[i][j] == "1":
                one_count += 1
        if zero_count > one_count:
            data += "0"
        else:
            data += "1"
        zero_count = 0
        one_count = 0
    
    data = ''.join(chr(int(data[i:i+8], 2)) for i in range(0, len(data), 8))
    return data

def receive_msg(s, lock):
    while True:
        if lock.locked():
            continue
        try:
            data = s.recv(1024).decode("ISO-8859-1")
            if not data.startswith("DELIVERY"):
                data = error_correction(s)    
            data = data.split()

            if data[0] == "DELIVERY":
                data_idx = 2
                message = ""

                while len(data) - 1 > data_idx:
                    message += data[data_idx] + " "
                    data_idx += 1

                message = message[:-1]
                
                if data[1] not in users:
                    users.append(data[1])
                    user_seq.append(-1)
                    user_msg.append([0] * 2048)
                
                if "RECEIVED-OK\n" not in data:
                    s.send(("SEND " + data[1] + " RECEIVED-OK\n").encode("utf-8"))

                if user_seq[users.index(data[1])] != data[data_idx]:
                    if "RECEIVED-OK" != data[data_idx]:
                        seq = int(data[data_idx])
                        user_idx = users.index(data[1])

                        if user_seq[user_idx] + 1 == seq:
                            print(data[1] + ": " + message)

                            while user_msg[user_idx][seq] != 0:
                                    print(data[1] + ": " + user_msg[user_idx][seq])
                                    user_msg[user_idx].pop(seq)
                                    seq += 1
        
                            user_seq[user_idx] = seq
                            print("\nSEND MESSAGE:")
                        else:
                            user_msg[user_idx][seq] = message
                else:
                    continue
        except OSError:
            print("\nChat server disconnected...")
            return

def receive_ack(s, username):
    while True:
        data = s.recv(1024).decode("ISO-8859-1")
        data = str(''.join(format(ord(c), '08b') for c in data))

        if len(data) == len("BAD-DEST-USER\n") * 8:
            user_seq.pop(users.index(username))
            user_msg.pop(users.index(username))
            users.pop(users.index(username))

            print("\nNO SUCH USER EXIST.")
            return
        else:
            if len(data) != len("SEND-OK\n") * 8:
                while len(data) != len("SEND-OK\n") * 8:
                    data = s.recv(1024).decode("ISO-8859-1")
                    data = str(''.join(format(ord(c), '08b') for c in data))
            data = s.recv(1024).decode("ISO-8859-1")
            data = str(''.join(format(ord(c), '08b') for c in data))

            if  len(data) != len("DELIVERY " + username + " RECEIVED-OK\n") * 8:
                while len(data) != len("DELIVERY " + username + " RECEIVED-OK\n") * 8: 
                    data = s.recv(1024).decode("ISO-8859-1")
                    data = str(''.join(format(ord(c), '08b') for c in data))
            print("\nMESSAGE SENT")
            print("MESSAGE DELIVERED")
            return

def receive_list(s):
    while True:
        data = error_correction(s)

        if data != None and "LIST-OK" in data:
            data = data.split()

            print("\nLIST of USERS:")
            print(data[1])  
            return

def set_values(s, value):
    while True:
        data = error_correction(s)

        if data != None:
            if "SET-OK" in data:
                print(value + " is set.")
            else:
                print("Either there is no such value or incorrect number has been given.")
            return

def send_msg(s, lock, my_id):       
    in_data = ""
    ack = 0

    while in_data != "!quit":
        in_data = input("\nSEND MESSAGE: \n")

        if in_data == "!who":
            lock.acquire()

            t3 = threading.Thread(target=receive_list, args=[s])
            t3.start()

            timeout = time.time() + 20

            while timeout >= time.time():
                if t3.is_alive():
                    s.send(("LIST\n").encode('utf-8'))
                    time.sleep(0.01)
                else:
                    break

            lock.release()
        elif in_data.startswith("SET"):
                lock.acquire()

                value = in_data.split()[1]

                t4 = threading.Thread(target=set_values, args=[s, value])
                t4.start()

                while t4.is_alive():
                    s.send((in_data+"\n").encode("utf-8"))
                    time.sleep(0.01)

                lock.release()
        else:
            if (len(in_data) > 0 and in_data[0] == "@"):
                in_data = in_data[1:]
                in_data = in_data.split()
        
                if len(in_data) <= 1:
                    print("Wrong format.")
                else:
                    username = in_data[0]

                    if username == my_id:
                        in_data = in_data[1:]
                        data_string = ""
                        for data in in_data:
                            data_string += " " + data
                        print(username + ":" + data_string)
                    else:
                        if username not in users:
                            users.append(username)
                            user_seq.append(-1)
                            user_msg.append([0]*2048)
                                    
                        message = ""
                        in_data_idx = 1
                        while len(in_data) > in_data_idx:
                            message += in_data[in_data_idx] + " "
                            in_data_idx += 1

                        lock.acquire()

                        t2 = threading.Thread(target=receive_ack, args=[s, username])
                        t2.start()

                        seq = user_seq[users.index(username)] + 1

                        timeout = time.time() + 20

                        while timeout >= time.time():
                            if t2.is_alive():
                                s.send(("SEND " + username + " " + message + " " + str(seq) + "\n").encode("utf-8"))
                                time.sleep(0.1)
                            else:
                                break
                        lock.release()
                        
                        if username in users:
                            user_seq[users.index(username)] = seq
            else:
                print("Wrong format.")
    s.close()

def login():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("143.47.184.219", 5382))

    username = input("Enter a username:\n")

    if username == "!quit":
        s.close()
    elif username.isalnum():
        message = ("HELLO-FROM " + username + "\n").encode("utf-8")
        s.send(message)

        data = s.recv(1024).decode()

        data = data.split()

        if data[0] == "IN-USE":
            print("The name is in use. Please select different name.")
            login()
        elif data[0] == "HELLO":
            print("\nHello " + data[1] + "! Welcome to the server.")

            lock = threading.Lock()

            t1 = threading.Thread(target=receive_msg, args=[s, lock])
            t1.start()
    
            send_msg(s, lock, data[1])
        elif data[0] == "BUSY":
            print("Server busy. Please come back later.")
            login()
    else:
        print("Only numbers and alphabets allowed.")
        login()

login()