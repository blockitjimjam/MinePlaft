import random
import socket
import threading
from ursina import *
import os
from ursina.prefabs.first_person_controller import FirstPersonController
from perlin_noise import PerlinNoise
from PIL import Image
from tkinter import messagebox
global client
try:
    def loadimg(image_path):
        img = Image.open(image_path)
        return Texture(img)
    global globalselectedtype
    globalselectedtype = "oak_planks"

    class Cube(Button):
        def __init__(self, position = (0,0,0), texture = loadimg("./assets/coarse_dirt.png")):
            super().__init__(
                model = "cube",
                parent = scene,
                position = position,
                texture = texture,
                origin_y = 0.5,
                color = color.white,
                highlight_color = color.lime,
            )
    
        def input(self, key):
            global globalselectedtype
            if self.hovered:
                if key == 'right mouse down':  # When left mouse button is pressed
                    try:
                        block_position = self.position + mouse.normal  
                        print(globalselectedtype)
                        send_block_placement(block_position, globalselectedtype)
                    except:
                        print("oops")
            else:
                if key == "1":
                    globalselectedtype = "oak_planks"

                elif key == "2":
                    globalselectedtype = "coarse_dirt"

                elif key == "3":
                    globalselectedtype = "bricks"

                elif key == "4":
                    globalselectedtype = "crafting_table.png"

                elif key == "5":
                    globalselectedtype = "glass"

                elif key == "6":
                    globalselectedtype = "gold_block"

                elif key == "7":
                    globalselectedtype = "iron_block"

                elif key == "8":
                    globalselectedtype = "leaves"

    class HomeMenu(Entity):
        def __init__(self):
            super().__init__()
            self.title = Text(text="Welcome to MinePlaft", position=(-0.5, 0.4), scale=2, color=color.white)
            self.ip_input = InputField(position=(-0.5, 0.1), placeholder="Enter Server IP", color=color.white)
            self.port_input = InputField(position=(-0.5, 0), placeholder="Enter Server Port", color=color.white)
            self.connect_button = Button(text="Connect", position=(-0.5, -0.1), scale=(0.2,0.1), color=color.azure, on_click=self.connect)

        def connect(self):
            server_ip = self.ip_input.text or '127.0.0.1'
            server_port = int(self.port_input.text or 5555)
            self.title.disable()
            self.ip_input.disable()
            self.port_input.disable()
            self.connect_button.disable()
            
            start_game(server_ip, server_port)
    class PauseMenu(Entity):
        def __init__(self):
            super().__init__()
            self.title = Text(text="Game Paused", position=(-0.5, 0.4), scale=2, color=color.white)
            self.connect_button = Button(text="Disconnect", position=(-0.5, -0.1), scale=(0.2,0.1), color=color.azure, on_click=self.connect)

        def connect(self):
            server_ip = self.ip_input.text or '127.0.0.1'
            server_port = int(self.port_input.text or 5555)
            self.title.disable()
            self.ip_input.disable()
            self.port_input.disable()
            self.connect_button.disable()
            
            start_game(server_ip, server_port)
    class Hotbar(Entity):
        def __init__(self):
            super().__init__()
            self.slots = []
            self.selected_index = 0

            for i in range(8):
                slot = Entity(parent=self, model='quad', texture='white_cube', color=color.gray, scale=(.1, .1),
                            position=(i * .12, -.05), z=-.1)
                self.slots.append(slot)

            self.selection_box = Entity(parent=self, model='quad', color=color.yellow, scale=(.11, .11),
                                        position=self.slots[self.selected_index].position, z=-.2)
            textures = {
                "coarse_dirt": loadimg("./assets/coarse_dirt.png"),
                "bricks": loadimg("./assets/bricks.png"),
                "crafting_table.png": loadimg("./assets/crafting_table.png"),
                "glass": loadimg("./assets/glass.png"),
                "grass": loadimg("./assets/grass.png"),
                "gold_block": loadimg("./assets/gold_blockpng.png"),
                "iron_block": loadimg("./assets/iron_block.png"),
                "leaves": loadimg("./assets/leaves.png"),
                "oak_planks": loadimg("./assets/oak_planks.png"),

            }
            self.item_textures = [textures.get("oak_planks"), textures.get("coarse_dirt"), textures.get("bricks"), textures.get("crafting_table.png"), textures.get("glass"), textures.get("gold_block"), textures.get("iron_block"), textures.get("leaves")] 
            for i, texture in enumerate(self.item_textures):
                self.slots[i].texture = texture

            for key in range(1, 9):
                hotkey = str(key)
                setattr(self, f'on_{hotkey}', lambda k=key-1: self.select_slot(k))

    def select_slot(self, index):
        self.selected_index = index
        self.selection_box.position = self.slots[self.selected_index].position
    chunk_size = 2
    render_distance = 3
    scale = 100 
    height_multiplier = 20 
    world_size = 1000
    global times
    times = 0
    global player_position
    player_position = False
    global noise 
    noise = False
    seed = False
    global player
    player = False
    
    textures = {
        "coarse_dirt": loadimg("./assets/coarse_dirt.png"),
        "bricks": loadimg("./assets/bricks.png"),
        "crafting_table.png": loadimg("./assets/crafting_table.png"),
        "glass": loadimg("./assets/glass.png"),
        "grass": loadimg("./assets/grass.png"),
        "gold_block": loadimg("./assets/gold_blockpng.png"),
        "iron_block": loadimg("./assets/iron_block.png"),
        "leaves": loadimg("./assets/leaves.png"),
        "oak_planks": loadimg("./assets/oak_planks.png"),

    }
    chunks = {}
    placed_blocks = {} 



    def is_within_world_bounds(chunk_x, chunk_z):
        half_world_size = world_size // 2
        min_coord = -half_world_size // chunk_size
        max_coord = half_world_size // chunk_size
        return min_coord <= chunk_x <= max_coord and min_coord <= chunk_z <= max_coord


    def generate_chunk(chunk_x, chunk_z):
        if not is_within_world_bounds(chunk_x, chunk_z):
            return  
        
        chunk = []
        for x in range(chunk_size):
            for z in range(chunk_size):
                world_x = chunk_x * chunk_size + x
                world_z = chunk_z * chunk_size + z
                y = round(noise([world_x / scale, world_z / scale]) * height_multiplier)
                if y > 5:
                    voxel = Cube(position=(world_x, y, world_z), texture=loadimg("./assets/snow.png"))
                elif y > 0.1:
                    voxel = Cube(position=(world_x, y, world_z), texture=loadimg("./assets/grass.png"))
                else:
                    voxel = Cube(position=(world_x, y, world_z), texture=loadimg("./assets/coarse_dirt.png"))
                voxel.disable() 
                chunk.append(voxel)
        chunks[(chunk_x, chunk_z)] = chunk

    def load_chunks():
        current_chunk_x = int(player.position.x // (chunk_size))
        current_chunk_z = int(player.position.z // (chunk_size))
        
        for x in range(current_chunk_x - render_distance, current_chunk_x + render_distance + 1):
            for z in range(current_chunk_z - render_distance, current_chunk_z + render_distance + 1):
                if (x, z) not in chunks and is_within_world_bounds(x, z):
                    generate_chunk(x, z)
                if (x, z) in chunks:
                    for voxel in chunks[(x, z)]:
                        voxel.enable()


    def unload_chunks():
        current_chunk_x = int(player.position.x // chunk_size)
        current_chunk_z = int(player.position.z // chunk_size)
        
        chunks_to_unload = []
        for chunk_coord in chunks:
            chunk_x, chunk_z = chunk_coord
            if abs(chunk_x - current_chunk_x) > render_distance or abs(chunk_z - current_chunk_z) > render_distance:
                chunks_to_unload.append(chunk_coord)
        
        for chunk_coord in chunks_to_unload:
            for voxel in chunks[chunk_coord]:
                voxel.disable()
            del chunks[chunk_coord]
    other_players = {}
    def send_block_placement(block_position, block_typee):
        block_data = f"{block_position[0]},{block_position[1]},{block_position[2]},{block_typee}"
        print(block_position[0], block_position[1], block_position[2])
        client.send(block_data.encode())
    def handle_position_update(game_statee):
        for player_id, state in game_statee.items():
            if player_id != addr[1]:
                if player_id not in other_players:
                    other_players[player_id] = Entity(model='cube', color=color.gray, scale=(1, 2, 1))
                other_players[player_id].position = state["position"]
                other_players[player_id].y += 1

    def handle_block_placement(game_state):
        x, y, z, block_type = game_state
        print(block_type)
        block = Cube(position=(x, y, z), texture=textures.get(block_type))
        print(x, y, z)
        placed_blocks[(x, y, z)] = block
    def place_missing_blocks(blocks: list):
        for block in blocks:
            cheese = Cube(position=block[0], texture=textures.get(block[1]))

    def receive_data():
        global client
        global player
        buffer = ""
        while True:
                if isinstance(client, socket.socket):
                    global noise
                    global seed
                    data = client.recv(1024).decode()
                    if not data:
                        continue
                    buffer += data
                    while "\n" in buffer:  
                        message, buffer = buffer.split("\n", 1)
                        if (message != ""):
                            if message.startswith("state: "):
                                game_state = eval(message.replace("state: ", ""))
                                handle_position_update(game_state)
                            elif message.startswith("place: "):
                                game_state = eval(message.replace("place: ", ""))
                                print("attempt on block place")
                                handle_block_placement(game_state)
                            elif message.startswith("welcomeseed: "):
                                
                                game_state: int = eval(message.replace("welcomeseed: ", ""))
                                seed = game_state
                                noise = PerlinNoise(octaves=2, seed=seed)
                                print(f"Using seed: {seed}")
                            elif message.startswith("welcomeblck: "):                    
                                game_state: list = eval(message.replace("welcomeblck: ", ""))
                                place_missing_blocks(game_state)
                            elif message.startswith("dc: "):                    
                                game_state: int = eval(message.replace("dc: ", ""))
                                del other_players[game_state]
                            elif message.startswith("tp: "):                    
                                pos: list = eval(message.replace("tp: ", ""))
                                player.set_position((pos[0], pos[1], pos[2]))
                            elif message.startswith("exec: "):                    
                                eval(message.replace("exec: ", ""))
                            elif message.startswith("kick: "):     
                                game_state: str = message.replace("kick: ", "")             
                                messagebox.showerror("Kicked", f"You were kicked for the following reason:\n {game_state}")
                                client.close()
                                app.quit()
                            elif message.startswith("ban: "):     
                                game_state: str = message.replace("ban: ", "")             
                                messagebox.showerror("Banned", f"You were banned for the following reason:\n {game_state}")
                                client.close()
                                app.quit()



    # Connect to the server
    
    # Function to update chunks based on player's movement
    def update():
        try:
            global player
            global player_position
            if (seed != False):
                player_position = f"{player.x},{player.y},{player.z}"
                update_chunks()
                
                
                try:
                    client.send(player_position.encode())
                except Exception as exc:
                    print(exc)
                if str(exc).startswith("[WinError 10053]"):
                    app.quit()
                    sys.exit()
        except:
            pass

    # Initialize player
    def start_game(server_ip, server_port):
        global addr
        global client
        global player
        global update_chunks
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server_ip, server_port))
        addr = client.getsockname()
        player = FirstPersonController()
        UI = Text(register_mouse_input=False, text='Username: ' + str(addr[1]), x=.5, y=.5)
        # Start receiving data from the server
        threading.Thread(target=receive_data).start()
        def update_chunks():
            unload_chunks()
            load_chunks()
        

        # Start the gam
        app.setBackgroundColor(r=0, g=29, b=230)
        app.setFrameRateMeter(False)
        # Set up update function
    if __name__ == "__main__":
        try:
            app = Ursina(position=(100, 100))
            HomeMenu()
            app.run()
        except Exception as e:
            print("Looks like the app counldnt fine NodePath. bruh")
            print(e)
finally:
    print("huh")
    client.shutdown(socket.SHUT_RDWR)
    client.close()
    app.quit()
    sys.exit()