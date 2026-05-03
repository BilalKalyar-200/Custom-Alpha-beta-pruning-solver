# ⬡ Alpha-Beta Minimax Simulator

A desktop application for visualizing and exploring the **Alpha-Beta Pruning** algorithm on Minimax game trees. Built with Python and Tkinter.

---

## Features

- **Interactive tree visualization** — see the full game tree rendered on a scrollable, zoomable canvas
- **Step-by-step walkthrough** — advance through the algorithm one step at a time with explanations in the log panel
- **Instant result mode** — run the full algorithm at once and see the optimal value highlighted
- **Live node editor** — click any node to edit its value, add/remove children, or flip MAX/MIN type
- **Alpha-Beta pruning display** — pruned subtrees are visually marked and crossed out
- **Best path highlighting** — the optimal decision path is highlighted in amber after evaluation
- **Color-coded node states** — active, evaluated, pruned, and best-path nodes each have distinct colors

---

## Requirements

- Python 3.7+
- Tkinter (included with most Python distributions)

No additional packages are required.

---

## Running the App

```bash
python minimax.py
```

The window launches maximized and is ready to use immediately.

---

## UI Overview

### Top Bar

| Control | Description |
|--------|-------------|
| **Depth** | Tree depth (1–4) |
| **Branch** | Number of children per internal node (2–5) |
| **Root** | Whether the root node is MAX or MIN |
| **🌲 New Tree** | Generate a fresh random tree with the current settings |
| **🎲 Randomize** | Randomize leaf values without changing the tree structure |
| **↺ Reset** | Clear algorithm state and return to the initial tree view |
| **⚡ Show Result** | Run the full algorithm instantly and display the result |
| **▶ Step by Step** | Enter step-by-step mode; use Prev/Next to navigate |

### Canvas (Center)

- **Scroll** — mouse wheel to scroll vertically
- **Zoom** — `Ctrl + mouse wheel` to zoom in/out
- **Pan** — middle-click and drag
- **Click a node** — select it and open the Node Editor in the right panel
- **`+` / `−` buttons** beside nodes — add or remove child nodes

### Right Panel

- **Step Log** — shows messages for each algorithm step
- **Prev / Next** — navigate steps in step-by-step mode
- **Node Editor** — edit leaf values via text input or slider; add/remove children on internal nodes; flip MAX/MIN assignment
- **Legend** — color reference for all node states

---

## Node Colors

| Color | Meaning |
|-------|---------|
| 🔵 Blue | MAX node (idle) |
| 🔴 Red | MIN node (idle) |
| 🟢 Green | Leaf node (idle) |
| 🟡 Amber | Best path node |
| 🟣 Purple | Currently active node |
| ⬜ Gray | Pruned (not explored) |
| 💚 Bright green | Evaluated node |

---

## How Alpha-Beta Pruning Works

The Minimax algorithm explores a game tree to find the optimal move for a player, assuming the opponent also plays optimally. **Alpha-Beta Pruning** improves efficiency by skipping subtrees that cannot affect the final decision:

- **α (alpha)** — the best value the MAX player is guaranteed so far
- **β (beta)** — the best value the MIN player is guaranteed so far
- A **cutoff** occurs when `β ≤ α`, meaning the current branch cannot improve the outcome for either player

This simulator makes the process concrete by walking through each visit, update, and cutoff event visually.

---

## Project Structure

```
minimax.py        # Single-file application
```

All logic, UI, and rendering are contained in one file, organized into these sections:

- **Color Theme** — all UI color constants
- **Node class** — tree node with algorithm state fields
- **`build_tree()`** — generates a random game tree
- **`generate_steps()`** — runs alpha-beta and records every event as a list of steps
- **`App` class** — main Tkinter application (UI, drawing, interaction, editor, log)

---

## Customization

- Leaf values range from −9 to 9 by default (editable via the Node Editor or slider up to ±20)
- Tree depth up to 4 levels and branching factor up to 5 are supported via the UI
- Colors can be changed by editing the constants at the top of the file

---

## License

This project is provided as-is for educational purposes.
