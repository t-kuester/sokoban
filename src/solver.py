from typing import Optional, List, Tuple, Set

from collections import deque


from search import find_deadends, plan_push, MOVES
from model import State, Pos, Move

DIRECTIONS_INV = {(0, +1, 1): "R", (0, -1, 1): "L", (-1, 0, 1): "U", (+1, 0, 1): "D",
                  (0, +1, 0): "r", (0, -1, 0): "l", (-1, 0, 0): "u", (+1, 0, 0): "d"}


def fingerprint(state: State) -> Tuple[Set[Pos], Pos]:
	# flood-fill to get reference position for player
	seen = set()
	queue = deque([state.player])
	while queue:
		pos = queue.popleft()
		if pos not in seen:
			seen.add(pos)
			queue.extend(pos2 for pos2 in map(pos.add, MOVES) if state.is_free(pos2))
	# only consider player reference position and boxes
	return (frozenset(state.boxes), min(seen))


def solveable(state: State) -> bool:
	return not any(box in state.level.deadends for box in state.boxes)	


def solve(state: State) -> Optional[List[Move]]:
	
	state.level.deadends = find_deadends(state.level)
	
	seen = set()
	queue = deque([(state, [])])
	iters = 0
	while queue:
		state, path = queue.popleft()
		iters += 1
		
		f = fingerprint(state)
		print(f, path_to_str(path))
		if f in seen:
			continue
			
		if not solveable(state):
			continue
		seen.add(f)
		
		if state.is_solved():
			print("FOUND", path_to_str(path))
			print(iters, len(queue), len(seen))
			return path
			
		for box in state.boxes:
			for move in MOVES:
				pos2 = box.add(move)
				
				if state.is_free(pos2) and pos2 not in state.level.deadends:
					p = plan_push(state, box, pos2)
					if p:
						state2 = state.copy()
						for m in p:
							state2.move(m)
						queue.append((state2, path + p))
				
	
	print("NOTHING FOUND")
		

def path_to_str(path):
	return ''.join(DIRECTIONS_INV[tuple(m)] for m in path)
	
	
	
	
