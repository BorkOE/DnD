'''
- Välja verktyg, undernivåer för verktyg. Grafik (cirklar?)
- Aktiva verktyg, hierarkier, logik, toogle hide/transparent, hovertext

- Root tools. Can have children or not. 
- Location organized by orientation (top, bot, left, right) and group
De som inte har någon parent är klickbara med en gång. De som har parents 
De som har parents renderas en steg inåt mitten
Handle resize. start of group is prioritized
'''
import pygame as pg
from pygame.math import Vector2 as V
from helper import load_image, post_key
from settings import green, yellow, hotkey_dict


path_dir = '../graphics/tools'
default_tool = {'parent':None, 'children':[], 'active':False}
read_tools = {                                                                                          # Note that key must have same name as hotkey dict if posting keypress
    'camera_center_player':default_tool.copy()|{'orient':'left', 'group':1},                               # Add parent before childern
    'camera_parent':default_tool.copy()|{'orient':'left', 'group':1},                               
    'camera_send':default_tool.copy()|{'orient':'left', 'group':1, 'parent':'camera_parent'},
    'camera_sync_pos':default_tool.copy()|{'orient':'left', 'group':1, 'parent':'camera_parent'},
    'camera_sync_zoom':default_tool.copy()|{'orient':'left', 'group':1, 'parent':'camera_parent'},
    'dm':default_tool.copy()|{'orient':'top', 'group':1},
    # 'test1':default_tool.copy()|{'orient':'left', 'group':2},
    # 'test2':default_tool.copy()|{'orient':'left', 'group':2},
}

# Margins from edge of screen 
marg = 30 
tool_space = 60
group_space = 20 # Extra to add
tool_size = 45
child_space = 60

class Tool():
    '''Basic tool class. Clickable circle. Conditions?'''
    def __init__(self, name, specs):
        self.name = name
        self.parent = specs.get('parent')
        self.children = []
        self.orient = specs.get('orient')
        self.group = specs.get('group')
        self.active = specs.get('active')
        self.has_active_children = False
        img = load_image(f'{path_dir}/{name}.png', get_rect=False)
        self.image = pg.transform.smoothscale(img, (tool_size,tool_size))
        self.rect = self.image.get_rect()

    def check_click(self, pos):
        if self.rect.collidepoint(pos):
            # print(f'clicked {self.name}')
            self.active = True
            return True
        else:
            self.active = False

class ToolGroup():
    '''Collection of root tools. Gets assigned orientation and group-number
    Calculates tool position within group'''
    def __init__(self, orient, color_dict):
        self.orient = orient
        self.toolbox = {}
        self.all_tools = []
        self.add_dimension = None
        self.color_dict = color_dict
    
    def add_tool(self, tool, specs):
        '''Check for parent/child here'''
        # print(f'adding {tool.name} to toolgroup: {self.orient}')
        if not tool.group in self.toolbox:
            self.toolbox[tool.group] = [tool]
        else:
            self.toolbox[tool.group].append(tool)
        self.all_tools.append(tool)

    def place_tools(self, context_surf):
        '''Finds position for always visible tools'''
        # TODO: use limit for tools outside
        size = context_surf.get_size()
        if self.orient == 'left':
            x = marg
            y = marg
            self.add_dimension = 1 # 0: x, 1: y
            # limit = size[1]
        elif self.orient == 'right':
            x = size[0] - marg
            y = marg
            self.add_dimension = 1
        elif self.orient == 'top':
            x = marg*5
            y = marg
            self.add_dimension = 0 
        elif self.orient == 'bottom':
            x = marg*5
            y = size[1] - marg
            self.add_dimension = 0 

        else: # DEVELOPMENT
            # print(f'Has not fixed {self.orient} yet')
            return
        pos = V(x,y)
        for groupnum, toollist in self.toolbox.items(): # Loops over groups
            for tool in toollist:                       # Loops over tools
                if tool.parent:                         # Placed separately
                    continue
                tool.rect.topleft = pos 
                pos[self.add_dimension] += tool_space 
            pos[self.add_dimension] += group_space
    
    def place_child_tools(self, parents):
        for p in parents:
            p_pos = V(p.rect.topleft)
            p_pos[not self.add_dimension] += child_space
            for c in p.children:
                c.rect.topleft = p_pos
                p_pos[self.add_dimension] += tool_space

    def blit_toolgroup(self, context_surf, kwargs):
        '''Blitting of tools'''
        for groupnum, toollist in self.toolbox.items(): # Loops over groups
            for tool in toollist:                   # Loops over tools
                if tool.parent:                         # Children only blitted if active (separate function)
                    continue
                blit_me = tool.image.copy()
                if 'dm' in kwargs:
                    if (tool.name == 'dm' and kwargs['dm']):
                        blit_me.blit(self.color_dict['yellow'], (0,0))
                context_surf.blit(blit_me, tool.rect)
    
    def blit_active_children(self, context_surf, active_children, kwargs):
        for ac in active_children:
            # print(kwargs)
            blit_me = ac.image.copy()
            if 'camera' in kwargs:
                camera = kwargs['camera']
                if (ac.name == 'camera_sync_pos' and camera.pair_camera) or \
                    (ac.name == 'camera_sync_zoom' and camera.pair_camera_zoom):
                        blit_me.blit(self.color_dict['yellow'], (0,0))
            
            context_surf.blit(blit_me, ac.rect)

