"""
Logseq Assets Analysis Module.
"""

from dataclasses import dataclass, field
from typing import ClassVar, Generator

import logseq_analyzer.patterns.content as ContentPatterns

from ..logseq_file.file import LogseqFile
from ..utils.enums import CritContent, CritEmb, FileType, Output
from .index import FileIndex

__all__ = [
    "LogseqAssets",
    "LogseqAssetsHls",
]


@dataclass(slots=True)
class LogseqAssetsHls:
    """Class to handle HLS assets in Logseq."""

    index: FileIndex
    asset_mapping: dict[str, LogseqFile] = field(default_factory=dict)
    backlinked: set[str] = field(default_factory=set)
    hls_bullets: set[str] = field(default_factory=set)
    not_backlinked: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Initialize the LogseqAssetsHls instance."""
        self.process()

    def process(self) -> None:
        """Process HLS assets to analyze backlinks and bullet content."""
        self.get_asset_files()
        if self.asset_mapping:
            self.convert_names_to_data()
            self.check_backlinks()

    def get_asset_files(self) -> None:
        """Retrieve asset files based on specific criteria."""
        asset_files = (f for f in self.index if f.path.file_type == FileType.SUB_ASSET)
        self.asset_mapping = {f.path.name: f for f in asset_files}

    def convert_names_to_data(self) -> None:
        """Convert a list of names to a dictionary of hashes and their corresponding files."""
        find_prop_value_pattern = ContentPatterns.PROPERTY_VALUE.finditer
        add_hls_bullet = self.hls_bullets.add
        hls_files = (f.bullets.all_bullets for f in self.index if f.is_hls)
        for f_all_bullets in hls_files:
            for bullet in f_all_bullets:
                if not bullet.strip().startswith("[:span]"):
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
                    add_hls_bullet(hls_bullet)

    def check_backlinks(self) -> None:
        """Check for backlinks in the HLS assets."""
        asset_mapping = self.asset_mapping
        add_backlinked = self.backlinked.add
        add_not_backlinked = self.not_backlinked.add
        remove_asset = set(asset_mapping.keys()).remove
        get_asset_file = asset_mapping.get
        hls_bullets = self.hls_bullets
        for name in hls_bullets:
            if not (asset_file := get_asset_file(name)):
                continue

            asset_file.path.file_type = FileType.ASSET

            try:
                remove_asset(name)
                add_backlinked(name)
                asset_file.node.backlinked = True
            except KeyError:
                add_not_backlinked(name)

    @property
    def report(self) -> str:
        """Generate a report of the asset analysis."""
        return {
            Output.HLS_ASSET_MAPPING: self.asset_mapping,
            Output.HLS_FORMATTED_BULLETS: self.hls_bullets,
            Output.HLS_NOT_BACKLINKED: self.not_backlinked,
            Output.HLS_BACKLINKED: self.backlinked,
        }


@dataclass(slots=True)
class LogseqAssets:
    """Class to handle assets in Logseq."""

    index: FileIndex
    backlinked: set[LogseqFile] = field(default_factory=set)
    not_backlinked: set[LogseqFile] = field(default_factory=set)

    _ASSET_CRITERIA: ClassVar[frozenset[CritContent]] = frozenset({CritEmb.ASSET, CritContent.ASSETS})

    def __post_init__(self) -> None:
        """Initialize the LogseqAssets instance."""
        self.process()

    def process(self) -> None:
        """Handle assets for the Logseq Analyzer."""
        asset_mentions = set()
        update_mentions = asset_mentions.update
        clear_mentions = asset_mentions.clear
        asset_criteria = LogseqAssets._ASSET_CRITERIA
        update_asset_backlink = LogseqAssets.update_asset_backlink
        yield_assets = self.yield_assets
        index = self.index

        for f in index:
            asset_file_processed = False
            if not (f_data := f.data):
                continue

            get_data = f_data.get
            for criteria in asset_criteria:
                update_mentions(get_data(criteria, []))

            if not asset_mentions:
                continue

            f_name = f.path.name
            for asset_file in yield_assets(backlinked=False):
                update_asset_backlink(asset_mentions, asset_file, f_name)
                asset_file_processed = True

            if not asset_file_processed:
                break

            clear_mentions()

        del asset_mentions

        self.backlinked.update(yield_assets(backlinked=True))
        self.not_backlinked.update(yield_assets(backlinked=False))

    @staticmethod
    def update_asset_backlink(asset_mentions: set[str], asset_file: LogseqFile, filename: str) -> None:
        """Update the asset backlink information."""
        names = (asset_file.path.name, filename)
        for asset_mention in asset_mentions:
            if any(name in asset_mention for name in names):
                asset_file.node.backlinked = True
                return

    def yield_assets(self, backlinked=None) -> Generator[LogseqFile, None]:
        """Yield all asset files from the index."""
        for file in (f for f in self.index if f.path.file_type == FileType.ASSET):
            if backlinked is None:
                yield file
            if file.node.backlinked is backlinked:
                yield file

    @property
    def report(self) -> str:
        """Generate a report of the asset analysis."""
        return {
            Output.ASSETS_BACKLINKED: self.backlinked,
            Output.ASSETS_NOT_BACKLINKED: self.not_backlinked,
        }
