import tkinter as tk
from tkinter import ttk
import socket
import threading
import pickle
from pytmx import TiledMap
from helper import check_name, get_tmx_ent_vars
from settings import HOST_PORT, HOST_ADDR, level_dict, data_stream_size, tile_size


class Window():
    def __init__(self, root):
        '''tkinter window'''
        # root = tk.Tk()
        root.title("Server")

        # Top frame consisting of two buttons widgets (i.e. btnStart, btnStop)
        self.topFrame = tk.Frame(root)
        self.btnStart = tk.Button(self.topFrame, text="Connect", command=lambda : network.start_server())
        self.btnStart.pack(side=tk.LEFT)
        self.btnStop = tk.Button(self.topFrame, text="Stop", command=lambda : network.stop_server(), state=tk.DISABLED)
        self.btnStop.pack(side=tk.LEFT)
        self.topFrame.pack(side=tk.TOP, pady=(5, 0))

        # Middle frame consisting of two labels for displaying the host and port info
        self.middleFrame = tk.Frame(root)
        self.lblHost = tk.Label(self.middleFrame, text = "Host: X.X.X.X")
        self.lblHost.pack(side=tk.LEFT)
        self.lblPort = tk.Label(self.middleFrame, text = "Port:XXXX")
        self.lblPort.pack(side=tk.LEFT)
        self.middleFrame.pack(side=tk.TOP, pady=(5, 0))

        # The client frame shows the client area
        self.clientFrame = tk.Frame(root)
        self.lblLine = tk.Label(self.clientFrame, text="**********Client List**********").pack()
        self.scrollBar = tk.Scrollbar(self.clientFrame)
        self.scrollBar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tkDisplay = tk.Text(self.clientFrame, height=15, width=30)
        self.tkDisplay.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
        self.scrollBar.config(command=self.tkDisplay.yview)
        self.tkDisplay.config(yscrollcommand=self.scrollBar.set, background="#F4F6F7", highlightbackground="grey", state="disabled")
        self.clientFrame.pack(side=tk.BOTTOM, pady=(5, 10))
    
        # Level select frame
        levelFrame = ttk.Frame(root)                                                                # Campaigns                           
        campaigns = list(level_dict.keys())
        campaign_lbl = ttk.Label(levelFrame, text='Select campaign:').pack()
        self.selected_campaign = tk.StringVar()
        self.selected_level = tk.StringVar()                                                        # Stores radiobtn value parameter
        combbox = ttk.Combobox(levelFrame, textvariable=self.selected_campaign, values=campaigns)
        combbox.current(0)                                                                          # Selects first campaign
        combbox.pack()
        combbox.state(['readonly'])
        level_lbl = ttk.Label(levelFrame, text='Select level:').pack()                              # Levels
        combbox.bind('<<ComboboxSelected>>', lambda x: self.update_radio_buttons(levelFrame))
        self.update_radio_buttons(levelFrame)
        ttk.Button(levelFrame, text='Load level', command=lambda : game.load_tmx(self.selected_level.get())).pack(side=tk.BOTTOM)
        levelFrame.pack(side=tk.TOP, pady=(5, 10))

        # Debugg btn
        btnDebug = tk.Button(root, text="Debug", command=lambda : game.debug())
        btnDebug.pack(side=tk.BOTTOM)


    def update_radio_buttons(self, levelFrame):
        # print('uppdating levels')
        for widget in levelFrame.winfo_children():                      # Destroy any old radionbuttons
            if widget.winfo_class() == 'TRadiobutton':
                widget.destroy()
        campaign = self.selected_campaign.get()
        levels = level_dict[campaign]
        btns = []
        for level, path in levels.items():                              # create new buttons
            btns.append(ttk.Radiobutton(levelFrame, text=level, 
            variable=self.selected_level, value=path))
            btns[-1].pack(side=tk.TOP)

        self.selected_level.set(list(levels.values())[0])               # Set selected level to first button


    # Update client name display on (dis)connect
    def update_client_names_display(self, name_list):
        self.tkDisplay.config(state=tk.NORMAL)
        self.tkDisplay.delete('1.0', tk.END)
        for c in name_list:
            self.tkDisplay.insert(tk.END, c+"\n")
        self.tkDisplay.config(state=tk.DISABLED)

