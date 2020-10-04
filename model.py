# -*- coding: utf8 -*-

"""
Sokoban Game Model, by Tobias Kuester, 2014-2017, 2020

This modules provides classes encapsulating the current state of the Sokoban
game. The model provides basic functionality for movement and for pushing boxes.
Parsing and more sophisticated search and planning are in separate modules.
"""

from typing import List, NamedTuple


#DIRECTIONS = ((0, +1), (0, -1), (-1, 0), (+1, 0))

# class LevelSet: from_file, levels, scores, load(num)
# class Game: levelset, state, backup (here or in UI? combine with levelset?)

class Move(NamedTuple):
	""" Data Class representing a move. """
	dr: int
	dr: int
	push: bool

	def inv(self):
		return Move(-self.dr, -self.dc, self.push)


class Pos(NamedTuple):
	""" Data Class representing a Position. """
	r: int
	c: int

	def add(self, move: Move):
		return Pos(self.r + move.dr, self.c + move.dc)


class State:
	""" Class representing a State in a game of Sokoban, referring to a level
	and holding the current positions of the boxes and the player, as well as
	the history of applied moves.
	"""
	
	def __init__(self, level, boxes, player, history=None):
		self.level = level
		self.boxes = set(boxes)
		self.player = player
		self.history = list(history or [])
		
	def copy(self):
		""" Create copy of this state, e.g. for making a savestate.
		"""
		return State(self.level, self.boxes, self.player, self.history)
	
	def is_free(self, pos: Pos) -> bool:
		""" Check whether given position is free.
		"""
		return pos in self.level.floor and pos not in self.boxes
	
	def can_move(self, move: Move) -> bool:
		"""Check whether player can move to an adjacent location, with or 
		without being allowed to push a box.
		"""
		next_     = self.player.add(move)
		return is_free(next_) or \
		       move.push and next_ in self.boxes and is_free(next_.add(move))
	
	def move(self, move: Move) -> bool:
		"""Move to an adjacent location, after checking whether that move would 
		be legal, with or without being allowed to move a box.
		"""
		# TODO use assert here?
		if self.can_move(move):
			self.player = self.player.add(move)
			push = self.player in self.boxes
			if push:
				self.boxes.remove(self.player)
				self.boxes.add(self.player.add(move))
			# add to history whether we _actually_ pushed a box
			self.history.append(Move(move.dr, move.dc, push))
			return True
		else:
			return False
	
	def undo(self) -> bool:
		"""Undo last step from game's progress, moving the player to the
		previous position and "pulling" the crate, if previously pushed,
		back to the player's current position.
		"""
		if self.history:
			move = self.history.pop()
			if move.push:
				self.boxes.add(self.player)
				self.boxes.remove(self.player.add(move))
			self.player = self.player.add(move.inv())
			return True
		else:
			return False
	
	def is_solved(self) -> bool:
		"""Check whether all goal tiles have a box placed on them.
		"""
		return all(g in self.boxes for g in self.level.goals)
	

class Level:
	""" Class representing a Sokoban level, with valid floor positions, goals,
	and initial state.
	"""
	# TODO add deadends here?
	
	def __init__(self, floor, goals, boxes, player):
		self.floor = frozenset(floor)
		self.goals = frozenset(goals)
		self.initial_state = State(self, boxes, player)
	
	def replay(self, moves: List[Move]) -> State:
		""" Recreate state from list of moves applied to initial state.
		"""
		state = self.initial_state.copy()
		for i, move in enumerate(moves):
			assert state.can_move(move)
			state.move(move)
		return state
	

# TODO include all game state currently stored in the UI class, e.g. the redo
# redo stack, or searching for the next/previous unsolved level

class SokobanGame:
	"""Class representing the current state of the Sokoban game.
	
	This class encapsulates the entire level set, the current level, the current
	position of the player, and a list of the moves so far taken.
	"""
	
	def __init__(self, levels):
		self.levels = levels
		self.number = 0
		self.load_level()
		self.backup = None
		self.deadends = set()
		
	def load_level(self, number=None):
		"""Load level with given number from current level set.
		If no number is given, reload the current level.
		"""
		self.deadends = set()
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

	
	def __str__(self):
		return "SokobanGame(level: %d/%d, position: %r, progress: %r)" % \
				(self.number, len(self.levels), (self.r, self.c), self.progress)


