# coding:utf-8

import socket

target_host = "localhost"
target_port = 9998

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((target_host, target_port))
client.send("GET / HTTP/1.1\r\nHost: www.google.com\r\n\r\n".encode())
response = client.recv(4096)
print(response)
