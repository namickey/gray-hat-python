# coding: utf-8
import sys
import socket
import getopt
import threading
import subprocess

listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

def usage():
    print("BHP Net Tool")
    sys.exit(0)

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target
    if not len(sys.argv[1:]):
        usage()
    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hle:t:p:cu:",
            ["help", "listen", "execute=", "target=", "port=", "command", "upload="])
    except getopt.GetoptError as err:
        print(str(err))
        usage()
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"
    if not listen and len(target) and port > 0:
        buffer = sys.stdin.read()
        client_sender(buffer)
    if listen:
        server_loop()

def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((target, port))
        if len(buffer):
            client.send(buffer)
        while True:
            recv_len = 1
            response = ""
            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data
                if recv_len < 4096:
                    break
            print(response)
            buffer = raw_input("")
            buffer += "\n"
            client.send(buffer)
    except:
        print("[*] Exception! Existing.")
        client.close()

def server_loop():
    global target
    if not len(target):
        target = "0.0.0.0"
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)
    print('11')
    while True:
        client_socket, addr = server.accept()
        print("[*] Accepted connection from: %s:%d" % (addr[0], addr[1]))
        print('12')
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()
        print('13')

def run_command(command):
    command = command.rstrip()
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command.\r\n"
    return output

def client_handler(client_socket):
    global upload
    global execute
    global command
    print("21")
    if len(upload_destination):
        file_buffer = ""
        while True:
            data = client_socket.recv(1024)
            if len(data) == 0:
                break
            else:
                file_buffer += data
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()
            client_socket.send("Successfully saved file to %s\r\n % upload_destination")
        except:
            client_socket.send("Failed to save file to %s\r\n % upload_destination")
    if len(execute):
        output = run_command(execute)
        client_socket.send(output)
    if command:
        prompt = "<BHP:#> "
        client_socket.send(prompt.encode())
        while True:
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                s = str(client_socket.recv(1024))
                print(s)
                cmd_buffer += s
            response = run_command(cmd_buffer)
            response += prompt
            client_socket.send(response)

main()
