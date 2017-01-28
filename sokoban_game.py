#!/usr/bin/env python3
# -*- coding: utf8 -*-

"""
Simple Sokoban Game, by Tobias Küster, 2014

Features:
- load Sokoban levels in standard sokoban level file format
- save progress (solved/unsolved, number of turns) for each level in JSON file
- controls with arrow-keys or with mouse
- save/restore snapshot of current level, undo-stack
- path-planning for movement and push-planning for pushing single boxes

Controls:
- Arrow Keys: Move/Push
- Mouse Click: Fast-move, push-planning
- q: quit, r: reload level, u: undo
- s: save snapshot, l: load snapshot
- PgUp/PgDn: Next/Previous Level
- Shift + PgUp/PgDn: Next/Previous unsolved Level (if any)
"""

import sokoban
import tkinter as tk
import json

DIRECTIONS = {"Right": (0, +1), "Left": (0, -1), "Up": (-1, 0), "Down": (+1, 0)}
DIRECTIONS_INV = dict((v, k) for (k, v) in DIRECTIONS.items())

class SokobanFrame(tk.Frame):
	"""Sokoban Game Frame.
	
	This class provides the graphical interface to the Sokoban game, including
	keyboard and mouse control, loading level sets, undo, etc.
	"""
	
	def __init__(self, game, scores):
		"""Create new Sokoban Frame instance, using a given game instance and
		a dictionary holding the scores for the individual levels.
		"""
		tk.Frame.__init__(self, None)
		self.master.title("Sokoban")
		self.game = game
		self.scores = scores
		self.pack(fill=tk.BOTH, expand=tk.YES)
		
		self.selected = None

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
		self.selected = None
		if event.keysym == "q":
			self.quit()
		if event.keysym == "r":
			self.game.load_level()
		if event.keysym == "u":
			steps = self.game.progress[:-1]
			self.game.replay(steps, True)
		if event.keysym == "s":
			self.game.save()
		if event.keysym == "l":
			self.game.load()
		if event.keysym in ("Prior", "Next"):
			inc = lambda num: (num +1 if event.keysym == "Next" else num-1) % len(self.game.levels)
			number = inc(self.game.number)
			# shift: fast-forward to next unsolved level, if any
			while shift and self.scores[number] and number != self.game.number:
				number = inc(number)
			self.game.load_level(number )
		if event.keysym in DIRECTIONS:
			dr, dc = DIRECTIONS[event.keysym]
			while self.game.move(dr, dc, not shift) and shift:
				# self.after(20, self.handle_keys, event, shift)
				pass
		self.update_state()
		
	def handle_mouse(self, event):
		"""Handle mouse events for planning movement and box-pushing,
		"""
		w = self.get_cellwidth()
		r, c = int(event.y // w), int(event.x // w)
		try:
			symbol = self.game.state[r][c]
			if sokoban.is_box(symbol):
				self.selected = (r, c)
			if sokoban.is_free(symbol) or sokoban.is_player(symbol):
				if self.selected is None:
					path = self.game.find_path(r, c)
					self.move_path(path, False)
				else:
					path = self.game.plan_push(self.selected, (r, c))
					self.move_path(path, True)
				self.selected = None
			self.update_state()
		except IndexError:
			pass

	def move_path(self, path, push):
		"""Move one step in the given path, then wait a short time, repaint, and
		continue.
		"""
		if path:
			dr, dc = path[0]
			self.game.move(dr, dc, push)
			self.after(25, self.move_path, path[1:], push)
		self.update_state()

	def update_state(self):
		"""Check the current state of the game (solved or not, number of steps, 
		etc.), update the status line, and redraw the canvas.
		"""
		num = self.game.number
		solved = self.game.check_solved()
		turns = len(self.game.progress)
		if solved and (self.scores[num] is None or turns < self.scores[num]):
			self.scores[num] = turns
		status = "%d/%d, %d Steps (Best: %r)" % (num + 1, 
				len(self.game.levels), turns, self.scores[num])
		history = " ".join(DIRECTIONS_INV[d][0] for d in self.game.progress[-30:])
		self.status.configure(text=status)
		self.history.configure(text=history)
		self.draw_state()
		
	def draw_state(self, event=None):
		"""Draw the current state of the game to the canvas.
		"""
		self.update()
		self.canvas.delete("all")
		w = self.get_cellwidth()
		for r, row in enumerate(self.game.state):
			for c, col in enumerate(row):
				cell = self.game.state[r][c]
				x, y = c*w, r*w
				if cell == sokoban.WALL:
					self.canvas.create_rectangle(x, y, x+w, y+w, fill="#888888")
				if sokoban.is_goal(cell):
					self.canvas.create_oval(x+w*.1, y+w*.1, x+w*.9, y+w*.9, fill="#88CC88")
				if sokoban.is_box(cell):
					if (r, c) == self.selected:
						self.canvas.create_rectangle(x, y, x+w, y+w, fill="#CC8888")
					self.canvas.create_rectangle(x+w*.2, y+w*.2, x+w*.8, y+w*.8, fill="#CCCC88")
				if sokoban.is_player(cell):
					self.canvas.create_oval(x+w*.3, y+w*.3, x+w*.7, y+w*.7, fill="#8888CC")

	def get_cellwidth(self):
		"""Simple helper method for getting the optimal width for a cell.
		"""
		width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
		return min(height / len(self.game.state), 
		           width  / max(map(len, self.game.state)))


if __name__ == "__main__":
	import optparse
	parser = optparse.OptionParser("sokoban_game.py [level file]")
	(options, args) = parser.parse_args()
	
	# load level file given as parameter
	levelfile = (args or ["levels/masmicroban.txt"])[0]
	levels = sokoban.load_levels(levelfile)
	
	#load highscores for level file
	savesfile = "sokoban_saves.json"
	try:
		with open(savesfile) as f:
			gamestate = json.load(f)
	except IOError:
		gamestate = {}
	scores = gamestate.get(levelfile, [None] * len(levels))

	# start game
	game = sokoban.SokobanGame(levels)
	frame = SokobanFrame(game, scores)
	frame.mainloop()

	# save highscores
	gamestate[levelfile] = scores
	with open(savesfile, 'w') as f:
		json.dump(gamestate, f)
