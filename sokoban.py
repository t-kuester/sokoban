#!/usr/bin/python
# -*- coding: utf8 -*-

"""
Sokoban Game Model, by Tobias Kuester, 2014

This modules provides a class encapsulating the current state of the Sokoban 
game as well as some helper methods for loading game files and other stuff.

The game model provides basic functionality for movement and for pushing boxes,
for path planning and for planning to push a box to a given location.
"""

import collections

WALL        = '#'
PLAYER      = '@'
PLAYER_GOAL = '+'
BOX         = '$'
BOX_GOAL    = '*'
FLOOR_GOAL  = '.'
FLOOR       = ' '
COMMENT     = ';'


def is_goal(symbol):
	"""return whether the given symbol represents a goal tile"""
	return symbol in (PLAYER_GOAL, BOX_GOAL, FLOOR_GOAL)

def is_free(symbol):
	"""return whether the given symbol represents passable space"""
	return symbol in (FLOOR, FLOOR_GOAL)
	
def is_player(symbol):
	"""return whether the given symbol represents a player"""
	return symbol in (PLAYER, PLAYER_GOAL)
	
def is_box(symbol):
	"""return whether the given symbol represents a box"""
	return symbol in (BOX, BOX_GOAL)

def load_levels(filename):
	"""Load levels from given level file. Levels are separated by empty or
	commented lines. If the levels can not be loaded, None is returned.
	"""
	with open(filename) as levelfile:
		levels = [[]]
		for line in levelfile.read().splitlines():
			if line.lstrip().startswith(WALL):
				levels[-1].append(line)
			elif levels[-1]:
				levels.append([])

		return tuple(map(tuple, filter(None, levels)))

def listify(list_of_lists):
	return list(map(list, list_of_lists))
	
def tuplefy(list_of_lists):
	return tuple(map(tuple, list_of_lists))

class SokobanGame:
	"""Class representing the current state of the Sokoban game.
	
	This class encapsulates the entire level set, the current level, the current
	position of the player, and a list of the moves so far taken.
	"""
	
	def __init__(self, levels):
		"""Create new Sokoban game instance.
		"""
		self.levels = levels
		self.number = 0
		self.load_level()
		self.backup = None
		
	def load_level(self, number=None):
		"""Load level with given number from current level set.
		If no number is given, reload the current level.
		"""
		self.number = number if number is not None else self.number
		self.state = listify(self.levels[self.number % len(self.levels)])
		self.progress = []
		self.r = self.c = 0
		for r, row in enumerate(self.state):
			for c, col in enumerate(row):
				if is_player(self.state[r][c]):
					self.r, self.c = r, c
		if number:
			self.backup = None

	def save(self):
		"""Save current state of the game.
		"""
		self.backup = listify(self.state), self.r, self.c, list(self.progress)
		
	def load(self):
		"""Restore previously saved game state.
		"""
		if self.backup:
			self.state, self.r, self.c, self.progress = self.backup
			self.save()
	
	def get_rel(self, dr, dc):
		"""Get symbol at row/column relative to player's position.
		"""
		return self.state[self.r + dr][self.c + dc]
	
	def set_rel(self, dr, dc, symbol):
		"""Set symbol at row/column relative to player's position.
		"""
		self.state[self.r + dr][self.c + dc] = symbol
	
	def can_move(self, dr, dc, push=False):
		"""Check whether player can move to an adjacent location, with or 
		without being allowed to push a box.
		"""
		next_ = self.get_rel(dr, dc)
		if is_free(next_):
			return True
		elif push and is_box(next_):
			return is_free(self.get_rel(2 * dr, 2 * dc))
		return False
	
	def move(self, dr, dc, push=False):
		"""Move to an adjacent location, after checking whether that move would 
		be legal, with or without being allowed to move a box.
		"""
		if self.can_move(dr, dc, push):
			cur = self.get_rel(0, 0)
			next_ = self.get_rel(dr, dc)
			self.set_rel(0, 0, FLOOR_GOAL if is_goal(cur) else FLOOR)
			self.set_rel(dr, dc, PLAYER_GOAL if is_goal(next_) else PLAYER)
			if push and is_box(next_):
				next_next = self.get_rel(2 * dr, 2 * dc)
				self.set_rel(2 * dr, 2 * dc, BOX_GOAL if is_goal(next_next) else BOX)
			self.r += dr
			self.c += dc
			self.progress.append((dr, dc))
			return True
		else:
			return False

	def find_path(self, row, col):
		"""Try to find a path to (row, col), without moving boxes, using BFS.
		"""
		queue = collections.deque([(self.r, self.c, [])])
		visited = set()
		while queue:
			(r, c, path) = queue.popleft()
			if (r, c) in visited:
				continue
			visited.add((r, c))
			if (r, c) == (row, col):
				return path
			for dr, dc in ((0, +1), (0, -1), (-1, 0), (+1, 0)):
				if is_free(self.state[r + dr][c + dc]):
					queue.append((r + dr, c + dc, path + [(dr, dc)]))
		return None
	
	def plan_push(self, start, goal):
		"""Plan how to push box from start to goal position. Planning is done
		using the same basic breadth-first-search as for movement planning, 
		except that we have to keep track of the actual game state, which is 
		done by simply replaying the so-far path in each step. Not terribly
		efficient, but fast enough, simple and robust. Positioning of the player
		is done using the basic movement planning algorithm.
		"""
		original_state = tuplefy(self.state)
		original_position = self.r, self.c
		original_progress = list(self.progress)

		result = None
		queue = collections.deque([(start, [])])
		visited = set()
		while queue:
			(r, c), path = queue.popleft()

			if (r, c) in visited:
				continue
			visited.add((r, c))

			if (r, c) == goal:
				result = path
				break
			
			self.state = listify(original_state)
			self.r, self.c = original_position
			self.replay(path, False)
		
			for dr, dc in ((0, +1), (0, -1), (-1, 0), (+1, 0)):
				target = self.state[r + dr][c + dc]
				if is_free(target) or is_player(target):
					positioning = self.find_path(r - dr, c - dc)
					if positioning is not None:
						queue.append(((r + dr, c + dc), path + positioning + [(dr, dc)]))

		self.state = listify(original_state)
		self.r, self.c = original_position
		self.progress = original_progress
		return result
	
	def replay(self, steps, reset):
		"""Resets the game state and replay the moves given in the list.
		"""
		if reset:
			self.load_level()
		for dr, dc in steps:
			self.move(dr, dc, True)
			
	def check_solved(self):
		"""Check whether all goal tiles have a box placed on them.
		"""
		return not any(symbol in (PLAYER_GOAL, FLOOR_GOAL) 
		               for row in self.state for symbol in row)
	
	def __str__(self):
		"""Create simple string representation of the game state."""
		return "SokobanGame(level: %d/%d, position: %r, progress: %r)" % \
				(self.number, len(self.levels), (self.r, self.c), self.progress)

# testing	
if __name__ == "__main__":
	levels = load_levels("levels/microban.txt")
	print("Number of levels:", len(levels))
	for line in levels[0]:
		print(line)
	print(SokobanGame(levels))
