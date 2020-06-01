# Libraries
import threading
from threading import Thread
import hashlib
import os
import pickle
import socket
import time
import sys
from time import sleep


# Global Variables 
Alive = True
myNode = None
limit = 5
size = 2**5
PORT = 13333
IP = "192.168.100.2"


# Node class
class Node():
    def __init__(self, port):
        self.ID = getHash(port)
        self.Port = port
        self.Successor1 = self
        self.Successor2 = self
        self.Predecessor = self
        self.FingerTable = []
        self.myFileInformation = []
        self.backupFileInformation = []

# Hash function 
def getHash(value):
    global size

    p = str(value)
    Hash = hashlib.sha1(p.encode())
    intVal = int(Hash.hexdigest(), 16)
    return intVal % size

# MENU thread
def menu():
    global Alive
    global myNode
    global IP

    while Alive:
        print("")
        print("")
        print("Enter 1 to download a file.")
        print("Enter 2 to upload a file")
        print("Enter 3 to know your ID.")
        print("Enter 4 to know who your Successor1 is.")
        print("Enter 5 to know who your Successor2 is.")
        print("Enter 6 to know who your Predecessor is.")
        print("Enter 7 to leave.")
        print("Enter 8 to see the files you are responsible for.")
        print("Enter 9 to see the backup files you have.")
        print("Enter 10 to see Fingertable")

        choice = input("Choice: ")
        choice = int(choice)
        print("")
        if choice == 10:
            for i in myNode.FingerTable:
                print(i.ID)
        elif choice == 8:
            for i in myNode.myFileInformation:
                print(i)
        elif choice == 9:
            for i in myNode.backupFileInformation:
                print(i)
        elif choice == 4:
            print("Successor1 ID is ", myNode.Successor1.ID)
        elif choice == 3:
            print("Your ID is ", myNode.ID)
        elif choice == 5:
            print("Successor2 ID is ", myNode.Successor2.ID)
        elif choice == 6:
            print("Predecessor ID is ", myNode.Predecessor.ID)
        elif choice == 2:
            filename = input("Enter the name of the file: ")
            find_file = os.path.isfile(filename)
            if find_file == False:
                print('No such file in the directory.')
                continue
            # if there is only one peer in the system
            if int(myNode.ID) == int(myNode.Successor1.ID):
                if filename not in myNode.myFileInformation:
                    myNode.myFileInformation.append(filename)
                continue
            else:
                hashOfFile = getHash(filename)
                print("Hash of file: ", hashOfFile)
                PeerResponsible = getPeerIDResponisble(hashOfFile)
                print("Peer responsible: ", PeerResponsible.ID)

                if int(myNode.ID) == int(PeerResponsible.ID):
                    if filename not in myNode.myFileInformation:
                        myNode.myFileInformation.append(filename)
                    else:
                        continue

                    # send to successor for backup 
                    temp2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp2.connect((IP, myNode.Successor1.Port))
                    sendd = (IP, hashOfFile, filename, "FileListen1")
                    temp2.send(pickle.dumps(sendd))
                    Rec = pickle.loads(temp2.recv(1024))
                    temp2.close()

                    if Rec == "haveitalready":
                        continue
                    temp3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp3.connect((Rec))

                    # sending file over
                    with open(filename, 'rb') as f:
                        data = f.read(1024)
                        while data:
                            temp3.send(data)
                            data = f.read(1024)
                    temp3.close()
                    print('file sent to successor')
                else:
                    tempp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    tempp.connect((IP, PeerResponsible.Port))
                    sendd = (IP, hashOfFile, filename, "FileListen2")
                    tempp.send(pickle.dumps(sendd))
                    Rec = pickle.loads(tempp.recv(1024))
                    tempp.close()
                    print('here2')
                    if Rec == "haveitalready":
                        continue

                    temp3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp3.connect((Rec))
                    print('here tooooooo')

                    # sending file
                    with open(filename, 'rb') as f:
                        data = f.read(1024)
                        while data:
                            temp3.send(data)
                            data = f.read(1024)
                    temp3.close()
        elif choice == 1:
            filename = input("Enter filename: ")

            hashOfFile = getHash(filename)
            responsible = getPeerIDResponisble(hashOfFile)
            resPort = responsible.Port
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((IP, resPort))
            sending = (IP, hashOfFile, filename, "getFile")
            s.send(pickle.dumps(sending))

            Recieved2 = pickle.loads(s.recv(1024))
            if Recieved2 == "sorry":
                s.close()
                continue
            else:
                with open(filename, 'wb') as f:
                    data = s.recv(1024)
                    while data:
                        f.write(data)
                        data = s.recv(1024)
            s.close()
        elif choice == 7:
            leave()
            Alive = False
            os._exit(0)
        else:
            print("Not an option")


