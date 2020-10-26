#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""
Simple Sokoban Game, by Tobias Küster, 2014-2017

Features:
- load Sokoban levels in standard sokoban level file format
- save progress (solved/unsolved, number of turns) for each level in JSON file
- controls with arrow-keys or with mouse
- save/restore snapshot of current level, undo/redo-stack
- path-planning for movement and push-planning for pushing single boxes

Controls:
- Arrow Keys: Move/Push
- Mouse Click: Fast-move, push-planning (RMB: skip animation)
- Mouse Wheel up/down: undo/redo (also: z/y keys)
- q: quit, r: reload level, s: save snapshot, l: load snapshot, d: show deadends
- PgUp/PgDn: Next/Previous Level
- Shift + PgUp/PgDn: Next/Previous unsolved Level (if any)
"""

import tkinter as tk
import json

from parser import load_levels
from model import SokobanGame, Pos, Move
import search

DIRECTIONS = {"Right": (0, +1), "Left": (0, -1), "Up": (-1, 0), "Down": (+1, 0)}
DIRECTIONS_INV = {(0, +1, 1): "R", (0, -1, 1): "L", (-1, 0, 1): "U", (+1, 0, 1): "D",
                  (0, +1, 0): "r", (0, -1, 0): "l", (-1, 0, 0): "u", (+1, 0, 0): "d"}


class Color:
	WALL = "#888888"
	GOAL = "#88CC88"
	BOX  = "#CCCC88"
	PLYR = "#8888CC"
	DEAD = "#CC8888"


class SokobanFrame(tk.Frame):
	"""Sokoban Game Frame.
	
	This class provides the graphical interface to the Sokoban game, including
	keyboard and mouse control, loading level sets, undo, etc.
	"""
	
	def __init__(self, master, game):
		"""Create new Sokoban Frame instance, using a given game instance and
		a dictionary holding the scores for the individual levels.
		"""
		tk.Frame.__init__(self, master)
		self.master.title(f"Sokoban - {game.title}")
		self.game = game
		self.pack(fill=tk.BOTH, expand=tk.YES)
		
		self.selected = None
		self.path = None

		self.canvas = tk.Canvas(self)
		self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
		
		self.status = tk.Label(self)
		self.status.pack(side=tk.LEFT)
		
		self.history = tk.Label(self)
		self.history.pack(side=tk.RIGHT)
		
		self.bind_all("<KeyPress>", self.handle_keys)
		self.bind_all("<Shift-KeyPress>", lambda e: self.handle_keys(e, True))
		self.canvas.bind("<ButtonRelease>", self.handle_mouse)
		self.bind("<Configure>", self.draw_state)
		self.update_state()
		
	def handle_keys(self, event, shift=False):
		"""Handle key events, e.g. or movement, save, load, undo, restart, etc.
		"""
		self.path = None
		self.selected = None
		if event.keysym == "q":
			self.master.destroy()
			return
		if event.keysym == "r":
			self.game.load_level()
		if event.keysym == "s":
			self.game.save_snapshot()
		if event.keysym == "l":
			self.game.load_snapshot()
		if event.keysym == "d":
			# TODO calculate just once, then store whether to show them in UI
			self.game.state.level.deadends = set() if self.game.state.level.deadends else \
					search.find_deadends(self.game.state.level)
		if event.keysym == "z":
			self.game.state.undo()
		if event.keysym == "y":
			self.game.state.redo()
		if event.keysym in ("Prior", "Next"):
			# TODO move logic for this to SokobanGame class
			inc = lambda num: (num +1 if event.keysym == "Next" else num-1) % len(self.game.levels)
			cur = inc(self.game.current)
			# shift: fast-forward to next unsolved level, if any
			while shift and self.game.scores[cur] and cur != self.game.current:
				cur = inc(cur)
			self.game.load_level(cur)
		if event.keysym in DIRECTIONS:
			dr, dc = DIRECTIONS[event.keysym]
			if self.game.state.move(Move(dr, dc, not shift)) and shift:
				self.after(20, self.handle_keys, event, shift)
		self.update_state()
		
	def handle_mouse(self, event):
		"""Handle mouse events for planning movement and box-pushing,
		"""
		if event.num in (4, 5):
			# mouse wheel: undo/redo
			if event.num == 4:
				self.game.state.undo()
			if event.num == 5:
				self.game.state.redo()

		if event.num in (1, 3):
			# left/right mouse button: move/push
			w = self.get_cellwidth()
			r, c = int(event.y // w), int(event.x // w)
			p = Pos(r, c)
			move_fast = event.num == 3  # RMB -> move fast
			try:
				if p in self.game.state.boxes:
					self.selected = p
				if self.game.state.is_free(p):
					if self.selected is None:
						self.path = search.find_path(self.game.state, p)
						self.move_path(move_fast)
					else:
						self.path = search.plan_push(self.game.state, self.selected, p)
						self.move_path(move_fast)
					self.selected = None
			except IndexError:
				pass
		self.update_state()

	def move_path(self, instant=False):
		"""Move one step in the given path, then wait a short time,
		repaint, and continue. If 'instant' parameter is True, then move
		instantly, to save time and prevent max. recursion limit.
		"""
		if self.path:
			if instant:
				while self.path:
					self.game.state.move(self.path.pop(0))
			else:
				self.game.state.move(self.path.pop(0))
				self.after(25, self.move_path)
		self.update_state()

	def update_state(self):
		"""Check the current state of the game (solved or not, number of steps, 
		etc.), update the status line, and redraw the canvas.
		"""
		self.game.update_score()
		num = self.game.current
		num_solved = sum(1 for x in self.game.scores if x is not None)
		turns = len(self.game.state.history)
		status = "%d, %d/%d, %d Steps (Best: %r)" % (num + 1, num_solved,
				len(self.game.levels), turns, self.game.scores[num])
		history = " ".join(DIRECTIONS_INV[d] for d in self.game.state.history[-30:])
		self.status.configure(text=status)
		self.history.configure(text=history)
		self.draw_state()
		
	def draw_state(self, event=None):
		"""Draw the current state of the game to the canvas.
		"""
		self.update()
		self.canvas.delete("all")
		s = self.game.state.level.size
		w = self.get_cellwidth()
		for r in range(s.r):
			for c in range(s.c):
				p = Pos(r, c)
				x, y = c*w, r*w
				if p in self.game.state.level.deadends:
					self.canvas.create_rectangle(x, y, x+w, y+w, fill=Color.DEAD)
				if p in self.game.state.level.walls:
					self.canvas.create_rectangle(x, y, x+w, y+w, fill=Color.WALL)
				if p in self.game.state.level.goals:
					self.canvas.create_oval(x+w*.1, y+w*.1, x+w*.9, y+w*.9, fill=Color.GOAL)
				if p in self.game.state.boxes:
					color = Color.PLYR if (r, c) == self.selected else Color.BOX
					self.canvas.create_rectangle(x+w*.2, y+w*.2, x+w*.8, y+w*.8, fill=color)
				if p == self.game.state.player:
					self.canvas.create_oval(x+w*.3, y+w*.3, x+w*.7, y+w*.7, fill=Color.PLYR)

	def get_cellwidth(self):
		"""Simple helper method for getting the optimal width for a cell.
		"""
		size = self.game.state.level.size
		return min(self.canvas.winfo_height() / size.r, self.canvas.winfo_width() / size.c)


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
	
	# load level file given as parameter, or select from saves
	if options.levelfile:
		source = options.levelfile
		filename = os.path.split(source)[-1]
		if filename not in gamestate:
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
		for n, (levelset, scores) in enumerate(sorted(gamestate.items()), start=1):
			solved = sum(s is not None for s in scores)
			solved_old = orig_solved[levelset]
			delta = "%+3d" % (solved - solved_old) if solved > solved_old else "   "
			complete = "*" if solved == len(scores) else " "
			print("%2d %3d/%3d %s %s %s" % (n, solved, len(scores), delta, complete, levelset))
		selection = input("Select level set (anything else to quit): ")
		if selection.isdigit() and 0 < int(selection) <= n:
			filename = sorted(gamestate)[int(selection) - 1]
		else:
			break

		# start game
		levels = load_levels(os.path.join(config_dir, filename))
		scores = gamestate[filename] or [None] * len(levels)
		game = SokobanGame(filename, levels, scores)
		root = tk.Tk()
		root.geometry("640x480")
		SokobanFrame(root, game)
		root.mainloop()

		# save highscores
		# XXX save actual best moves, and improve format
		gamestate[filename] = scores
		with open(savesfile, 'w') as f:
			json.dump(gamestate, f, indent=2)
		print()


if __name__ == "__main__":
	main()