class ContextMenu():
    '''The highest level class that organizes toolgroups and handles logic'''
    def __init__(self):
        self.get_new_surface()
        self.reset_surface()
        color_dict = {'green':self.generate_circle(green), 'yellow':self.generate_circle(yellow)}
        self.tools = {}
        self.toolgroups = {}
        self.active_children = []
        for o in ['left','right','top','bottom']:
            self.toolgroups.update({o:ToolGroup(o, color_dict)})
        self.load_tools()
        self.update()

    def generate_circle(self, col):
        # TODO: Import nice antialiased cirkle instead
        surf = pg.Surface((tool_size, tool_size)).convert_alpha()
        pg.draw.circle(surf, col, (tool_size/2,tool_size/2), tool_size/2, 2)
        return surf

    def get_new_surface(self):
        # TODO: Få denna att funka
        self.context_surf = pg.Surface(pg.display.get_window_size()).convert_alpha()
    
    def reset_surface(self):
        self.context_surf.fill((0,0,0,0))

    def load_tools(self):
        # TODO: Sort read_tools first on orient, group and parents
        parents = []
        for toolname, specs in read_tools.items():
            current_tool = Tool(toolname, specs)
            self.tools.update({toolname:current_tool}) # Make tooldict
            if current_tool.parent:
                # print(f'{current_tool.name} has parent {current_tool.parent}')
                current_tool.parent = self.tools[current_tool.parent] # Exchange string for actuall parent object
                # print(f'adding {current_tool.name} as child of {current_tool.parent.name}')
                current_tool.parent.children.append(current_tool)     # Adds children to parent
                if current_tool.parent not in parents:
                    parents.append(current_tool.parent)
            o = specs.get('orient')
            t = self.tools.get(toolname)
            self.toolgroups[o].add_tool(t, specs)
        
        for tg in self.toolgroups.values(): 
            tg.place_tools(self.context_surf)
            tg.place_child_tools([p for p in parents if p in tg.all_tools])

    def check_click(self, pos):
        '''Checks for click and updates if detected'''
        any_hit = False
        for t in self.tools.values():
            if t.check_click(pos):
                if t.parent and not t in self.active_children: # Pressed child tool thats not visible
                    return
                any_hit = True
                self.active_children.extend(t.children)
                # if t not in self.active_children:
                #     self.active_children = t.children # If empty, it 'closes' the previous active children
                self.handle_click(t.name)
        if not any_hit:
            self.active_children = []

    def handle_click(self, btn):
        key = hotkey_dict.get(btn)
        if key:
            post_key(key)
        
    def update(self, kwargs={}):
        # Blit new 
        # print(self.active_children)
        self.reset_surface()
        for tg in self.toolgroups.values():
            tg.blit_toolgroup(self.context_surf, kwargs)
        if self.active_children:
            tg = self.toolgroups[self.active_children[-1].orient]
            tg.blit_active_children(self.context_surf, self.active_children, kwargs)
                
    def blit(self, screen, **kwargs):
        '''Blits context menu to main surface'''
        self.update(kwargs)
        screen.blit(self.context_surf, (0,0))
