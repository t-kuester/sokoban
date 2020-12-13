# -*- coding: utf8 -*-

"""
Sokoban Planning Algorithms, by Tobias Kuester, 2014-2017, 2020

This module provides the planning algorithms used in the Sokoban game, i.e.
everything that goes beyond simulating a simple move or push. Currently it
includes algorithms for finding the path to a certain position, for planning
how to push a box to a certain position, or for identifying "dead-end" positions
in a level. More might be added in the future.
"""

from typing import List, Set, Optional
import collections
import heapq

from model import State, Level, Pos, Move


MOVES   = [Move(dr, dc) for dr, dc in ((0, +1), (0, -1), (-1, 0), (+1, 0))]
MOVES_P = [Move(dr, dc, True) for dr, dc, _ in MOVES]


def reachable(state: State) -> Set[Pos]:
	""" Flood-fill to get all cells reachable by player in the current state
	without pushing any box.
	"""
	seen = set()
	queue = collections.deque([state.player])
	while queue:
		pos = queue.popleft()
		if pos not in seen:
			seen.add(pos)
			queue.extend(pos2 for pos2 in map(pos.add, MOVES) if state.is_free(pos2))
	return seen


def find_path(state: State, goal: Pos) -> Optional[List[Move]]:
	"""Try to find a path for the player to the goal in the given state.
	This is also used for the push-planning algorithm below for checking whether
	the player can be repositioned for attacking the box from a different side.
	This is using a simple Breadth First Search; I also tried A* some time ago
	(like for push-planning), but it was not any faster here.
	"""
	if not state.is_free(goal):
		return None
	if state.player == goal:
		return []
	
	queue = collections.deque([(state.player, [])])
	visited = set()

	while queue:
		p, path = queue.popleft()
		if p == goal:
			return path

		for m in MOVES:
			p2 = p.add(m)
			if state.is_free(p2) and p2 not in visited:
				queue.append((p2, path + [m]))
				visited.add(p2)


def find_deadends(level: Level) -> Set[Pos]:
	"""Find all (most of) the "dead end" positions where block can not be
	moved out of again. Those position are then highlighted in the game
	and also prohibited from being visited by the push-planner, making it
	both more safe and (on some maps) a good deal faster.
	"""
	# step 1: find reachable floor
	queue = collections.deque(level.goals)
	floor = set()
	while queue:
		p = queue.popleft()
		if p not in floor:
			floor.add(p)
			queue.extend(p2 for m, p2 in ((m, p.add(m)) for m in MOVES)
			                if p2 not in level.walls)

	# step 2: find floor reachable with one buffer to next wall
	queue = collections.deque(level.goals)
	visited = set()
	while queue:
		p = queue.popleft()
		if p not in visited:
			visited.add(p)
			queue.extend(p2 for m, p2 in ((m, p.add(m)) for m in MOVES)
			                if p2 not in level.walls and p2.add(m) not in level.walls)

	# difference of the above are the dead-ends and forbidden areas
	return floor - visited


def plan_push(state: State, start: Pos, goal: Pos) -> Optional[List[Move]]:
	"""Plan how to push box from start to goal position. Planning is done using
	A* planning, taking the players movements into account. We also have to keep
	track of the actual game state, updating the original state. Positioning of
	the player is done using the basic movement planning algorithm.
	"""
	queue = [(start.dist(goal), start, state.player, [])]
	visited = set()

	while queue:
		_, box, player, path = heapq.heappop(queue)
		if box == goal:
			return path

		if (box, player) in visited:
			continue
		visited.add((box, player))

		# update state with new player and box positions, expand neighbor states
		# (temporarily modifying the original state is _not_ faster, I tried)
		state2 = State(state.level, state.boxes - {start} | {box}, player)
		for m in MOVES_P:
			box2 = box.add(m)
			if state2.is_free(box2) and box2 not in state.level.deadends:
				positioning = find_path(state2, box.add(m.inv()))
				if positioning is not None:
					path2 = path + positioning + [m]
					heapq.heappush(queue, (len(path2) + box2.dist(goal), box2, box, path2))
