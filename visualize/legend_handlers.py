# ------------------------------------------------------------------------------------------------------------------- #
# imports
# ------------------------------------------------------------------------------------------------------------------- #

from matplotlib.legend_handler import HandlerBase
from matplotlib.lines import Line2D

# ------------------------------------------------------------------------------------------------------------------- #
# class
# ------------------------------------------------------------------------------------------------------------------- #

# Dummy handle for the reference line
class RefLine:
    pass

# Custom handler to draw horizontal line with vertical ticks (|-|)
class HandlerRefLine(HandlerBase):
    def create_artists(self, legend, orig_handle,
                       xdescent, ydescent, width, height, fontsize, trans):
        y = height / 2.0
        tick_height = height * 0.3   # vertical tick height
        lw = 2

        # Horizontal line
        line = Line2D([xdescent, xdescent + width],
                      [y, y], color="#26373C", lw=lw, transform=trans)

        # Vertical ticks at ends
        left_tick = Line2D([xdescent, xdescent],
                           [y - tick_height/2, y + tick_height/2],
                           color="#26373C", lw=lw, transform=trans)
        right_tick = Line2D([xdescent + width, xdescent + width],
                            [y - tick_height/2, y + tick_height/2],
                            color="#26373C", lw=lw, transform=trans)

        return [line, left_tick, right_tick]