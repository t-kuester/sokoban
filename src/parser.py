# -*- coding: utf8 -*-

"""
Sokoban Map Parser, by Tobias Kuester, 2014-2017, 2020

This modules provides functions for parsing standard Sokoban map files in TXT
format and for creating Levels and initial States from those files.
"""

from typing import Iterable, List
from itertools import groupby

from model import Pos, Level


WALL        = '#'
PLAYER      = '@'
PLAYER_GOAL = '+'
BOX         = '$'
BOX_GOAL    = '*'
FLOOR_GOAL  = '.'
FLOOR       = ' '
COMMENT     = ';'


def load_level(lines: Iterable[str]) -> Level:
	"""Load individual level in standard Sokoban Txt Format, using the above
	defined symbols. Creates a Level instance with an according initial State.
	"""
	walls = set()
	goals = set()
	boxes = set()
	player = None
	for r, line in enumerate(lines):
		for c, char in enumerate(line):
			p = Pos(r, c)
			if char in (WALL,):
				walls.add(p)
			if char in (PLAYER_GOAL, BOX_GOAL, FLOOR_GOAL):
				goals.add(p)
			if char in (BOX, BOX_GOAL):
				boxes.add(p)
			if char in (PLAYER, PLAYER_GOAL):
				player = p
	return Level(walls, goals, boxes, player)


def load_levels(filename: str) -> List[Level]:
	"""Load levels from given level file. Levels are separated by empty or
	commented lines. If the levels can not be loaded, None is returned.
	"""
	with open(filename) as levelfile:
		return [load_level(group)
				for k, group in groupby(levelfile, key=lambda line: line.lstrip().startswith(WALL)) if k]


# testing	
if __name__ == "__main__":
	levels = load_levels("test.txt")
	print("Number of levels:", len(levels))
	for level in levels:
		print(level)
		print("Goals", level.goals)
		print("Boxes", level.initial_state.boxes)
		print("Player", level.initial_state.player)
