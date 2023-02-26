import pygame as pg
from pygame.math import Vector2 as V
from settings import tile_size, smoothscale_zoom, hotkey_dict
from helper import load_image, send_dummy_post


class Grid():
    def __init__(self) -> None:
        self.active = False
        self.selection = 1
        self.transparency = 1
        grid_1 = load_image('../graphics/grid/grid_black.png')
        grid_2 = load_image('../graphics/grid/grid_lightblue.png')
        grid_3 = load_image('../graphics/grid/grid_red.png')
        self.grid_dict = {1:grid_1, 2:grid_2, 3:grid_3}
        self.current_grid = self.grid_dict[self.selection]
    
    def change_grid_to(self, selection):
        # if selection > len(self.grid_dict): selection = 1
        self.selection = selection
        self.current_grid = self.grid_dict[selection]
        self.current_grid.set_alpha((int(self.transparency * 255)))
    
    def change_transparency_to(self, selected_transparency):
        if selected_transparency > 1: selected_transparency = 1
        if selected_transparency < 0: selected_transparency = 0
        self.transparency = selected_transparency
        self.current_grid.set_alpha((int(self.transparency * 255))) 
        
    def draw_grid(self, display_surf, camera):
        display_surf.blit(self.current_grid, (-(camera.offset.x % tile_size), -(camera.offset.y % tile_size)))

