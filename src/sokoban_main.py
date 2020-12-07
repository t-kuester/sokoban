#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""
Sokoban Game Starter, by Tobias Küster, 2020

This modes handles loading the known and levels, showing a simple menu for
selecting the level to play, and saving the newly solved levels.

- load Sokoban levels in standard sokoban level file format
- select Sokoban level to play next
- show Sokoban UI for selected level set
- save progress (solved/unsolved, number of turns) for each level in JSON file
"""

import json

from parser import load_levels
from model import SokobanGame
from sokoban_ui import show_ui


def main():
	"""Load high scores, select level file, start game, save scores.
	"""
	import optparse
	import os, shutil
	fmt = optparse.IndentedHelpFormatter()
	fmt.format_description = lambda desc: desc.strip() + "\n"
	parser = optparse.OptionParser("sokoban_game.py [options]", formatter=fmt, description=__doc__)
	parser.add_option("-f", dest="levelfile", help="add new level file")
	(options, args) = parser.parse_args()

	# load highscores for level file
	config_dir = os.path.join(os.environ["HOME"], ".config", "t-kuester", "sokoban")
	os.makedirs(config_dir, exist_ok=True)
	savesfile = os.path.join(config_dir, "sokoban_saves.json")
	try:
		with open(savesfile) as f:
			gamestate = json.load(f)
	except IOError:
		gamestate = {}
	
	# EXPERIMENTAL: Aliases for level files	
	try:
		with open(os.path.join(config_dir, "aliases.json")) as f:
			aliases = json.load(f)
	except IOError:
		aliases = {}
	
	# load level file given as parameter, or select from saves
	if options.levelfile:
		source = options.levelfile
		filename = os.path.split(source)[-1]
		if filename not in gamestate:
			# TODO set alias when loading level, just append to aliases file
			shutil.copy(source, os.path.join(config_dir, filename))
			gamestate[filename] = [None] * len(load_levels(source))
			with open(savesfile, 'w') as f:
				json.dump(gamestate, f, indent=2)
			print("Level added")
		else:
			print("Level already exists")
		exit(0)
		
	if not gamestate:
		print("No levels known. Run with -f parameter to load levels first")
		exit(1)
	
	orig_solved = {ls: sum(s is not None for s in sc) for ls, sc in gamestate.items()}
	while True:
		# print level selection menu
		print("Known Level Sets")
		levels_dict = dict(enumerate(sorted(gamestate, key=lambda s: aliases.get(s, s)), start=1))
		for n, levelset in levels_dict.items():
			alias = aliases.get(levelset, levelset)
			scores = gamestate[levelset]
			solved = sum(s is not None for s in scores)
			solved_old = orig_solved[levelset]
			delta = "%+3d" % (solved - solved_old) if solved > solved_old else "   "
			complete = "*" if solved == len(scores) else " "
			print("%2d %3d/%3d %s %s %s" % (n, solved, len(scores), delta, complete, alias))
		selection = input("Select level set (anything else to quit): ")
		if selection.isdigit() and 0 < int(selection) <= n:
			filename = levels_dict[int(selection)]
		else:
			break

		# start game
		levels = load_levels(os.path.join(config_dir, filename))
		scores = gamestate[filename] or [None] * len(levels)
		show_ui(SokobanGame(filename, levels, scores))

		# save highscores
		# XXX save actual best moves, and improve format
		gamestate[filename] = scores
		with open(savesfile, 'w') as f:
			json.dump(gamestate, f, indent=2)
		print()


if __name__ == "__main__":
	main()

