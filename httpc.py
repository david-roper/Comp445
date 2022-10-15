import socket
import argparse
import sys
import re
from urllib.parse import urlparse, parse_qs
from json import dumps

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

def run_client(
    request,
    url: str, 
    data, 
    infile, 
    outfile, 
    headers,
    help, 
    verbose,
    port,
    parser: argparse.ArgumentParser
):
    if help:
        if len(help) > 1:
            if help[1].lower() == 'get':
                print(HELP_GET)
            elif help[1].lower() == 'post':
                print(HELP_POST)
        else:
            # general help with no arguments
            print(HELP_GENERAL)
            pass
        return
    if not url:
        print('Please specify a url.')
        return
    # if 'http:' not in url or 'https:' not in url:
    #     url = 'http://' + url
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        # print("connected")
        
        # print('request:', request)
        print(args)
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        print('host:', host)
        path = parsed_url.path
        print('path:', path)
        query_params = parsed_url.query
        conn.connect((host, port))

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
        if verbose:
            print('**********************REQUEST**********************')
            print(line)
            print('***************************************************')
        
        request = line.encode("utf-8")
        conn.sendall(request)
        
        # MSG_WAITALL waits for full request or error
        response = b""
        
        while True:
            chunk = conn.recv(4096)
            if len(chunk) == 0:     # No more data received, quitting
                break
            response = response + chunk
       
        
        # sys.stdout.write("request recieved \n")
        decoded_resp = response.decode("utf-8")
        if verbose:
            sys.stdout.write("Output: \n" + decoded_resp)
        else:
            non_verbose_resp = decoded_resp.split('\r\n\r\n')
            sys.stdout.write("\n" + non_verbose_resp[1])
        with open('response.txt', 'w') as ftw:
            ftw.write(decoded_resp)
    finally:
        conn.close()


# Usage: python httpc.py --host host --port port
# example: python httpc.py --host httpbin.org --port 80
# parser = argparse.ArgumentParser()
# parser.add_argument("--get", help="""usage: httpc get [-v] [-h key:value] URL 
# Get executes a HTTP GET request for a given URL.\n 
# -v Prints the detail of the response such as protocol, status, and headers. \n
# -h key:value Associates headers to HTTP Request with the format 'key:value'.""",type=str, default="httpbin.org/get?status=418")

parser = argparse.ArgumentParser(description='httpc is a curl like application that supports http get and post requests.', add_help=False)
parser.add_argument('help', nargs = '*', help='Used to provide info on httpc functionality', default = '')
parser.add_argument('request', choices=['get', 'post', 'GET', 'POST'], nargs = '?', help='HTTP request method, the option are the following: \n get \n post')
parser.add_argument('url', help='URL', nargs = '?')
parser.add_argument('--d', dest='data', help='payload data to post', default=None)
parser.add_argument('-f', dest='infile', help='file containing POST data',default=None)
parser.add_argument('-o', dest='outfile', help='file to store response',default=None)
parser.add_argument('-h', dest='headers', action='append', help='HTTP headers to include',default=None)
parser.add_argument('-v', dest='verbose', action='store_true', help='prints verbose output', default=False)
parser.add_argument("--port", help="server port to connect to", type=int, default=80)
args = parser.parse_args()
# print(args)
run_client(
    args.request,
    args.url,
    args.data,
    args.infile,
    args.outfile,
    args.headers,
    args.help,
    args.verbose,
    args.port,
    parser
)
