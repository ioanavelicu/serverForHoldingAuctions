import socket
import threading

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.client_name = None

    def start(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        print("Conexiunea la server a fost stabilită.")

        self.client_name = input("Introduceți numele dvs.: ")
        self.send_message(self.client_name)

        data_recv = self.client_socket.recv(1024).decode()
        if data_recv:
            print(f'{self.client_name} conectat!')
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.start()
            command = ""
            while command.strip().lower() != "exit":
                command = input()
                self.client_socket.sendall(command.encode())
        else:
            print('Conexiune refuzata')

    def send_message(self, message):
        try:
            self.client_socket.send(message.encode())
        except:
            pass

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode()
                print(message)
            except:
                break

# Exemplu de utilizare
host = "localhost"
port = 12345

client = Client(host, port)
client.start()