# Finds the successor
def getSuccessor(key):
    global myNode
    global IP

    if int(key) > int(myNode.ID):
        if int(key) > int(myNode.Successor1.ID) and int(myNode.ID) > int(myNode.Successor1.ID):
            return myNode.Successor1
        elif int(key) < int(myNode.Successor1.ID):
            return myNode.Successor1
        elif int(key) > int(myNode.Successor1.ID):
            K = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            K.connect((IP, myNode.Successor1.Port))
            sending = (IP, "findSucc", key)
            K.send(pickle.dumps(sending))
            reply = pickle.loads(K.recv(1024))
            K.close()
            return reply
        else:
            print("collision")
    elif int(key) < int(myNode.ID):
        if int(key) < int(myNode.Predecessor.ID) and int(myNode.ID) < int(myNode.Predecessor.ID):
            return myNode
        elif int(key) > int(myNode.Predecessor.ID):
            return myNode
        elif int(key) < int(myNode.Predecessor.ID):
            K = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            K.connect((IP, myNode.Predecessor.Port))
            sending = (IP, "findSucc", key)
            K.send(pickle.dumps(sending))
            reply = pickle.loads(K.recv(1024))
            K.close()
            return reply
        else:
            print('collision')
    else:
        print('collision')


# LISTEN thread
def listen():
    global myNode 
    global PORT
    global IP
    global Alive
    global myNode

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((IP, PORT))
    s.listen(100000000)


    while Alive:
        # try:
            client, address = s.accept()
            msg = pickle.loads(client.recv(1024))
            if msg[1] == "Alive":
                reply = (IP, myNode.Predecessor, myNode.Successor1)
                client.send(pickle.dumps(reply))
            elif msg[1] == "filetransfer1":
                for i in myNode.backupFileInformation:
                    myNode.myFileInformation.append(i)
                    myNode.backupFileInformation.remove(i)
                reply = "done"
                client.send(pickle.dumps(reply))
            elif msg[1] == "filetransfer2":
                for i in myNode.backupFileInformation:
                    myNode.myFileInformation.append(i)
                    myNode.backupFileInformation.remove(i)
                    hashOfFile = getHash(i)
                    temp2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp2.connect((IP, myNode.Successor1.Port))
                    sendd = (IP, hashOfFile, i, "FileListen3")
                    temp2.send(pickle.dumps(sendd))
                    Rec = pickle.loads(temp2.recv(1024))
                    temp2.close()

                    if Rec == "haveitalready":
                        continue
                    temp3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp3.connect((Rec))

                    # sending file over
                    with open(i, 'rb') as f:
                        data = f.read(1024)
                        while data:
                            temp3.send(data)
                            data = f.read(1024)
                    temp3.close()

            elif msg[1] == "findSucc":
                succ1 = getSuccessor(msg[2])
                reply = succ1
                client.send(pickle.dumps(reply))
            elif msg[1] == "getSucc1":
                succ1 = myNode.Successor1
                reply = succ1
                client.send(pickle.dumps(reply))
            elif msg[1] == "getPred":
                pred = myNode.Predecessor
                reply = pred
                client.send(pickle.dumps(reply))
            elif msg[1] == "newSuccessor1":
                myNode.Successor1 = msg[2]
                reply = "ok"
                client.send(pickle.dumps(reply))
            elif msg[1] == "newSuccessor2":
                myNode.Successor2 = msg[2]
                reply = "ok"
                client.send(pickle.dumps(reply))
            elif msg[1] == "newPredecessor":
                myNode.Predecessor = msg[2]
                reply = "ok"
                client.send(pickle.dumps(reply))
            elif msg[1] == "findfilekey":
                find = getPeerIDResponisble(msg[2])
                client.send(pickle.dumps(find))
            elif msg[2] == "join":
                if int(myNode.Predecessor.ID) == int(myNode.ID) and int(myNode.ID) == int(myNode.Successor1.ID):
                    reply = (IP, myNode, msg[1], myNode)
                    myNode.Predecessor = msg[1]
                    myNode.Successor1 = msg[1]
                    client.send(pickle.dumps(reply))
                elif int(myNode.Successor2.ID) == int(myNode.ID):
                    succ1 = getSuccessor(msg[1].ID)
                    succ2 = succ1.Successor1

                    if int(myNode.ID) != int(succ1.Predecessor.ID):
                        kk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        kk.connect((IP, succ1.Port))
                        send = (IP, "getPred")
                        kk.send(pickle.dumps(send))
                        pred = pickle.loads(kk.recv(1024))
                        kk.close()
                    else:
                        pred = myNode

                    if int(succ1.ID) == int(myNode.ID):
                        myNode.Predecessor = msg[1]
                        myNode.Successor2 = msg[1]
                    else:
                        l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        l.connect((IP, succ1.Port))
                        send = (IP, "newPredecessor", msg[1])
                        l.send(pickle.dumps(send))
                        reply = pickle.loads(l.recv(1024))
                        l.close()

                        l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        l.connect((IP, succ2.Port))
                        send = (IP, "newSuccessor2", msg[1])
                        l.send(pickle.dumps(send))
                        reply = pickle.loads(l.recv(1024))
                        l.close()

                    if int(pred.ID) == int(myNode.ID):
                        myNode.Successor1 = msg[1]
                        myNode.Successor2 = myNode.Predecessor
                    else:
                        l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        l.connect((IP, succ2.Port))
                        send = (IP, "newSuccessor1", msg[1])
                        l.send(pickle.dumps(send))
                        reply = pickle.loads(l.recv(1024))
                        l.close()

                        l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        l.connect((IP, succ2.Port))
                        send = (IP, "newSuccessor2", myNode)
                        l.send(pickle.dumps(send))
                        reply = pickle.loads(l.recv(1024))
                        l.close()
                    reply = (IP, succ1, pred, pred)
                    client.send(pickle.dumps(reply))
                else:
                    succ1 = getSuccessor(msg[1].ID)
                    succ2 = succ1.Successor1
                    pred = succ1.Predecessor
                    if int(myNode.ID) != int(succ1.Predecessor.ID):
                        kk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        kk.connect((IP, succ1.Port))
                        send = (IP, "getPred")
                        kk.send(pickle.dumps(send))
                        pred = pickle.loads(kk.recv(1024))
                        kk.close()
                    else:
                        pred = myNode


                    lols = pred.Predecessor
                    if int(lols.ID) != int(myNode.ID):
                        l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        l.connect((IP, lols.Port))
                        send = (IP, "newSuccessor2", msg[1])
                        l.send(pickle.dumps(send))
                        reply = pickle.loads(l.recv(1024))
                        l.close()
                    else:
                        myNode.Successor2 = msg[1]

                    if int(pred.ID) != int(myNode.ID):
                        l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        l.connect((IP, pred.Port))
                        send = (IP, "newSuccessor2", succ1)
                        l.send(pickle.dumps(send))
                        reply = pickle.loads(l.recv(1024))
                        l.close()

                        l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        l.connect((IP, pred.Port))
                        send = (IP, "newSuccessor1", msg[1])
                        l.send(pickle.dumps(send))
                        reply = pickle.loads(l.recv(1024))
                        l.close()
                    else:
                        myNode.Successor2 = succ1
                        myNode.Successor1 = msg[1]

                    if int(succ1.ID) != int(myNode.ID):
                        l = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        l.connect((IP, succ1.Port))
                        send = (IP, "newPredecessor", msg[1])
                        l.send(pickle.dumps(send))
                        reply = pickle.loads(l.recv(1024))
                        l.close()
                    else:
                        myNode.Predecessor = msg[1]

                    reply = (IP, succ1, succ2, pred)
                    client.send(pickle.dumps(reply))
            elif msg[3] =="FileListen1":
                filename = msg[2]
                if filename not in myNode.backupFileInformation:
                    temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp.bind((IP, 7245))
                    addressOnWhichToListen = temp.getsockname()
                    client.send(pickle.dumps(addressOnWhichToListen))
                    temp.listen(10)
                    client2, address2 = temp.accept()
                    if filename not in myNode.backupFileInformation:
                        with open(filename, 'wb') as f:
                            data = client2.recv(1024)
                            while data:
                                f.write(data)
                                data = client2.recv(1024)
                        myNode.backupFileInformation.append(filename)
                    temp.close()
                else:
                    reply = "haveitalready"
                    client.send(pickle.dumps(reply))
            elif msg[3] =="FileListen3":
                filename = msg[2]
                if filename not in myNode.backupFileInformation:
                    temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp.bind((IP, 7249))
                    addressOnWhichToListen = temp.getsockname()
                    client.send(pickle.dumps(addressOnWhichToListen))
                    temp.listen(10)
                    client2, address2 = temp.accept()
                    if filename not in myNode.backupFileInformation:
                        with open(filename, 'wb') as f:
                            data = client2.recv(1024)
                            while data:
                                f.write(data)
                                data = client2.recv(1024)
                        myNode.backupFileInformation.append(filename)
                    temp.close()
                else:
                    reply = "haveitalready"
                    client.send(pickle.dumps(reply))
            elif msg[3] == "FileListen2":
                filename = msg[2]
                if filename not in myNode.myFileInformation:
                    temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp.bind((IP, 7734))
                    addressOnWhichToListen = temp.getsockname()
                    client.send(pickle.dumps(addressOnWhichToListen))
                    temp.listen(10)
                    client2, address2 = temp.accept()
                    if filename not in myNode.myFileInformation:
                        with open(filename, 'wb') as f:
                            data = client2.recv(1024)
                            while data:
                                f.write(data)
                                data = client2.recv(1024)
                        myNode.myFileInformation.append(filename)
                        temp.close()
                    else:
                        continue

                    # sending file to successor as backup
                    succPort = myNode.Successor1.Port
                    hashOfFile = msg[0]
                    temp2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp2.connect((IP, succPort))
                    sending2 = (IP, hashOfFile, filename, "FileListen1")
                    temp2.send(pickle.dumps(sending2))
                    re = pickle.loads(temp2.recv(1024))
                    temp2.close()

                    if re == "haveitalready":
                        continue

                    temp3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp3.connect((re))

                    # sending file
                    with open(filename, 'rb') as f:
                        data = f.read(1024)
                        while data:
                            temp3.send(data)
                            data = f.read(1024)
                        temp3.close()
                else:
                    reply = "haveitalready"
                    client.send(pickle.dumps(reply))
            elif msg[3] == "getFile":
                filename = msg[2]
                if filename in myNode.myFileInformation:
                    client.send(pickle.dumps("Ihaveit"))
                    with open(filename, 'rb') as f:
                        data = f.read(1024)
                        while data:
                            client.send(data)
                            data = f.read(1024)
                else:
                    client.send(pickle.dumps("sorry"))
                    continue
        # except:
        #     Alive = False
        #     os._exit(1)

