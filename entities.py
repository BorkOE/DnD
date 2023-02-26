import pygame
import pygame.gfxdraw
from settings import tile_size, portrait_radius
from math import atan2, cos, sin
from helper import load_image
from pygame.math import Vector2 as V
from helper import send_dummy_post, get_portrait, distance

def get_entity(type, player_dict, **kwargs): # Kwargs is a dictionary with named arguments
    '''This method returns the right type of entity when the game loads them'''
    if type == 'players':
        # Check if player already is instantiated. If so, only update position
        if kwargs['name'] in player_dict:
            player_dict[kwargs['name']].rect.center = kwargs['game_pos']
            return player_dict[kwargs['name']]
        # In player not already instantanitated 
        return (Player(
            kwargs['name'],
            kwargs['max_hp'],
            kwargs['current_hp'],
            kwargs['armor_class'],
            kwargs['speed'],
            kwargs['tmx_data'],
            kwargs['tmx_pos'],
            kwargs['index'],
            kwargs['groups'],
            kwargs['server_pos']
            ))
    if type == 'enemies':
        return (Enemy(
            kwargs['name'],
            kwargs['max_hp'],
            kwargs['current_hp'],
            kwargs['armor_class'],
            kwargs['speed'],
            kwargs['tmx_data'],
            kwargs['tmx_pos'],
            kwargs['index'],
            kwargs['groups'],
            kwargs['server_pos']
            ))

class Entity(pygame.sprite.Sprite):
    '''This is the base class for players and enemies.'''
    any_entity_moving = 0
    def __init__(self, groups, name, max_hp, current_hp, armor_class, speed, tmx_data, tmx_pos, index, pos):
        super().__init__(groups)
        self.id = name
        self.max_hp = int(max_hp)
        self.current_hp = int(current_hp)
        self.armor_class = int(armor_class)
        self.speed = int(speed)
        self.image, self.rect = get_portrait(tmx_data, tmx_pos, index)
        self.rect.center = pos
        self.marked = False
        self.moving = False
        self.start_pos = None
        self.distance_moved = None
        self.send_snap = False
        self.outside_move_sphere = False
        self.movement_radius = (self.speed / 5) * tile_size # One tile is 5 ft
        self.font_move = pygame.font.SysFont(None, 20)
        self.move_text_color = (50,50,50)
        self.move_text_background = load_image('../graphics/gui/measure_background.png')
        self.crowned = False
        self.visible = True

    def check_click(self,mouse_click, player_dict, enemy_dict, network):
        if self.rect.collidepoint(mouse_click) or self.outside_move_sphere:
            send_dummy_post()
            if not self.marked:
                if not Entity.any_entity_moving:
                    self.marked = True
                    network.send_data_to_server(self.get_data('mark'))
            else:                           # Already marked
                if self.moving:             # Drop entity if not overlaping
                    if self.check_overlap(self.rect.center, player_dict|enemy_dict):
                        self.send_snap = True
                        self.moving = False
                        self.marked = False
                        Entity.any_entity_moving = 0
                        send_dummy_post()
                else:                       # Pick up entity
                    self.moving = True
                    self.start_pos = self.rect.center
                    Entity.any_entity_moving = 1
        else:
            send_dummy_post()
            if self.marked:
                self.marked = False             # Unmark by clicking away
                network.send_data_to_server(self.get_data('mark'))
    
    def snap(self):
        '''Returns self center position snapped to nearest tile'''
        x, y = self.rect.center[0], self.rect.center[1]
        if x > 0: x_half = tile_size/2 
        else: x_half = - tile_size/2
        if y > 0: y_half = tile_size/2 
        else: y_half = - tile_size/2

        x_snap = int(x / tile_size) * tile_size + x_half
        y_snap = int(y / tile_size) * tile_size + y_half
        return V(x_snap,y_snap)

    def limit(self,pos): # Den här sköter så att vi inte kan flytta spelaren utanför en movement-circle
        x = pos[0]
        y = pos[1]
        self.distance_moved = distance([x,y], self.start_pos)
        if self.distance_moved < self.movement_radius:
            self.outside_move_sphere = False
            return (x,y)
        else:
            self.distance_moved = self.movement_radius # För att begränsa vad stegräknaren visar
            self.outside_move_sphere = True
            x = x - self.start_pos[0]
            y = y - self.start_pos[1]
            radians = atan2(y,x)
            return (
                cos(radians) * self.movement_radius + self.start_pos[0],
                sin(radians) * self.movement_radius + self.start_pos[1]
            )

    def check_overlap(self, target_pos, entitiy_dict):
        '''Returns True if snap-pos is unoccupied'''
        for _, entity in entitiy_dict.items():
            if entity == self: continue
            if distance(target_pos, entity.rect.center) < tile_size/2 + 5:
                return False
        return True

    def get_data(self, type):
        if type == 'pos':
            data = {'type':type, 'entity':self.type, 'id':self.id, 'pos':self.rect.center, 
            'marked':self.marked, 'start_pos':self.start_pos, 
            'move_sphere':self.outside_move_sphere, 'dist_move':self.distance_moved}
        if type == 'mark':
            data = {'type':type, 'entity':self.type, 'id':self.id, 'marked':self.marked}
        return data

    def update(self, camera, network, limit=True):
        if self.moving or self.send_snap:
            pos = camera.get_mouse_game_pos()                                       # Get ingame position from mouse
            if limit:
                self.rect.center = self.limit(pos)

            if not self.send_snap:  # Continuous movement
                network.send_data_to_server(self.get_data('pos'))
            else:                   # Last move
                self.rect.center = self.snap()
                self.start_pos = None
                self.outside_move_sphere = False
                self.send_snap = False
                network.send_data_to_server(self.get_data('pos'))

    def get_entity_parameters(self):
        '''Gets and packages parameters for entity'''
        data = {'type':'entity_new_parameters'}
        data.update({'parameter_dict':{
            'name':self.id,
            'type':self.type,
            'max_hp':self.max_hp,
            'current_hp':self.current_hp,
            'armor_class':self.armor_class,
            'speed':self.speed
        }})
        return data
    
    def set_entity_parameters(self, param_dict):
        self.max_hp = int(param_dict['max_hp'])
        self.current_hp = int(param_dict['current_hp'])
        self.armor_class = int(param_dict['armor_class'])
        self.speed = int(param_dict['speed'])

    def crown(self):
        # print(f'crowning {self.id}')
        self.crowned = True
    
    def decrown(self):
        self.crowned = False

class Player(Entity):
    '''Overrides only player specific parameters and functions'''
    def __init__(self, name, max_hp, current_hp, armor_class, speed, tmx_data, tmx_pos, index, groups, pos):
        super().__init__(groups, name, max_hp, current_hp, armor_class, speed,tmx_data, tmx_pos, index, pos)
        self.type = 'player'
        self.movement_line_col = (0,150,50)
        self.marked_img, self.marked_img_rect = load_image('../graphics/players/marked_player.png', True)
        self.marked_img_orig = self.marked_img.copy()
        
class Enemy(Entity):
    '''Overrides only enemy specific parameters and functions'''
    def __init__(self, name, max_hp, current_hp, armor_class, speed, tmx_data, tmx_pos, index, groups, pos):
        super().__init__(groups, name, max_hp, current_hp, armor_class, speed, tmx_data, tmx_pos, index, pos)
        self.type = 'enemy'
        self.movement_line_col = (200,100,50)
        self.marked_img, self.marked_img_rect = load_image('../graphics/players/marked_enemy.png', True)
        self.marked_img_orig = self.marked_img.copy()


