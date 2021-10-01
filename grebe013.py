#!/usr/bin/env python3
# See https://docs.python.org/3.2/library/socket.html
# for a decscription of python socket and its parameters
import socket
import os
import stat
import sys
import datetime
from threading import Thread
from argparse import ArgumentParser

#two questions so far
#first: how can i get images to work?
#second: sometimes not all the data from the form is submitted, only partial data.
# if this case happens, is it fair to return an error to the user?

BUFSIZE = 4096
CRLF = '\r\n'
OK = 'HTTP/1.1 200 OK{}'.format(CRLF)
METHOD_NOT_ALLOWED = 'HTTP/1.1 405  METHOD NOT ALLOWED{}Allow: GET, HEAD, POST {}Connection: close{}{}'.format(CRLF, CRLF, CRLF, CRLF)
NOT_FOUND = 'HTTP/1.1 404 NOT FOUND{}Connection: close{}{}'.format(CRLF, CRLF, CRLF)
FORBIDDEN = 'HTTP/1.1 403 FORBIDDEN{}Connection: close{}{}'.format(CRLF, CRLF, CRLF)
BAD_TYPE = 'HTTP/1.1 406 NOT ACCEPTABLE{}Connection: close{}{}'.format(CRLF, CRLF, CRLF)
MOVED_PERMANENTLY = 'HTTP/1.1 301 MOVED PERMANENTLY{}Location:  https://www.youtube.com/{}Connection: close{}{}'.format(CRLF, CRLF, CRLF, CRLF)
BAD_REQUEST = 'HTTP/1.1 400 BAD REQUEST{}CONNECTION: close{}{}'.format(CRLF, CRLF, CRLF)

def path_exists(request):
    return os.path.exists(request)

def get_contents(fname):
    with open(fname, 'r') as f:
        return f.read()

def check_perms(path):
    stmode = os.stat(path).st_mode
    return (getattr(stat, 'S_IROTH') & stmode) > 0

def get_file_types(allowed_begin):
    allowed = allowed_begin.split(",")
    allowed_ = allowed[0];
    allowed_ = allowed_.split()
    fin = allowed_[1] + "\n"
    i = 1;
    while i < len(allowed):
        if i == (len(allowed)-1):
            allowed_2 = allowed[i]
            allowed_2 = allowed_2.split(";")
            fin = fin + allowed_2[0] + "\n"
        else:
            fin = fin + allowed[i] + "\n"
        i = i + 1
    return fin