class Network():
    def __init__(self):
        '''Network'''
        self.HOST_PORT = HOST_PORT
        if HOST_ADDR == '':
            self.hostname = socket.gethostname()             
            self.HOST_ADDR = socket.gethostbyname(self.hostname)  # Grabs the ip from router (I believe). Might not work as intended on every network setup.
        else:
            self.HOST_ADDR = HOST_ADDR
        self.clients = []                                # Will hold all active client connections
        self.clients_names = []                          # For displaying connected clients in server window
        self.client_id = 0
        self.connection_player = {}                      # keeping track on which connection corresponds to which player

    def start_server(self):
        try:
            print('Initializing game server')
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.HOST_ADDR, self.HOST_PORT))
            self.server.listen(10)                                                 # server is listening for client connection
            threading._start_new_thread(self.accept_clients, (self.server, " "))   # start a thread running the accept_clients function
            window.btnStart.config(state=tk.DISABLED)
            window.btnStop.config(state=tk.NORMAL)
            window.lblHost["text"] = "Host: " + self.HOST_ADDR
            window.lblPort["text"] = "Port: " + str(HOST_PORT)
        except OSError:
            print('Port seems unavaiable, testing another')
            self.HOST_PORT += 1
            if self.HOST_PORT - HOST_PORT < 10: # Avoid to many attempts 
                self.start_server()

    def stop_server(self):
        '''This is currently only cosmetic'''
        window.btnStart.config(state=tk.NORMAL)
        window.btnStop.config(state=tk.DISABLED)

    def accept_clients(self, the_server, y):
        '''Continuously running function that looks for new client connections'''
        while True:
            client, addr = the_server.accept()
            self.clients.append(client)
            threading._start_new_thread(self.send_receive_client_message, (client, addr))    # On new connection, start thread that manages the connection

    def send_receive_client_message(self, client_connection, client_ip_addr):
        '''First connection with client'''
        data = pickle.loads(client_connection.recv(data_stream_size))                        # This is the first incoming data from client on establishing connection
        client_name = data['client_name']                                                    # Grab client namne
        self.clients_names.append(client_name)                                               # Add client name to list with active clients
        window.update_client_names_display(self.clients_names)                               # Update client names in server window
        print(f'connected to {client_name}')
        server_msg = game.get_data_package('connect')
        client_connection.send(pickle.dumps(server_msg))
        self.connection_player.update({client_connection:str(self.client_id)})               # Uppdate dict with connections and client id
        self.client_id += 1                                                                  # Increment player id

        '''Continuous communication with client'''
        while True:
            try:
                data = pickle.loads(client_connection.recv(data_stream_size))   # Recive client communication
            except Exception as e:                                  # Crashes if client closes application, break loop
                print(e)
                break
            if not data: break

            '''Process positional data'''
            if data['type'] == 'pos':                   # Keep track of entity positions in server memory
                # print(data)
                if data['entity'] == 'player':
                    game.player_dict[data['id']].update({'pos':data['pos']})    
                if data['entity'] == 'enemy':
                    game.enemy_dict[data['id']].update({'pos':data['pos']})

            '''Process stats'''
            if data['type'] == 'entity_new_parameters':
                print(f'recieved entity parameters: {data}')
                # Update server dicts 
                ent_params = data['parameter_dict']
                ent_dict = game.get_ent_dict(ent_params['type'])
                id = ent_params['name']
                ent_dict[id].update(ent_params)

            '''Pass along to other clients'''
            # if data['type'] in ['pos', 'cam', 'mark', 'battletracker_update', 'battletracker_new_parameters', 'entity_new_parameters', 'battletracker_change_bar']:
            # Vilken typ är det som inte ska skickas vidare? ping? 
            if data['type'] not in []:
                self.send_data_to_clients(data, ignore=[client_connection]) 


        # If connection is broken, remove associated data
        print('Closing connection')
        idx = self.get_client_index(self.clients, client_connection)
        del self.clients_names[idx]
        del self.clients[idx]
        client_connection.close()
        window.update_client_names_display(self.clients_names)  # update client names display

    def send_data_to_clients(self, data, ignore=[], send_only_to=[]):
        server_msg = pickle.dumps(data)
        if send_only_to:
            for c in send_only_to:
                    c.send(server_msg)
        else:
            # print(f'sending to clients: {data}')
            for c in self.clients:
                if c not in ignore:
                    c.send(server_msg)

    # Return the index of the current client in the list of clients
    def get_client_index(self, client_list, curr_client):
        idx = 0
        for conn in client_list:
            if conn == curr_client:
                break
            idx = idx + 1
        return idx

