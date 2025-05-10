"""
Logseq Graph Class
"""

from typing import Any, Dict

from logseq_analyzer.io.filesystem import ConfigFile, GlobalConfigFile
from logseq_analyzer.utils.helpers import singleton
from logseq_analyzer.config.arguments import Args
from logseq_analyzer.config.edn_parser import loads


@singleton
class LogseqGraphConfig:
    """
    A class to LogseqGraphConfig.
    """

    def __init__(self):
        """Initialize the LogseqGraphConfig class."""
        self.ls_config: Dict = {}
        self.user_config_data: Dict = {}
        self.global_config_data: Dict = {}

    def initialize_user_config_edn(self):
        """Extract user config."""
        user_config_file = ConfigFile()
        with user_config_file.path.open("r", encoding="utf-8") as user_config:
            self.user_config_data = loads(user_config.read())

    def initialize_global_config_edn(self):
        """Extract global config."""
        args = Args()
        if not args.global_config:
            return

        global_config_file = GlobalConfigFile()
        with global_config_file.path.open("r", encoding="utf-8") as global_config:
            self.global_config_data = loads(global_config.read())

    def merge(self):
        """Merge user and global config."""
        config = get_default_logseq_config_edn()
        config.update(self.user_config_data)
        config.update(self.global_config_data)
        self.ls_config = config


def get_default_logseq_config_edn() -> Dict[str, Any]:
    """
    Get the default Logseq configuration in EDN format.

    Returns:
        dict: Default Logseq configuration in EDN format.
    """
    config = {
        ":meta/version": 1,
        ":preferred-format": "Markdown",
        ":preferred-workflow": ":now",
        ":hidden": [],
        ":default-templates": {":journals": ""},
        ":journal/page-title-format": "MMM do, yyyy",
        ":journal/file-name-format": "yyyy_MM_dd",
        ":ui/enable-tooltip?": True,
        ":ui/show-brackets?": True,
        ":ui/show-full-blocks?": False,
        ":ui/auto-expand-block-refs?": True,
        ":feature/enable-block-timestamps?": False,
        ":feature/enable-search-remove-accents?": True,
        ":feature/enable-journals?": True,
        ":feature/enable-flashcards?": True,
        ":feature/enable-whiteboards?": True,
        ":feature/disable-scheduled-and-deadline-query?": False,
        ":scheduled/future-days": 7,
        ":start-of-week": 6,
        ":export/bullet-indentation": ":tab",
        ":publishing/all-pages-public?": False,
        ":pages-directory": "pages",
        ":journals-directory": "journals",
        ":whiteboards-directory": "whiteboards",
        ":shortcuts": {},
        ":shortcut/doc-mode-enter-for-new-block?": False,
        ":block/content-max-length": 10000,
        ":ui/show-command-doc?": True,
        ":ui/show-empty-bullets?": False,
        ":query/views": {":pprint": ["fn", ["r"], [":pre.code", ["pprint", "r"]]]},
        ":query/result-transforms": {
            ":sort-by-priority": [
                "fn",
                ["result"],
                ["sort-by", ["fn", ["h"], ["get", "h", ":block/priority", "Z"]], "result"],
            ]
        },
        ":default-queries": {
            ":journals": [
                {
                    ":title": "🔨 NOW",
                    ":query": [
                        ":find",
                        ["pull", "?h", ["*"]],
                        ":in",
                        "$",
                        "?start",
                        "?today",
                        ":where",
                        ["?h", ":block/marker", "?marker"],
                        [["contains?", {"NOW", "DOING"}, "?marker"]],
                        ["?h", ":block/page", "?p"],
                        ["?p", ":block/journal?", True],
                        ["?p", ":block/journal-day", "?d"],
                        [[">=", "?d", "?start"]],
                        [["<=", "?d", "?today"]],
                    ],
                    ":inputs": [":14d", ":today"],
                    ":result-transform": [
                        "fn",
                        ["result"],
                        [
                            "sort-by",
                            ["fn", ["h"], ["get", "h", ":block/priority", "Z"]],
                            "result",
                        ],
                    ],
                    ":group-by-page?": False,
                    ":collapsed?": False,
                },
                {
                    ":title": "📅 NEXT",
                    ":query": [
                        ":find",
                        ["pull", "?h", ["*"]],
                        ":in",
                        "$",
                        "?start",
                        "?next",
                        ":where",
                        ["?h", ":block/marker", "?marker"],
                        [["contains?", {"NOW", "LATER", "TODO"}, "?marker"]],
                        ["?h", ":block/page", "?p"],
                        ["?p", ":block/journal?", True],
                        ["?p", ":block/journal-day", "?d"],
                        [[">", "?d", "?start"]],
                        [["<", "?d", "?next"]],
                    ],
                    ":inputs": [":today", ":7d-after"],
                    ":group-by-page?": False,
                    ":collapsed?": False,
                },
            ]
        },
        ":commands": [],
        ":outliner/block-title-collapse-enabled?": False,
        ":macros": {},
        ":ref/default-open-blocks-level": 2,
        ":ref/linked-references-collapsed-threshold": 100,
        ":graph/settings": {
            ":orphan-pages?": True,
            ":builtin-pages?": False,
            ":excluded-pages?": False,
            ":journal?": False,
        },
        ":graph/forcesettings": {
            ":link-dist": 180,
            ":charge-strength": -600,
            ":charge-range": 600,
        },
        ":favorites": [],
        ":srs/learning-fraction": 0.5,
        ":srs/initial-interval": 4,
        ":property-pages/enabled?": True,
        ":editor/extra-codemirror-options": {
            ":lineWrapping": False,
            ":lineNumbers": True,
            ":readOnly": False,
        },
        ":editor/logical-outdenting?": False,
        ":editor/preferred-pasting-file?": False,
        ":dwim/settings": {
            ":admonition&src?": True,
            ":markup?": False,
            ":block-ref?": True,
            ":page-ref?": True,
            ":properties?": True,
            ":list?": False,
        },
        ":file/name-format": ":triple-lowbar",
    }
    return config
