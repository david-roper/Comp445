import socket
import threading
import argparse
import os
import sys
import re
from urllib.parse import urlparse, parse_qs
from json import dumps
from helpers import search_data_dir, edit_data
from packet import Packet

#Code created by David Roper (40131739) and Gianfranco Dumoulin (40097768) 

# Usage python3 udps.py --port 8080 [--port port-number]
# desktop = os.path.join(os.environ['USERPROFILE'])
# desktop = desktop + '\Desktop\Comp445\data'

def handle_get(path, dir):
    if path == '/':
        
        content = search_data_dir(dir)
    else:
        
        content = search_data_dir(dir, path)
    return content
   
def handle_post(path, value, dir, overwrite = True):
    if not value or path == '/':
        content = "400 Bad Request"
        return content
    edit_data(path, value, dir, overwrite)
    return "201 Created"


def parse_http_one_request(data) -> dict:
    if not data:
        return dict()
    # takes in http1.0 data and returns a dict
    decodedData = data.decode('utf-8')
    decodedData = decodedData + '\r\n\r\n' + ""

    decodedDataEdit = decodedData.strip("\n")
    decodedDataEdit = decodedDataEdit.strip("\r")
    decodedDataEdit = decodedDataEdit.replace("\n", " ")                
    decodedDataEdit = decodedDataEdit.replace("\r", "")

    decodedDataList = decodedDataEdit.split(" ")
    if decodedDataList[1] == '':
        decodedDataList[1] = '/'
    
    decodedDataList = list(filter(None, decodedDataList))

    return decodedDataList

def run_server(host, port,verbose,dir):
    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.settimeout(5)
    try:
        conn.bind(('localhost', port))
        print(f'DEBUG: Server listening on port {port}...')
        while True:
            data, sender = conn.recvfrom(1024)
            threading.Thread(target=handle_client, args=(conn, verbose,dir,data, sender)).start()
    except socket.timeout:
        print("ERROR socket timeout")
    finally:
        conn.close()


    # listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # try:
    #     listener.bind((host, port))
    #     if verbose:
    #         print(f'DEBUG: Server running')
    #     listener.listen(5)
    #     if verbose:
    #         print(f'DEBUG: Server listening on port {port}...')
    #     while True:
    #         conn, addr = listener.accept()
    #         threading.Thread(target=handle_client, args=(conn, addr,verbose,dir)).start()
    # finally:
    #     listener.close()

