import os
import socket
import threading
import random
from tkinter import *
from tkinter.ttk import *
from tkinter.scrolledtext import ScrolledText
# Server settings
server_ip = '0.0.0.0'
server_port = 5555
max_players = 10
# Game state
players = {}
placed_blocks = []  # List of placed blocks
seed = random.randint(1, 1000000)
# Function to handle client connections

server_running = False        

# Start the server
player_connections = []

class ServerControlApp:
    def __init__(self, root, save):
        global server_running
        self.root = root
        self.root.title("Server Control Panel")
        self.root.resizable(False, False)
        
        # Server control buttons
        self.start_button = Button(root, text="Start Server", command=self.start_server)
        self.start_button.grid(row=0, column=0, padx=5, pady=10)
        self.options_button = Button(root, text="Manage Server", state=DISABLED, command=self.open_management_window)
        self.options_button.grid(row=0, column=1, padx=5, pady=10)
        self.stop_button = Button(root, text="Stop Server", command=self.stop_server)
        self.stop_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Logs display (ScrolledText)
        self.log_display = ScrolledText(root, height=15, width=60, state='disabled', wrap=WORD)
        self.log_display.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        root.rowconfigure(1, weight=1)
        # Command input
        self.command_entry = Entry(root, width=50)
        self.command_entry.grid(row=2, column=0, padx=10, pady=10)
        
        # Send command button
        self.send_button = Button(root, text="Send Command", command=self.send_command)
        self.send_button.grid(row=2, column=1, padx=10, pady=10)
        
        # Simulated server status
        server_running = False

    def start_server(self):
        global server_running
        if not server_running:
            server_running = True
            self.options_button["state"] = NORMAL
            threading.Thread(target=start_server, args=(self,)).start()
        else:
            self.append_info("Server is already running.")

    def stop_server(self):
        global server_running
        if server_running:
            server_running = False
            self.append_info("Initiating shutdown...")
            self.append_info("Terminating all player connnections...")
            for conn in player_connections:
                conn.shutdown(socket.SHUT_RDWR)
                conn.close()
            self.append_info("All player connections terminated.")
            player_connections.clear()  # Clear all player connections
            self.append_info("Cleared player connections from memory.")
            
        else:
            self.append_info("Server is not running.")

    def send_command(self):
        command = self.command_entry.get()
        splitc = command.split(" ")
        if command:
            self.append_info(f"Command sent: {command}")
            if splitc[0] == "tp":
                broadcast_tp(splitc[1], (splitc[2], splitc[3], splitc[4]))
            if splitc[0] == "exec":
                broadcast_exec(splitc[1], splitc[2])
            if splitc[0] == "listplayers":
                self.append_info(str(players))
        self.command_entry.delete(0, END)

    def append_info(self, message):
        self.root.after(0, self._append_info, message)

    def _append_info(self, message):
        self.log_display.configure(state='normal')
        self.log_display.insert(END, "[INFO] " + message + '\n')
        self.log_display.configure(state='disabled')
        self.log_display.yview(END)  # Auto-scroll to the end

    def append_warn(self, message):
        self.root.after(0, self._append_warn, message)

    def _append_warn(self, message):
        self.log_display.configure(state='normal')
        self.log_display.insert(END, "[WARN] " + message + '\n')
        self.log_display.configure(state='disabled')
        self.log_display.yview(END)  # Auto-scroll to the end
    def append_err(self, message):
        self.root.after(0, self._append_err, message)

    def _append_err(self, message):
        self.log_display.configure(state='normal')
        self.log_display.insert(END, "[ERROR] " + message + '\n')
        self.log_display.configure(state='disabled')
        self.log_display.yview(END)  # Auto-scroll to the end
    def open_management_window(self):
        manager = Toplevel(self.root)
        manager.title("Server Management")
        
        # Create Listbox
        self.listbox = Listbox(manager)
        self.listbox.pack(padx=20, pady=20)

        # Create Kick and Ban buttons
        self.kick_button = Button(manager, text="Kick", command=self.kick_player, state=DISABLED)
        self.kick_button.pack(pady=5)

        self.ban_button = Button(manager, text="Ban", command=self.ban_player, state=DISABLED)
        self.ban_button.pack(pady=5)

        # Bind selection event to update button states
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        # Schedule listbox updates
        self.update_listbox()
    def update_listbox(self):
        self.listbox.delete(0, END)
        for key in players.keys():
            self.listbox.insert(END, key)
        self.root.after(10000, self.update_listbox)

    def on_select(self, event):
        # Enable or disable buttons based on selection
        if self.listbox.curselection():  # Check if something is selected
            self.kick_button.config(state=NORMAL)
            self.ban_button.config(state=NORMAL)
        else:
            self.kick_button.config(state=DISABLED)
            self.ban_button.config(state=DISABLED)

    def kick_player(self):
        selected = self.listbox.curselection()
        if selected:
            def kick_them():
                broadcast_kick(self.listbox.get(selected), reason_for_kick.get())
                self.kick_button.config(state=DISABLED)
                self.ban_button.config(state=DISABLED)
                print(f"Kicked player with port: {player_key}")
                players.pop(int(player_key), None)
                kick_prompt.destroy()
                kick_prompt.update()
            kick_prompt = Toplevel(self.root)
            kick_prompt.title("Kick Player")
            Label(kick_prompt, text="Enter your reason for clicking the player").pack()
            reason_for_kick = Entry(kick_prompt)
            reason_for_kick.pack()
            Button(kick_prompt, text="Kick player", command=kick_them).pack()
            player_key = self.listbox.get(selected)
            self.update_listbox()  # Refresh the listbox
    def ban_player(self):
        selected = self.listbox.curselection()
        if selected:
            def ban_them():
                broadcast_ban(self.listbox.get(selected), reason_for_ban.get())
                self.kick_button.config(state=DISABLED)
                self.ban_button.config(state=DISABLED)
                print(f"Banned player with port: {player_key}")
                players.pop(int(player_key), None)
                ban_prompt.destroy()
                ban_prompt.update()
            ban_prompt = Toplevel(self.root)
            ban_prompt.title("Ban Player")
            Label(ban_prompt, text="Enter your reason for banning the player").pack()
            reason_for_ban = Entry(ban_prompt)
            reason_for_ban.pack()
            Button(ban_prompt, text="Ban player", command=ban_them).pack()
            player_key = self.listbox.get(selected)
            self.update_listbox()  # Refresh the listbox
