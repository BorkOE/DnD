import pygame as pg
from pygame.math import Vector2 as V
from helper import send_dummy_post

'''Instantiates ping frames at startup'''
size = V((100,100))
ping_frames = []
surf = pg.Surface(size, pg.SRCALPHA)
radius_list = [50,50,50,50,50,49,48,47,45,43,40,7,6]
size_list = [1,1,2,2,3,3,4,4,3,1,1]
for temp_radius, temp_size in zip(radius_list,size_list):
    s_temp = surf.copy()
    pg.draw.circle(s_temp, 'white', size/2, temp_radius, temp_size)
    ping_frames.append(s_temp)

class Ping:
    def __init__(self, camera, pos):
        '''Sends ping-frames for camera to draw'''
        # print('pinging!')
        self.pos = pos
        camera.anim_que.update({tuple(pos-size/2):ping_frames.copy()})
        send_dummy_post()
    
    def send(self, network):
        '''Send ping-msg to server'''
        data = {'type':'cam', 'operation':'ping', 'pos':self.pos}
        network.send_data_to_server(data)