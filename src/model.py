# -*- coding: utf8 -*-

"""
Sokoban Game Model, by Tobias Kuester, 2014-2017, 2020

This modules provides classes encapsulating the current state of the Sokoban
game. The model provides basic functionality for movement and for pushing boxes.
Parsing and more sophisticated search and planning are in separate modules.
"""

from typing import List, NamedTuple


class Move(NamedTuple):
	""" Data Class representing a move. """
	dr: int
	dc: int
	push: bool = False

	def inv(self):
		return Move(-self.dr, -self.dc, self.push)


class Pos(NamedTuple):
	""" Data Class representing a Position. """
	r: int
	c: int

	def add(self, move: Move):
		return Pos(self.r + move.dr, self.c + move.dc)
	
	def dist(self, pos) -> int:
		return abs(self.r - pos.r) + abs(self.c - pos.c)


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
		self.redoable = []
		
	def copy(self):
		""" Create copy of this state, e.g. for making a savestate.
		"""
		return State(self.level, self.boxes, self.player, self.history)
	
	def is_free(self, pos: Pos) -> bool:
		""" Check whether given position is free.
		"""
		return pos not in self.level.walls and pos not in self.boxes
	
	def can_move(self, move: Move) -> bool:
		""" Check whether player can move to an adjacent location, with or 
		without being allowed to push a box.
		"""
		next_ = self.player.add(move)
		return (self.is_free(next_) or
				move.push and next_ in self.boxes and self.is_free(next_.add(move)))
	
	def move(self, move: Move, _clear_redo=True):
		""" Move to an adjacent location, after checking whether that move would 
		be legal, with or without being allowed to move a box.
		"""
		if self.can_move(move):
			self.player = self.player.add(move)
			push = self.player in self.boxes
			if push:
				self.boxes.remove(self.player)
				self.boxes.add(self.player.add(move))
			# add to history whether we _actually_ pushed a box
			self.history.append(Move(move.dr, move.dc, push))
			if _clear_redo:
				self.redoable = []
			return True
		else:
			return False
	
	def undo(self) -> Move:
		""" Undo last step from game's progress, moving the player to the
		previous position and "pulling" the crate, if previously pushed,
		back to the player's current position.
		"""
		if self.history:
			move = self.history.pop()
			if move.push:
				self.boxes.add(self.player)
				self.boxes.remove(self.player.add(move))
			self.player = self.player.add(move.inv())
			self.redoable.append(move)
			return move
	
	def redo(self):
		""" Redo previously undone move, if any.
		"""
		if self.redoable:
			self.move(self.redoable.pop(), _clear_redo=False)
	
	def is_solved(self) -> bool:
		""" Check whether all goal tiles have a box placed on them.
		"""
		return all(g in self.boxes for g in self.level.goals)
	

class Level:
	""" Class representing a Sokoban level, with valid floor positions, goals,
	and initial state.
	"""
	
	def __init__(self, walls, goals, boxes, player):
		self.walls = frozenset(walls)
		self.goals = frozenset(goals)
		self.size = Pos(max(r+1 for r, c in walls), max(c+1 for r, c in walls))
		self.deadends = set()
		self.initial_state = State(self, boxes, player)
	
	def replay(self, moves: List[Move]) -> State:
		""" Recreate state from list of moves applied to initial state.
		"""
		# TODO is this method actually still needed?
		state = self.initial_state.copy()
		for i, move in enumerate(moves):
			assert state.can_move(move)
			state.move(move)
		return state
	

class SokobanGame:
	"""Class representing the current state of the Sokoban game.
	"""
	
	def __init__(self, levels: List[Level]):
		self.levels = levels
		self.number = 0
		self.state = None
		self.snapshot = None
		self.load_level()
	
	def load_level(self, number=None):
		""" Load level with given number from current level set.
		If no number is given, reload the current level.
		"""
		if number is not None:
			self.number = number
			self.snapshot = None
		self.state = self.levels[self.number].initial_state.copy()

	def save_snapshot(self):
		""" Save snapshot of current state.
		"""
		self.snapshot = self.state.copy()
	
	def load_snapshot(self):
		""" Restore snapshot of current state, if present.
		"""
		if self.snapshot:
			self.state = self.snapshot.copy()
