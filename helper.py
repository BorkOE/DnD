import pygame as pg
from pygame.math import Vector2 as V
from pathlib import Path
import sys
from settings import portrait_radius, tile_size


def load_image(path, get_rect=False, force_alpha=False):
    """ Load image and return image object"""
    try:
        image = pg.image.load(path)
        if image.get_alpha() is None and not force_alpha:
            image = image.convert()
        else:
            image = image.convert_alpha()
    except FileNotFoundError as e:
        print(f'Cannot load image: {path}')
        print(e)
        raise SystemExit
    if get_rect:
        return image, image.get_rect()
    return image

def grab_animation_surfaces(tmx_data):
    gid_animation_dict = {}
    for gid, props in tmx_data.tile_properties.items():
        if props['frames'] != []:
            gid_animation_dict.update({tmx_data.get_tile_image_by_gid(props['frames'][0][0]):
                                    [tmx_data.get_tile_image_by_gid(
                                        gid[0]) for gid in props['frames']]
                                    })
    return gid_animation_dict

def check_name(name, collection):
    i = 2
    while name in collection:
        name = name.split('_')[0]
        name = f'{name}_{i}'
        i += 1
    return name

def get_portrait(tmx_data, tmx_pos, index):
    '''Reads portrait img and mask and merges them.'''
    try:
        portrait_path_ = Path(tmx_data.get_tile_properties(tmx_pos[0], tmx_pos[1], index)['portrait_path'])
        portrait_mask_path_ = Path(tmx_data.get_tile_properties(tmx_pos[0], tmx_pos[1], index)['portrait_mask_path'])
    except Exception as e:
        print(e)
        print('Did you maybe place an enemy on the player layer in Tiled?')
        sys.exit()
    
    portrait_path = Path('/'.join(portrait_path_.parts[1:]))
    portrait_mask_path = Path('/'.join(portrait_mask_path_.parts[1:]))
    portrait_img = load_image(portrait_path)
    portrait_size = portrait_img.get_size()
    port_scale =  portrait_radius / min(portrait_size)
    portrait_img = pg.transform.smoothscale(portrait_img, (portrait_size[0]*port_scale, portrait_size[1]*port_scale))
    portrait_mask = load_image(portrait_mask_path) 
    portrait_mask = pg.transform.scale(portrait_mask, (portrait_radius, portrait_radius))
    col_in = (255,255,0)
    col_out = (255,0,0)
    portrait_mask.set_colorkey(col_in)
    portrait = portrait_img.copy()
    portrait.blit(portrait_mask, (0,0))
    portrait.set_colorkey(col_out)
    portrait_rect = portrait.get_rect()
    return portrait, portrait_rect

def get_tmx_ent_vars(tmx_data, layer_index, pos):
    name = tmx_data.get_tile_properties(pos[0], pos[1], layer_index)['name']
    max_hp = tmx_data.get_tile_properties(pos[0], pos[1], layer_index)['max_hp']
    armor_class = tmx_data.get_tile_properties(pos[0], pos[1], layer_index)['armor_class']
    speed = tmx_data.get_tile_properties(pos[0], pos[1], layer_index)['speed']
    return name, max_hp, max_hp, armor_class, speed

def distance(dot1, dot2, type='distance'):
    '''Returns dot1's distance from dot2'''
    if type == 'distance':
        return ((dot1[0] - dot2[0]) **2 + (dot1[1] - dot2[1]) **2) ** 0.5
    elif type == 'xy':
        return ((dot1[0] - dot2[0]), (dot1[1] - dot2[1]))

def render_text(string, font, topleft=None, center=None, topright=None, text_col=(20,20,20)):
    '''takes sting and return surface and rect'''
    text = font.render(str(string), True, text_col)
    if topleft:
        rect = text.get_rect(topleft=topleft)
    elif center:
        rect = text.get_rect(center=center)
    elif topright:
        rect = text.get_rect(topright=topright)
    else:
        rect = text.get_rect()
    return text, rect

def snap_coordinates(vector):
    '''Returns vector snapped to nearest center tile'''
    if not isinstance(vector, V):
        vector = V(vector)
    x, y = vector.x, vector.y
    if x > 0: x_half = tile_size/2 
    else: x_half = - tile_size/2
    if y > 0: y_half = tile_size/2 
    else: y_half = - tile_size/2

    x_snap = int(x / tile_size) * tile_size + x_half
    y_snap = int(y / tile_size) * tile_size + y_half
    return V(x_snap,y_snap)


'''Events'''
network_event = pg.USEREVENT + 99
input_event = pg.USEREVENT + 1

# anim_event_marked = pg.USEREVENT + 50

def send_dummy_post():
    pg.event.post(pg.event.Event(0, {}))

def post_network_event():
    pg.event.post(pg.event.Event(network_event, {}))

def post_key(key):
    '''Posts keypress as event'''
    pg.event.post(pg.event.Event(pg.KEYUP, {'key':key}))
    

# def send_animation_post(id, type):
#     pygame.event.post(pygame.event.Event(anim_event_marked, {'id':id, 'type':type}))

# def start_animation_timer(id, type):
#     send_dummy_post()
#     animation_event = pygame.event.Event(anim_event_marked, {'id':id, 'ent_type':type})
#     pygame.time.set_timer(animation_event, 200)