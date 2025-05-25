"""
Logseq Assets Analysis Module.
"""

from re import Pattern
from typing import TYPE_CHECKING

from ..utils.enums import Criteria
from ..utils.helpers import singleton

if TYPE_CHECKING:
    from ..logseq_file.file import LogseqFile
    from .index import FileIndex


@singleton
class LogseqAssets:
    """Class to handle assets in Logseq."""

    __slots__ = ("backlinked", "not_backlinked")

    def __init__(self) -> None:
        """Initialize the LogseqAssets instance."""
        self.backlinked: list[str] = []
        self.not_backlinked: list[str] = []

    def __repr__(self) -> str:
        """Return a string representation of the LogseqAssets instance."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqAssets instance."""
        return f"{self.__class__.__qualname__}"

    def handle_assets(self, index: "FileIndex") -> None:
        """Handle assets for the Logseq Analyzer."""
        asset_criteria = {"file_type": "asset"}
        is_assets = list(index.filter_files(**asset_criteria))
        for file in index:
            emb_link_asset = file.data.get(Criteria.EMBEDDED_LINKS_ASSET.value, [])
            asset_captured = file.data.get(Criteria.ASSETS.value, [])
            if not (emb_link_asset or asset_captured):
                continue
            for asset_file in is_assets:
                if asset_file.node.is_backlinked:
                    continue
                self.update_asset_backlink(file.path.name, emb_link_asset, asset_file)
                self.update_asset_backlink(file.path.name, asset_captured, asset_file)
        backlinked_criteria = {"is_backlinked": True, "file_type": "asset"}
        not_backlinked_criteria = {"is_backlinked": False, "file_type": "asset"}
        self.backlinked = sorted(index.filter_files(**backlinked_criteria))
        self.not_backlinked = sorted(index.filter_files(**not_backlinked_criteria))

    @staticmethod
    def update_asset_backlink(file_name: str, asset_mentions: list[str], asset: "LogseqFile") -> None:
        """Update the backlink status of an asset file based on mentions in another file."""
        for mention in asset_mentions:
            if asset.path.name in mention or file_name in mention:
                asset.node.is_backlinked = True
                return


@singleton
class LogseqAssetsHls:
    """Class to handle HLS assets in Logseq."""

    __slots__ = (
        "asset_mapping",
        "asset_names",
        "backlinked",
        "formatted_bullets",
        "not_backlinked",
    )

    def __init__(self) -> None:
        """Initialize the LogseqAssetsHls instance."""
        self.asset_mapping: dict[str, "LogseqFile"] = {}
        self.asset_names: set[str] = set()
        self.backlinked: set[str] = set()
        self.formatted_bullets: set[str] = set()
        self.not_backlinked: set[str] = set()

    def __repr__(self) -> str:
        """Return a string representation of the LogseqAssetsHls instance."""
        return f"{self.__class__.__qualname__}()"

    def __str__(self) -> str:
        """Return a string representation of the LogseqAssetsHls instance."""
        return f"{self.__class__.__qualname__}"

    def get_asset_files(self, index: "FileIndex") -> None:
        """Retrieve asset files based on specific criteria."""
        sub_asset_criteria = {"file_type": "sub_asset"}
        asset_files = index.filter_files(**sub_asset_criteria)
        asset_mapping = {file.path.name: file for file in asset_files}
        self.asset_names.update(asset_mapping.keys())
        self.asset_mapping.update(asset_mapping)

    def convert_names_to_data(self, index: "FileIndex", property_value_pattern: Pattern) -> None:
        """Convert a list of names to a dictionary of hashes and their corresponding files."""
        hls_criteria = {"is_hls": True}
        formatted_bullets = self.formatted_bullets
        for file in index.filter_files(**hls_criteria):
            for bullet in file.bullets.all_bullets:
                bullet = bullet.strip()
                if not bullet.startswith("[:span]"):
                    continue

                hl_page, id_bullet, hl_stamp = "", "", ""
                for prop_value in property_value_pattern.finditer(bullet):
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
                    formatted_bullets.add(f"{hl_page}_{id_bullet}_{hl_stamp}")

    def check_backlinks(self) -> None:
        """Check for backlinks in the HLS assets."""
        asset_names = self.asset_names
        formatted_bullets = self.formatted_bullets
        self.backlinked = asset_names.intersection(formatted_bullets)
        self.not_backlinked = asset_names.difference(formatted_bullets)
        self.update_sub_asset_files()

    def update_sub_asset_files(self) -> None:
        """Update the asset files with backlink status and file type."""
        backlinked = self.backlinked
        not_backlinked = self.not_backlinked
        asset_mapping = self.asset_mapping
        for name in backlinked:
            asset_mapping[name].node.is_backlinked = True
            asset_mapping[name].path.file_type = "asset"
        for name in not_backlinked:
            asset_mapping[name].path.file_type = "asset"