load = os.path.isfile("./world/world.mpw")
root = Tk()
app = ServerControlApp(root, load)
def manstart(appp):
    appp.start_server()
def handle_client(conn, addr, instance):
    instance.append_info(f"New connection from {addr}")
    player_id = addr[1]

    players[player_id] = {"position": (0, 0, 0)}  # Initialize player position

    conn.send(("welcomeseed: " + str(seed) + "\n").encode())
    conn.send(("welcomeblck: " + str(placed_blocks) + "\n").encode())
    # Send initial game state to client
    conn.send(str(players).encode())
    try:
        while True:
            try:
                data = conn.recv(1024).decode()
                if not data:
                    break

                # Process block placement or player position
                if "," in data:
                    data_list = data.split(',')
                    if len(data_list) == 3:
                        new_position = tuple(map(float, data_list))
                        players[player_id]["position"] = new_position
                        broadcast_state()
                    elif len(data_list) == 4:
                        x, y, z, block_type = data_list
                        block_position = (float(x), float(y), float(z))
                        placed_blocks.append((block_position, block_type))
                        with open("./world/world.mpw", "w") as world:
                            world.write(f"({seed}, {placed_blocks})")
                        broadcast_block_placement(block_position, block_type)

            except Exception as e:
                print(e)
                break
    finally:
        instance.append_warn(f"Connection with {addr} closed")
        conn.close()
        if players[player_id]:
            del players[player_id]
        player_connections.remove(conn)
        broadcast_disconnect(player_id)



def isbanned(ip: str) -> bool:
    isbannedfile = os.path.isfile("banned_players.txt")
    if isbannedfile:
        with open("banned_players.txt", "r") as file:
            text = file.read()
            banned_ips = text.splitlines()
            for x in banned_ips:
                if x == ip:
                    return True
            return False

# Function to broadcast the game state to all connected clients
def broadcast_state():
    game_state = "state: " + str(players)  # Append a unique separator
    for player_conn in player_connections:
        try:
            player_conn.send((game_state + "\n").encode())
        except:
            continue
