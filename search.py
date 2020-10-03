import collections
import heapq

from sokoban import *


def find_path(state, start, goal):
	"""Try to find a path from start to goal in the given state. This is
	a more general version of SokobanGame.find_path, that can also be
	applied for "future" states in SokobanGame.plan_push.
	"""
	# initialize queue and set of visited states
	queue = collections.deque([(start, [])])
	visited = set()

	while queue:
		# pop state, check whether already visited or goal
		(r, c), path = queue.popleft()
		if (r, c) == goal:
			return path

		# expand neighbor states
		queue.extend(((r + dr, c + dc), path + [(dr, dc, False)])
				for dr, dc in DIRECTIONS
				if is_free(state[r + dr][c + dc]) and check_add(visited, (r+dr, c+dc)))


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


def plan_push(state, player, start, goal, deadends=None):
	"""Plan how to push box from start to goal position. Planning is
	done using A* planning, taking the players movements into account.
	We also have to keep track of the actual game state, updating
	the original state. Positioning of the player is done using the
	basic movement planning algorithm.
	"""
	# create copy of state, initialize queue and visited states
	original_state = tuplefy(state)
	g, h = 0, distance(start, goal)
	queue = [((g+h, h), start, player, [])]
	visited = set()

	while queue:
		# pop state, check whether already visited or goal state
		_, (r, c), pos, path = heapq.heappop(queue)

		if not check_add(visited, ((r, c), pos)):
			continue

		if (r, c) == goal:
			return path

		# update state with new player and box positions
		state = listify(original_state)
		set_state(state, player, FLOOR)
		set_state(state, start, FLOOR)
		set_state(state, (r, c), BOX)

		# expand neighbor states
		for dr, dc in DIRECTIONS:
			target = state[r + dr][c + dc]
			if (is_free(target) or is_player(target)) and (r+dr, c+dc) not in (deadends or []):
				positioning = find_path(state, pos, (r - dr, c - dc))
				if positioning is not None:
					new_pos = (r + dr, c + dc)
					g = len(path) + len(positioning) + 1
					h = distance(new_pos, goal)
					heapq.heappush(queue, ((g+h, h), new_pos, (r, c), path + positioning + [(dr, dc, True)]))
