"""
Logseq Assets Analysis Module.
"""

from typing import Literal

from ..logseq_file.file import LogseqFile
from ..utils.enums import Criteria
from ..utils.helpers import singleton
from ..utils.patterns import ContentPatterns
from .index import FileIndex


@singleton
class LogseqAssets:
    """Class to handle assets in Logseq."""

    __slots__ = ("backlinked", "not_backlinked")

    def __init__(self) -> None:
        """Initialize the LogseqAssets instance."""
        self.backlinked = []
        self.not_backlinked = []

    def __len__(self) -> int:
        """Return the number of assets."""
        return len(self.backlinked) + len(self.not_backlinked)

    def handle_assets(self, index: FileIndex) -> None:
        """Handle assets for the Logseq Analyzer."""
        criteria = {"file_type": "asset"}
        for file in index:
            file_data = file.data
            emb_link_asset = file_data.get(Criteria.EMBEDDED_LINKS_ASSET.value, [])
            asset_captured = file_data.get(Criteria.ASSETS.value, [])
            if not (emb_link_asset or asset_captured):
                continue
            for asset_file in index.yield_files_with_keys_and_values(**criteria):
                if asset_file.is_backlinked:
                    continue
                file_name = file.path.name
                if emb_link_asset:
                    LogseqAssets.update_asset_backlink(file_name, emb_link_asset, asset_file)
                if asset_captured:
                    LogseqAssets.update_asset_backlink(file_name, asset_captured, asset_file)
        backlinked_kwargs = {"is_backlinked": True, "file_type": "asset"}
        not_backlinked_kwargs = {"is_backlinked": False, "file_type": "asset"}
        self.backlinked = list(index.yield_files_with_keys_and_values(**backlinked_kwargs))
        self.not_backlinked = list(index.yield_files_with_keys_and_values(**not_backlinked_kwargs))

    @staticmethod
    def update_asset_backlink(file_name: str, asset_mentions: list[str], asset_file: LogseqFile) -> None:
        """Update the backlink status of an asset file based on mentions in another file."""
        asset_file.is_backlinked = any(
            asset_file.path.name in mention or file_name in mention for mention in asset_mentions
        )


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
        self.asset_mapping = {}
        self.asset_names = set()
        self.backlinked = set()
        self.formatted_bullets = set()
        self.not_backlinked = set()

    def __repr__(self) -> Literal["LogseqAssetsHls()"]:
        """Return a string representation of the LogseqAssetsHls instance."""
        return "LogseqAssetsHls()"

    def __str__(self) -> Literal["LogseqAssetsHls"]:
        """Return a string representation of the LogseqAssetsHls instance."""
        return "LogseqAssetsHls"

    def __len__(self) -> int:
        """Return the number of hls assets found."""
        return len(self.formatted_bullets)

    def get_asset_files(self, index: FileIndex) -> None:
        """Retrieve asset files based on specific criteria."""
        criteria = {"file_type": "sub_asset"}
        asset_files = index.yield_files_with_keys_and_values(**criteria)
        self.asset_mapping = {file.path.name: file for file in asset_files}
        self.asset_names = set(self.asset_mapping.keys())

    def convert_names_to_data(self, index: FileIndex) -> None:
        """Convert a list of names to a dictionary of hashes and their corresponding files."""
        property_value_pattern = ContentPatterns.property_value
        criteria = {"is_hls": True}
        formatted_bullets = set()
        for file in index.yield_files_with_keys_and_values(**criteria):
            for bullet in file.bullets.all_bullets:
                bullet = bullet.strip()
                if not bullet.startswith("[:span]"):
                    continue

                hl_page, id_bullet, hl_stamp = "", "", ""
                for match in property_value_pattern.finditer(bullet):
                    if match.group(1) == "hl-page":
                        hl_page = match.group(2)
                    elif match.group(1) == "id":
                        id_bullet = match.group(2)
                    elif match.group(1) == "hl-stamp":
                        hl_stamp = match.group(2)

                if all([hl_page, id_bullet, hl_stamp]):
                    formatted_bullet = f"{hl_page.strip()}_{id_bullet.strip()}_{hl_stamp.strip()}"
                    formatted_bullets.add(formatted_bullet)
        self.formatted_bullets = formatted_bullets

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
            asset_mapping[name].is_backlinked = True
            asset_mapping[name].file_type = "asset"
        for name in not_backlinked:
            asset_mapping[name].file_type = "asset"
