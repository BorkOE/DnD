from ctypes.wintypes import SC_HANDLE
from tkinter import E
import pygame as pg
# from sprite_group import SpecialBarGroup
from settings import hotkey_dict
from helper import load_image, distance, input_event, send_dummy_post, render_text
from pygame.math import Vector2 as V
from random import randint

# Settings
top_marginal = 20
right_marginal = 20
scroll_speed = 6

# TODO:
'''

'''

class ScrollBox:
    '''A box that orders given surfaces in a scrollable window'''
    '''Make sure elements are contained within width of box to makes sure click works'''
    def __init__(self, width, height, elements, center=None, topleft=None, y_marg=0, col=(230, 230, 230, 0)):
        self.w, self.h = width, height
        self.y_marg = y_marg
        try:
            self.surf = pg.surface.Surface((width, height))
        except pg.error as e:
            print('Window was probably to small which caused battletracker to crasch.')
            print(e)
            self.surf = pg.surface.Surface((100, 100))
        if center: self.rect = self.surf.get_rect(center=center)
        if topleft: self.rect = self.surf.get_rect(topleft=topleft)
        self.surf.fill(col)
        self.surf_empty = self.surf.copy()
        self.elements = elements        # Dict with surface as values
        self.scroll_val = 0
        self.height_diff = None
        self.get_height_diff()
    
    def get_height_diff(self):
        '''Checks if elements fit within box'''
        # TODO: run if checkning for new elements 
        tot_h = 0
        for e in self.elements.values():
            tot_h += e.rect.h + self.y_marg
        self.height_diff = tot_h - self.h
    
    def scroll(self, scroll_value):
        '''scrolls trough elements if they are longer than box'''
        if self.height_diff < 0:        # Only scroll if elements overshoot box
            return
        scroll_delta = scroll_value * scroll_speed
        new_scroll_val = self.scroll_val + scroll_delta
        if new_scroll_val * -1 < self.height_diff:
            self.scroll_val = new_scroll_val
        if new_scroll_val * -1 > self.height_diff:
            self.scroll_val = self.height_diff * -1
        if new_scroll_val * -1 < 0:
            self.scroll_val = 0
    
    def check_click(self, bt_mouse_pos):
        scrollbox_mouse_pos = self.get_mouse_pos(bt_mouse_pos)
        for e in self.elements.values():
            if e.rect.collidepoint(scrollbox_mouse_pos):
                return e.check_click(scrollbox_mouse_pos)

    def get_mouse_pos(self, bt_mouse_pos):
        '''returns normalized mouse pos to the scroll window'''
        return distance(bt_mouse_pos, self.rect.topleft, type='xy')

    def get_sorted_element_list(self):
        '''Returns sorted list of bars'''
        sprite_list = self.elements.values()
        return sorted(sprite_list, key=lambda x: (x.initiative, x.id), reverse=True) # Sorts according to initiative

    def draw(self):
        '''draws elements on scrollbox based on order in elements'''
        # TODO: move class to its own file. Only override this function in this file
        last_height = 0
        self.surf = self.surf_empty.copy()
        for e in self.get_sorted_element_list():
            e.rect.center = (self.w/2, 0)
            e.rect.top = last_height + self.scroll_val
            self.surf.blit(e.image, e.rect)
            last_height += e.rect.h + self.y_marg

