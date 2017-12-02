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
- Mouse Click: Fast-move, push-planning (RMB: move instantaneous)
- Mouse Wheel up/down: undo/redo (also: z/y keys)
- q: quit, r: reload level, s: save snapshot, l: load snapshot, d: show deadends
- PgUp/PgDn: Next/Previous Level
- Shift + PgUp/PgDn: Next/Previous unsolved Level (if any)
"""

import sokoban
import tkinter as tk
import json

DIRECTIONS = {"Right": (0, +1), "Left": (0, -1), "Up": (-1, 0), "Down": (+1, 0)}
DIRECTIONS_INV = {(0, +1, 1): "R", (0, -1, 1): "L", (-1, 0, 1): "U", (+1, 0, 1): "D",
                  (0, +1, 0): "r", (0, -1, 0): "l", (-1, 0, 0): "u", (+1, 0, 0): "d"}

class SokobanFrame(tk.Frame):
	"""Sokoban Game Frame.
	
	This class provides the graphical interface to the Sokoban game, including
	keyboard and mouse control, loading level sets, undo, etc.
	"""
	
	def __init__(self, master, game, scores):
		"""Create new Sokoban Frame instance, using a given game instance and
		a dictionary holding the scores for the individual levels.
		"""
		tk.Frame.__init__(self, master)
		self.master.title("Sokoban")
		self.game = game
		self.scores = scores
		self.pack(fill=tk.BOTH, expand=tk.YES)
		
		self.selected = None
		self.path = None
		self.redo = []

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
			self.quit()
		if event.keysym == "r":
			self.game.load_level()
		if event.keysym == "s":
			self.game.save()
		if event.keysym == "l":
			self.game.load()
		if event.keysym == "d":
			self.game.deadends = set() if self.game.deadends else \
					sokoban.find_deadends(self.game.state)
		if event.keysym == "z" and self.game.progress:
			self.redo.append(self.game.undo())
		if event.keysym == "y" and self.undo:
			self.game.move(*self.redo.pop())
		if event.keysym in ("Prior", "Next"):
			inc = lambda num: (num +1 if event.keysym == "Next" else num-1) % len(self.game.levels)
			number = inc(self.game.number)
			# shift: fast-forward to next unsolved level, if any
			while shift and self.scores[number] and number != self.game.number:
				number = inc(number)
			self.redo = []
			self.game.load_level(number )
		if event.keysym in DIRECTIONS:
			self.redo = []
			dr, dc = DIRECTIONS[event.keysym]
			while self.game.move(dr, dc, not shift) and shift:
				# self.after(20, self.handle_keys, event, shift)
				pass
		self.update_state()
		
	def handle_mouse(self, event):
		"""Handle mouse events for planning movement and box-pushing,
		"""
		if event.num in (4, 5):
			# mouse wheel: undo/redo
			if event.num == 4 and self.game.progress:
				self.redo.append(self.game.undo())
			if event.num == 5 and self.redo:
				self.game.move(*self.redo.pop())

		if event.num in (1, 3):
			# left/right mouse button: move/push
			w = self.get_cellwidth()
			r, c = int(event.y // w), int(event.x // w)
			move_fast = event.num == 3 # RMB -> move fast
			try:
				symbol = self.game.state[r][c]
				if sokoban.is_box(symbol):
					self.selected = (r, c)
				if sokoban.is_free(symbol) or sokoban.is_player(symbol):
					self.redo = []
					if self.selected is None:
						self.path = self.game.find_path(r, c)
						self.move_path(move_fast)
					else:
						self.path = self.game.plan_push(self.selected, (r, c))
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
				self.game.replay(self.path, False)
				self.path = []
			else:
				dr, dc, push = self.path.pop(0)
				self.game.move(dr, dc, push)
				self.after(25, self.move_path)
		self.update_state()

	def update_state(self):
		"""Check the current state of the game (solved or not, number of steps, 
		etc.), update the status line, and redraw the canvas.
		"""
		num = self.game.number
		solved = self.game.check_solved()
		num_solved = sum(x is not None for x in self.scores)
		turns = len(self.game.progress)
		if solved and (self.scores[num] is None or turns < self.scores[num]):
			self.scores[num] = turns
		status = "%d, %d/%d, %d Steps (Best: %r)" % (num + 1, num_solved,
				len(self.game.levels), turns, self.scores[num])
		history = " ".join(DIRECTIONS_INV[d] for d in self.game.progress[-30:])
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
				if (r, c) in self.game.deadends:
					self.canvas.create_rectangle(x, y, x+w, y+w, fill="#CC8888")
				if cell == sokoban.WALL:
					self.canvas.create_rectangle(x, y, x+w, y+w, fill="#888888")
				if sokoban.is_goal(cell):
					self.canvas.create_oval(x+w*.1, y+w*.1, x+w*.9, y+w*.9, fill="#88CC88")
				if sokoban.is_box(cell):
					color = "#8888CC" if (r, c) == self.selected else "#CCCC88"
					self.canvas.create_rectangle(x+w*.2, y+w*.2, x+w*.8, y+w*.8, fill=color)
				if sokoban.is_player(cell):
					self.canvas.create_oval(x+w*.3, y+w*.3, x+w*.7, y+w*.7, fill="#8888CC")

	def get_cellwidth(self):
		"""Simple helper method for getting the optimal width for a cell.
		"""
		width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
		return min(height / len(self.game.state), 
		           width  / max(map(len, self.game.state)))


def main():
	"""Load high scores, select level file, start game, save scores.
	"""
	import optparse
	fmt = optparse.IndentedHelpFormatter()
	fmt.format_description = lambda desc: desc.strip() + "\n"
	parser = optparse.OptionParser("sokoban_game.py [options]", formatter=fmt, description=__doc__)
	parser.add_option("-m", dest="show_menu", help="show level menu", action="store_true")
	parser.add_option("-f", dest="levelfile", help="select level file")
	(options, args) = parser.parse_args()

	# load highscores for level file
	savesfile = "sokoban_saves.json"
	try:
		with open(savesfile) as f:
			gamestate = json.load(f)
	except IOError:
		gamestate = {}
	
	# load level file given as parameter, or select from saves
	levelfile = None
	if options.levelfile:
		levelfile = options.levelfile
	elif options.show_menu and gamestate:
		for n, (levelset, scores) in enumerate(sorted(gamestate.items()), start=1):
			solved = sum(s is not None for s in scores)
			complete = "*" if solved == len(scores) else " "
			print("%2d %3d/%3d %s %s" % (n, solved, len(scores), complete, levelset))
		selection = input("Select level set: ")
		if selection.isdigit() and 0 < int(selection) <= n:
			levelfile = sorted(gamestate)[int(selection) - 1]
	elif options.show_menu:
		print("No levels known; use -f to load level file.")
	else:
		parser.print_help()
	if levelfile is None:
		exit()

	# start game
	levels = sokoban.load_levels(levelfile)
	scores = gamestate.get(levelfile, [None] * len(levels))
	game = sokoban.SokobanGame(levels)
	root = tk.Tk()
	root.geometry("640x480")
	SokobanFrame(root, game, scores)
	root.mainloop()

	# save highscores
	gamestate[levelfile] = scores
	with open(savesfile, 'w') as f:
		json.dump(gamestate, f)

if __name__ == "__main__":
	main()
