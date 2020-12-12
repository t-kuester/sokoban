from typing import Optional, List, Tuple, Set

from collections import deque
from itertools import count
from heapq import heappush, heappop


from search import find_deadends, plan_push, MOVES
from model import State, Pos, Move

# TODO 
# - cleanup, documentation, etc.
# - use heapq for shortest paths, using path-length as key
#   - but with "fingerprint" shortest might get pruned
# - add flag "fast" vs "thorough" whether to use fingerprint or not
# - run through profiler (also for push-plan optimization)



DIRECTIONS_INV = {(0, +1, 1): "R", (0, -1, 1): "L", (-1, 0, 1): "U", (+1, 0, 1): "D",
                  (0, +1, 0): "r", (0, -1, 0): "l", (-1, 0, 0): "u", (+1, 0, 0): "d"}


# much faster by pruning many more states, but might miss best state
USE_FF = True

def reachable(state: State) -> Set[Pos]:
	# flood-fill to get reference position for player
	seen = set()
	queue = deque([state.player])
	while queue:
		pos = queue.popleft()
		if pos not in seen:
			seen.add(pos)
			queue.extend(pos2 for pos2 in map(pos.add, MOVES) if state.is_free(pos2))
	return seen

def fingerprint(state: State) -> Tuple[Set[Pos], Pos]:
	return (frozenset(state.boxes),
	        min(reachable(state)) if USE_FF else state.player)


def solveable(state: State) -> bool:
	return not any(box in state.level.deadends for box in state.boxes)	


def solve(state: State) -> Optional[List[Move]]:
	
	state.level.deadends = find_deadends(state.level)
	
	c = count()
	seen = set()
	heap = [(0, next(c), state, [])]
	while heap:
		_, _, state, path = heappop(heap)
		
		f = fingerprint(state)
		print(f, path_to_str(path))
		if f in seen:
			continue
			
		if not solveable(state):
			continue
		seen.add(f)
		
		if state.is_solved():
			print(next(c), len(heap), len(seen))
			return path
			
		for box in state.boxes:
			for pos2 in map(box.add, MOVES):
				
				if state.is_free(pos2) and pos2 not in state.level.deadends:
					p = plan_push(state, box, pos2)
					if p:
						state2 = state.copy()
						for m in p:
							state2.move(m)
						p2 = path + p
						heappush(heap, (len(p2), next(c), state2, p2))
		

def path_to_str(path):
	return ''.join(DIRECTIONS_INV[tuple(m)] for m in path)
	
	
def main():
	""" for testing / profiling """
	import os
	from parser import load_levels, load_level
	from model import SokobanGame
	filename = "microban.txt"
	level = 0
	config_dir = os.path.join(os.environ["HOME"], ".config", "t-kuester", "sokoban")
	levels = load_levels(os.path.join(config_dir, filename))
	game = SokobanGame(filename, levels, [0] * 155)
	game.load_level(level)
	print(path_to_str(solve(game.state) or []))


if __name__ == "__main__":
	main()