class Bar(pg.sprite.Sprite):
    portrait_scale = 0.9
    def __init__(self, entity, bar_type_dict, dm, initiative=None, status_text=''):
        self.dm = dm
        self.interactive_dict = {}
        self.bar_type_dict = bar_type_dict
        self.font_1 = pg.font.SysFont(None, 20)      
        self.font_2 = pg.font.SysFont(None, 16)      
        self.entity = entity
        self.id = entity.id
        self.status_text = status_text
        self.bar_empty = bar_type_dict[f'bar_{entity.type}'].copy() 
        self.rect = self.bar_empty.get_rect()
        self.blit_static_elements()
        if initiative != None:
            self.initiative = int(initiative)
        else:
            self.initiative = randint(0,20)     # TODO: set auto-roll enabled/disabled in settings
        self.image = None # Holds the final bar for blitting
   
        self.update()
        
        self.interactive_dict = {'initiative':self.initiative_rect, 'tbx':self.textbox_rect, 'ac':self.armor_class_rect, 'add':self.btn_add_rect, 'remove':self.btn_remove_rect}
        if self.dm or self.entity.type == 'player':         # Makes hp-text clickable
            self.interactive_dict.update({'c_hp':self.c_hp_rect, 'm_hp':self.m_hp_rect})
    
    def blit_static_elements(self): 
        '''Blits elements that will not change. Instantiates rects that will be clickable.'''
        name_pos = (65,7)
        textbox_pos = (90, 30)
        armorclass_pos = (55,30)
        add_pos = (400, 13)
        remove_pos = (400, self.rect.h - 13)
        h = int(self.entity.image.get_height() * self.portrait_scale)
        w = int(self.entity.image.get_width() * self.portrait_scale)
        portrait = pg.transform.scale(self.entity.image, (w,h)).convert_alpha()
        y = self.rect.h /2 - portrait.get_height() / 2
        name, name_rect = render_text(self.entity.id, self.font_1, name_pos)
        self.textbox = self.bar_type_dict['tbx'].copy()
        self.textbox_rect = self.textbox.get_rect(topleft=textbox_pos)
        self.armor_class = self.bar_type_dict['armor_class'].copy()
        self.armor_class_rect = self.armor_class.get_rect(topleft=armorclass_pos)
        btn_add = self.bar_type_dict['add'].copy()
        self.btn_add_rect = btn_add.get_rect(topleft=add_pos)
        btn_remove = self.bar_type_dict['remove'].copy()
        self.btn_remove_rect = btn_remove.get_rect(bottomleft=remove_pos)
        
        self.bar_empty.blit(portrait, (5,y))
        self.bar_empty.blit(name, name_rect)
        self.bar_empty.blit(btn_add, self.btn_add_rect)
        self.bar_empty.blit(btn_remove, self.btn_remove_rect)

    def check_click(self, scrollbox_mouse_pos):
        '''Handle click on bar'''
        bar_mouse_pos = self.get_mouse_pos(scrollbox_mouse_pos)
        int_btns = ['initiative', 'ac', 'c_hp', 'm_hp']     # Btns that trigger int-inputpromt
        str_btns = ['tbx']                                  # Btns that trigger string-inputpromt
        push_btns = ['add', 'remove']                       # Simple clickable buttons, returns data
        for btn, rect in self.interactive_dict.items():
            if rect.collidepoint(bar_mouse_pos):
                if btn in int_btns:
                    execute_on_sucess = f'self.battle_tracker[-1].handle_inputbox_event("{btn}", "{self.id}", self.input_box[-1].value)'
                    pg.event.post(pg.event.Event(input_event, {'execute_on_sucess':execute_on_sucess, 'datatype':int}, prev_input=''))
                if btn in str_btns:
                    execute_on_sucess = f'self.battle_tracker[-1].handle_inputbox_event("{btn}", "{self.id}", self.input_box[-1].value)'
                    pg.event.post(pg.event.Event(input_event, {'execute_on_sucess':execute_on_sucess, 'datatype':str}, prev_input=self.status_text))
                if btn in push_btns:
                    return {'btn':btn, 'entity':self.entity, 'bar':self}
        self.update() # Update bar in case changes were made to parameters

    def update(self):
        '''Updates bar-visuals according to new parameters'''
        self.image = self.bar_empty.copy() # New empty bar
        initiative_text, self.initiative_rect = render_text(self.initiative, self.font_2)  # Render initiative text
        status_text, status_text_rect = render_text(self.status_text, self.font_1, (2,2)) 
        ac_text, ac_rect = render_text(self.entity.armor_class, self.font_1, center=(12,15))
        current_hp_text, max_hp_text, slash, slash_rect = self.get_hp_text()

        '''Render and Blit dynamic elements to bar'''
        if self.entity.current_hp == 0:
            self.image.blit(self.bar_type_dict['death'].copy(), (0,0))            
        self.image.blit(initiative_text, self.initiative_rect)
        tbx = self.textbox.copy()
        armor_class = self.armor_class.copy()
        tbx.blit(status_text, status_text_rect)
        self.image.blit(tbx, self.textbox_rect)
        armor_class.blit(ac_text, ac_rect)
        self.image.blit(armor_class, self.armor_class_rect)
        self.image.blit(current_hp_text, self.c_hp_rect)
        self.image.blit(max_hp_text, self.m_hp_rect)
        self.image.blit(slash, slash_rect)
        if self.entity.current_hp <= self.entity.max_hp / 2:
            self.image.blit(self.bar_type_dict['bloodied'].copy(), (0,0))
        send_dummy_post()
    
    def mark(self):
        self.bar_empty = self.bar_type_dict['bar_selected'].copy()
        self.blit_static_elements()
        self.update()
    
    def unmark(self):
        self.bar_empty = self.bar_type_dict[f'bar_{self.entity.type}'].copy() 
        self.blit_static_elements()
        self.update()

    def get_hp_text(self):
        marg, x, y = 5, 370, 29
        if self.dm or self.entity.type == 'player':
            c_hp = self.entity.current_hp
            m_hp = self.entity.max_hp
        else:
            c_hp = '?'
            m_hp = '?'

        current_hp_text, self.c_hp_rect = render_text(c_hp, self.font_1, topright=(x-marg, y))
        max_hp_text, self.m_hp_rect = render_text(m_hp, self.font_1, topleft=(x+marg, y))
        slash, slash_rect = render_text('/', self.font_1, topleft=(x-2,y))    
        if self.interactive_dict and (self.dm or self.entity.type == 'player'): 
            self.interactive_dict.update({'c_hp':self.c_hp_rect, 'm_hp':self.m_hp_rect})
        return current_hp_text, max_hp_text, slash, slash_rect

    def get_mouse_pos(self, scrollbox_mouse_pos):
        return distance(scrollbox_mouse_pos, self.rect.topleft, type='xy')

