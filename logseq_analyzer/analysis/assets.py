"""
Logseq Assets Analysis Module.
"""

from .index import FileIndex
from ..utils.helpers import singleton
from ..utils.patterns import ContentPatterns
from ..utils.enums import Criteria
from .query_graph import Query
from .graph import LogseqGraph


@singleton
class LogseqAssets:
    """
    Class to handle assets in Logseq.
    """

    def __init__(self):
        """Initialize the LogseqAssets instance."""
        self.backlinked = []
        self.not_backlinked = []

    def handle_assets(self, asset_filenames: list):
        """Handle assets for the Logseq Analyzer."""
        for file in LogseqGraph().index.files:
            emb_link_asset = file.data.get(Criteria.EMBEDDED_LINKS_ASSET.value, [])
            asset_captured = file.data.get(Criteria.ASSETS.value, [])
            if not (emb_link_asset or asset_captured):
                continue
            for asset_name in asset_filenames:
                if not (asset_files := LogseqGraph().index.get(asset_name)):
                    continue
                for asset_file in asset_files:
                    if asset_file.is_backlinked:
                        continue
                    self.update_asset_backlink(file.path.name, emb_link_asset, asset_file)
                    self.update_asset_backlink(file.path.name, asset_captured, asset_file)
        backlinked_kwargs = {"is_backlinked": True, "file_type": "asset"}
        not_backlinked_kwargs = {"is_backlinked": False, "file_type": "asset"}
        self.backlinked = Query().list_files_with_keys_and_values(**backlinked_kwargs)
        self.not_backlinked = Query().list_files_with_keys_and_values(**not_backlinked_kwargs)

    def update_asset_backlink(self, file_name, asset_mentions, asset_file):
        """
        Update the backlink status of an asset file based on mentions in another file.
        """
        if asset_mentions:
            for asset_mention in asset_mentions:
                if asset_file.path.name in asset_mention or file_name in asset_mention:
                    asset_file.is_backlinked = True
                    break


@singleton
class LogseqAssetsHls:
    """
    Class to handle HLS assets in Logseq.
    """

    def __init__(self):
        """Initialize the LogseqAssetsHls instance."""
        self.asset_mapping = {}
        self.asset_names = None
        self.backlinked = set()
        self.formatted_bullets = []
        self.not_backlinked = set()

    def get_asset_files(self):
        """Retrieve asset files based on specific criteria."""
        criteria = {"file_type": "sub_asset"}
        asset_files = Query().list_files_with_keys_and_values(**criteria)
        self.asset_mapping = {file.path.name: file for file in asset_files}
        self.asset_names = list(self.asset_mapping.keys())

    def convert_names_to_data(self, names: list) -> dict:
        """
        Convert a list of names to a dictionary of hashes and their corresponding files.
        """
        data = {}
        for name in names:
            for file in FileIndex().get(name):
                for bullet in file.bullets.all_bullets:
                    bullet = bullet.strip()
                    if bullet.startswith("[:span]"):
                        hash_ = hash(bullet)
                        for match in ContentPatterns().property_value.finditer(bullet):
                            data.setdefault(name, {})
                            data[name].setdefault(hash_, {})
                            data[name][hash_][match.group(1)] = match.group(2)
                        hl_page = data[name][hash_].get("hl-page")
                        id_bullet = data[name][hash_].get("id")
                        hl_stamp = data[name][hash_].get("hl-stamp")
                        formatted_bullet = f"{hl_page.strip()}_{id_bullet.strip()}_{hl_stamp.strip()}"
                        self.formatted_bullets.append(formatted_bullet)

    def check_backlinks(self):
        """
        Check for backlinks in the HLS assets.
        """
        set_asset_names = set(self.asset_names)  # To check
        set_formatted_bullets = set(self.formatted_bullets)  # Backlinked
        self.backlinked = set_asset_names.intersection(set_formatted_bullets)
        self.not_backlinked = set_asset_names.difference(set_formatted_bullets)
        self.update_sub_asset_files()

    def update_sub_asset_files(self):
        """
        Update the asset files with backlink status and file type.
        """
        for name in self.backlinked:
            self.asset_mapping[name].is_backlinked = True
            self.asset_mapping[name].file_type = "asset"
        for name in self.not_backlinked:
            self.asset_mapping[name].is_backlinked = False
            self.asset_mapping[name].file_type = "asset"
