import pygame as pg

class Tile(pg.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)

class Map(Tile):
    def __init__(self, pos, surf, groups, obj):
        super().__init__(pos, surf, groups)
        obj.rotation = int(obj.rotation)
        if obj.rotation % 90 != 0:
            raise ValueError('Cannot support image-rotations not divisible by 90') 
        if obj.rotation != 0:
            self.image = pg.transform.rotate(self.image, -obj.rotation)
            if obj.rotation == 90:
                self.rect.topleft = (pos[0], pos[1] + obj.height)
                self.image = pg.transform.scale(self.image, (obj.height, obj.width))
            elif obj.rotation == 180:
                self.rect.topleft = (pos[0] - obj.width, pos[1] + obj.height)
                self.image = pg.transform.scale(self.image, (obj.width, obj.height))
            elif obj.rotation == 270:
                self.rect.topleft = (pos[0] - obj.height, pos[1] + obj.height - obj.width)
                self.image = pg.transform.scale(self.image, (obj.height, obj.width))

        else: # No rotation
            self.rect.topleft = (pos[0], pos[1])
            self.image = pg.transform.scale(self.image, (obj.width, obj.height))
            