class BattleTracker:
    def __init__(self, camera, all_entities, network, dm):
        # Placement
        self.main_window_empty, self.rect = load_image('../graphics/battletracker/main_window.png', True, True)
        self.marked_bgrd, self.marked_rect = load_image('../graphics/battletracker/main_window_marked.png', True, True)
        self.normalize_window()
        self.marked_rect.center = self.rect.center
        self.camera = camera
        self.all_entities = all_entities

        # Instantiate bars
        self.bar_type_dict = self.load_bar_images()
        self.bars = {}
        self.dm = dm
        self.add_bars()
        self.font_bt = pg.font.SysFont(None, 28)      
        self.round = 1
        self.marked = True
        self.minimized = False
        self.kill = False
        self.network = network
        self.instantiate_scrollbox()
        self.blit_static_elements()
        self.blit_dynamic_elements()
        self.current_bar = 0
        self.prev_marked_bar = None
        self.mark_current_bar()

    def add_bars(self):
        '''used when instantiating bt and when updating for new entities in view'''
        entities_in_view = self.camera.check_objects_in_view(self.all_entities.values())
        for entity in entities_in_view:
            if entity.id not in self.bars:
                self.bars.update({entity.id:Bar(entity, self.bar_type_dict, self.dm)}) # Instantiate bar

    def mark_current_bar(self):
        if self.prev_marked_bar:
            self.prev_marked_bar.unmark()
            self.prev_marked_bar.entity.decrown()
            # Unmark crown
        elem_list = self.scrollbox.get_sorted_element_list()
        if not len(elem_list):
            return
        if self.current_bar >= len(elem_list):
            self.current_bar = 0
            self.round += 1
            self.blit_dynamic_elements()
        if self.current_bar < 0:
            self.current_bar = len(elem_list) - 1 
            self.round -= 1
            self.blit_dynamic_elements()
        mark_this_bar = elem_list[self.current_bar]
        mark_this_bar.mark()
        mark_this_bar.entity.crown()
        self.prev_marked_bar = mark_this_bar

    def change_selected_bar(self, change=None, current_bar=None, send=False):
        if change != None:
            if change == 'next':
                self.current_bar += 1
            if change == 'prev':
                self.current_bar -= 1
        if current_bar != None:
            self.current_bar = current_bar
        self.mark_current_bar()
        self.blit_dynamic_elements()
        if send:
            self.send_change_bar()
        
    def blit_static_elements(self):
        self.main_window = self.main_window_empty.copy()
        next_pos = self.get_normalized_pos(self.scrollbox.rect.bottomleft) + V(140, 30)
        prev_pos = self.get_normalized_pos(self.scrollbox.rect.bottomleft) + V(15, 30)
        handle_pos = self.get_normalized_pos((self.rect.left, self.rect.centery)) + V(14, 0)
        reload_pos = self.get_normalized_pos(self.rect.topright) + V(-35, 20)
        next_btn = self.bar_type_dict['next'].copy()
        self.next_btn_rect = next_btn.get_rect(topleft=next_pos)
        prev_btn = self.bar_type_dict['prev'].copy()
        self.prev_btn_rect = prev_btn.get_rect(topleft=prev_pos)
        handle = self.bar_type_dict['handle'].copy()
        self.handle_rect = handle.get_rect(center=handle_pos)
        reload = self.bar_type_dict['reload'].copy()
        self.reload_rect = reload.get_rect(center=reload_pos)
        
        self.main_window.blit(next_btn, self.next_btn_rect)
        self.main_window.blit(prev_btn, self.prev_btn_rect)
        self.main_window.blit(handle, self.handle_rect)
        self.main_window.blit(reload, self.reload_rect)
        self.main_window_static = self.main_window.copy()

    def blit_dynamic_elements(self):
        '''Elements that can change during battletrackers lifetime'''
        self.main_window = self.main_window_static.copy()
        round_pos = self.next_btn_rect.center + V(175, 0)
        round_text, round_rect = render_text(f'Round: {self.round}', self.font_bt, center=round_pos)
        self.main_window.blit(round_text, round_rect)
        self.interactive_dict = {'next':self.next_btn_rect, 'prev':self.prev_btn_rect, 'handle':self.handle_rect, 'reload':self.reload_rect}

    def instantiate_scrollbox(self):
        # Instantiate scrollbox
        _, win_h = pg.display.get_window_size()
        x_marg = 50
        y_marg = 20
        outside = win_h - (self.rect.height + y_marg)
        y_fix = y_marg*2
        if outside < 0: 
            y_fix = 0
        self.scrollbox = ScrollBox(
            self.rect.w - x_marg, 
            win_h - 150 - y_fix, 
            self.bars,
            y_marg=y_marg,
            topleft=((self.rect.centerx - (self.rect.w - x_marg)/2), y_marg*3),
            #col = (50,50,50)
            )

    def load_bar_images(self):
        # TODO: get all bar resources from this func
        bar_type_dict = {}
        for type in ['bar_player', 'bar_enemy', 'bar_selected', 'bloodied', 'tbx', 'death', 'armor_class', 'add', 'remove', 'next', 'prev', 'handle', 'reload']:
            bar_type_dict.update({type:load_image(f'../graphics/battletracker/{type}.png')})
        return bar_type_dict

    def handle_inputbox_event(self, type, id, input_val):
        if type == 'initiative':
            self.update_initiative(id, input_val)
        if type == 'tbx':
            self.update_textbox(id, input_val)
        if type == 'ac':
            self.bars[id].entity.armor_class = input_val
            self.bars[id].update()
            self.send_network_new_ent_params(id)
        if type == 'c_hp':
            self.bars[id].entity.current_hp = input_val
            self.bars[id].update()
            self.send_network_new_ent_params(id)
        if type == 'm_hp':
            self.bars[id].entity.max_hp = input_val
            self.bars[id].update()
            self.send_network_new_ent_params(id)

    def handle_btn_respons(self, respons):
        if respons['btn'] == 'add': 
            respons['entity'].current_hp += 1
        if respons['btn'] == 'remove':
            if respons['entity'].current_hp - 1 >= 0:
                respons['entity'].current_hp -= 1
        respons['bar'].update()
        self.send_network_new_ent_params(respons['entity'].id)

    def update_initiative(self, id, val, from_network=False):
        '''Writes new initiative value to bar''' # This function is executed after successful input box or from network
        self.bars[id].initiative = int(val)
        self.bars[id].update()
        if not from_network:    
            self.send_bt_params_change(id)
    
    def update_textbox(self, id, val, from_network=False):
        '''writes new statustext to bar'''
        self.bars[id].status_text = val
        self.bars[id].update()
        if not from_network:    
            self.send_bt_params_change(id)

    def update(self, event_list, mouse_pos):
        '''Update-function for battletracker. Checks for user input'''
        for e in event_list:
            if e.type == pg.MOUSEBUTTONUP and e.button == 1:
                if self.rect.collidepoint(mouse_pos):                   # Click on battletracker
                    self.marked = True
                    if self.scrollbox.rect.collidepoint(mouse_pos):     # Click on scrollbox
                        respons = self.scrollbox.check_click(mouse_pos)
                        if respons:
                            self.handle_btn_respons(respons)
                    else:
                        self.check_click(mouse_pos)
                else:
                    self.marked = False
            if e.type == pg.KEYUP:      # Don't need marked window
                if e.key == hotkey_dict.get('bt_minimize'):
                    self.minimize()
            if not self.marked:     # No further checks if window not marked
                return
            if e.type == pg.KEYUP:
                # if e.key == pg.K_s:     # TODO: make btn for this 
                #     self.add_bars()
                # if e.key == pg.K_u:     # TODO: make btn for this 
                #     self.send_network_update()
                if e.key == hotkey_dict.get('bt_next'):
                    self.change_selected_bar(change='next', send=True)
                if e.key == hotkey_dict.get('bt_prev'):
                    self.change_selected_bar(change='prev', send=True)
            if e.type == pg.MOUSEWHEEL:
                self.scrollbox.scroll(e.y)

    def check_click(self, mouse_pos):
        '''Checks click on battletracker window (not scrollbox)'''
        battletracker_mousepos = self.get_normalized_pos(mouse_pos)
        for btn, rect in self.interactive_dict.items():
            if rect.collidepoint(battletracker_mousepos):
                if btn in ['next', 'prev']:
                    self.change_selected_bar(change=btn, send=True)
                if btn == 'handle':
                    self.minimize()
                if btn == 'reload':
                    self.add_bars()
                    self.send_network_update()

    def get_normalized_pos(self, pos):
        '''returns normalized mouse pos to the battletracker window'''
        return distance(pos, self.rect.topleft, type='xy')

    def minimize(self):
        self.normalize_window()
        if not self.minimized:
            self.rect.center += V(400,0)
        self.instantiate_scrollbox()
        self.blit_static_elements()
        self.blit_dynamic_elements()
        self.marked_rect.center = self.rect.center
        self.minimized = not self.minimized
    
    def normalize_window(self):
        '''Puts window next to right window border'''
        win_w, win_h = pg.display.get_window_size()
        self.rect.topright = (win_w - right_marginal, top_marginal)
        self.marked_rect.center = self.rect.center

    def draw(self, display_surf):
        self.scrollbox.draw()                                       # Draws elements in scrollbox
        if not self.minimized:
            if self.marked: 
                display_surf.blit(self.marked_bgrd, self.marked_rect)   # If marked, draws marking
            display_surf.blit(self.main_window, self.rect)
        display_surf.blit(self.scrollbox.surf, self.scrollbox.rect)
    
    '''Network functions'''
    def parse_network_update(self, network_data, all_entities):
        if network_data['type'] == 'battletracker_update':
            '''Updates battletracker according to incomming data'''
            self.bars = {}
            for id, bt_parameters in network_data['bt_dict'].items():
                self.bars.update({id:Bar(all_entities[id], 
                                self.bar_type_dict, 
                                self.dm,
                                bt_parameters['initiative'],
                                bt_parameters['statustext'],
                                )})
            self.instantiate_scrollbox()
            self.update_battletracker_status(network_data)
        
        if network_data['type'] == 'battletracker_new_parameters':
            self.update_initiative(network_data['id'], network_data['initiative'], from_network=True)
            self.update_textbox(network_data['id'], network_data['statustext'], from_network=True)
            send_dummy_post()

        if network_data['type'] == 'battletracker_change_bar':
            self.update_battletracker_status(network_data)
    
    def update_battletracker_status(self, network_data):
        '''Updates selected bar and round'''
        self.change_selected_bar(current_bar=network_data['selected_bar'])
        self.round = network_data['round']
        self.blit_dynamic_elements()

    def send_network_new_ent_params(self, id):
        '''gathers all neccesary params from entity and sends to server'''
        data = self.bars[id].entity.get_entity_parameters()
        self.network.send_data_to_server(data) 

    def send_network_update(self):
        '''Asks server to relay bt data to other clients'''
        data = self.get_data_update()
        self.network.send_data_to_server(data)

    def send_bt_params_change(self, id):
        data = self.get_id_parameters(id)
        self.network.send_data_to_server(data)

    def get_data_update(self):
        '''Gets all id's and parameters (initiative etc) for battletracker'''
        data = {}
        data.update({'bt_dict':self.get_bt_dict(), 'type':'battletracker_update'})
        data.update(self.get_battletracker_status())
        return data
    
    def send_change_bar(self):
        data = {'type':'battletracker_change_bar'}
        data.update(self.get_battletracker_status())
        self.network.send_data_to_server(data)

    def get_battletracker_status(self):
        return {'selected_bar':self.current_bar, 'round':self.round}

    def get_id_parameters(self, id):
        '''Gets battletracker parameters for one id'''
        data = {}
        data.update({'id':id, 'initiative':self.bars[id].initiative, 'statustext':self.bars[id].status_text, 'type':'battletracker_new_parameters'})
        return data
    
    def get_bt_dict(self):
        bt_dict = {}
        for id in self.bars.keys():
            bt_dict.update({id:{
                'initiative':self.bars[id].initiative,
                'statustext':self.bars[id].status_text,
                }})
        return bt_dict

