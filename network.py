from sqlite3 import connect
from settings import HOST_ADDR, HOST_PORT, tile_size, data_stream_size
import socket
import pickle
import threading
import sys
import pygame as pg
from helper import post_network_event


class Network():
    hostname = socket.gethostname()
    if HOST_ADDR == "":                             # Indicates that client is on the same system as server
        HOST_ADDR = socket.gethostbyname(hostname)
    else:
        HOST_ADDR = HOST_ADDR

    def __init__(self, game):
        self.game = game
        self.package_que = []

    def connect_to_server(self, HOST_PORT=HOST_PORT):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
            self.client.connect((self.HOST_ADDR, HOST_PORT))                             # Connect to server
            client_msg = {'type':'connect', 'client_name':self.hostname}
            self.client.send(pickle.dumps(client_msg))                                   # Send this computers name to server after connecting
            first_data = pickle.loads(self.client.recv(data_stream_size))                # First respons from server
            # start a thread to keep receiving message from server
            threading._start_new_thread(self.receive_message_from_server, (self.client, "m"))
            return first_data
        
        except ConnectionRefusedError as e:
            print(e)
            # print('\nCould not connect to game server. Is it running?\nMake sure that ip and port is configured in settings')
            print('trying to connect to next port')
            # sys.exit()
            return self.connect_to_server(HOST_PORT+1)

    def receive_message_from_server(self, sck, m):
        while True:
            data = pickle.loads(sck.recv(data_stream_size))
            print(data['type']) # debugg
            if not data: break

            if data['type'] == 'mark':
                self.mark_entity(data)
            if data['type'] == 'pos': 
                self.move_entity(data)
            if data['type'] == 'load_level':  
                print(f'Loading new level {data["tmx_path"]}')
                self.game.close_battletracker()
                self.game.load_tmx(data)
            if data['type'] == 'cam': 
                self.control_camera(data)
            if data['type'] in ['battletracker_update', 'battletracker_new_parameters', 'battletracker_change_bar']:
                self.game.update_battletracker(data)
            if data['type'] == 'entity_new_parameters':
                self.update_entity_parameters(data)
            if data['type'] in ['new_canvas', 'paint']:
                self.game.drawing.parse_network_update(data)
            
            post_network_event()       # Needed because of idle state when no event list

        sck.close()

    def send_data_to_server(self, data):
        '''generic communication function, one way'''
        # print(f'sending to server: {data}')
        self.client.send(pickle.dumps(data))

    def ping_server(self, data):
        '''sends communication to server and returns server response''' # Had some problems with freezing using this...
        # print(f'pinging with {data}')
        self.client.send(pickle.dumps(data))
        return pickle.loads(self.client.recv(data_stream_size))

    def get_ent(self, data):
        type = data['entity']
        if type == 'player':
            ent = self.game.player_dict[data['id']]
        if type == 'enemy':
            ent = self.game.enemy_dict[data['id']]
        return ent

    def mark_entity(self, data):
        ent = self.get_ent(data)
        ent.marked = data['marked']

    def move_entity(self, data):
        ent = self.get_ent(data)
        ent.rect.center = data['pos']
        ent.marked = data['marked']
        ent.start_pos = data['start_pos']
        ent.outside_move_sphere = data['move_sphere']
        ent.distance_moved = data['dist_move']
    
    def update_entity_parameters(self, data):
        ent_params = data['parameter_dict']
        ent_params.update({'entity':ent_params['type'], 'id':ent_params['name']})
        self.get_ent(ent_params).set_entity_parameters(ent_params)
        if self.game.battle_tracker:
            self.game.battle_tracker[-1].bars[ent_params['name']].update()

    def control_camera(self, data):
        if data['operation'] == 'center':
            self.game.camera.center_target(data['pos'])
            if data['zoom']:
                self.game.camera.zoom_scale = data['zoom']
        if data['operation'] == 'ping':
            self.game.ping(pos=data['pos'])
        
    def que(self, package):
        '''Use if sending a collection of data eg. move tool. 
        Packages will be sent one every frame'''
        self.package_que.append(package)

    def handle_que(self):
        if self.package_que:
            data = self.package_que.pop()
            self.send_data_to_server(data)