def getPeerIDResponisble(key):
    global myNode
    global IP

    if int(myNode.ID) == int(key):
        return Node
    elif int(key) > int(myNode.ID):
        if int(key) >= int(myNode.Successor1.ID) and int(myNode.ID) > int(myNode.Successor1.ID):
            return myNode.Successor1
        elif int(key) > int(myNode.Successor1.ID):
            K = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            K.connect((IP, myNode.Successor1.Port))
            sending = (IP, "findfilekey", key)
            K.send(pickle.dumps(sending))
            reply = pickle.loads(K.recv(1024))
            K.close()
            return reply
        elif int(key) <= int(myNode.Successor1.ID):
            return myNode.Successor1
    else:
        if int(key) < int(myNode.Predecessor.ID) and int(myNode.ID) < int(myNode.Predecessor.ID):
            return myNode
        elif int(key) >= int(myNode.Predecessor.ID):
            return myNode
        elif int(key) < int(myNode.Predecessor.ID):
            K = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            K.connect((IP, myNode.Predecessor.Port))
            sending = (IP, "findfilekey", key)
            K.send(pickle.dumps(sending))
            reply = pickle.loads(K.recv(1024))
            K.close()
            return reply

def leave():
    global myNode
    global IP
    global Alive
    if int(myNode.Predecessor.ID) == int(myNode.ID) and int(myNode.ID) == int(myNode.Successor1.ID):
        return 
    elif int(myNode.Successor2.ID) == int(myNode.ID):
        succPort = myNode.Successor1.Port
        k1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k1.connect((IP, succPort))
        send1 = (IP, "newPredecessor", myNode.Successor1)
        k1.send(pickle.dumps(send1))
        reply = pickle.loads(k1.recv(1024)) 
        k1.close()

        k2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k2.connect((IP, succPort))
        send2 = (IP, "newSuccessor1", myNode.Successor1)
        k2.send(pickle.dumps(send2))
        reply = pickle.loads(k2.recv(1024)) 
        k2.close()

        k3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k3.connect((IP, succPort))
        send3 = (IP, "newSuccessor2", myNode.Successor1)
        k3.send(pickle.dumps(send3))
        reply = pickle.loads(k3.recv(1024)) 
        k3.close()


        k4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k4.connect((IP, succPort))
        send4 = (IP, "filetransfer1", myNode)
        k4.send(pickle.dumps(send4))
        reply = pickle.loads(k4.recv(1024))
        k4.close()
    elif int(myNode.Successor2.ID) == int(myNode.Predecessor.ID):
        succPort = myNode.Successor1.Port
        predPort = myNode.Predecessor.Port

        k1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k1.connect((IP, succPort))
        send1 = (IP, "newPredecessor", myNode.Predecessor)
        k1.send(pickle.dumps(send1))
        reply = pickle.loads(k1.recv(1024))
        k1.close()

        k2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k2.connect((IP, succPort))
        send2 = (IP, "newSuccessor1", myNode.Predecessor)
        k2.send(pickle.dumps(send2))
        reply = pickle.loads(k2.recv(1024))
        k2.close()

        k3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k3.connect((IP, succPort))
        send3 = (IP, "newSuccessor2", myNode.Successor1)
        k3.send(pickle.dumps(send3))
        reply = pickle.loads(k3.recv(1024))
        k3.close()

        k4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k4.connect((IP, predPort))
        send4 = (IP, "newPredecessor", myNode.Successor1)
        k4.send(pickle.dumps(send4))
        reply = pickle.loads(k4.recv(1024))
        k4.close()

        k5 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k5.connect((IP, predPort))
        send5 = (IP, "newSuccessor1", myNode.Successor1)
        k5.send(pickle.dumps(send5))
        reply = pickle.loads(k5.recv(1024))
        k5.close()

        k6 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k6.connect((IP, predPort))
        send6 = (IP, "newSuccessor2", myNode.Predecessor)
        k6.send(pickle.dumps(send6))
        reply = pickle.loads(k6.recv(1024))
        k6.close()

        k7 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k7.connect((IP, succPort))
        send7 = (IP, "filetransfer2", myNode)
        k7.send(pickle.dumps(send7))
        k7.close()
    else:
        succPort = myNode.Successor1.Port
        predPort = myNode.Predecessor.Port

        k1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k1.connect((IP, predPort))
        send1 = (IP, "newSuccessor1", myNode.Successor1)
        k1.send(pickle.dumps(send1))
        k1.close()

        k2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k2.connect((IP, succPort))
        send2 = (IP, "newPredecessor", myNode.Predecessor)
        k2.send(pickle.dumps(send2))
        k2.close()

        k7 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        k7.connect((IP, succPort))
        send7 = (IP, "filetransfer2", myNode)
        k7.send(pickle.dumps(send7))
        k7.close()