def broadcast_disconnect(playerid: int):
    game_state = "dc: " + str(playerid)  # Append a unique separator
    for player_conn in player_connections:
        try:
            player_conn.send((game_state + "\n").encode())
        except:
            continue
# Function to broadcast block placement to all clients
def broadcast_block_placement(block_position, block_type):
    print("Block placed")
    block_data = f"place: ({block_position[0]},{block_position[1]},{block_position[2]},'{block_type}')\n".encode()
    print(block_type)
    for player_conn in player_connections:
            player_conn.send(block_data)
            print("Block sent to client")
def broadcast_tp(username, pos):
    tp_data = f"tp: ({pos[0]},{pos[1]},{pos[2]})\n".encode()
    if username == "@a":
        for player_conn in player_connections:
                player_conn.send(tp_data)
    else:
        for player_conn in player_connections:
            if int(player_conn.getpeername()[1]) == int(username):
                player_conn.send(tp_data)
                break
def broadcast_exec(username, command):
    exec_data = f"exec: {command.replace(';', ' ')}\n".encode()
    if username == "@a":
        for player_conn in player_connections:
                player_conn.send(exec_data)
    else:
        for player_conn in player_connections:
            if int(player_conn.getpeername()[1]) == int(username):
                player_conn.send(exec_data)
                break
def broadcast_kick(username, reason):
    kick_data = f"kick: {reason}\n".encode()
    if username == "@a":
        for player_conn in player_connections:
                player_conn.send(kick_data)
    else:
        for player_conn in player_connections:
            if int(player_conn.getpeername()[1]) == int(username):
                player_conn.send(kick_data)
                break
def broadcast_ban(username, reason):
    ban_data = f"ban: {reason}\n".encode()
    if username == "@a":
        for player_conn in player_connections:
                player_conn.send(ban_data)
    else:
        for player_conn in player_connections:
            if int(player_conn.getpeername()[1]) == int(username):
                player_conn.send(ban_data)
                if os.path.isfile("./banned_players.txt"):
                    with open("./banned_players.txt", "a") as banned_file:
                        banned_file.write(f"\n{player_conn.getpeername()[0]}")
                else:
                   with open("./banned_players.txt", "w") as banned_file:
                        banned_file.write(f"\n{player_conn.getpeername()[0]}") 
                break
def start_server(instance):
    global seed
    global placed_blocks
    load = os.path.isfile("./world/world.mpw")
    if load:
        instance.append_info("World Located. Starting loading process...")
        with open("./world/world.mpw", "r") as world:
            worldinfo = eval(world.read())
            instance.append_info("Reading file...")
            if isinstance(worldinfo, tuple):
                instance.append_info("File in successful format!")
                seed = worldinfo[0]
                instance.append_info(f"Seed read as {seed}.")
                placed_blocks = worldinfo[1]
                instance.append_info(f"Block placements read.")
    else:
        instance.append_warn("No world found. Generation proceeding. If you think this is a mistake, please shut down the server.")
        instance.append_info("Using seed: " + str(seed))

    instance.append_info("Creating socket...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse socket for fast reconnect
    instance.append_info("Binding server IP and Port...")
    server.bind((server_ip, server_port))
    instance.append_info("Setting max player count...")
    server.listen(max_players)
    server.settimeout(1.0)

    instance.append_info("Server Running on IP: " + server_ip + " with port " + str(server_port))
    instance.append_info("Max players: " + str(max_players))
    instance.append_info("Server now allowing connections...")

    while server_running:
        try:
            conn, addr = server.accept()
            if isbanned(addr[0]):
                instance.append_info(f"Banned player {addr} attempted to join the server.")
                conn.send("ban: You are banned from this server.\n".encode()) 
                conn.close()
            else:
                player_connections.append(conn)
                threading.Thread(target=handle_client, args=(conn, addr, instance)).start()
        except socket.timeout:
            if not server_running:
                break
        except Exception as e:
            instance.append_err(f"Unexpected error: {e}")
    instance.append_info(f"Saving world...")
    with open("./world/world.mpw", "w") as world:
        world.write(f"({seed}, {placed_blocks})")
    instance.append_info(f"World saved sucessfully.")
    instance.append_info(f"Shutting down server...")
    server.close()
    instance.append_info(f"Server closed.")
root.mainloop()