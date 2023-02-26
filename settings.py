from glob import glob
from pathlib import Path
import pygame as pg


'''Network'''
#"192.168.10.245"
HOST_ADDR = '127.0.0.1'        # Leave as empty string "" if client is on the same computer as server. Else, input host computers ip, e.g. "192.168.10.245" (shown in server window)
# HOST_ADDR = ''
HOST_PORT = 8090
data_stream_size = 4096*2

'''Game'''
smoothscale_zoom = True     # Prettier pixels when zooming - set to False for better performance
tile_size = 64
portrait_radius = 64
green = (116,252,95)
yellow = (239,249,102)

'''Hotkeys'''

hotkey_dict = {
    'hold_to_move':pg.K_SPACE,              # Press + mouse drag moves map
    'camera_center_player':pg.K_F1,         # Moves camera to mean position of players
    'camera_send':pg.K_F4,                  # Sends camera center to other clients once
    'camera_sync_pos':pg.K_F6,              # Syncs camera position with other clients
    'camera_sync_zoom':pg.K_F7,             # Syncs camera zoom level with other clients
    'camera_reset_zoom':pg.K_r,             # Reset camera zoom-factor to 1
    'dm':pg.K_0,                            # Toogles Dungeon Master status (can see though drawings, enemy health)
    'bt_instantiate': pg.K_b,               # Toogles battletracker
    'bt_minimize':pg.K_TAB,                 # Minimize battletracker
    'bt_next':pg.K_n,                       # Next entity in battletracker
    'bt_prev':pg.K_p,                       # Previous entity in battletracker
    'ping':pg.K_PERIOD,                     # Make a ping
    'tool_marker':pg.K_m,                   # Activates multiple select
    'draw_new_canvas':pg.K_d,               # Makes new canvas to draw on at center of screen
    'draw_toogle':pg.K_a,                   # Toogles drawing
    'draw_change_type':pg.K_t               # Change brushtype
    }                            

hotkey_dict.get('')

level_dict = {}
campaign_paths = glob('../data/campaigns/*')
for cp in campaign_paths:
    campaign = Path(cp).parts[-1]
    cp_level_paths = glob(f'{cp}/*.tmx')
    cp_level_names = [Path(l).parts[-1][:-4] for l in cp_level_paths] 
    level_path_dict = dict(zip(cp_level_names, cp_level_paths)) 
    level_dict.update({campaign:level_path_dict})
