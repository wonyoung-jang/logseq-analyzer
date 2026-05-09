"""Logseq Assets Analysis Module."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from logseq_analyzer.utils.enums import Crit, CritEmb, FileType, Output
from logseq_analyzer.utils.patterns import ContentPatterns

if TYPE_CHECKING:
    from logseq_analyzer.analysis.index import FileIndex
    from logseq_analyzer.logseq_file.file import LogseqFile


@dataclass(slots=True)
class LogseqAssetsHls:
    """Class to handle HLS assets in Logseq."""

    index: FileIndex
    asset_mapping: dict[str, LogseqFile] = field(default_factory=dict)
    hls_bullets: set[str] = field(default_factory=set)
    backlinked: set[str] = field(default_factory=set)
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
            self._get_asset_files(f)

    def convert_names_to_data(self) -> None:
        """Convert a list of names to a dictionary of hashes and their corresponding files."""
        for f in self.index:
            self._convert_names_to_data(f)

    def _get_asset_files(self, f: LogseqFile) -> None:
        """Get asset files from the index."""
        if f.path.file_type == FileType.SUB_ASSET:
            self.asset_mapping[f.path.name] = f

    def _convert_names_to_data(self, f: LogseqFile) -> None:
        """Convert a list of names to a dictionary of hashes and their corresponding files."""
        if not f.is_hls:
            return
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


_ASSET_CRITERIA = frozenset({CritEmb.ASSET, Crit.Content.ASSETS})


@dataclass(slots=True)
class LogseqAssets:
    """Class to handle assets in Logseq."""

    index: FileIndex
    backlinked: set[LogseqFile] = field(default_factory=set)
    not_backlinked: set[LogseqFile] = field(default_factory=set)
    _mentioned: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        """Initialize the LogseqAssets instance."""
        for f in self.index:
            self._process(f)
        self.backlinked.update(self.index.yield_assets_with_backlink(backlinked=True))
        self.not_backlinked.update(self.index.yield_assets_with_backlink(backlinked=False))

    def _process(self, f: LogseqFile) -> None:
        _is_asset_processed = False
        if not (f_data := f.data):
            return
        for criteria in _ASSET_CRITERIA:
            self._mentioned.update(f_data.get(criteria, []))
        if not self._mentioned:
            return
        for file in self.index.yield_assets_with_backlink(backlinked=False):
            self._update_asset_backlink(file, f.path.name)
            _is_asset_processed = True
        if not _is_asset_processed:
            return
        self._mentioned.clear()
        return

    def _update_asset_backlink(self, file: LogseqFile, target_name: str) -> None:
        """Update the asset backlink information."""
        for mention in self._mentioned:
            if any(name in mention for name in (file.path.name, target_name)):
                file.node.backlinked = True
                return

    @property
    def report(self) -> dict[str, set[LogseqFile]]:
        """Generate a report of the asset analysis."""
        return {
            Output.ASSETS_BACKLINKED: self.backlinked,
            Output.ASSETS_NOT_BACKLINKED: self.not_backlinked,
        }
