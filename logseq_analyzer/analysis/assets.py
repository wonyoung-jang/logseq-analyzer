"""
Logseq Assets Analysis Module.
"""

from typing import List

from ..logseq_file.file import LogseqFile
from ..utils.enums import Criteria
from ..utils.helpers import singleton
from ..utils.patterns import ContentPatterns
from .index import FileIndex


@singleton
class LogseqAssets:
    """Class to handle assets in Logseq."""

    def __init__(self):
        """Initialize the LogseqAssets instance."""
        self.backlinked = []
        self.not_backlinked = []

    def __repr__(self):
        """Return a string representation of the LogseqAssets instance."""
        return "LogseqAssets()"

    def __str__(self):
        """Return a string representation of the LogseqAssets instance."""
        return "LogseqAssets"

    def __len__(self):
        """Return the number of assets."""
        return len(self.backlinked) + len(self.not_backlinked)

    def handle_assets(self):
        """Handle assets for the Logseq Analyzer."""
        idx = FileIndex()
        criteria = {"file_type": "asset"}
        for file in idx.files:
            emb_link_asset = file.data.get(Criteria.EMBEDDED_LINKS_ASSET.value, [])
            asset_captured = file.data.get(Criteria.ASSETS.value, [])
            if not (emb_link_asset or asset_captured):
                continue
            for asset_file in idx.yield_files_with_keys_and_values(**criteria):
                if asset_file.is_backlinked:
                    continue
                self.update_asset_backlink(file.path.name, emb_link_asset, asset_file)
                self.update_asset_backlink(file.path.name, asset_captured, asset_file)
        backlinked_kwargs = {"is_backlinked": True, "file_type": "asset"}
        not_backlinked_kwargs = {"is_backlinked": False, "file_type": "asset"}
        self.backlinked = idx.list_files_with_keys_and_values(**backlinked_kwargs)
        self.not_backlinked = idx.list_files_with_keys_and_values(**not_backlinked_kwargs)

    def update_asset_backlink(self, file_name: str, asset_mentions: List[str], asset_file: LogseqFile):
        """Update the backlink status of an asset file based on mentions in another file."""
        if not asset_mentions:
            return

        for asset_mention in asset_mentions:
            if asset_file.path.name in asset_mention or file_name in asset_mention:
                asset_file.is_backlinked = True
                break


@singleton
class LogseqAssetsHls:
    """Class to handle HLS assets in Logseq."""

    def __init__(self):
        """Initialize the LogseqAssetsHls instance."""
        self.asset_mapping = {}
        self.asset_names = set()
        self.backlinked = set()
        self.formatted_bullets = set()
        self.not_backlinked = set()

    def __repr__(self):
        """Return a string representation of the LogseqAssetsHls instance."""
        return "LogseqAssetsHls()"

    def __str__(self):
        """Return a string representation of the LogseqAssetsHls instance."""
        return "LogseqAssetsHls"

    def __len__(self):
        """Return the number of hls assets found."""
        return len(self.formatted_bullets)

    def get_asset_files(self):
        """Retrieve asset files based on specific criteria."""
        index = FileIndex()
        criteria = {"file_type": "sub_asset"}
        asset_files = index.yield_files_with_keys_and_values(**criteria)
        self.asset_mapping = {file.path.name: file for file in asset_files}
        self.asset_names = set(self.asset_mapping.keys())

    def convert_names_to_data(self):
        """Convert a list of names to a dictionary of hashes and their corresponding files."""
        index = FileIndex()
        criteria = {"is_hls": True}
        content_patterns = ContentPatterns()
        prop_value_pattern = content_patterns.property_value
        for file in index.yield_files_with_keys_and_values(**criteria):
            for bullet in file.bullets.all_bullets:
                bullet = bullet.strip()
                if not bullet.startswith("[:span]"):
                    continue

                hl_page, id_bullet, hl_stamp = "", "", ""
                for match in prop_value_pattern.finditer(bullet):
                    if match.group(1) == "hl-page":
                        hl_page = match.group(2)
                    elif match.group(1) == "id":
                        id_bullet = match.group(2)
                    elif match.group(1) == "hl-stamp":
                        hl_stamp = match.group(2)

                if all([hl_page, id_bullet, hl_stamp]):
                    formatted_bullet = f"{hl_page.strip()}_{id_bullet.strip()}_{hl_stamp.strip()}"
                    self.formatted_bullets.add(formatted_bullet)

    def check_backlinks(self):
        """Check for backlinks in the HLS assets."""
        self.backlinked = self.asset_names.intersection(self.formatted_bullets)
        self.not_backlinked = self.asset_names.difference(self.formatted_bullets)
        self.update_sub_asset_files()

    def update_sub_asset_files(self):
        """Update the asset files with backlink status and file type."""
        for name in self.backlinked:
            self.asset_mapping[name].is_backlinked = True
            self.asset_mapping[name].file_type = "asset"
        for name in self.not_backlinked:
            self.asset_mapping[name].file_type = "asset"
