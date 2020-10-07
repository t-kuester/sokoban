# -*- coding: utf8 -*-

"""
Sokoban Planning Algorithms, by Tobias Kuester, 2014-2017, 2020

This module provides the planning algorithms used in the Sokoban game, i.e.
everything that goes beyond simulating a simple move or push. Currently it
includes algorithms for finding the path to a certain position, for planning
how to push a box to a certain position, or for identifying "dead-end" positions
in a level. More might be added in the future.
"""

from typing import List
import collections
import heapq

from model import State, Pos, Move


MOVES   = [Move(dr, dc) for dr, dc in ((0, +1), (0, -1), (-1, 0), (+1, 0))]
MOVES_P = [Move(dr, dc, True) for dr, dc, _ in MOVES]


def find_path(state: State, goal: Pos) -> List[Move]:
	"""Try to find a path for the player to the goal in the given state.
	This is also used for the push-planning algorithm below for checking whether
	the player can be repositioned for attacking the box from a different side.
	This is using a simple Breadth First Search; I also tried A* some time ago
	(like for push-planning), but it was not any faster here.
	"""
	if not state.is_free(goal):
		return None
	
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


def find_deadends(level):
	"""Find all (most of) the "dead end" positions where block can not be
	moved out of again. Those position are then highlighted in the game
	and also prohibited from being visited by the push-planner, making it
	both more safe and (on some maps) a good deal faster.
	This does not automatically set SokobanGame.deadends, though.
	"""
	# find all goal tiles
	goals = [(r, c) for r, row in enumerate(level)
	                for c, sym in enumerate(row) if is_goal(sym)]

	# step 1: find reachable floor
	queue = collections.deque(goals)
	floor = set()
	while queue:
		(r, c) = queue.popleft()
		queue.extend((r+dr, c+dc) for dr, dc in DIRECTIONS
				if level[r+dr][c+dc] != WALL and check_add(floor, (r+dr, c+dc)))

	# step 2: find floor reachable with one buffer to next wall
	queue = collections.deque(goals)
	visited = set(goals)
	while queue:
		(r, c) = queue.popleft()
		for dr, dc in DIRECTIONS:
			if level[r+dr][c+dc] != WALL and level[r+2*dr][c+2*dc] != WALL and check_add(visited, (r+dr, c+dc)):
				queue.append((r+dr, c+dc))

	# difference of the above are the dead-ends and forbidden areas
	return floor - visited


def plan_push(state: State, start: Pos, goal: Pos, deadends=None):
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
		# TODO only temporarily apply the changes, then revert?
		state2 = State(state.level, state.boxes - {start} | {box}, player)
		for m in MOVES_P:
			box2 = box.add(m)
			if state2.is_free(box2) and (box2 not in (deadends or [])):
				positioning = find_path(state2, box.add(m.inv()))
				if positioning is not None:
					path2 = path + positioning + [m]
					heapq.heappush(queue, (len(path2) + box2.dist(goal), box2, box, path2))
