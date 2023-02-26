import pygame as pg
from pygame.math import Vector2 as V
from settings import tile_size
from helper import load_image

class CameraGroup(pg.sprite.Group):
    def __init__(self):
        super().__init__()

    def custom_draw(self, camera):
        '''Only draw sprites on internal surf. Camera will handle final blitting to display surf'''
        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - camera.offset + camera.internal_offset
            camera.internal_surf.blit(sprite.image, offset_pos)
        
    def check_click(self, game_click_pos, player_dict, enemy_dict, network):
        for sprite in self.sprites():
            sprite.check_click(game_click_pos, player_dict, enemy_dict, network)
    
class DefaultCustomDrawGroup(CameraGroup):
    def __init__(self):
        super().__init__()
    
class EntityGroup(CameraGroup):
    '''spritegroup for entities'''
    def __init__(self):
        super().__init__()
        self.crown_img = load_image('../graphics/battletracker/crown.png')

    def get_movement_text(self, sprite):
        ft = str(int(sprite.distance_moved / tile_size * 5))
        m = str(int((sprite.distance_moved / tile_size * 5) * 0.3048))
        text_move = sprite.font_move.render(f'{ft} ft / {m} m', True, sprite.move_text_color)
        text_rect = text_move.get_rect(center=V(sprite.move_text_background.get_size())/2)
        lbl = sprite.move_text_background.copy()
        lbl.blit(text_move, text_rect)
        return lbl

    def custom_draw(self, camera):
        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - camera.offset + camera.internal_offset
            if sprite.marked:
                ent_center = offset_pos + V(tile_size/2, tile_size/2)
                sprite.marked_img_rect.center = ent_center
                camera.internal_surf.blit(sprite.marked_img, sprite.marked_img_rect)
                if sprite.start_pos:    # Entity is being moved 
                    line_start = sprite.start_pos - camera.offset + camera.internal_offset
                    pg.draw.line(camera.internal_surf, sprite.movement_line_col, line_start, ent_center, 2)
                    move_text = self.get_movement_text(sprite)
                    camera.internal_surf.blit(move_text, offset_pos+V(-5, 80))
                    if sprite.outside_move_sphere:
                        pg.draw.circle(camera.internal_surf, sprite.movement_line_col, line_start, sprite.movement_radius, 2)
            if sprite.crowned:
                ent_center = offset_pos + V(tile_size/2, tile_size/2)
                camera.internal_surf.blit(self.crown_img, (ent_center + V(-9,-55)))
            try:
                camera.internal_surf.blit(sprite.image, offset_pos)
            except Exception as e:
                print('Something crasched while blitting')
                print(e)

    def update(self, camera, network):
        for sprite in self.sprites():
            sprite.update(camera, network)

class SpecialBarGroup(pg.sprite.Group):
    def __init__(self):
        super().__init__(self)
    def update_bar(self, dm_battletracker=False, event_list=[]):
        for bar in self.sprites():
            bar.update_bar(dm_battletracker, event_list)