"""
Logseq Assets Analysis Module.
"""

import re
from typing import TYPE_CHECKING

import logseq_analyzer.utils.patterns_content as ContentPatterns

from ..utils.enums import Criteria, Output
from ..utils.helpers import singleton

if TYPE_CHECKING:
    from ..logseq_file.file import LogseqFile
    from .index import FileIndex


__all__ = [
    "LogseqAssets",
    "LogseqAssetsHls",
]


@singleton
class LogseqAssets:
    """Class to handle assets in Logseq."""

    __slots__ = ("backlinked", "not_backlinked")

    def __init__(self) -> None:
        """Initialize the LogseqAssets instance."""
        self.backlinked: set[LogseqFile] = set()
        self.not_backlinked: set[LogseqFile] = set()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqAssets instance."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqAssets instance."""
        return f"{self.__class__.__qualname__}"

    def process(self, index: "FileIndex") -> None:
        """Handle assets for the Logseq Analyzer."""
        asset_mentions = set()
        for file in index:
            if not file.data:
                continue

            for criteria in (Criteria.EMB_LINK_ASSET, Criteria.CON_ASSETS):
                asset_mentions.update(file.data.get(criteria.value, []))

            if not asset_mentions:
                continue

            for asset_file in index.filter_files(file_type="asset", backlinked=False):
                asset_file.update_asset_backlink(asset_mentions, file.filename.name)

            asset_mentions.clear()
        del asset_mentions

        self.backlinked.update(sorted(index.filter_files(file_type="asset", backlinked=True)))
        self.not_backlinked.update(sorted(index.filter_files(file_type="asset", backlinked=False)))

    @property
    def report(self) -> str:
        """Generate a report of the asset analysis."""
        return {
            Output.ASSETS_BACKLINKED.value: self.backlinked,
            Output.ASSETS_NOT_BACKLINKED.value: self.not_backlinked,
        }


@singleton
class LogseqAssetsHls:
    """Class to handle HLS assets in Logseq."""

    __slots__ = (
        "asset_mapping",
        "asset_names",
        "backlinked",
        "hls_bullets",
        "not_backlinked",
    )

    def __init__(self) -> None:
        """Initialize the LogseqAssetsHls instance."""
        self.asset_mapping: dict[str, "LogseqFile"] = {}
        self.asset_names: set[str] = set()
        self.backlinked: set[str] = set()
        self.hls_bullets: set[str] = set()
        self.not_backlinked: set[str] = set()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqAssetsHls instance."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqAssetsHls instance."""
        return f"{self.__class__.__qualname__}"

    def process(self, index: "FileIndex") -> None:
        """Process HLS assets to analyze backlinks and bullet content."""
        self.get_asset_files(index)
        self.convert_names_to_data(index)
        self.check_backlinks()

    def get_asset_files(self, index: "FileIndex") -> None:
        """Retrieve asset files based on specific criteria."""
        asset_files = index.filter_files(file_type="sub_asset")
        self.asset_mapping = {f.filename.name: f for f in asset_files}
        self.asset_names.update(self.asset_mapping.keys())

    def convert_names_to_data(
        self, index: "FileIndex", prop_value_pattern: re.Pattern = ContentPatterns.PROPERTY_VALUE
    ) -> None:
        """Convert a list of names to a dictionary of hashes and their corresponding files."""
        for file in index.filter_files(is_hls=True):
            for bullet in file.bullets.content_bullets:
                bullet = bullet.strip()
                if not bullet.startswith("[:span]"):
                    continue
                hl_page, id_bullet, hl_stamp = "", "", ""
                for prop_value in prop_value_pattern.finditer(bullet):
                    propkey = prop_value.group(1)
                    value = prop_value.group(2).strip()
                    match propkey:
                        case "hl-page":
                            hl_page = value
                        case "id":
                            id_bullet = value
                        case "hl-stamp":
                            hl_stamp = value
                        case _:
                            continue
                if all((hl_page, id_bullet, hl_stamp)):
                    self.hls_bullets.add(f"{hl_page}_{id_bullet}_{hl_stamp}")

    def check_backlinks(self) -> None:
        """Check for backlinks in the HLS assets."""
        self.backlinked = self.asset_names.intersection(self.hls_bullets)
        self.not_backlinked = self.asset_names.difference(self.hls_bullets)
        for name in self.backlinked:
            self.asset_mapping[name].node.backlinked = True
            self.asset_mapping[name].filename.file_type = "asset"
        for name in self.not_backlinked:
            self.asset_mapping[name].filename.file_type = "asset"

    @property
    def report(self) -> str:
        """Generate a report of the asset analysis."""
        return {
            Output.HLS_ASSET_MAPPING.value: self.asset_mapping,
            Output.HLS_ASSET_NAMES.value: self.asset_names,
            Output.HLS_FORMATTED_BULLETS.value: self.hls_bullets,
            Output.HLS_NOT_BACKLINKED.value: self.not_backlinked,
            Output.HLS_BACKLINKED.value: self.backlinked,
        }
