import socket
import argparse
import ipaddress
import sys
import re
from urllib.parse import urlparse, parse_qs
from json import dumps
from packet import Packet

#Code created by David Roper (40131739) and Gianfranco Dumoulin (40097768) 

#server test python3 udpc.py get http://localhost --port 8080
#run router as such
#cd to source/router.go directory
#run the following go command
#go run router.go --port=3000 --drop-rate=0.2 --max-delay=10ms --seed=1
#./router --port=3000 --drop-rate=0.2 --max-delay=10ms --seed=1

HELP_GET = """usage: httpc get [-v] [-h key:value] URL 
Get executes a HTTP GET request for a given URL. 
 -v Prints the detail of the response such as protocol, status, and headers. 
 -h key:value Associates headers to HTTP Request with the format 'key:value'."""

HELP_POST = """usage: httpc post [-v] [-h key:value] [-d inline-data] [-f file] URL
Post executes a HTTP POST request for a given URL with inline data or from
file.
 -v Prints the detail of the response such as protocol, status, and headers.
 -h key:value Associates headers to HTTP Request with the format 'key:value'.
 -d string Associates an inline data to the body HTTP POST request.
 -f file Associates the content of a file to the body HTTP POST request.
Either [-d] or [-f] can be used but not both.
"""

HELP_GENERAL = """httpc is a curl-like application but supports HTTP protocol only.
Usage:
    httpc command [arguments]
The commands are:
    get or GET executes a HTTP GET request and prints the response.
    post or POST executes a HTTP POST request and prints the response.
    help prints this screen.
Use "httpc help [command]" for more information about a command."""

def print_help(request):
    if not request:
        request = ''
    if help:
    # if len(help) > 1:
        if request.lower() == 'get':
            print(HELP_GET)
            return
        elif request.lower() == 'post':
            print(HELP_POST)
            return
        else:
            # general help with no arguments
            print(HELP_GENERAL)
            return
    # print('url', url)


def run_client(
    request,
    url, 
    data, 
    infile, 
    outfile, 
    headers,
    verbose,
    port
):
    if not url:
        print('Please specify a url.')
        return
    if '\'' in url or '\"' in url or '‘' in url or '’' in url:
        filter_chars = ['\'', '\"', '‘', '’']
        url = ''.join(letter for letter in url if letter not in filter_chars)

    router_addr = 'localhost'
    router_port = 3000

    server_addr = 'localhost'
    server_port = 8080

    
    peer_ip = ipaddress.ip_address(socket.gethostbyname('localhost'))

    #handshake 1

    msg = "Hi server"

    h1 = Packet(packet_type=2,
                   seq_num=2,
                   peer_ip_addr=peer_ip,
                   peer_port=server_port,
                   payload=msg.encode("utf-8"))

    #handshake 2
    msg2 = "Ack msg to Server"

    h2 = Packet(packet_type=4,
                   seq_num=4,
                   peer_ip_addr=peer_ip,
                   peer_port=server_port,
                   payload=msg2.encode("utf-8"))


    #final ack
    msg3 = "Ack to server end connection"
    final = Packet(packet_type=5,
                   seq_num=69,
                   peer_ip_addr=peer_ip,
                   peer_port=server_port,
                   payload=msg3.encode("utf-8"))

    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    timeout = 5

    eSeq = 0
    sentSuccess = True

    
    
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    path = parsed_url.path
    query_params = parsed_url.query
    #router host and port
    #conn.connect((host, port))

    # Build request string
    line = f'{request.upper()} {path}'
    if query_params:
        line += f'?{parsed_url.query}'
    line += ' HTTP/1.0\n'
    line += f'Host: {host}\n'
    # Add headers
    if headers:
        for header in headers:
            line += f'{header}\n'
    # if request is of type get, don't send payload
    # because it vioaltes http specifications
    if request.lower() != 'get' and data:
        line += f'Content-Length: {len(data)}'
        line += f'\n\n{data}\n\n'
    # add a newline at the end
    line += '\n'

    
    request = line.encode("utf-8")

    #print(request.decode("utf-8"))

    p = Packet(packet_type=0,
                seq_num=0,
                peer_ip_addr=peer_ip,
                peer_port=server_port,
                payload=request)
    
    packetList = [h1,p,final]
    packNum = 0

    

    while packNum < len(packetList):
        sentSuccess = True
        try:
            if packetList[packNum].packet_type == 2: 
                eSeq = 3
            
            elif packetList[packNum].packet_type == 0: 
                
                eSeq = packetList[packNum].seq_num
                print("expected packet type 0 seq: ", eSeq)
            
            elif packetList[packNum].packet_type == 5: 
                eSeq = 69
            conn.sendto(packetList[packNum].to_bytes(), ("localhost",3000))
            print('Send "{}" to router'.format(packetList[packNum].payload.decode("utf-8")))
            conn.settimeout(timeout)

            while True:
                response, sender = conn.recvfrom(4096)
                recP = Packet.from_bytes(response)
                print('Router: ', sender)
                print('Packet: ', recP)
                print('Payload: ' + recP.payload.decode("utf-8"))
                if response:
                    print("Expect seq num: ",eSeq)
                    print("Actual seq num: ", recP.seq_num)
                    if recP.seq_num == eSeq:
                        if recP.packet_type == 1:
                            msg = "ACK packet"

                            rPac =  Packet(packet_type=4,
                            seq_num=(recP.seq_num+1)%2,
                            peer_ip_addr=peer_ip,
                            peer_port=server_port,
                            payload=msg.encode("utf-8"))

                            conn.sendto(rPac.to_bytes(), ("localhost",3000))

                        elif recP.packet_type == 3:

                            conn.sendto(h2.to_bytes(), ("localhost",3000))
                        break
                    elif recP.seq_num == 0 or recP.packet_type == 1:

                        msg = "ACK packet"
                        rPac =  Packet(packet_type=4,
                        seq_num=recP.seq_num,
                        peer_ip_addr=peer_ip,
                        peer_port=server_port,
                        payload=msg.encode("utf-8"))
                        conn.sendto(rPac.to_bytes(), ("localhost",3000)) 

        except socket.timeout:
                sentSuccess = False
                print("trying to send", packetList[packNum])

        
        print('Waiting for a response')
            
            
        if sentSuccess:
            print('recieved response')
            packNum += 1
            try:
                response, sender = conn.recvfrom(4096)
                recP = Packet.from_bytes(response)
                print('Router: ', sender)
                print('Packet: ', recP.seq_num)
                print('Payload: ' + recP.payload.decode("utf-8"))
                
                # MSG_WAITALL waits for full request or error
                # response = b""
                
                # while True:
                #     chunk = conn.recv(4096)
                #     if len(chunk) == 0:     # No more data received, quitting
                #         break
                #     response = response + chunk
            
                decoded_resp = recP.payload.decode("utf-8")
                if verbose:
                    sys.stdout.write("Output: \n" + decoded_resp)
                else:
                    sys.stdout.write("\n" + decoded_resp)
                    decoded_resp = decoded_resp.split('\r\n\r\n')[1]
                    sys.stdout.write("\n" + decoded_resp)
                if outfile:
                    with open(outfile, 'w') as ftw:
                        ftw.write(decoded_resp)
            except socket.timeout:
                print()
            
        

    conn.close()


