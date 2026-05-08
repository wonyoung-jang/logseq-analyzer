"""Logseq Assets Analysis Module."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from logseq_analyzer.patterns.content import ContentPatterns
from logseq_analyzer.utils.enums import CritContent, CritEmb, FileType, Output

if TYPE_CHECKING:
    from collections.abc import Iterator

    from logseq_analyzer.analysis.index import FileIndex
    from logseq_analyzer.logseq_file.file import LogseqFile


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
        self.get_asset_files()
        if self.asset_mapping:
            self.convert_names_to_data()
            self.check_backlinks()

    def get_asset_files(self) -> None:
        """Retrieve asset files based on specific criteria."""
        for f in self.index:
            if f.path.file_type == FileType.SUB_ASSET:
                self.asset_mapping[f.path.name] = f

    def convert_names_to_data(self) -> None:
        """Convert a list of names to a dictionary of hashes and their corresponding files."""
        for f in self.index:
            if not f.is_hls:
                continue
            for bullet in f.bullets.all_bullets:
                if not bullet.strip().startswith("[:span]"):
                    continue
                hl_page, id_, hl_stamp = "", "", ""
                for prop_value in ContentPatterns.PROPERTY_VALUE.finditer(bullet):
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
        _asset_mapping_keys = set(self.asset_mapping.keys())
        for name in self.hls_bullets:
            if not (asset_file := self.asset_mapping.get(name)):
                continue
            asset_file.path.file_type = FileType.ASSET
            if name in _asset_mapping_keys:
                _asset_mapping_keys.remove(name)
                self.backlinked.add(name)
                asset_file.node.backlinked = True
            else:
                self.not_backlinked.add(name)

    @property
    def report(self) -> dict[str, Any]:
        """Generate a report of the asset analysis."""
        return {
            Output.HLS_ASSET_MAPPING: self.asset_mapping,
            Output.HLS_FORMATTED_BULLETS: self.hls_bullets,
            Output.HLS_NOT_BACKLINKED: self.not_backlinked,
            Output.HLS_BACKLINKED: self.backlinked,
        }


def _update_asset_backlink(mentions: set[str], file: LogseqFile, filename: str) -> None:
    """Update the asset backlink information."""
    for mention in mentions:
        if any(name in mention for name in (file.path.name, filename)):
            file.node.backlinked = True
            return


_ASSET_CRITERIA = frozenset({CritEmb.ASSET, CritContent.ASSETS})


@dataclass(slots=True)
class LogseqAssets:
    """Class to handle assets in Logseq."""

    index: FileIndex
    backlinked: set[LogseqFile] = field(default_factory=set)
    not_backlinked: set[LogseqFile] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Initialize the LogseqAssets instance."""
        _mentioned = set()
        for f in self.index:
            _is_asset_processed = False
            if not (f_data := f.data):
                continue
            for criteria in _ASSET_CRITERIA:
                _mentioned.update(f_data.get(criteria, []))
            if not _mentioned:
                continue
            for file in self.yield_assets(backlinked=False):
                _update_asset_backlink(_mentioned, file, f.path.name)
                _is_asset_processed = True
            if not _is_asset_processed:
                break
            _mentioned.clear()
        self.backlinked.update(self.yield_assets(backlinked=True))
        self.not_backlinked.update(self.yield_assets(backlinked=False))

    def yield_assets(self, *, backlinked: bool | None = None) -> Iterator[LogseqFile]:
        """Yield all asset files from the index."""
        for f in self.index:
            if f.path.file_type != FileType.ASSET:
                continue
            if backlinked is None or f.node.backlinked is backlinked:
                yield f

    @property
    def report(self) -> dict[str, set[LogseqFile]]:
        """Generate a report of the asset analysis."""
        return {
            Output.ASSETS_BACKLINKED: self.backlinked,
            Output.ASSETS_NOT_BACKLINKED: self.not_backlinked,
        }
