import socket
import argparse
import sys



def run_client(request,url, data,infile,outfile,header,verbose):
    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print("connected")
        if(request == "get"):
            print("this is a get request")
        elif(request == "post"):
            print("this is a post request")
            
        print(url)
        host = 'httpbin.org'
        port = 80
        conn.connect((host, port))
        line = "GET /status/418 HTTP/1.0\nHost: httpbin.org\n\n"
        print(line == request)
        print(line)
        # if(get != None):
        #     print("here")
        #     line = get
        #print(line)
        request = line.encode("utf-8")
        print(request)
        conn.sendall(request)
        
        # MSG_WAITALL waits for full request or error
        response = conn.recv(4096)
        sys.stdout.write("request recieved \n")
        sys.stdout.write("Replied: " + response.decode("utf-8"))
    finally:
        conn.close()


# Usage: python httpc.py --host host --port port
# example: python httpc.py --host httpbin.org --port 80
# parser = argparse.ArgumentParser()
# parser.add_argument("--get", help="""usage: httpc get [-v] [-h key:value] URL 
# Get executes a HTTP GET request for a given URL.\n 
# -v Prints the detail of the response such as protocol, status, and headers. \n
# -h key:value Associates headers to HTTP Request with the format 'key:value'.""",type=str, default="httpbin.org/get?status=418")

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('request', choices=['get', 'post'], help='HTTP request method, the option are the following: \n get \n post')
parser.add_argument('url', help='URL')
parser.add_argument('-d', dest='data', help='POST data', default=None)
parser.add_argument('-f', dest='infile', help='file containing POST data',default=None)
parser.add_argument('-o', dest='outfile', help='file to store response',default=None)
parser.add_argument('-H', dest='headers', action='append', help='HTTP Header to include',default=None)
parser.add_argument('-v', dest='verbose', action='count', help='verbose',default=False)
parser.add_argument("--host", help="server host", default="localhost")
parser.add_argument("--port", help="server port", type=int, default=8007)
args = parser.parse_args()
print(args)
run_client(args.request,args.url,args.data,args.infile,args.outfile,args.headers,args.verbose)