def handle_client(conn, verbose, dir,data,sender):
    if verbose:
        print(f'DEBUG: New client from {sender}')
        print(f'DEBUG: directory of server set to \"{dir}\"')
    global curPack
    p = Packet.from_bytes(data)

    peerIp = p.peer_ip_addr
    serverPort = p.peer_port
    timeout = 5
    eSeq = 4
    endConn = False

    if p.packet_type == 5:
        msg3 = "Ack to server end connection"
        final = Packet(packet_type=5,
                   seq_num=99,
                   peer_ip_addr=peerIp,
                   peer_port=serverPort,
                   payload=msg3.encode("utf-8"))
        endConn = True
        conn.sendto(final.to_bytes(),sender)
        return
    elif p.packet_type == 2:
        msg2 = "Hello from server"
        curPack = Packet(packet_type=3,
                   seq_num=3,
                   peer_ip_addr=peerIp,
                   peer_port=serverPort,
                   payload=msg2.encode("utf-8"))
        eSeq = 4
        handleAck = True
        while handleAck:
            try:
                conn.sendto(curPack.to_bytes(),sender)
                conn.settimeout(timeout)
                while True:
                    Ack, router = conn.recvfrom(1024)
                    if Ack:
                        pAck = Packet.from_bytes(Ack)
                        if pAck.seq_num == eSeq:
                            print("recieved packet: ", pAck)
                            handleAck = False
                            break
                        
            except conn.timeout:
                print("Connection time out")


    try:
        while True:
            while True:
                try:
                    data, sender = conn.recvfrom(1024)
                    if data:
                        p = Packet.from_bytes(data)
                        if p.seq_num == 5:
                            msg3 = "Ack to server end connection"
                            final = Packet(packet_type=5,
                            seq_num=99,
                            peer_ip_addr=peerIp,
                            peer_port=serverPort,
                            payload=msg3.encode("utf-8"))
                            conn.sendto(final.to_bytes(),sender)
                            endConn = True
                            break
                        elif p.seq_num != 4:
                            break
                except conn.timeout:
                    continue
            if endConn:
                break  
            p = Packet.from_bytes(data)
            print("Router: ", sender)
            print("Packet: ", p)
            print("Payload: ", p.payload.decode("utf-8"))

            data = p.payload

            if verbose:
                print(F'DEBUG: Receiving data...')
            if not data:
                break
            elif data:
                decodedData = data.decode('utf-8')
                if (verbose):
                    print('DEBUG request data received:\n', decodedData)
                decodedDataList = parse_http_one_request(data)
                
                decodedData = decodedData + '\r\n\r\n'
               
                

                if (decodedDataList[0] == 'GET'):
                    getData = handle_get(decodedDataList[1], dir)
                    if verbose:
                        print("DEBUG GET data being sent: ",getData)
                    decodedData = getData
                elif (decodedDataList[0] == 'POST'):
                    overwrite = False

                    if('overwrite:true' in decodedDataList):
                        overwrite = True
                    if('Content-Length:' in decodedDataList):
                        cPoint = decodedDataList.index('Content-Length:')
                        
                        dataPoint = len(decodedDataList) -2 - cPoint
                        
                        dataList = decodedDataList[-dataPoint:]

                        postText = ' '.join(dataList)
                        
                        
                        decodedData = handle_post(decodedDataList[1], postText, dir, overwrite)
                        if verbose:
                            print("DEBUG POST data being sent\n",decodedData)
                    else:
                        decodedData = handle_post(decodedDataList[1],"", dir, overwrite)
                        if verbose:
                            print("DEBUG POST data being sent\n",decodedData)
                        
                    
                    
                
                decodedData = decodedData + '\r\n\r\n'
                decodedData = decodedData.encode('utf-8')
                p.payload = decodedData
                #sys.stdout.write(decodedData)
                #os.path("")
                break
        curPack = Packet(packet_type=1,
                           seq_num=p.seq_num,
                           peer_ip_addr=peerIp,
                           peer_port=serverPort,
                           payload=p.payload)
        eSeq = (curPack.seq_num+1)%2
        

        sendAck = True
        while sendAck:
            try:
                conn.sendto(p.to_bytes(), sender)
                conn.settimeout(timeout)
                while True:
                    dAck, sender = conn.recvfrom(1024)
                    AckPack = Packet.from_bytes(dAck)
                    if AckPack.seq_num == 5:
                        msg3 = "Ack to server end connection"
                        final = Packet(packet_type=5,
                        seq_num=99,
                        peer_ip_addr=peerIp,
                        peer_port=serverPort,
                        payload=msg3.encode("utf-8"))
                        conn.sendto(final.to_bytes(),sender)
                        endConn = True
                        sendAck = False
                        break
                    elif AckPack.seq_num == eSeq:
                        print("Data received from packet")
                        sendAck = False
                        break


            except conn.timeout:
                print("Connection timeout")
        
        #conn.sendall(decodedData) #has to send an encoded in utf-8 string
        #check in os system for data
    
    except Exception as e:
        print("Error: ", e)

    finally:
        conn.close()

# Usage python3 udps.py --port 8080 [--port port-number]

parser = argparse.ArgumentParser()
verbose_option = {'dest':'verbose', 'action':'store_true', 'help':'prints verbose output', 'default': False}
directory_option = {'dest':'dir','help':'the directory of the file server, no preceding /, no trailing /', 'default': 'data'}
parser.add_argument("--port", help="echo server port", type=int, default=8080)
parser.add_argument("-v", **verbose_option)
parser.add_argument("-d", **directory_option)

args = parser.parse_args()
run_server('', args.port,args.verbose,args.dir)

# python3 udps.py --port 8080 -d "data2"