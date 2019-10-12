# coding: utf-8
import sys
import socket
import getopt
import threading
import subprocess
import time

listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

def usage():
    print("BHP Net Tool")
    print("\nfor server")
    print("python netcat.py -l -p 9999 -c")
    print("python netcat.py -l -p 9999 -c -u some.txt")
    print("\nfor client")
    print("python netcat.py -t localhost -p 9999")
    print("cat some.txt | python netcat.py -t localhost -p 9999")
    print("\n")
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
            client.send(buffer.encode())
        while True:
            recv_len = 1
            response = ""
            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data.decode()
                if recv_len < 4096:
                    break
            print(response)
            buffer = input("<BHP> ")
            buffer += "\n"
            client.send(buffer.encode())
            if "exit\n" == buffer:
                break
    except Exception as e:
        print(e)
        print("[*] Exception! Existing.")
        client.send("exit\n".encode())
    client.close()

def server_loop():
    global target
    if not len(target):
        target = "0.0.0.0"
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)
    while True:
        client_socket, addr = server.accept()
        print("[*] Accepted connection from: %s:%d" % (addr[0], addr[1]))
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

def run_command(command):
    command = command.rstrip()
    try:
        print("command:" + command)
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except Exception as e:
        print(e)
        output = "Failed to execute command.\r\n".encode()
    print("output:" + output.decode())
    return output

def client_handler(client_socket):
    global upload
    global upload_destination
    global execute
    global command
    if len(upload_destination):
        file_buffer = "".encode()
        while True:
            data = client_socket.recv(1024)
            print("data len:" + str(len(data)))
            file_buffer += data
            if len(data) < 1024:
                break
        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()
            client_socket.send(("Successfully saved file to %s\r\n" % upload_destination).encode())
        except:
            client_socket.send(("Failed to save file to %s\r\n" % upload_destination).encode())
        upload_destination = ""
    if len(execute):
        output = run_command(execute)
        client_socket.send(output)
    if command:
        prompt = "\n"
        client_socket.send(prompt.encode())
        while True:
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                time.sleep(1)
                cmd_buffer += client_socket.recv(1024).decode()
            if "exit\n" == cmd_buffer:
                break
            response = run_command(cmd_buffer).decode()
            response += prompt
            client_socket.send(response.encode())

main()
