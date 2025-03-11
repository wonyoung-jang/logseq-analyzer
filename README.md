# Logseq Analyzer

Simple utility to analyze a Logseq graph for basic information to assist with the upcoming database version.

![Logseq Analyzer's GUI](/images/Logseq%20Analyzer%20Main.png?)

> [!WARNING]  
> Only supports Markdown (.md) graphs.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [About](#about)
- [License](#license) 

## Installation 

- Ensure Python 3 is installed

- If using the GUI, ensure PySide6 is installed and install requirements with:

`pip install -r requirements.txt`

## Usage

- To run: `python main.py -g path_to_your_graph_folder`

- For help: `python main.py -h`

- For a simple GUI (WIP): `python gui.py`

### Useful flags

- `-ma` or `--move-unlinked-assets` will move unlinked assets out of your graph to this projects folder for review.

- `-mb` or `--move-bak` will move the contents of Logseq's `logseq/bak` folder similar to above

- `-mr` or `--move-recycle` same thing as the above but with `logseq/.recycle`

## About

### Graphs, backlinks, and orphans

Logseq currenty runs with two definitions of an "Orphan" page.
1. The `All pages` view: Page that is not backlinked and has no content
2. The `Graph` view: Page that is not backlinked and has no backlinks

Anybody with a sizeable number of pages will tell you that the Graph view in Logseq becomes unwieldly very quickly. While the All pages orphans can be removed with the "Remove orphaned pages?" action from `All pages`, the Graph orphans are only accessible via the `Graph` view. The Graph orphans may contain lots of content, but since they aren't don't link to or from anything, they have high chance of not surfacing again. This analyzer will show each type of orphan in the graph for further review.

Note: While Logseq doesn't count namespace hierarchies as backlinks, this program does, as it reflects how the Graph view interprets backlinks, otherwise many pages may potentially be considered orphans, depending on the complexity of some namespaces.

### Upcoming database version and namespaces

Read more here: https://github.com/logseq/db-test/issues/7

Essentially two issues arise:
1. The split namespace parts may conflict with existing, non-namespace pages
2. Some parents may appear across multiple namespaces at different depths

This analyzer will output all conflicts for review in the `/namespace` output folder.

### Outputs

Text files with information in the default `output` folder.

### Definitions

- **True Orphans** - Not backlinked, has no backlinks, and has no content. 
- **Graph Orphans** - Not backlinked, and has no backlinks.
- **Leaf Node** - Backlinked, and has no backlinks.
- **Root Node** - Not backlinked, and has backlinks.
- **Branch Node** - Backlinked, and has backlinks.
- **Dangling Link** - Backlinked, and does not exist as a file in the system.

#### A table of the above definitions for clarity
| Node Type        | Backlinked ✅ | Has Backlinks ✅ | Has Content ✅ | Exists as File ✅ |
|-----------------|--------------|-----------------|--------------|----------------|
| **True Orphans**  | ❌           | ❌              | ❌           | ✅             |
| **Graph Orphans** | ❌           | ❌              | ✅           | ✅             |
| **Leaf Node**     | ✅           | ❌              | 🟡           | ✅             |
| **Root Node**     | ❌           | ✅              | ✅           | ✅             |
| **Branch Node**   | ✅           | ✅              | ✅           | ✅             |
| **Dangling Link** | ✅           | ❌              | ❌           | ❌             |

## License
[MIT License](LICENSE)