parser = argparse.ArgumentParser(description='httpc is a curl like application that supports http get and post requests.', add_help=False)
subparsers = parser.add_subparsers(help='sub-command help')

# help parser
help_parser = subparsers.add_parser('help', help='Used to provide info on httpc functionality', add_help=False)
help_parser.set_defaults(which='help')
help_parser.add_argument('request', choices = ['get', 'post', 'GET', 'POST', ''], nargs = '?')

# GET parser
get_parser = subparsers.add_parser('get', help='HTTP get method, the option are the following: \n get \n post', add_help=False)
get_parser.set_defaults(which='get')
get_parser.add_argument('url', help = 'URL')

#POST parser
post_parser = subparsers.add_parser('post', help='HTTP post method, the option are the following: \n get \n post', add_help=False)
post_parser.set_defaults(which='post')
post_parser.add_argument('url', help = 'URL')

data_options = {'dest':'data', 'help':'payload data to post', 'default':None}
infile_options = {'dest':'infile', 'help':'file containing POST data','default':None}
outfile_options = {'dest':'outfile', 'help':'file to store response','default':None}
header_options = {'dest':'headers', 'action':'append', 'help':'HTTP headers to include','default':None}
verbose_option = {'dest':'verbose', 'action':'store_true', 'help':'prints verbose output', 'default':False}
port_option = {'help':"server port to connect to", 'type':int, 'default':80}

get_parser.add_argument('--d', **data_options)
get_parser.add_argument('-f', **infile_options)
get_parser.add_argument('-o', **outfile_options)
get_parser.add_argument('-h',**header_options)
get_parser.add_argument('-v',**verbose_option)
get_parser.add_argument('--port',**port_option)


post_parser.add_argument('--d', **data_options)
post_parser.add_argument('-f', **infile_options)
post_parser.add_argument('-o', **outfile_options)
post_parser.add_argument('-h', **header_options)
post_parser.add_argument('-v', **verbose_option)
post_parser.add_argument('--port', **port_option)

args = parser.parse_args()

if args.which == 'help':
    print_help(args.request)
else:
    run_client(
        args.which,
        args.url,
        args.data,
        args.infile,
        args.outfile,
        args.headers,
        args.verbose,
        args.port
    )