# Pings Thread
def pings():
    global Alive
    global PORT
    global IP
    global myNode

    Unanswered = 0

    while Alive:
        try:
            succ = myNode.Successor1
            pred = myNode.Predecessor
            succPort = succ.Port
            time.sleep(3)
            if int(succ.ID) != int(myNode.ID) and int(pred.ID) != int(myNode.ID):
                try:
                    jj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    jj.connect((IP, succPort))
                    sd = (IP, "Alive")
                    jj.send(pickle.dumps(sd))
                    re = pickle.loads(jj.recv(1024))

                    if int(re[1].ID) != int(myNode.ID):
                        myNode.Successor1 = re[1]
                        if int(myNode.Successor1.ID) != int(myNode.ID):
                            lols = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            lols.connect((IP, myNode.Successor1.Port))
                            sjf = (IP, "newPredecessor", myNode)
                            lols.send(pickle.dumps(sjf))
                            reply = pickle.loads(lols.recv(1024))
                        else:
                            myNode.Predecessor = myNode

                    myNode.Successor2 = re[2]
                    Unanswered = 0
                    jj.close()
                except:
                    Unanswered = Unanswered + 1
                    print("Unanswered: ", Unanswered)
                    if Unanswered == 3:
                        if int(myNode.Successor2.ID) == int(myNode.ID):
                            myNode.Predecessor = myNode
                            myNode.Successor1 = myNode
                            myNode.Successor2 = myNode
                            Unanswered = 0
                        else:
                            myNode.Successor1 = myNode.Successor2
                            succNew = myNode.Successor1
                            succNewPort = succNew.Port

                            if int(myNode.Predecessor.ID) == int(myNode.Successor2.ID):
                                gh = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                gh.connect((IP, succNewPort))
                                se = (IP, "newPredecessor", myNode)
                                gh.send(pickle.dumps(se))
                                reply = pickle.loads(gh.recv(1024))
                                gh.close()

                                gh = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                gh.connect((IP, succNewPort))
                                se = (IP, "newSuccessor2", succNew)
                                gh.send(pickle.dumps(se))
                                reply = pickle.loads(gh.recv(1024))

                                myNode.Successor2 = succNew
                                myNode.Predecessor = succNew
                        Unanswered = 0

            else:
                continue
        except:
            Alive = False
            os._exit(0)

