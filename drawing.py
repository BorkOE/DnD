import pygame as pg
from helper import distance, send_dummy_post
from settings import hotkey_dict

RECT_FACTOR = 1.6
SIZE_CHANGE_FACTOR = 5
DM_OPACITY = 130 # 0=transparent 255=opaque
DEFAULT_COLOR = (20,20,20,255)
MIN_BRUSHSIZE = 5
MAX_BRUSHSIZE = 600
CANVAS_SIZE = (2500,2500)

class Drawing():
    def __init__(self):
        self.diameter = 40
        self.brushtype = 1 # Type of brush, circle or square
        self.active = False
        # self.content = False
        self.new_canvas((0,0)) # Creates empty canvas from the start

    def event_handler(self, event_list, camera, network):
        for event in event_list:
            if event.type == pg.KEYUP:
                if event.key == hotkey_dict.get('draw_new_canvas'):
                    self.new_canvas(camera.get_screen_center_game_pos(), network)
                if event.key == hotkey_dict.get('draw_toogle'):
                    self.toogle_active()
                if event.key == hotkey_dict.get('draw_change_type'):
                    self.change_brushtype()

        # Painting input
        pressed_keys = pg.key.get_pressed()
        pressed_mouse = pg.mouse.get_pressed()
        pressed_mods = pg.key.get_mods()
        if self.active and not pressed_keys[hotkey_dict.get('hold_to_move')]:
            gamepos = camera.get_mouse_game_pos()
            if pressed_mouse[0] and pressed_mods != 64:
                self.paint(gamepos, network=network)
            if (pressed_mouse[2]) or (pressed_mouse[0] and pressed_mods == 64):
                self.paint(gamepos, color=(0,0,0,0), network=network)
            if event.type == pg.MOUSEWHEEL:
                self.change_size(event.y)

    def new_canvas(self, center, network=None):
        self.drawing_surf = pg.Surface(CANVAS_SIZE)
        self.drawing_surf = self.drawing_surf.convert_alpha()
        self.drawing_surf.fill((0,0,0,0))
        self.rect = self.drawing_surf.get_rect(center=center)
        # self.content = True
        # self.active = True
        send_dummy_post()
        if network:
            self.send_new_canvas(center, network)

    def change_size(self, delta):
        '''Changes paint size'''
        target = self.diameter + delta * SIZE_CHANGE_FACTOR
        if MIN_BRUSHSIZE < target < MAX_BRUSHSIZE:
            self.diameter = target
    
    def change_brushtype(self):
        self.brushtype = not self.brushtype

    def paint(self, pos, color=DEFAULT_COLOR, diameter=None, brushtype=None, network=None):
        '''Main painting function, both for networked input and local'''
        # print('painting!')
        if diameter == None:
            diameter = self.diameter
        if brushtype == None:
            brushtype = self.brushtype
        draw_pos = distance(pos, self.rect.topleft, 'xy')
        if brushtype:
            pg.draw.circle(self.drawing_surf, color, draw_pos, diameter, 0) # Filled cirlce
        else:
            rect = pg.rect.Rect(0,0,diameter * RECT_FACTOR, diameter * RECT_FACTOR)
            rect.center = draw_pos
            pg.draw.rect(self.drawing_surf, color, rect, 0)
        # Send to network
        if network:
            self.send_paint(pos, diameter, brushtype, color, network)


    def toogle_dm(self, dm):
        # if self.content:
        if dm:
            self.drawing_surf.set_alpha(DM_OPACITY)
        else:
            self.drawing_surf.set_alpha(255)
        send_dummy_post()
    
    def toogle_active(self):
        self.active = not self.active
        send_dummy_post()

    def blit(self, camera, mouse_pos):
        offset_pos = self.rect.topleft - camera.offset + camera.internal_offset
        camera.internal_surf.blit(self.drawing_surf, offset_pos)
        if self.active: # Draw marker
            draw_pos = camera.screenpos_to_gamepos(mouse_pos) - camera.offset + camera.internal_offset
            if self.brushtype:
                pg.draw.circle(camera.internal_surf, (255,255,255,255), draw_pos, self.diameter, 1) 
            else:
                rect = pg.rect.Rect(0,0,self.diameter*RECT_FACTOR,self.diameter*RECT_FACTOR)
                rect.center = draw_pos
                pg.draw.rect(camera.internal_surf, (255,255,255,255), rect, 1)

    # Network functions
    def parse_network_update(self, network_data):
        print('recieved network data')
        if network_data['type'] == 'new_canvas':
            self.new_canvas(network_data['center'])
        if network_data['type'] == 'paint':
            self.paint(
                network_data['pos'], 
                color = network_data['color'], 
                diameter = network_data['diameter'], 
                brushtype = network_data['brushtype'])

    def send_new_canvas(self, center, network):
        data = {'type':'new_canvas', 'center':center}
        network.send_data_to_server(data)

    def send_paint(self, pos, diameter, brushtype, color, network):
        data = {'type':'paint', 'pos':pos, 'diameter':diameter, 'brushtype':brushtype, 'color':color}
        network.send_data_to_server(data)
        