import socket
import threading
import json
from database import DatabaseManager

HOST = '0.0.0.0'
PORT = 1234
client_handlers = []
handlers_lock = threading.Lock()
db = DatabaseManager()

def send_json(writer, obj):
    msg = json.dumps(obj) + "\n" #to string
    writer.write(msg)
    writer.flush()

class ClientHandler(threading.Thread):
    def __init__(self, conn: socket.socket, addr):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.user = None
        self.reader = conn.makefile('r', encoding='utf-8')
        self.writer = conn.makefile('w', encoding='utf-8')

    def run(self):
        try:
            while True:
                line = self.reader.readline()
                if not line:
                    break
                try:
                    data = json.loads(line.strip()) # to dict
                except:
                    send_json(self.writer, {"status": "error", "message": "Invalid data"})
                    continue
                msg_type = data.get("type")
                if msg_type == "signup":
                    self.handle_signup(data)
                elif msg_type == "login":
                    self.handle_login(data)
                elif msg_type == "message":
                    self.handle_message(data)
                else:
                    send_json(self.writer, {"status": "error", "message": "Unknown command"})
        except Exception as e:
            print(f"[ERROR] {self.addr}: {e}")
        finally:
            self.remove_handler_and_close()

    def handle_signup(self, data):
        username = data.get("username", "")
        password = data.get("password", "")
        phone = data.get("phone", "")
        try:
            db.add_user(username, password, phone)
            send_json(self.writer, {"status": "ok", "message": "Signup succeed"})
        except Exception as e:
            send_json(self.writer, {"status": "error", "message": str(e)})

    def handle_login(self, data):
        username = data.get("username", "")
        password = data.get("password", "")
        user = db.verify_user(username, password)
        if user:
            self.user = user
            send_json(self.writer, {"status": "ok", "message": "Login succeed", "username": username})
            with handlers_lock:
                if self not in client_handlers:
                    client_handlers.append(self)
        else:
            send_json(self.writer, {"status": "error", "message": "Invalid credentials"})

    def handle_message(self, data):
        if not self.user:
            send_json(self.writer, {"status": "error", "message": "Please login first"})
            return
        content = data.get("content", "")
        receiver_username = data.get("to", "")
        receiver = db.get_user_by_username(receiver_username)
        if not receiver:
            send_json(self.writer, {"status": "error", "message": "Receiver not found"})
            return
        db.add_message(self.user.id, receiver.id, content)
        with handlers_lock:
            for handler in client_handlers:
                if handler.user and handler.user.username == receiver_username:
                    send_json(handler.writer, {
                        "type": "message",
                        "from": self.user.username,
                        "content": content
                    })
        send_json(self.writer, {"status": "ok", "message": "Message sent"})

    def remove_handler_and_close(self):
        with handlers_lock:
            if self in client_handlers:
                client_handlers.remove(self)
        try:
            self.reader.close()
            self.writer.close()
            self.conn.close()
        except:
            pass
        print(f"[INFO] Closed connection: {self.addr}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        try:
            server_sock.bind((HOST, PORT))
            server_sock.listen()
            print(f"[✅ SERVER] Auth chat server is running on {HOST}:{PORT}...")
        except OSError as e:
            print(f"[❌ ERROR] Could not bind to port {PORT}: {e}")
            return
        try:
            while True:
                conn, addr = server_sock.accept()
                print(f"[NEW] Connection from {addr}")
                handler = ClientHandler(conn, addr)
                handler.start()
        except KeyboardInterrupt:
            print("\n[⛔️ SERVER] Shutdown requested.")
        finally:
            with handlers_lock:
                for handler in client_handlers.copy():
                    handler.remove_handler_and_close()
            print("[SERVER] All connections closed.")

if __name__ == '__main__':
    start_server()