def process_request(data_decoded, client_sock):
    #split the data into an array
    data_request = data_decoded.split()
    # get request
    if len(data_request) == 0:
        return BAD_REQUEST
    if data_request[0] == "GET":
        #get the request
        request = data_request[1]
        #get the type of data requested
        found = False
        #temp variable
        type = "text/html"
        x = 0
        while found == False:
            if data_request[x] == "Accept:":
                type = data_request[x+1]
                found = True
            x = x + 1
        type = type.split(",")
        type = type[0]
        #cut off the extra /
        request = request[1:len(request)]
        #print the reqest
        print(data_request[0] + " " + request)
        #if the request is mytube, we return youtube to the client_talk func
        if request == "mytube":
            return "youtube"
        else:
            #check if path exists
            path = path_exists(request)
            if path == False:
                # error code
                print(NOT_FOUND)
                return NOT_FOUND + get_contents("404.html")
            else:
                #check if permissions exist
                perm = check_perms(request)
                if perm == False:
                    #error code
                    print(FORBIDDEN)
                    return FORBIDDEN + get_contents("403.html")
                else:
                    # get the type of file the client is requesting
                    mimetype = "";
                    if(request.endswith(".png")):
                        # images need to be sent a little differently than html files or css
                        mimetype = 'image/png'
                        if type != "image/webp":
                            if type != mimetype:
                                print(BAD_TYPE)
                                return BAD_TYPE + "<!DOCTYPE html><html><head><body><h><b>ERROR 406</b><h></body></head></html>"
                        # open the image
                        request_image = open(request, "r")
                        # send the 200 status code
                        client_sock.sendall(bytes(OK))
                        # send the seperator for the head and body
                        client_sock.sendall(bytes(CRLF))
                        # while theres still image data to send, send it to the client
                        while True:
                            image_data = request_image.readline(512)
                            if not image_data:
                                break
                            client_sock.send(image_data)
                        # close the file
                        request_image.close()
                        print(OK)
                        # return "image" to client_talk so the server knows it doesn't need
                        # to send a response
                        return "image"
                    # same deal as above with pngs as with jpgs
                    elif(request.endswith(".jpg")):
                        mimetype = 'image/jpg'
                        if type != "image/webp":
                            if type != mimetype:
                                print(BAD_TYPE)
                                return BAD_TYPE + "<!DOCTYPE html><html><head><body><h><b>ERROR 406</b><h></body></head></html>"
                        request1 = open(request, "r")
                        client_sock.sendall(bytes(OK))
                        client_sock.sendall(bytes(CRLF))
                        while True:
                            strng = request1.readline(512)
                            if not strng:
                                break
                            client_sock.send(strng)
                        request1.close()
                        print(OK)
                        return "image"
                    # checks the end of the request against different file types that are allowed
                    # links css, js files
                    elif(request.endswith(".css")):
                        mimetype = 'text/css'
                    elif(request.endswith(".js")):
                        mimetype = 'text/javascript'
                    elif(request.endswith(".mp3")):
                        mimetype = 'audio/mp3'
                    elif(request.endswith(".html")):
                        mimetype = 'text/html'
                    else:
                        mimetype = "*/*"
                    if type != mimetype:
                        print(BAD_TYPE)
                        return BAD_TYPE + "<!DOCTYPE html><html><head><body><h><b>ERROR 406</b><h></body></head></html>"
                    print(OK)
                    # return the status message, the type of content, and then the contents of the request
                    return OK + "Content-Type: " + str(mimetype) + "\r\n\r\n\r\n" + get_contents(request)
    #follows the same logic as above but without sending the body of the contents to the user
    elif data_request[0] == "HEAD":
        # do the same thing as above but do not return the file
        #get the request
        request = data_request[1]
        #cut off the extra /
        request = request[1:len(request)]
        #get the type of data asked for
        type = "text/html"
        x = 0
        while found == False:
            if data_request[x] == "Accept:":
                type = data_request[x+1]
                found = True
            x = x + 1
        type = type.split(",")
        type = type[0]
        #check if path exists
        path = path_exists(request)
        if path == False:
            #error code (same as above)
            print(NOT_FOUND)
            return NOT_FOUND
        else:
            #check if permissions exist
            perm = check_perms(request)
            if perm == False:
                #error code (same as above)
                print(FORBIDDEN)
                return FORBIDDEN
            else:
                # check if the data type requested matches
                mimetype = "";
                if(request.endswith(".png")):
                    # images need to be sent a little differently than html files or css
                    mimetype = 'image/png'
                    if type != "image/webp":
                        if type != mimetype:
                            print(BAD_TYPE)
                            return BAD_TYPE
                # same deal as above with pngs as with jpgs
                elif(request.endswith(".jpg")):
                    mimetype = 'image/jpg'
                    if type != "image/webp":
                        if type != mimetype:
                            print(BAD_TYPE)
                            return BAD_TYPE
                # checks the end of the request against different file types that are allowed
                # links css, js files
                elif(request.endswith(".css")):
                    mimetype = 'text/css'
                elif(request.endswith(".js")):
                    mimetype = 'text/javascript'
                elif(request.endswith(".mp3")):
                    mimetype = 'audio/mp3'
                elif(request.endswith(".html")):
                    mimetype = 'text/html'
                else:
                    mimetype = "*/*"
                if type != mimetype:
                    print(BAD_TYPE)
                    return BAD_TYPE + "<!DOCTYPE html><html><head><body><h><b>ERROR 406</b><h></body></head></html>"
                #good code, same as above but without get_contents
                print(OK)
                return OK
    elif data_request[0] == "POST":
        data = data_request[len(data_request)-1]
        print(data_request[0] + " " + data)
        #found that in safari browser, the data is sent 'deflated' sometimes
        #wasn't sure how to deal with this so i just made an error for it
        if(data == "deflate"):
            print(BAD_REQUEST)
            return BAD_REQUEST
        #split the form data up by &. this breaks it into the name, email, etc fields
        data = data.split('&')
        #get name
        name = data[0]
        #cut off extra name=
        name = name[5:len(name)]
        #get rid of + symbols
        name = name.split("+")
        #variable for iterating through the different elements of the form.
        x = 0;
        fin_name = ""
        #iterate through and format the name correctly
        while x < len(name):
            fin_name = fin_name + name[x] + " "
            x = x + 1
        x = 0
        #get email
        email = data[1]
        #cut off the extra email=
        email = email[6:len(email)]
        #split by the @ symbol
        email = email.split("%40")
        #format email correclty
        fin_email = email[0] + "@" + email[1]
        #get address
        address = data[2]
        #cut off extra address=
        address = address[8:len(address)]
        #split by +, aka space
        address = address.split("+")
        fin_add = ""
        x = 0
        #iterate through and format the address
        while x < len(address):
            #we get a part of the address, like the house number, street, etc
            curr = address[x]
            #split by comma
            curr = curr.split("%2C")
            #if it was split successfully by a comma, we make sure to add one for this
            #part of the address
            if len(curr) > 1:
                fin_add = fin_add + curr[0] + ", "
            #otherwise simply add it to the final address
            else:
                fin_add = fin_add + curr[0] + " "
            x = x + 1
        #get favorite place
        fave = data[3]
        #cut off extra faveorite=
        fave = fave[6:len(fave)]
        #split by space
        fave = fave.split("+")
        fin_fave = ""
        x = 0
        #format the favorite place
        while x < len(fave):
            #account for commas
            temp_fave = fave[x].split("%2C")
            #if its length is greater than 1, then there's a trailing comma and
            #we need to format accordingly
            if len(temp_fave) > 1:
                fin_fave = fin_fave + temp_fave[0] + ", "
            else:
                fin_fave = fin_fave + fave[x] + " "
            x = x + 1
        #get the url
        url = data[4]
        #cut off the extra url=
        url = url[4:len(url)]
        #split by ://
        url = url.split("%3A%2F%2F")
        #begin formatting the url
        fin_url = url[0] + "://"
        #split the rest of the url by / symbols
        rest_of_url = url[1].split("%2F")
        #format the url by properly adding the / symbols back
        if len(rest_of_url) > 0:
            x = 1
            fin_url = fin_url + rest_of_url[0] + "/"
            while x < len(rest_of_url):
                #if we are at the end of the string, we dont need another /
                if x == len(rest_of_url)-1:
                    fin_url = fin_url + rest_of_url[x]
                else:
                    fin_url = fin_url + rest_of_url[x]  + "/"
                x = x + 1
        #create the response page for the user
        response = "<!DOCTYPE html><html><head><body>"
        response = response + "<p><b>Name: </b>" + fin_name + "</p>"
        response = response + "<p><b>Email: </b>" + fin_email + "</p>"
        response = response + "<p><b>Address: </b>" + fin_add + "</p>"
        response = response + "<p><b>Favorite Place: </b>" + fin_fave + "</p>"
        response = response + "<p><b>Url of Fave Place: </b>" + fin_url + "</p>"
        response = response + "</body></head></html>"
        #return the result to client+talk
        print(OK)
        return OK + "\r\n\r\n" + response
    #if all of the above if/else statements fails, then the method is not allowed
    print(METHOD_NOT_ALLOWED)
    return METHOD_NOT_ALLOWED + "<!DOCTYPE html><html><head><body><h><b>ERROR 405</b><h></body></head></html>"