class Game():
    '''This class keeps track of the gamestates and game data'''
    def __init__(self):
        self.player_dict = {}
        self.enemy_dict = {}
        self.battletracker_dict = {} # {id:initiative}
        self.current_level = ''

    def get_current_level_path(self):
        return self.current_level
    
    def get_ent_dict(self, type):
        if type == 'player':
            return self.get_player_dict()
        if type == 'enemy':
            return self.get_enemy_dict()

    def get_player_dict(self):
        return self.player_dict

    def get_enemy_dict(self):
        return self.enemy_dict
    
    def load_tmx(self, path):
        print(f'Loading {path} into server')
        self.current_level = path
        self.enemy_dict = {}        # Reset enemy dict
        tmx_data = TiledMap(path)
        self.parse_tmx(tmx_data)
        network.send_data_to_clients(self.get_data_package('load_level'))

    def parse_tmx(self, tmx_data):
        for layer_index, layer in enumerate(tmx_data.layers):
            if hasattr(layer,'data'):
                for x, y, surf in layer.tiles():
                    pos = (x * tile_size + tile_size/2, y * tile_size + tile_size/2) # Find center coordinates
                    if 'entity' in layer.name:
                        type = layer.name.split('_')[-1]
                        ent_name, max_hp, current_hp, armor_class, speed = get_tmx_ent_vars(tmx_data, layer_index, (x,y))
                        if type == 'players':               # Select dict to update
                            ent_dict = self.player_dict
                        if type == 'enemies':
                            ent_dict = self.enemy_dict
                            ent_name = check_name(ent_name, ent_dict)
                        
                        ent_dict.update({ent_name:{
                            'name': ent_name,
                            'pos':pos,
                            'max_hp':max_hp,
                            'current_hp':current_hp,
                            'armor_class':armor_class,
                            'speed':speed,
                            }})

    def get_data_package(self, type):
        data = {'type':type}
        if type == 'connect':               # First respons to client
            data.update({              
                'tmx_path':game.get_current_level_path(),
                'entity_dicts':{
                    'player_dict':game.get_player_dict(),
                    'enemy_dict': game.get_enemy_dict()}
                    })     
        
        if type == 'load_level':             # Prompt to load level
            data.update({
                'tmx_path':self.get_current_level_path(),
                'entity_dicts':{
                    'player_dict':game.get_player_dict(),
                    'enemy_dict': game.get_enemy_dict()}
                    })
        
        if type == 'battletracker_init':         # Respons on opening opening battletracker
            data.update({
                'bt_dict':self.battletracker_dict
            })
        
        return data

    def debug(self):
        print(self.player_dict)

root = tk.Tk()
window = Window(root)                           # instantiate tkinter window for gui
network = Network()
game = Game()

root.mainloop()