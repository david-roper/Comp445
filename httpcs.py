import socket
import threading
import argparse
import os
import sys
import re
from urllib.parse import urlparse, parse_qs
from json import dumps


def run_server(host, port):
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        listener.bind((host, port))
        listener.listen(5)
        print('httpcs server is listening at', port)
        while True:
            conn, addr = listener.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()
    finally:
        listener.close()


def handle_client(conn, addr):
    print ('New client from', addr)
    try:
        while True:
            data = conn.recv(4024)
            if not data:
                break
            elif data:
                decodedData = data.decode('utf-8')
                decodedData = decodedData + '\r\n\r\n'
                sys.stdout.write(decodedData)
                #decodedData - decodedData.encode('utf-8')
                break
        conn.sendall(decodedData)
        #check in os system for data


    finally:
        conn.close()


# Usage python3 httpcs.py --port 8080 [--port port-number]
parser = argparse.ArgumentParser()
parser.add_argument("--port", help="echo server port", type=int, default=8080)
args = parser.parse_args()
run_server('', args.port)
