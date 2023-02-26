import pygame as pg
from helper import send_dummy_post
from pygame.math import Vector2 as V

'''TODO
Negative values
'''

class InputBox():
    '''A small popup box that promts for input'''
    col = (20,20,20)
    size = 20
    def __init__(self, execute_on_sucess, datatype, prev_input='', width=150, height=40):
        self.font = pg.font.SysFont(None, self.size)
        if datatype == str:
            width = 250
        self.surf_empty = pg.surface.Surface((width, height))
        win_size = pg.display.get_window_size()
        self.rect = self.surf_empty.get_rect(center=V(win_size)/2)
        self.surf_empty.fill('gray')
        self.execute_on_sucess = execute_on_sucess        
        self.datatype = datatype
        self.input = prev_input
        self.value = None       # Holds the final value 
        self.sucess = False
        self.kill = False
    
    def draw(self, display):
        self.update_text()
        display.blit(self.surf, self.rect)
    
    def update_text(self):
        text = self.font.render(self.input, True, self.col)
        self.surf = self.surf_empty.copy()
        rect = text.get_rect(center=V(self.rect.w, self.rect.h)/2)
        self.surf.blit(text, rect)

    def update(self, event_list, mouse_pos):
        for e in event_list:
            if e.type == pg.MOUSEBUTTONUP:
                if self.rect.collidepoint(mouse_pos):
                    pass
            if e.type == pg.KEYUP:
                if e.key == pg.K_RETURN:
                    if self.datatype == int:
                        if self.input.isdigit():
                            self.sucess = True
                    if self.datatype == str:
                        self.sucess = True
                    self.kill = True
                elif e.key == pg.K_ESCAPE:
                    self.kill = True
                elif e.key == pg.K_BACKSPACE:
                    self.input = self.input[:-1]
                elif e.key == pg.K_DELETE:
                    self.input = ''
                elif e.key == pg.K_TAB:
                    return
                else:
                    self.input += e.unicode
            if self.kill:
                send_dummy_post()
        
        if self.datatype == int and self.input.isdigit():
            self.value = int(self.input)
        if self.datatype == str:
            self.value = self.input

       