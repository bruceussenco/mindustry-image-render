import math
import sys
from PIL import Image, ImageOps

image_path = sys.argv[1]
schematic_name = sys.argv[4]

display_cols = int(sys.argv[2])
display_rows = int(sys.argv[3])

display_size = 32
display_border = 6

pixel_size = 1
width  = display_cols*display_size - display_border*2
height = display_rows*display_size - display_border*2

width  = width //pixel_size
height = height//pixel_size

code_line_limit = 999
draw_buffer_limit = 256

# ========== mlog functions ========== #
def rect(x, y, w, h): return f"draw rect {x} {y} {w} {h}\n"
def line_h(x, y, s):  return f"draw rect {x} {y} {s*pixel_size} {pixel_size}\n"
def line_v(x, y, s):  return f"draw rect {x} {y} {pixel_size} {s*pixel_size}\n"
def pixel(x, y):      return f"draw rect {x*pixel_size} {y*pixel_size} {pixel_size} {pixel_size}\n"
def color(r, g, b):   return f"draw color {r} {g} {b} 255\n"
def clear(r, g, b):   return f"draw clear {r} {g} {b} 255\n"
def drawflush(d):     return f"drawflush display{d}\n"

# ========== render image ========== #
# load image, resize and posterize
img = Image.open(image_path)
img2 = img.resize((width, height))
img3 = ImageOps.posterize(img2, 4)
pixels = img3.load()

# map with all the pixel positions for each color, to group then
color_group = {}
for j in range(height):
    for i in range(width):
        cur_color = pixels[i, j]

        if cur_color in color_group:
            color_group[cur_color].append((i, j))
        else:
            color_group[cur_color] = [(i, j)]

# merge near pixel into a vertical line (x, y, size)
h_rects = {}
for cur_color, poss in color_group.items():
    pos_count = len(poss)
    if pos_count == 1:
        h_rects[cur_color] = [(poss[0][0], poss[0][1], 1)]
        continue

    h_rect = []
    last_x = poss[0][0]
    last_y = poss[0][1]
    origin_x = poss[0][0]
    size = 1
    for i in range(1, pos_count):
        cur_x, cur_y = poss[i]
        if last_x+1 == cur_x and last_y == cur_y:
            size += 1
        else:
            h_rect.append((origin_x, last_y, size))
            origin_x = cur_x
            size = 1
        last_x, last_y = cur_x, cur_y

        if i == pos_count-1:
            h_rect.append((origin_x, last_y, size))

    h_rects[cur_color] = h_rect


codes = [""]
cur_code = 0
code_line_count = 2

for cur_color, h_rect in h_rects.items():
    draw_buffer_count = 0
    if code_line_count + 1 >= code_line_limit:
        codes[cur_code] += "stop"
        codes.append("")
        cur_code += 1
        code_line_count = 2

    r, g, b = cur_color
    codes[cur_code] += color(r, g, b)
    draw_buffer_count += 1
    code_line_count += 1

    for rect in h_rect:
        if draw_buffer_count >= draw_buffer_limit:
            code_line_count += 3
        else:
            code_line_count += 1

        if code_line_count + 2 >= code_line_limit:
            codes[cur_code] += drawflush(1)
            codes[cur_code] += "stop"
            codes.append("")
            cur_code += 1
            code_line_count = 3
            codes[cur_code] += color(r, g, b)
            draw_buffer_count = 1

        if draw_buffer_count >= draw_buffer_limit:
            codes[cur_code] += drawflush(1)
            codes[cur_code] += color(r, g, b)
            draw_buffer_count += 1

        codes[cur_code] += line_h(rect[0], height-rect[1], rect[2])
        draw_buffer_count += 1

    codes[cur_code] += drawflush(1)
    code_line_count += 1

codes[cur_code] += "stop"

# ==================== #

def spiral_around_rect(w: int, h: int, n: int) -> list[tuple[int, int]]:
    if n <= 0: return []

    # rectangle limits
    top = h
    bottom = -1
    right = w
    left = -1

    spiral = []

    while len(spiral) < n:
        # top (left -> right)
        for x in range(left+1, right+1):
            spiral.append((x, top))
            if len(spiral) == n: return spiral

        # right (top -> bottom)
        for y in range(top-1, bottom-1, - 1):
            spiral.append((right, y))
            if len(spiral) == n: return spiral

        # bottom (right -> left)
        for x in range(right-1, left-1, -1):
            spiral.append((x, bottom))
            if len(spiral) == n: return spiral

        # left (bottom -> top)
        for y in range(bottom+1, top+1):
            spiral.append((left, y))
            if len(spiral) == n: return spiral

        # expand the limits, so the processors don't go on top of another
        top += 1
        bottom -= 1
        right += 1
        left -= 1

    return spiral

# ==================== #

processors = []
processor_poss = spiral_around_rect(display_cols, display_rows, len(codes))

for i in range(len(codes)):
    x, y = processor_poss[i]

    dx = min(max(x, 0), display_cols-1)
    dy = min(max(y, 0), display_rows-1)

    processor = f"@micro-processor at ({x} , {y}) processor\n" + \
    f"links display{dx}_{dy} as display1 end\n" + \
    f"mlog = \"\"\"\n{codes[i]}\n\"\"\"\nend\n"

    processors.append(processor)

display_schemacode = ""
for j in range(display_rows):
    for i in range(display_cols):
        tag = f"display{i}_{j}: "
        display_schemacode += f"{tag}@tile-logic-display at ({i}, {j})\n"

schemacode = f'schematic \nname = "{schematic_name}"\n'
for processor in processors:
    schemacode += processor
schemacode += display_schemacode
schemacode += "end\n"

try:
    with open(schematic_name + ".mnd", "w") as f:
        f.write(schemacode)
except IOError as e:
    print(f"Couldn't write to file ({e})")

