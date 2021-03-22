print('Initialising...')

from ast import literal_eval as make_tuple
import os
import sys

import clipboard
import easygui
import pygame

pygame.init()


window_width = pygame.display.Info().current_w
window_height = pygame.display.Info().current_h


def find_equation(point_1, point_2):
    if point_2[0] - point_1[0] == 0:
        return f'x={round(point_1[0], 3)}\\left\\{{{round(max(point_1[1], point_2[1]), 3)}>y>{round(min(point_1[1], point_2[1]), 3)}\\right\\}}'
    else:
        m = (point_2[1]-point_1[1]) / (point_2[0]-point_1[0])
        y_intercept = point_1[1] + (-m*point_1[0])

        m_formatted = round(m, 3)
        y_int_formatted = round(y_intercept, 3)

        return f'y={round(m,3)}x{"+" if y_intercept >= 0 else ""}{round(y_intercept,3)}\\left\\{{{round(min(point_1[0], point_2[0]), 3)}<x<{round(max(point_1[0], point_2[0]), 3)}\\right\\}}'


class Image:
    """Stores information and helper functions related to the input image.
    """

    def __init__(self, img_src, screen):
        self.original_image = pygame.image.load(img_src)

        self._set_variables()

        self.surface = pygame.Surface.subsurface(screen, self.margin_x, self.margin_y, self.width, self.height)
        self.current_image = pygame.transform.smoothscale(self.original_image, (self.width, self.height))

    def _set_variables(self):
        self.height = window_height - 100
        self.width = int(self.original_image.get_rect().size[0] / (self.original_image.get_rect().size[1]/self.height))

        if self.width > window_width * (2/3):
            self.height =int(self.height / (self.width / (window_width * (2/3))))
            self.width = int(window_width * (2/3))

        self.margin_x = (window_width-self.width)//2
        self.margin_y = (window_height-self.height)//2 + 41

    def draw(self, screen, offset_x, offset_y):
        # Draw black rectangle behind image
        pygame.draw.rect(screen, (0, 0, 0), (self.margin_x, self.margin_y, self.width, self.height))

        screen.blit(self.current_image, 
            (self.margin_x, self.margin_y), 
            (offset_x, offset_y, self.width, self.height))


class Font:
    """All the fonts required for the program.
    """
    
    button = pygame.font.SysFont('Arial', 24)
    symbol = pygame.font.SysFont('Arial', 48)
    notification = pygame.font.SysFont('Arial', 36)


class Text:
    """A text element.
    """

    def __init__(self, text_element, pos, centered=True):
        self.text_element = text_element
        self.pos = pos
        self.centered = centered


class TextButton:
    """A button containing text
    """

    def __init__(self, rect, text, text_pos, color):
        self.rect = rect
        self.text = text
        self.text_pos = text_pos
        self.color = color


