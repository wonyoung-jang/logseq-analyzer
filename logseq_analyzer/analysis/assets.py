"""
Logseq Assets Analysis Module.
"""

import re
from typing import TYPE_CHECKING, Generator

import logseq_analyzer.utils.patterns_content as ContentPatterns

from ..utils.enums import Criteria, FileTypes, Output
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

    _ASSET_CRITERIA: frozenset[Criteria] = frozenset({Criteria.EMB_LINK_ASSET, Criteria.CON_ASSETS})

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

        for f in index:
            for criteria in LogseqAssets._ASSET_CRITERIA:
                asset_mentions.update(f.data.get(criteria.value, []))

            if not asset_mentions:
                continue

            for asset_file in LogseqAssets.yield_assets(index, backlinked=False):
                asset_file.node.update_asset_backlink(asset_mentions, (asset_file.name, f.name))

            asset_mentions.clear()

        del asset_mentions

        self.backlinked.update(LogseqAssets.yield_assets(index, backlinked=True))
        self.not_backlinked.update(LogseqAssets.yield_assets(index, backlinked=False))

    @staticmethod
    def yield_assets(index: "FileIndex", backlinked: bool | None = None) -> Generator["LogseqFile", None]:
        """Yield all asset files from the index."""
        for f in index:
            if f.file_type == FileTypes.ASSET.value:
                if backlinked is None:
                    yield f
                elif f.backlinked == backlinked:
                    yield f

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
        "backlinked",
        "hls_bullets",
        "not_backlinked",
    )

    def __init__(self) -> None:
        """Initialize the LogseqAssetsHls instance."""
        self.asset_mapping: dict[str, "LogseqFile"] = {}
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
        if self.asset_mapping:
            self.convert_names_to_data(index)
            self.check_backlinks()

    def get_asset_files(self, index: "FileIndex") -> None:
        """Retrieve asset files based on specific criteria."""
        asset_files = (f for f in index if f.file_type == FileTypes.SUB_ASSET.value)
        self.asset_mapping = {f.name: f for f in asset_files}

    def convert_names_to_data(
        self, index: "FileIndex", prop_value_pattern: re.Pattern = ContentPatterns.PROPERTY_VALUE
    ) -> None:
        """Convert a list of names to a dictionary of hashes and their corresponding files."""
        for f in (fh for fh in index if fh.is_hls):
            for bullet in f.bullets.all:
                bullet = bullet.strip()
                if not bullet.startswith("[:span]"):
                    continue
                hl_page, id_, hl_stamp = "", "", ""
                for prop_value in prop_value_pattern.finditer(bullet):
                    propkey = prop_value.group(1)
                    value = prop_value.group(2).strip()
                    match propkey:
                        case "hl-page":
                            hl_page = value
                        case "id":
                            id_ = value
                        case "hl-stamp":
                            hl_stamp = value
                        case _:
                            continue
                if all((hl_page, id_, hl_stamp)):
                    hls_bullet = f"{hl_page}_{id_}_{hl_stamp}"
                    self.hls_bullets.add(hls_bullet)

    def check_backlinks(self) -> None:
        """Check for backlinks in the HLS assets."""
        asset_names = set(self.asset_mapping.keys())
        self.backlinked = asset_names.intersection(self.hls_bullets)
        self.not_backlinked = asset_names.difference(self.hls_bullets)
        for name in self.backlinked:
            self.asset_mapping[name].node.backlinked = True
            self.asset_mapping[name].path.file_type = "asset"
        for name in self.not_backlinked:
            self.asset_mapping[name].path.file_type = "asset"

    @property
    def report(self) -> str:
        """Generate a report of the asset analysis."""
        return {
            Output.HLS_ASSET_MAPPING.value: self.asset_mapping,
            Output.HLS_FORMATTED_BULLETS.value: self.hls_bullets,
            Output.HLS_NOT_BACKLINKED.value: self.not_backlinked,
            Output.HLS_BACKLINKED.value: self.backlinked,
        }
