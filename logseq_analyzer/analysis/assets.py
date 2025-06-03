"""
Logseq Assets Analysis Module.
"""

from typing import Generator

import logseq_analyzer.patterns.content as ContentPatterns

from ..logseq_file.file import LogseqFile
from ..utils.enums import Criteria, FileTypes, Output
from .index import FileIndex

__all__ = [
    "LogseqAssets",
    "LogseqAssetsHls",
]


class LogseqAssets:
    """Class to handle assets in Logseq."""

    __slots__ = ("backlinked", "not_backlinked")

    _ASSET_CRITERIA: frozenset[Criteria] = frozenset({Criteria.EMB_LINK_ASSET.value, Criteria.CON_ASSETS.value})

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

    def process(self, index: FileIndex) -> None:
        """Handle assets for the Logseq Analyzer."""
        asset_mentions = set()
        update_mentions = asset_mentions.update
        clear_mentions = asset_mentions.clear
        asset_criteria = LogseqAssets._ASSET_CRITERIA
        yield_assets = LogseqAssets.yield_assets

        for f in index:
            if not (f_data := f.data):
                continue

            get_data = f_data.get
            for criteria in asset_criteria:
                update_mentions(get_data(criteria, []))

            if not asset_mentions:
                continue

            f_name = f.name
            for asset_file in yield_assets(index, backlinked=False):
                asset_file.node.update_asset_backlink(asset_mentions, (asset_file.name, f_name))

            clear_mentions()

        del asset_mentions

        self.backlinked.update(yield_assets(index, backlinked=True))
        self.not_backlinked.update(yield_assets(index, backlinked=False))

    @staticmethod
    def yield_assets(index: FileIndex, backlinked: bool | None = None) -> Generator[LogseqFile, None]:
        """Yield all asset files from the index."""
        asset_file_type = FileTypes.ASSET.value
        for f in (f for f in index if f.path.file_type == asset_file_type):
            if backlinked is None:
                yield f
            if f.node.backlinked is backlinked:
                yield f

    @property
    def report(self) -> str:
        """Generate a report of the asset analysis."""
        return {
            Output.ASSETS_BACKLINKED.value: self.backlinked,
            Output.ASSETS_NOT_BACKLINKED.value: self.not_backlinked,
        }


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
        self.asset_mapping: dict[str, LogseqFile] = {}
        self.backlinked: set[str] = set()
        self.hls_bullets: set[str] = set()
        self.not_backlinked: set[str] = set()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqAssetsHls instance."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqAssetsHls instance."""
        return f"{self.__class__.__qualname__}"

    def process(self, index: FileIndex) -> None:
        """Process HLS assets to analyze backlinks and bullet content."""
        self.get_asset_files(index)
        if self.asset_mapping:
            self.convert_names_to_data(index)
            self.check_backlinks()

    def get_asset_files(self, index: FileIndex) -> None:
        """Retrieve asset files based on specific criteria."""
        sub_asset_file_type = FileTypes.SUB_ASSET.value
        asset_files = (f for f in index if f.path.file_type == sub_asset_file_type)
        self.asset_mapping = {f.name: f for f in asset_files}

    def convert_names_to_data(self, index: FileIndex) -> None:
        """Convert a list of names to a dictionary of hashes and their corresponding files."""
        find_prop_value_pattern = ContentPatterns.PROPERTY_VALUE.finditer
        for f in (fh for fh in index if fh.is_hls):
            for bullet in f.bullets.all_bullets:
                bullet = bullet.strip()
                if not bullet.startswith("[:span]"):
                    continue
                hl_page, id_, hl_stamp = "", "", ""
                for prop_value in find_prop_value_pattern(bullet):
                    propkey = prop_value.group(1)
                    value = prop_value.group(2).strip()
                    match propkey:
                        case "hl-page":
                            hl_page = value
                        case "id":
                            id_ = value
                        case "hl-stamp":
                            hl_stamp = value
                if all((hl_page, id_, hl_stamp)):
                    hls_bullet = f"{hl_page}_{id_}_{hl_stamp}"
                    self.hls_bullets.add(hls_bullet)

    def check_backlinks(self) -> None:
        """Check for backlinks in the HLS assets."""
        asset_names = set(self.asset_mapping.keys())
        self.backlinked.update(asset_names.intersection(self.hls_bullets))
        self.not_backlinked.update(asset_names.difference(self.hls_bullets))
        asset_file_type = FileTypes.ASSET.value
        for name in self.backlinked:
            lf: LogseqFile = self.asset_mapping[name]
            lf.node.backlinked = True
            lf.path.file_type = asset_file_type
        for name in self.not_backlinked:
            lf: LogseqFile = self.asset_mapping[name]
            lf.node.backlinked = False

    @property
    def report(self) -> str:
        """Generate a report of the asset analysis."""
        return {
            Output.HLS_ASSET_MAPPING.value: self.asset_mapping,
            Output.HLS_FORMATTED_BULLETS.value: self.hls_bullets,
            Output.HLS_NOT_BACKLINKED.value: self.not_backlinked,
            Output.HLS_BACKLINKED.value: self.backlinked,
        }
