import random
from dataclasses import dataclass, field
from logging import Logger
from pathlib import Path

import numpy as np
from psychopy import core, event, visual

from reaction_time.utils.logging import logger
from reaction_time.utils.marker import MarkerWriter

MRK_LEFT_ARROW = 2
MRK_RIGHT_ARROW = 3


@dataclass
class Context:
    screen_ix: int = 0
    screen_size: tuple[int, int] = (1680, 1050)
    fullscr: bool = False
    script_dir: Path = Path("./reaction_time/")
    stim_dir: Path = Path("./assets/")
    win_color: tuple[int, int, int] = (-1, -1, -1)

    reactions: list = field(default_factory=list)  # tracking
    block_stimuli: list = field(default_factory=list)
    lsl_outlet: object = None

    # parametrization
    reaction_time_max_s: float = 2.0  # number of seconds to react
    max_random_wait_s: float = 1  # max time to wait before showing stimulus
    min_random_wait_s: float = 0.5  # min time to wait before showing stimulus
    n_pictures_per_stim: int = 5  # number of pictures per stimulus/side

    def __init__(self):
        self.window = visual.Window(
            fullscr=self.fullscr,
            size=self.screen_size,
            units="norm",
            screen=self.screen_ix,
            color=self.win_color,
        )
        # marker writer
        self.marker_writer: MarkerWriter = MarkerWriter("COM4")


class ReactionTimeTaskManager:
    def __init__(
        self,
        ctx: Context,
        logger: Logger = logger,
    ):
        """
        Base class for facial emotion recognition experiment

        Parameters:
        -----------
        ctx: Context
            the context object to store general configurations and especially
            the window object
        """
        self.ctx = ctx
        self.logger = logger

        # link to context for convenience
        self.win = self.ctx.window

    def exec_block(self):
        """Run a block"""

        stimuli = self.load_stimuli()
        self.clock = core.Clock()

        self.show_countdown()

        for mrk, stim in stimuli:
            t_wait_s = self.ctx.min_random_wait_s + (
                np.random.rand()
                * (self.ctx.max_random_wait_s - self.ctx.min_random_wait_s)
            )
            core.wait(t_wait_s)
            k, t = self.present_stimulus(stim, mrk)

            # also logging marker here makes parsing simpler
            self.logger.info(f"Reaction {k}|{t} - mrk: {mrk}")

            # show blank for a bit
            self.win.flip()

    def show_countdown(self, show_time_per: float = 1, from_int: int = 3):
        """Present a little countdown to prepare player"""

        text = visual.TextStim(self.win, text="Reaktionszeitmessung beginnt")
        text.draw()
        self.win.flip()
        core.wait(2)

        for i in range(from_int)[::-1]:
            text = visual.TextStim(self.win, text=f"{i + 1}", color="#00bfff")
            text.draw()
            self.win.flip()
            core.wait(show_time_per)
        self.win.flip()

    def present_stimulus(
        self, stim: visual.image.ImageStim, mrk: int
    ) -> tuple[float, str]:
        self.clock.reset(newT=0.0)
        stim.draw()
        self.win.flip()
        self.send_marker(mrk)

        keys = event.waitKeys(
            maxWait=self.ctx.reaction_time_max_s,
            keyList=["left", "right"],
            timeStamped=self.clock,
            clearEvents=True,
        )

        if keys is not None:
            k, t = keys[0]
        else:
            k, t = "time out", None

        return k, t

    def load_stimuli(self):
        r_arrow_file = list(self.ctx.stim_dir.rglob("arrow_right.png"))[0]
        l_arrow_file = list(self.ctx.stim_dir.rglob("arrow_left.png"))[0]

        r_img = visual.image.ImageStim(self.win, image=r_arrow_file)
        l_img = visual.image.ImageStim(self.win, image=l_arrow_file)

        stimuli = [
            (MRK_RIGHT_ARROW, r_img),
            (MRK_LEFT_ARROW, l_img),
        ] * self.ctx.n_pictures_per_stim
        random.shuffle(stimuli)

        stim_labels = [
            (mrk, "left" if s == l_img else "right") for mrk, s in stimuli
        ]

        self.logger.info(f"Prepared stimuli: {stim_labels}")

        return stimuli

    def send_marker(self, val):
        if isinstance(val, int) and val < 256:
            self.ctx.marker_writer.write(val)
        else:
            raise ValueError(
                "Please provide an int value < 256 to be written as a marker"
                f" - received: {val=}"
            )


def run_one_block_reaction_time() -> int:
    ctx = Context()
    ReactionTimeTaskManager(ctx).exec_block()

    logger.debug("Finished reaction time task - closing window")
    ctx.window.close()

    return 0


if __name__ == "__main__":
    logger.setLevel("DEBUG")
    ctx = Context()
    ReactionTimeTaskManager(ctx).exec_block()
