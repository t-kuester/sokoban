# -*- coding: utf8 -*-

"""
Sokoban Solver, by Tobias Küster, 2020

This module provides a very simple solver for the Sokoban game based on the
game model and basic search- and planning-functions in the other modules.
It is not very fast, but finds solutions for small levels with few boxes.
"""

from typing import Optional, List, Tuple, Set, FrozenSet

from collections import deque
from itertools import count
from heapq import heappush, heappop
import time

from search import find_deadends, reachable, plan_push, find_path, MOVES
from model import State, Pos, Move


# much faster by pruning many more states, but might miss best state
USE_FF = False


def fingerprint(state: State) -> Tuple[FrozenSet[Pos], Pos]:
	""" Create a hashable "fingerprint" of the state; depending on the value of
	USE_FF, this will just getthe boxes and player-position, or consider all
	states where the player is in the same "area" of reachable states the same
	"""
	return (frozenset(state.boxes),
	        min(reachable(state)) if USE_FF else state.player)


def solveable(state: State) -> bool:
	""" Check whether a state is still solveable, i.e. no boxes are in deadends
	(a state may still be unsolveable even if this functions returns true)
	"""
	return not any(box in state.level.deadends for box in state.boxes)	


def solve(state: State) -> Optional[List[Move]]:
	""" Try to solve the given state and return the sequence of moves to get to
	a solved state, if such sequence exists. If the state can be solved, this
	will eventually find the solution, but the algorithm is not very fast.
	Also, if the USE_FF flag is set, it may not always return the best solution.
	"""
	start = time.time()
	state.level.deadends = find_deadends(state.level)
	
	c = count()
	i = count()
	seen = set()
	heap = [(0, next(c), state, [])]
	while heap:
		_, _, state, path = heappop(heap)
		print(next(i), path_to_str(path))
		
		f = fingerprint(state)
		if f in seen:
			continue
		seen.add(f)
		
		if state.is_solved():
			print(next(c), len(heap), len(seen), time.time() - start)
			return path
			
		for box in state.boxes:
			for pos2 in map(box.add, MOVES):
				
				if state.is_free(pos2) and pos2 not in state.level.deadends:
					p = plan_push(state, box, pos2)
					if p is not None:
						state2 = state.copy()
						for m in p:
							state2.move(m)
						p2 = path + p
						heappush(heap, (len(p2), next(c), state2, p2))
	# no path found to solve the level
	return None
		

DIRECTIONS_INV = {(0, +1, 1): "R", (0, -1, 1): "L", (-1, 0, 1): "U", (+1, 0, 1): "D",
                  (0, +1, 0): "r", (0, -1, 0): "l", (-1, 0, 0): "u", (+1, 0, 0): "d"}

def path_to_str(path):
	return ''.join(DIRECTIONS_INV[tuple(m)] for m in path)
	
	
def main():
	""" for testing / profiling """
	import os, sys
	from parser import load_levels, load_level
	from model import SokobanGame
	filename = "microban.txt"
	level = int(sys.argv[1]) if len(sys.argv) > 1 else 1
	config_dir = os.path.join(os.environ["HOME"], ".config", "t-kuester", "sokoban")
	levels = load_levels(os.path.join(config_dir, filename))
	game = SokobanGame(filename, levels, [0] * 155)
	game.load_level(level)
	print(path_to_str(solve(game.state) or []))


if __name__ == "__main__":
	main()
