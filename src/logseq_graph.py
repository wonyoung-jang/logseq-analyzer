"""
LogseqGraph class to represent a graph of Logseq files.
This class allows for the addition of nodes, which are instances of LogseqFile.
"""

from src.logseq_file import LogseqFile


class LogseqGraph:
    def __init__(self):
        self.graph = {}
        self.nodes = set()

    def add_node(self, logseq_file: LogseqFile):
        name = logseq_file.name
        name_secondary = logseq_file.name_secondary
        self.nodes.add(name)
        if name in self.graph:
            self.graph[name_secondary] = logseq_file
        else:
            self.graph[name] = logseq_file
