from machine import Pin, I2C, ADC, PWM
from ssd1306 import SSD1306_I2C
from time import sleep
import framebuf
import random
import sys
WIDTH  = 128                                            # oled display width
HEIGHT = 64                                             # oled display height
cell_size = 6
number_of_cells = 16
up = Pin(2, Pin.IN, Pin.PULL_UP)                     # for future games
down = Pin(3, Pin.IN, Pin.PULL_UP)                   # for future games
left = Pin(4, Pin.IN, Pin.PULL_UP)
right = Pin(5, Pin.IN, Pin.PULL_UP)
button1 = Pin(14, Pin.IN, Pin.PULL_UP)
i2c = I2C(0,scl=Pin(9),sda=Pin(8),freq=400000)                                            # Init I2C using I2C0 defaults, SCL=Pin(GP9), SDA=Pin(GP8), freq=400000
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c,0x3C)
def run_tetris():
    class Grid:
        def __init__(self):
            self.num_rows = 10
            self.num_cols = 20
            self.cell_size = 6
            self.grid = [[0 for j in range(self.num_cols)] for i in range(self.num_rows)]
            
        def print_grid(self):
            for row in range(self.num_rows):
                for column in range(self.num_cols):
                    print(self.grid[row][column], end = "")
                print()
        def is_inside(self, row, column):
            if row>= 0 and row<self.num_rows and column >=0 and column<self.num_cols:
                return True
            return False
        def is_inside(self, row, column):
            if row >= 0 and row < self.num_rows and column >= 0 and column < self.num_cols:
                return True
            return False

        def is_empty(self, row, column):
            if self.grid[row][column] == 0:
                return True
            return False

        def is_row_full(self, row):
            for column in range(self.num_rows):
                if self.grid[column][row] == 0:
                    return False
            return True

        def clear_row(self, row):
            for column in range(self.num_rows):
                self.grid[column][row] = 0

        def move_row_down(self, row, num_rows):
            for column in range(self.num_rows):
                self.grid[column][row-num_rows]= self.grid[column][row]
                self.grid[column][row] = 0

        def clear_full_rows(self):
            completed = 0
            for row in range(0, self.num_cols-1, 1):
                if self.is_row_full(row):
                    self.clear_row(row)
                    completed += 1
                elif completed > 0:
                    self.move_row_down(row, completed)
            return completed

        def draw(self):
            for column in range(self.num_cols):
                for row in range(self.num_rows):
                    cell_value = self.grid[row][column]
                    oled.fill_rect(column*self.cell_size,row*self.cell_size,self.cell_size+1,self.cell_size+1,cell_value)
        

    class Position:
        def __init__(self, row, column):
            self.row = row
            self.column = column

    class Block:
        def __init__(self,id):
            self.id = id
            self.cells = {}
            self.cell_size = 6
            self.rotation_state = 0
            self.row_offset = 0
            self.column_offset = 0
        def move(self, rows, columns):
            self.row_offset +=rows
            self.column_offset +=columns
        

        def rotate(self):
            self.rotation_state +=1
            if self.rotation_state == len(self.cells):
                self.rotation_state = 0
        def undo_rotation(self):
            self.rotation_state-= 1
            if self.rotation_state == -1:
                self.rotation_state = len(self.cells) - 1
        def get_cell_positions(self):
            tiles = self.cells[self.rotation_state]
            moved_tiles = []
            for position in tiles:
                position = Position(position.row + self.row_offset, position.column - self.column_offset)
                moved_tiles.append(position)
            return moved_tiles
        def draw(self):
            tiles = self.get_cell_positions()
            for tile in tiles:
                oled.rect(tile.column*self.cell_size, tile.row*self.cell_size, self.cell_size+1, self.cell_size+1,1)

    class LBlock(Block):
        def __init__(self):
            super().__init__(id = 1)
            self.cells = {
                0: [Position(0,19), Position(1,19), Position(2,19), Position(2,20)],
                1: [Position(1,20), Position(1,19), Position(1,18), Position(2,18)],
                2: [Position(0,19), Position(1,19), Position(2,19), Position(0,18)],
                3: [Position(0,20), Position(1,20), Position(1,19), Position(1,18)]
            }
            self.move(3,0)
    class IBlock(Block):
        def __init__(self):
            super().__init__(id = 1)
            self.cells = {
                0: [Position(0,19), Position(1,19), Position(2,19), Position(3,19)],
                1: [Position(2,20), Position(2,19), Position(2,18), Position(2,17)],
                2: [Position(0,18), Position(1,18), Position(2,18), Position(3,18)],
                3: [Position(1,20), Position(1,19), Position(1,18), Position(1,17)]
            }
            self.move(3,-1)
    class JBlock(Block):
        def __init__(self):
            super().__init__(id = 1)
            self.cells = {
                0: [Position(0,19), Position(1,19), Position(2,19), Position(0,20)],
                1: [Position(1,20), Position(1,19), Position(1,18), Position(2,20)],
                2: [Position(0,19), Position(1,19), Position(2,19), Position(2,18)],
                3: [Position(0,18), Position(1,20), Position(1,19), Position(1,18)]
            }
            self.move(3,0)
    class OBlock(Block):
        def __init__(self):
            super().__init__(id = 1)
            self.cells = {
                0: [Position(0,20), Position(1,20), Position(0,19), Position(1,19)],
                1: [Position(0,20), Position(1,20), Position(0,19), Position(1,19)],
                2: [Position(0,20), Position(1,20), Position(0,19), Position(1,19)],
                3: [Position(0,20), Position(1,20), Position(0,19), Position(1,19)]
            }
            self.move(4,0)
    class ZBlock(Block):
        def __init__(self):
            super().__init__(id = 1)
            self.cells = {
                0: [Position(0,20), Position(1,20), Position(1,19), Position(2,19)],
                1: [Position(2,20), Position(2,19), Position(1,19), Position(1,18)],
                2: [Position(0,19), Position(1,19), Position(1,18), Position(2,18)],
                3: [Position(1,20), Position(1,19), Position(0,19), Position(0,18)]
            }
            self.move(3,0)
    class SBlock(Block):
        def __init__(self):
            super().__init__(id = 1)
            self.cells = {
                0: [Position(0,19), Position(1,19), Position(1,20), Position(2,20)],
                1: [Position(1,20), Position(1,19), Position(2,19), Position(2,18)],
                2: [Position(0,18), Position(1,18), Position(1,19), Position(2,19)],
                3: [Position(0,20), Position(0,19), Position(1,19), Position(1,18)]
            }
            self.move(3,0)
    class TBlock(Block):
        def __init__(self):
            super().__init__(id = 1)
            self.cells = {
                0: [Position(1,20), Position(1,19), Position(2,19), Position(0,19)],
                1: [Position(1,20), Position(1,19), Position(1,18), Position(2,19)],
                2: [Position(0,19), Position(1,19), Position(2,19), Position(1,18)],
                3: [Position(1,20), Position(0,19), Position(1,19), Position(1,18)]
            }
            self.move(3,0)
    class Game:
        def __init__(self):
            self.grid = Grid()
            self.blocks = [IBlock(), JBlock(), LBlock(), OBlock(), SBlock(), TBlock(), ZBlock()]
            self.current_block = self.get_random_block()
            self.next_block = self.get_random_block()
        def get_random_block(self):
            if len(self.blocks) == 0:
                self.blocks = [IBlock(), JBlock(), LBlock(), OBlock(), SBlock(), TBlock(), ZBlock()]
            block = random.choice(self.blocks)
            self.blocks.remove(block)
            return block
        def draw(self):
            self.grid.draw()
            self.current_block.draw()
        def move_left(self):
            self.current_block.move(-1,0)
            if self.block_inside() == False or self.block_fits() == False:
                self.current_block.move(1,0)
        def move_right(self):
            self.current_block.move(1,0)
            if self.block_inside() == False or self.block_fits() == False:
                self.current_block.move(-1,0)
        def move_down(self):
            self.current_block.move(0,1)
            if self.block_inside() == False or self.block_fits() == False:
                self.current_block.move(0,-1)
                self.lock_block()
        def lock_block(self):
            tiles = self.current_block.get_cell_positions()
            for position in tiles:
                self.grid.grid[position.row][position.column] = self.current_block.id
            self.current_block = self.next_block
            self.next_block = self.get_random_block()
            self.grid.clear_full_rows()
                                             
        def block_inside(self):
            tiles = self.current_block.get_cell_positions()
            for tile in tiles:
                if self.grid.is_inside(tile.row, tile.column) == False:
                    return False
            return True
        def block_fits(self):
            tiles = self.current_block.get_cell_positions()
            for tile in tiles:
                if self.grid.is_empty(tile.row, tile.column) == False:
                    return False
            return True
        def rotate(self):
            self.current_block.rotate()
            if self.block_inside() == False or self.block_fits() == False:
                self.current_block.undo_rotation()
     #self.grid = [[0 for j in range(self.num_cols)] for i in range(self.num_rows)]
    game = Game()
    while True:
        oled.fill(0)
        game.draw()
        game.move_down()
        oled.show()

        sleep(0.4)
        if up.value() == 0:
            game.rotate()
            sleep(0.1)
        if right.value() == 0:
            game.move_right()
            sleep(0.02)
        if left.value() == 0:
            game.move_left()
            sleep(0.02)
        if down.value() == 0:
            game.move_down()
            sleep(0.02)
run_tetris()
