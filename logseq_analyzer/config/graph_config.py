"""
Logseq Graph Class
"""

from typing import Any

from ..io.filesystem import ConfigFile, GlobalConfigFile
from ..utils.helpers import singleton
from .edn_parser import loads


@singleton
class LogseqGraphConfig:
    """
    A class to LogseqGraphConfig.
    """

    def __init__(self) -> None:
        """Initialize the LogseqGraphConfig class."""
        self.config_merged: dict[str, Any] = {}
        self.config_user: dict[str, Any] = {}
        self.config_global: dict[str, Any] = {}

    def initialize_user_config_edn(self, cf: ConfigFile) -> None:
        """
        Extract user config.

        Args:
            cf (ConfigFile): The config file object.
        """
        with cf.path.open("r", encoding="utf-8") as user_config:
            self.config_user = loads(user_config.read())

    def initialize_global_config_edn(self, gcf: GlobalConfigFile) -> None:
        """
        Extract global config.

        Args:
            gcf (GlobalConfigFile): The global config file object.
        """
        with gcf.path.open("r", encoding="utf-8") as global_config:
            self.config_global = loads(global_config.read())

    def merge(self) -> dict[str, Any]:
        """
        Merge user and global config.

        Returns:
            dict: Merged configuration.
        """
        config = _get_default_logseq_config_edn()
        config.update(self.config_user)
        config.update(self.config_global)
        return config


def _get_default_logseq_config_edn() -> dict[str, Any]:
    """
    Get the default Logseq configuration in EDN format.

    Returns:
        dict[str, Any]: Default Logseq configuration in EDN format.
    """
    return {
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