class UI:
    """Stores UI components such as buttons and text
    """

    def __init__(self):
        self.buttons = [
            TextButton(pygame.Rect(window_width - 120, window_height - 150, 40, 40), 
                                   Font.symbol.render('+', True, (0, 0, 0)),
                                   (window_width - 111, window_height - 160), (0, 255, 0)),
            TextButton(pygame.Rect(window_width - 70, window_height - 150, 40, 40), 
                                   Font.symbol.render('-', True, (0, 0, 0)),
                                   (window_width - 57, window_height - 160), (255, 0, 0)),
            TextButton(pygame.Rect(window_width - 120, window_height - 70, 90, 40),
                                   Font.button.render('Output', True, (0, 0, 0)),
                                   (window_width - 107, window_height - 65), (200, 200, 200))
        ]

        self.tools = [
            TextButton(pygame.Rect(50, window_height - 150, 120, 50),
                                   Font.button.render('Line Tool', True, (0, 0, 0)),
                                   (70, window_height - 140), (200, 200, 200)),
            TextButton(pygame.Rect(50, window_height - 70, 120, 50), 
                                   Font.button.render('Eraser', True, (0, 0, 0)),
                                   (80, window_height - 60), (200, 200, 200))
        ]
        
        self.text = [
            Text(Font.notification.render('', True, (0, 0, 0)), (0, 50), centered=True)
        ]

    def draw(self, screen, selected_tool):
        for button in self.buttons:
            pygame.draw.rect(screen, button.color, button.rect)
            screen.blit(button.text, button.text_pos)

        for i, tool in enumerate(self.tools):
            if i == selected_tool:
                pygame.draw.rect(screen, (0, 255, 0), tool.rect)
            else:
                pygame.draw.rect(screen, tool.color, tool.rect)
            screen.blit(tool.text, tool.text_pos)

        for text in self.text:
            if text.centered:
                text_rect = text.text_element.get_rect(center=(window_width//2, text.pos[1]))
            screen.blit(text.text_element, text_rect)


class LineCreator:
    """The main class for the Line Creator Program. Runs the event loop.
    """

    def __init__(self, img_src, graph_width, graph_height):
        self.graph_width = graph_width
        self.graph_height = graph_height
        self.offset_x = 0
        self.offset_y = 0

        self.screen = pygame.display.set_mode((window_width, window_height))

        self.zoom_level = 1
        self.mouse_start_pos = None
        self.selected_tool = 0
        self.erase_pos = None
        self.placed_points = []

        self.image = Image(img_src, self.screen)
        self.UI = UI()

        self._main_loop()

    def _get_pixel_pos(self, mouse_x, mouse_y):
        pixel_x = int((mouse_x - self.image.margin_x + self.offset_x) / self.zoom_level)
        pixel_y = int((mouse_y - self.image.margin_y + self.offset_y) / self.zoom_level)
        return pixel_x, pixel_y

    def _get_coordinate_pos(self, pixel_x, pixel_y):
        coord_x = (pixel_x - (self.image.width/2)) * (self.graph_width / (self.image.width/2))
        coord_y = -(pixel_y - (self.image.height/2)) * (self.graph_height / (self.image.height/2))
        return coord_x, coord_y

    def _coordinate_to_pixel(self, coord_x, coord_y):
        pixel_x = int((int(coord_x * ((self.image.width/2)/self.graph_width)) + (self.image.width/2)) * self.zoom_level) - self.offset_x
        pixel_y = int((-int(coord_y * ((self.image.height/2)/self.graph_height)) + (self.image.height/2)) * self.zoom_level) - self.offset_y
        return pixel_x, pixel_y

    def _draw_and_update_lines(self):
        for point in self.placed_points:
            pixel_x, pixel_y = self._coordinate_to_pixel(point[0], point[1])
            pygame.draw.circle(self.image.surface, (0, 0, 200), (pixel_x, pixel_y), 4)

        to_erase = None
        for i in range(0, len(self.placed_points), 2):
            if i != len(self.placed_points) - 1:
                point1_x, point1_y = self._coordinate_to_pixel(self.placed_points[i][0], self.placed_points[i][1])
                point2_x, point2_y = self._coordinate_to_pixel(self.placed_points[i+1][0], self.placed_points[i+1][1])

                pygame.draw.line(self.image.surface, (255, 0, 0), 
                    (point1_x, point1_y), (point2_x, point2_y), 4)

                # Erase line if necassary
                if self.erase_pos is not None:
                    for y in range(-4, 5):
                        for x in range(-4, 5):
                            try:
                                if self.image.surface.get_at((self.erase_pos[0]+x, self.erase_pos[1]+y))[:3] == (255, 0, 0) and to_erase is None:
                                    to_erase = i
                            except:
                                pass
        self.erase_pos = None

        if to_erase is not None:
            del self.placed_points[to_erase:to_erase+2]

    def _main_loop(self):
        pygame.font.SysFont('Arial', 24)
        done = False
        while not done:
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True

                # Check button events
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos

                    # Left click
                    if event.button == 1:
                        if self.UI.buttons[0].rect.collidepoint(mouse_pos):
                            self.zoom_level += 0.4
                            self.image.current_image = pygame.transform.smoothscale(self.image.original_image, 
                                (int(self.image.width*self.zoom_level), int(self.image.height*self.zoom_level)))


                        elif self.UI.buttons[1].rect.collidepoint(mouse_pos):
                            self.zoom_level = max(1, self.zoom_level - 0.4)
                            self.image.current_image = pygame.transform.smoothscale(self.image.original_image, 
                                (int(self.image.width*self.zoom_level), int(self.image.height*self.zoom_level)))

                        elif self.UI.buttons[2].rect.collidepoint(mouse_pos):
                            self.UI.text[0].text_element = Font.notification.render('Equations copied to clipboard!', True, (0, 0, 0))
                            to_copy = ''

                            for i in range(0, len(self.placed_points), 2):
                                if i != len(self.placed_points) - 1:
                                    to_copy += find_equation(self.placed_points[i], self.placed_points[i+1]) + '\n'
                                    print(find_equation(self.placed_points[i], self.placed_points[i+1]))

                            clipboard.copy(to_copy[:-1])

                        for tool_index in range(len(self.UI.tools)):
                            if self.UI.tools[tool_index].rect.collidepoint(mouse_pos):
                                self.selected_tool = tool_index

                    # Right click
                    elif event.button == 3:
                        pixel_x, pixel_y = self._get_pixel_pos(mouse_pos[0], mouse_pos[1])
                        coord_x, coord_y = self._get_coordinate_pos(pixel_x, pixel_y)

                        if self.selected_tool == 0:
                            if coord_x >= -self.graph_width and coord_x <= self.graph_width:
                                if coord_y >= -self.graph_height and coord_y <= self.graph_height:
                                    self.placed_points.append((coord_x, coord_y))
                        else:
                            # Convert coord back to pixel to match format
                            self.erase_pos = self._coordinate_to_pixel(coord_x, coord_y)

                elif pygame.mouse.get_pressed()[0]:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.mouse_start_pos == None:
                        self.mouse_start_pos = (mouse_pos[0]+self.offset_x, mouse_pos[1]+self.offset_y)
                    else:
                        self.offset_x = self.mouse_start_pos[0] - mouse_pos[0]
                        self.offset_y = self.mouse_start_pos[1] - mouse_pos[1]

                elif event.type == pygame.MOUSEBUTTONUP:
                    self.mouse_start_pos = None

            # Drawing
            self.screen.fill((255, 255, 255))

            self.image.draw(self.screen, self.offset_x, self.offset_y)
            self.UI.draw(self.screen, self.selected_tool)
            self._draw_and_update_lines()

            pygame.display.flip()

        pygame.quit()


if __name__ == '__main__':
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

    print('Instructions:')
    print('Right click to place a point. Right click again to create the line')
    print('If the eraser is selected, simply right click a line to delete it')
    print('Pan around the image by selecting and dragging your mouse')
    print('Zoom in or out using the green and red buttons')
    print('When you are done, press the output button to copy the functions which can be pasted directly into Desmos')
    print('Press enter to continue...')
    input()

    # Get width and height from user
    message = 'Enter the width and height of your image in Desmos'
    field_values = []
    while True:
        field_values = easygui.multenterbox(message, 'Dimensions of Image', ['Width', 'Height'], field_values)
        try:
            graph_width = float(field_values[0])/2
            graph_height = float(field_values[1])/2
            break
        except:
            message = 'Both inputs must be numerical!'

    img_src = easygui.fileopenbox('Please select an image')
    if not img_src:
        sys.exit()
    if img_src.split('.')[-1].lower() not in ['jpg', 'jpeg', 'png', 'gif']:
        print('That\'s not a supported file type!')
        input()
        sys.exit()

    line_creator = LineCreator(img_src, graph_width, graph_height)

