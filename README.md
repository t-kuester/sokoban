Sokoban
=======

_2015-2017, Tobias Küster_

Just my version of the classic Sokoban puzzle. Initially, this was just one among
many little entries in my `games` repository, but I like this one quite a bit (in
fact more than other, more professional versions of the game I've played so far)
and thus decided to move this to it's own repo and give it a bit more polish.

It has a super-minimalistic UI, but it can read arbitrary Sokoban level files and
keep a record of what level has been solved in how many moves. Also, it featurse
some amount of "planning", not only for finding the path to a certain location, 
but also for planning the "push-path" for moving a single crate to a new location.
This does not make the puzzles any easier, but it makes the game much less tedious
to play and more fun. Also features basic undo and snapshot-taking. Levels are not
included, but plenty can be found on the internet.

Features:
* load Sokoban levels in standard sokoban level file format
* save progress (solved/unsolved, number of turns) for each level in JSON file
* controls with arrow-keys or with mouse
* save/restore snapshot of current level, undo/redo-stack
* path-planning for movement and push-planning for pushing single boxes


Game Start and Loading Level Files
----------------------------------

TODO


Game Controls
-------------

UI Symbols:
* blue dot: player
* green circle: target for box
* yellow box: a regular box
* blue box: box selected for push-planning
* dark-gray boxes: walls/obstacles

Status Line Format:
* current Level
* solved / total number of levels in current level set
* number of steps used so far
* best number of steps used for this level
* last 30 moves (u/l/r/r; upper-case means pushed)

Keyboard-Controls:
* Arrow Keys: Move/Push
* Shift + Arrow Keys: Move until next obstacle
* PgUp / PgDn: Next/Previous Level
* Shift + PgUp / PgDn: Next/Previous unsolved Level (if any)
* R: reload level
* S / L: save or load single snapshot (lost when switching the level)
* D: show deadends
* Z / Y: undo/redo last moves
* Q: quit

Mouse-Controls:
* Click on ground: Move player to that position, if possible (right-click: skip animation)
* Click on box: select box for push-planning
* Click on ground with selected box: Move box to that position, if possible (right-click: skip animation)
* Mouse Wheel up/down: undo/redo last moves


Planning
--------

TODO
