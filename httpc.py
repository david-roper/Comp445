import socket
import argparse
import sys
import re
from urllib.parse import urlparse, parse_qs
from json import dumps

#Code created by David Roper (40131739) and Gianfranco Dumoulin (40097768)

#the following code is a simple http client which can make simple requests
#running the code 

#server test python3 httpc.py get http://localhost --port 8080
# python3 httpc.py get 'http://httpbin.org/get?course=networking&assignment=1'
# python3 httpc.py get 'http://httpbin.org/status/418'

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
        
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        path = parsed_url.path
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

        
        request = line.encode("utf-8")
        conn.sendall(request)
        
        # MSG_WAITALL waits for full request or error
        response = b""
        
        while True:
            chunk = conn.recv(4096)
            if len(chunk) == 0:     # No more data received, quitting
                break
            response = response + chunk
       
        decoded_resp = response.decode("utf-8")
        if verbose:
            sys.stdout.write("Output: \n" + decoded_resp)
        else:
            sys.stdout.write("\n" + decoded_resp)
            decoded_resp = decoded_resp.split('\r\n\r\n')[1]
            sys.stdout.write("\n" + decoded_resp)
        if outfile:
            with open(outfile, 'w') as ftw:
                ftw.write(decoded_resp)
    finally:
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