def main():
    global myNode
    global PORT
    global IP


    print("Enter 0 if you want to make a NEW system.")
    print("Enter 1 if you want to join to an existing system.")

    choice = input("Choice: ")
    choice = int(choice)

    if choice == 0:
        myNode = Node(PORT)

        menuThread = Thread(target = menu, args = ())
        listenThread = Thread(target = listen, args = ())
        pingThread = Thread(target = pings, args = ())
        # fingerThread = Thread(target = fingertable, args = ())
        listenThread.start()
        menuThread.start()
        pingThread.start()
        # fingerThread.start()

    elif choice == 1:
        myNode = Node(PORT)

        portNumber = input("Enter the port of the peer you want to connect to: ")
        portNumber = int(portNumber)

        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.connect((IP, portNumber))

        sending = (IP, myNode, "join")
        s2.send(pickle.dumps(sending))
        reply = pickle.loads(s2.recv(1024))

        myNode.Successor1 = reply[1]
        myNode.Successor2 = reply[2]
        myNode.Predecessor = reply[3]

        s2.close()

        menuThread = Thread(target = menu, args = ())
        listenThread = Thread(target = listen, args = ())
        pingThread = Thread(target = pings, args = ())
        # fingerThread = Thread(target = fingertable, args = ())
        listenThread.start()
        menuThread.start()
        pingThread.start()
        # fingerThread.start()

    if Alive == False:
        listenThread.join()
        pingThread.join()
        menuThread.join()
        # fingertable.join()
        os._exit(0)





main()






