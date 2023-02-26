import pygame as pg
from helper import send_dummy_post, snap_coordinates
from settings import tile_size
from pygame.math import Vector2 as V

MARK_COLOR = (150,250,150)
LINE_SIZE = 2

class Marker():
    def __init__(self):
        self.active = False
        self.start_click = None
        self.mark_rect = None 
        self.marked_entities = []
        self.triggered = False # When marked and ready to move
 
    def toogle(self):
        self.active = not self.active
        self.unmark_entities()
        # Change cursor
        send_dummy_post()


    def set_start_click(self, pos):
        self.unmark_entities()
        self.start_click = pos

    def mark_area(self, camera):
        if self.start_click:
            self.mark_rect = self.construct_rect(self.start_click, camera.get_mouse_game_pos())
            blit_rect = self.mark_rect.copy()
            blit_rect.center += - camera.offset + camera.internal_offset
            pg.draw.rect(camera.internal_surf, MARK_COLOR, blit_rect, LINE_SIZE)

    def construct_rect(self, start_pos, current_pos):
        width = abs(start_pos[0] - current_pos[0])
        height = abs(start_pos[1] - current_pos[1])
        rect = pg.rect.Rect(0,0,width, height)
        left = False
        top = False
        if start_pos[0] - current_pos[0] < 0:
            left = True
        if start_pos[1] - current_pos[1] < 0:
            top = True
        if left and top:
            rect.topleft = start_pos
        elif left and not top:
            rect.bottomleft = start_pos
        elif not left and top:
            rect.topright = start_pos
        elif not left and not top:
            rect.bottomright = start_pos
        else:
            return None
        return rect

    def check_marking(self, entities):
        self.start_click = None
        if self.mark_rect:
            for e in entities:
                if self.mark_rect.colliderect(e.rect):
                    self.marked_entities.append(e)
        if self.marked_entities:
            self.mark_entities()
            self.triggered = True
        send_dummy_post()
    
    def mark_entities(self):
        for e in self.marked_entities:
            e.marked = True
        
    def unmark_entities(self):
        for e in self.marked_entities:
            e.marked = False
            e.moving = False
        self.marked_entities = []
        self.triggered = False
        
    def move_entities(self, camera, ent_dict, network):
        '''Finds target position, moves entities and sends to network'''
        if self.triggered:
            center = snap_coordinates(camera.find_mean_pos(self.marked_entities)) 
            target = snap_coordinates(camera.get_mouse_game_pos())
            move_vector = target-center
            for e in self.marked_entities:
                target = e.rect.center + move_vector
                while not e.check_overlap(target, ent_dict):
                    target = snap_coordinates(target + V(tile_size, 0))
                e.rect.center = target
                data = e.get_data('pos')
                data['marked'] = False
                network.que(data)

            self.unmark_entities()
