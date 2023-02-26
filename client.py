import pygame as pg
from pytmx import load_pygame
from tiles import Map
from entities import get_entity
from camera import Camera
from sprite_group import DefaultCustomDrawGroup, EntityGroup
from settings import HOST_ADDR, HOST_PORT, tile_size, hotkey_dict
from network import Network
from helper import check_name, get_tmx_ent_vars, input_event, send_dummy_post
from tools import Ping
from battletracker import BattleTracker
from input_box import InputBox
from drawing import Drawing
from marker import Marker
from context_menu import ContextMenu

     
class Game():

    def __init__(self):
        pg.init()
        flags = pg.RESIZABLE
        self.screen = pg.display.set_mode((1000, 800), flags)
        self.camera = Camera(self.screen)
        self.map_group = DefaultCustomDrawGroup()
        self.player_group = EntityGroup()
        self.enemy_group = EntityGroup()
        self.drawing = Drawing()
        self.marker = Marker()
        self.context_menu = ContextMenu()
        self.tmx_data = None
        self.player_dict = {}
        self.enemy_dict = {}
        self.battle_tracker = [] # holds the active battle tracker
        self.input_box = []
        self.dm = False          # Dungeon Master or not

    def load_tmx(self, data):
        print(f'Loadning tmx: {data["tmx_path"]}')
        self.tmx_data = load_pygame(data['tmx_path'])
        self.load_map()
        self.load_entities(data['entity_dicts'])
        
    def load_map(self):
        for obj in self.tmx_data.objects:
            pos = obj.x, obj.y
            if obj.image:
                self.map_group.empty()                     # Removes any old map
                Map(pos=pos, surf=obj.image,            
                groups=self.map_group, obj=obj)
    
    def load_entities(self, server_dicts):
        '''Load entities into pygame'''
        self.enemy_group.empty()
        self.enemy_dict = {}        # The dicts is how the network class finds the right entity to move
        for layer_index, layer in enumerate(self.tmx_data.layers):
            if hasattr(layer,'data'):
                for x, y, surf in layer.tiles():
                    game_pos = (x*tile_size+tile_size/2, y*tile_size+tile_size/2)
                    if 'entity' in layer.name:
                        type = layer.name.split('_')[-1]
                        ent_name, max_hp, current_hp, armor_class, speed = get_tmx_ent_vars(self.tmx_data, layer_index, (x,y))
                        if type == 'players':                                    # Select dict to update
                            server_dict = server_dicts['player_dict']
                            game_dict = self.player_dict
                            group = self.player_group
                        if type == 'enemies':
                            server_dict = server_dicts['enemy_dict']
                            game_dict = self.enemy_dict
                            group = self.enemy_group
                            ent_name = check_name(ent_name, self.enemy_dict)      # Gives unique names to enemies if more than one of same type
                        
                        if ent_name in server_dict: # Update stats according to server dict if name matches. 
                            max_hp, current_hp, armor_class, speed = self.get_params_from_gamedict(ent_name, server_dict)

                        game_dict.update({
                            ent_name:get_entity(type, self.player_dict, 
                            name=ent_name, 
                            max_hp=max_hp,
                            current_hp=current_hp,
                            armor_class=armor_class,
                            speed=speed,
                            tmx_data=self.tmx_data,
                            tmx_pos=(x,y),
                            index=layer_index,
                            groups=group,
                            server_pos=server_dict[ent_name]['pos'],
                            game_pos=(game_pos)
                            )
                        })

    def get_params_from_gamedict(self, ent_name, server_dict):
        '''return parameters from dict for entity creation'''
        return server_dict[ent_name]['max_hp'], server_dict[ent_name]['current_hp'], server_dict[ent_name]['armor_class'], server_dict[ent_name]['speed']

    def update_input(self, event_list, mouse_pos):
        self.camera.camera_control(event_list, mouse_pos, self.player_dict, network, self.battle_tracker, self.drawing)    # Handles camera controll input (zoom, scroll)
        self.drawing.event_handler(event_list, self.camera, network)
        '''Check entity input and send entity position to network'''
        self.player_group.update(self.camera, network)
        self.enemy_group.update(self.camera, network)
    
    def draw_graphics(self, mouse_pos):
        '''Drawing order, everyting is drawn on a internal surf that can be zoomed in and out'''
        self.screen.fill('black')                                              # Resets display-screen
        self.map_group.custom_draw(self.camera)
        self.enemy_group.custom_draw(self.camera) 
        self.drawing.blit(self.camera, mouse_pos)
        self.player_group.custom_draw(self.camera)
        if self.marker.active:
            self.marker.mark_area(self.camera)
        self.camera.final_draw(self.screen)                       # Makes the final blitting to display screen
        self.context_menu.blit(self.screen, camera=self.camera, dm=self.dm, drawing=self.drawing)                       # Blits context menu on top of game. Uses kwargs

    def check_click(self):
        if self.battle_tracker:
            if self.battle_tracker[-1].marked: 
                return
        if self.marker.active:
            return
        game_click_pos = self.camera.get_mouse_game_pos()
        self.player_group.check_click(game_click_pos, self.player_dict, self.enemy_dict, network)
        self.enemy_group.check_click(game_click_pos, self.player_dict, self.enemy_dict, network)

    def ping(self, pos=None, send=False):
        '''Handles both local ping and recived ping from network'''
        if send:
            Ping(self.camera, self.camera.get_mouse_game_pos()).send(network)
        else:
            Ping(self.camera, pos)

    def instantiate_battletracker(self, screen):
        if not self.battle_tracker:
            self.battle_tracker.append(BattleTracker(self.camera, self.get_entities(type='dict'), network, self.dm))
            if self.battle_tracker[-1].kill: # check if we should terminate bt
                self.close_battletracker()
        else:
            self.close_battletracker()
    
    def close_battletracker(self):
        if self.battle_tracker:
            del self.battle_tracker[-1]
        for e in self.get_entities():
            e.is_marked = False
            e.crowned = False
        send_dummy_post()    

    def update_battletracker(self, network_data):
        '''Passes along data from network to battletracker'''
        if self.battle_tracker:
            self.battle_tracker[-1].parse_network_update(network_data, self.get_entities('dict'))

    def get_entities(self, type='list'):
        if type == 'list':
            return list(self.player_dict.values()) + list(self.enemy_dict.values())
        if type == 'dict':
            return self.player_dict|self.enemy_dict
    
    def toogle_dm(self):
        self.dm = not self.dm
        self.drawing.toogle_dm(self.dm)

    def handle_events(self, event_list, mouse_pos, mouse_keys):
        for event in event_list:
            if event.type == pg.QUIT:
                exit()
            if event.type == pg.MOUSEBUTTONDOWN:
                if mouse_keys[0]:
                    if self.marker.active:
                        self.marker.move_entities(self.camera, self.get_entities('dict'), network)
                        self.marker.set_start_click(self.camera.get_mouse_game_pos())
                if mouse_keys[2]:
                    if self.marker.triggered:
                        self.marker.unmark_entities()
            if event.type == pg.MOUSEBUTTONUP and event.button == 1 :    # Leftclick
                self.context_menu.check_click(mouse_pos)
                if not (self.input_box or self.drawing.active):
                    self.check_click()
                    self.marker.check_marking(self.get_entities())

            if event.type == pg.VIDEORESIZE:
                self.camera.update_camera()
                self.context_menu.get_new_surface()
            if event.type == input_event:
                self.input_box.append(InputBox(event.execute_on_sucess, event.datatype, event.prev_input))

            if event.type == pg.KEYUP:
                if not self.input_box:
                    if event.key == hotkey_dict.get('ping'):
                        self.ping(send=True)
                    if event.key == hotkey_dict.get('bt_instantiate'):
                        self.instantiate_battletracker(self.screen)
                    if event.key == hotkey_dict.get('dm'):
                        self.toogle_dm()
                    if event.key == hotkey_dict.get('tool_marker'):
                        self.marker.toogle()


    def run(self):
        clock = pg.time.Clock()
        running = True
        pg.display.set_caption(f'DnD Client')
        first_data = network.connect_to_server()
        self.load_tmx(first_data)
        self.camera.center_target(self.camera.find_mean_pos(self.player_dict.values()))
 
        while running:
            '''Main client loop'''
            event_list = pg.event.get()
            mouse_pos = pg.mouse.get_pos()
            mouse_keys = pg.mouse.get_pressed()

            if not event_list and not self.camera.pos_queue and not network.package_que:                        # If no events are detected, leave previously drawn screen the same
                pass
            else:                                                                   # Only draws new stuff if events or camera movement
                self.update_input(event_list, mouse_pos)
                self.draw_graphics(mouse_pos)
                self.handle_events(event_list, mouse_pos, mouse_keys)

                # Handle battletracker
                if self.battle_tracker:
                    if not self.input_box:
                        self.battle_tracker[-1].update(event_list, mouse_pos)
                    self.battle_tracker[-1].draw(self.screen)
                    if self.battle_tracker[-1].kill: # check if we should terminate bt
                        self.close_battletracker()
                
                # handle Inputbox
                if self.input_box:
                    if self.input_box[-1].kill:
                        if self.input_box[-1].sucess:
                            exec(self.input_box[-1].execute_on_sucess)
                        self.input_box = []
                    else:
                        self.input_box[-1].update(event_list, mouse_pos)
                        self.input_box[-1].draw(self.screen)

                # Handle network que
                network.handle_que()

            pg.display.update()
            clock.tick(30) 
        pg.quit()

game = Game()
network = Network(game)
game.run()