def client_talk(client_sock, client_addr, self):
    print('talking to {}'.format(client_addr))
    data = client_sock.recv(BUFSIZE)
    data_decoded = data.decode('utf-8')
    # get the server response
    server_response = process_request(data_decoded, client_sock)
    # if the response is simply youtube, then redirect to youtube
    if server_response == "youtube":
        print(MOVED_PERMANENTLY)
        client_sock.sendall(bytes(MOVED_PERMANENTLY))
    # if the response is not an image, send the requested rss
    elif server_response != "image":
        client_sock.sendall(bytes(server_response))
    # clean up
    client_sock.shutdown(1)
    client_sock.close()
    print('connection closed.')

class Server:
  def __init__(self, host, port):
    print('listening on port {}'.format(port))
    self.host = host
    self.port = port

    self.setup_socket()

    self.accept()

    self.sock.shutdown()
    self.sock.close()

  def setup_socket(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.bind((self.host, self.port))
    self.sock.listen(128)

  def accept(self):
    while True:
      (client, address) = self.sock.accept()
      th = Thread(target=client_talk, args=(client, address, self))
      th.start()

def parse_args():
  parser = ArgumentParser()
  parser.add_argument('--host', type=str, default='localhost',
                      help='specify a host to operate on (default: localhost)')
  parser.add_argument('-p', '--port', type=int, default=9001,
                      help='specify a port to operate on (default: 9001)')
  args = parser.parse_args()
  return (args.host, args.port)


if __name__ == '__main__':
  (host, port) = parse_args()
  Server(host, port)