class Camera():
    '''Camera settings'''
    zoom_speed = 0.05
    scroll_speed = 12
    min_zoom = 0.4
    max_zoom = 3

    def __init__(self, surface):
        self.dm_mode = False
        self.display_surface = surface
        self.window_vector = V(pg.display.get_window_size())
        self.w, self.h = self.display_surface.get_size()
        self.half_w = self.w / 2
        self.half_h = self.h / 2
        self.internal_surf_size = (4000,3000)
        self.offset = V(0,0)
        self.internal_surf = pg.Surface(self.internal_surf_size, pg.SRCALPHA).convert_alpha()
        self.internal_rect = self.internal_surf.get_rect(center=(self.half_w, self.half_h))
        self.internal_offset = V()
        self.internal_offset.x = self.internal_surf_size[0] / 2 - self.half_w
        self.internal_offset.y = self.internal_surf_size[1] / 2 - self.half_h
        self.pos_queue = []
        self.prev_mouse_pos = V()
        self.freeze_input = False

        # Zoom
        self.zoom_scale = 1
        self.prev_zoom_scale = 1
        self.internal_surface_size_vector = pg.math.Vector2(self.internal_surf_size)

        # Animation
        self.anim_que = {}  # pos:[frames]

        # Network
        self.pair_camera = False
        self.pair_camera_zoom = False

    def camera_control(self, event_list, mouse_pos, player_dict, network, battle_tracker, drawing):
        if battle_tracker:
            if battle_tracker[-1].marked: return
        cam_change = False
        if self.pos_queue: # If there are positions in que, set camera to this position 
            self.perform_camera_movement()
        
        pressed_key = pg.key.get_pressed()
        pressed_mouse = pg.mouse.get_pressed()
        mod_key = pg.key.get_mods()
        # Scroll camera with mouse
        if (pressed_mouse[1]) or ((mod_key == 4160 or pressed_key[hotkey_dict.get('hold_to_move')]) and pressed_mouse[0]):
            cam_change = True
            self.pos_queue = [] # Resets if the camera is moving
            self.offset += (self.prev_mouse_pos - mouse_pos) / self.zoom_scale
        self.prev_mouse_pos *= 0 # reset
        self.prev_mouse_pos += mouse_pos
        for event in event_list:
            if event.type == pg.MOUSEWHEEL and mod_key == 64 and not drawing.active: # Zoom
                cam_change = True
                zoom_delta = event.y * self.zoom_speed
                if self.min_zoom < self.zoom_scale - zoom_delta < self.max_zoom:        # Check if zoom change is within limits
                    self.zoom_scale -= zoom_delta
                    self.update_camera()
            if event.type == pg.MOUSEWHEEL and mod_key != 64 and not drawing.active: # Scroll canvas with mousescroll
                cam_change = True
                self.pos_queue = [] # Resets if the camera is moving
                self.offset.x -= event.x * self.scroll_speed
                self.offset.y += event.y * self.scroll_speed
            if event.type == pg.KEYUP:
                if event.key == hotkey_dict.get('camera_reset_zoom'):                     # Reset zoom
                    cam_change = True
                    self.zoom_scale = 1
                    self.update_camera()
                if event.key == hotkey_dict.get('camera_center_player'):
                    cam_change = True
                    self.move_camera_to(self.find_mean_pos(player_dict.values()))
                if event.key == hotkey_dict.get('camera_send') and not self.pair_camera:
                    self.send_cam_to_network(network)
                if event.key == hotkey_dict.get('camera_sync_pos'):                    # Camera paring logic
                    if self.pair_camera:
                        self.pair_camera_zoom = False
                    self.pair_camera = not self.pair_camera
                if event.key == hotkey_dict.get('camera_sync_zoom'):
                    self.pair_camera = True
                    self.pair_camera_zoom = not self.pair_camera_zoom

        if self.pair_camera and (cam_change or self.pos_queue): 
            self.send_cam_to_network(network)

    def update_camera(self):
        self.window_vector = V(pg.display.get_window_size())
        self.w, self.h = self.window_vector[0], self.window_vector[1]
        self.internal_offset.x += self.half_w - self.window_vector[0]/2
        self.internal_offset.y += self.half_h - self.window_vector[1]/2
        self.half_w = self.window_vector[0] / 2
        self.half_h = self.window_vector[1] / 2
        self.internal_rect.center = (self.half_w, self.half_h)

    def move_camera_to(self, pos):
        '''Give position and camera moves smoothly there'''
        self.pos_queue.extend(self.find_camera_positions(pos))

    def find_camera_positions(self, end_pos):
        start_pos = (self.offset[0] + self.half_w, self.offset[1] + self.half_h)
        len_list = 30
        x_step = ((start_pos[0] - end_pos[0]) / len_list)
        y_step = ((start_pos[1] - end_pos[1]) / len_list)
        x_list, y_list = [start_pos[0]], [start_pos[1]]
        for step in range(len_list+1):
            if step in [9,11,12,13,14,15,16,17,19]:
                continue
            x_list.append((x_list[-1] - x_step))
            y_list.append((y_list[-1] - y_step))
        len_list = 20
        x_step = ((x_list[-1] - end_pos[0]) / len_list)
        y_step = ((y_list[-1] - end_pos[1]) / len_list)
        for step in range(len_list):
            x_list.append((x_list[-1] - x_step))
            y_list.append((y_list[-1] - y_step))
        x_list.append(end_pos[0])
        y_list.append(end_pos[1])
        return tuple(zip(x_list, y_list))

    def perform_camera_movement(self):
        if self.pos_queue:
            self.center_target(self.pos_queue.pop(0))

    def center_target(self, target_pos):
        self.offset -= self.offset # Reset to zero
        self.offset.x = target_pos[0] - self.half_w
        self.offset.y = target_pos[1] - self.half_h
    
    def find_mean_pos(self, collection):
        '''Find mean center position for entities in collection'''
        # players = player_dict.values()
        mid_x = sum([p.rect.centerx for p in collection]) / len(collection)
        mid_y = sum([p.rect.centery for p in collection]) / len(collection)
        return (mid_x, mid_y)

    def get_mouse_game_pos(self, snap=False):
        '''Gets mouseclick as game coordinates'''
        mouse_pos = V(pg.mouse.get_pos())
        game_pos = self.screenpos_to_gamepos(mouse_pos)
        if snap:
            pos_x = int(game_pos[0] / tile_size) * tile_size
            pos_y = int(game_pos[1] / tile_size) * tile_size
            game_pos = V(pos_x, pos_y)
        return game_pos
    
    def get_screen_center_game_pos(self):
        game_center = self.screenpos_to_gamepos(V(self.half_w, self.half_h))
        return game_center

    def screenpos_to_gamepos(self, pos):
        '''Converts given pos to true game position'''
        if self.zoom_scale == 1:
            game_pos = pos + self.offset
        else:
            centerpos = pos - V(self.half_w, self.half_h)
            game_pos = (centerpos / self.zoom_scale + self.offset) + V(self.half_w, self.half_h)
        return game_pos
    
    # def gamepos_to_internal_blitpos(self, gamepos):
    #     return V(gamepos) - self.offset + self.internal_offset

    def get_ingame_view_rect(self):
        '''Gets rect same as view-window'''
        center = self.get_screen_center_game_pos()
        topleft = center - (V(self.w, self.h) / 2) / self.zoom_scale
        zoom_wh = V(self.w, self.h) / self.zoom_scale
        return pg.rect.Rect(topleft, zoom_wh) 

    def check_objects_in_view(self, collection):
        '''Takes in collection of sprites and returns those that are in view of camera'''
        in_view= []
        view_rect = self.get_ingame_view_rect()
        for entity in collection:
            if view_rect.collidepoint(entity.rect.center):
                in_view.append(entity)
        return in_view

    def send_cam_to_network(self, network):
        cam_center = self.get_screen_center_game_pos()
        data = {'type':'cam', 'operation':'center', 'pos':cam_center, 'zoom':None}
        if self.pair_camera_zoom:
            data.update({'zoom':self.zoom_scale})
        network.send_data_to_server(data)

    def handle_animation_que(self):
        if self.anim_que:
            for pos, frame_list in self.anim_que.items():
                if frame_list:
                    kill = None
                    frame = frame_list.pop()
                    drawpos = pos - self.offset + self.internal_offset
                    self.internal_surf.blit(frame, drawpos)
                    send_dummy_post()
                else:
                    kill = pos
            if kill:
                del self.anim_que[kill]

    def final_draw(self, display_surf):
        '''Animation que'''
        self.handle_animation_que()
        
        '''Zoom and blit internal surf on display surf'''
        if 0.85 < self.zoom_scale < 1.15:
            blit_surf = self.internal_surf
        else:
            if smoothscale_zoom:
                blit_surf = pg.transform.smoothscale(self.internal_surf, self.internal_surface_size_vector * self.zoom_scale) # Resize to zoom scale, prettier but more resource intensive
            else:
                blit_surf = pg.transform.scale(self.internal_surf, self.internal_surface_size_vector * self.zoom_scale)       # Resize to zoom scale, ugly but faster

        blit_rect = blit_surf.get_rect(center=(self.half_w, self.half_h))                                           # Center scaled surf    
        display_surf.blit(blit_surf, blit_rect)                                                                     # Blit to screen
        self.internal_surf.fill('black')                                                                            # Reset internal surf
        


