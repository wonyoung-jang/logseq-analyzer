"""
Logseq Analyzer class to analyze Logseq graph files.
This class handles command line arguments, logging, output directory setup,
and the extraction of Logseq configuration and directories.
"""

import argparse
import logging
import re
import shutil
import pickle
import json
from pathlib import Path
from pprint import pprint

from src.compile_regex import compile_re_config
import src.config as config
from src.reporting import write_output
from src.logseq_graph import LogseqGraph
from src.logseq_file import LogseqFile

PATTERNS = compile_re_config()

# TODO:
# filedata.py ✅
# filename_processing.py ✅
# setup.py ✅

# compile_regex.py 🔕
# config.py 🔕
# reporting.py 🔕

# app.py
# contentdata.py
# core.py
# helpers.py
# namespace.py
# summarydata.py


class LogseqAnalyzer:
    def __init__(self):
        self.args = None
        self.log_file = None
        self.output_dir = None
        self.graph_dir = None
        self.recycle_dir = None
        self.bak_dir = None
        self.config_edn_data = None
        self.target_dirs = None
        self.initialize_all()
        
        self.logseq_graph = LogseqGraph()
        
        for file_path in self.iter_files():
            logseq_file = LogseqFile(file_path)
            self.logseq_graph.add_node(logseq_file)
            
        with open(f"{self.output_dir}/logseq_graph.pickle", "wb") as f:
            pickle.dump(self.logseq_graph.graph, f)
        
        write_output(
            self.output_dir,
            "logseq_graph",
            self.logseq_graph.graph,
        )
        
        pprint(vars(self))
    
    def initialize_all(self):
        self.setup_args()
        self.setup_logging_file()
        self.setup_output_directory()
        self.get_logseq_graph_directory()
        self.get_logseq_bak_recycle_directories()
        self.get_logseq_config_edn_file()
    
    def setup_args(self):
        """
        Setup command line arguments for the Logseq Analyzer.
        """
        parser = argparse.ArgumentParser(description="Logseq Analyzer")
        parser.add_argument(
            "-g",
            "--graph-folder",
            action="store",
            help="path to Logseq graph folder",
            required=True,
        )
        parser.add_argument(
            "-o",
            "--output-folder",
            action="store",
            help="path to output folder",
        )
        parser.add_argument(
            "-l",
            "--log-file",
            action="store",
            help="path to log file",
        )
        parser.add_argument(
            "-wg",
            "--write-graph",
            action="store_true",
            help="write all graph content to output folder (warning: may result in large file)",
        )
        parser.add_argument(
            "-ma",
            "--move-unlinked-assets",
            action="store_true",
            help='move unlinked assets to "unlinked_assets" folder',
        )
        parser.add_argument(
            "-mb",
            "--move-bak",
            action="store_true",
            help="move bak files to bak folder in output directory",
        )
        parser.add_argument(
            "-mr",
            "--move-recycle",
            action="store_true",
            help="move recycle files to recycle folder in output directory",
        )
        parser.add_argument(
            "--global-config",
            action="store",
            help="path to global configuration file",
        )
        self.args = vars(parser.parse_args())

    def setup_logging_file(self):
        """
        Setup logging configuration.
        """
        self.log_file = Path(self.args["log_file"]) if self.args["log_file"] else Path(config.DEFAULT_LOG_FILE)
        if Path.exists(self.log_file):
            Path.unlink(self.log_file)
        logging.basicConfig(
            filename=self.log_file,
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            force=True,
        )
        logging.getLogger().handlers = [
            h for h in logging.getLogger().handlers if not isinstance(h, logging.StreamHandler) or h.stream != None
        ]

        logging.info(f"Logging initialized to {self.log_file}")
        logging.info("Starting Logseq Analyzer.")

    def setup_output_directory(self):
        self.output_dir = Path(self.args["output_folder"]) if self.args["output_folder"] else Path(config.DEFAULT_OUTPUT_DIR)
        if self.output_dir.exists() and self.output_dir.is_dir():
            try:
                shutil.rmtree(self.output_dir)
                logging.info(f"Removed existing output directory: {self.output_dir}")
            except Exception as e:
                logging.debug(f"Failed to remove directory {self.output_dir}: {e}")

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created output directory: {self.output_dir}")
        except Exception as e:
            logging.debug(f"Failed to create output directory {self.output_dir}: {e}")
            raise

    def get_logseq_graph_directory(self):
        self.graph_dir = Path(self.args["graph_folder"])
        if not self.graph_dir.exists() or not self.graph_dir.is_dir():
            logging.warning(f"Graph folder does not exist or is not a directory: {self.graph_dir}")
            raise FileNotFoundError(f"Graph folder does not exist or is not a directory: {self.graph_dir}")

        logging.info(f"Graph folder set to: {self.graph_dir}")

    def get_logseq_bak_recycle_directories(self):
        logseq_folder = self.graph_dir / config.DEFAULT_LOGSEQ_DIR
        folders = [self.graph_dir, logseq_folder]
        for folder in folders:
            if not folder.exists():
                logging.warning(f"Folder does not exist: {folder}")
                raise FileNotFoundError(f"Folder does not exist: {folder}")

        self.recycle_dir = logseq_folder / config.DEFAULT_RECYCLE_DIR
        self.bak_dir = logseq_folder / config.DEFAULT_BAK_DIR

        for folder in [self.recycle_dir, self.bak_dir]:
            if not folder.exists():
                logging.warning(f"Folder does not exist: {folder}")
                raise FileNotFoundError(f"Folder does not exist: {folder}")

    def get_logseq_config_edn_file(self):
        global_config_edn_file = None
        if self.args["global_config"]:
            global_config_edn_file = config.GLOBAL_CONFIG_FILE = Path(self.args["global_config"])
            if not global_config_edn_file.exists():
                logging.warning(f"Global config file does not exist: {global_config_edn_file}")
                raise FileNotFoundError(f"Global config file does not exist: {global_config_edn_file}")

        logseq_folder = self.graph_dir / config.DEFAULT_LOGSEQ_DIR
        config_edn_file = logseq_folder / config.DEFAULT_CONFIG_FILE
        folders = [self.graph_dir, logseq_folder, config_edn_file]
        for folder in folders:
            if not folder.exists():
                logging.warning(f"Folder does not exist: {folder}")
                raise FileNotFoundError(f"Folder does not exist: {folder}")

        config_edn_content = config_edn_file.read_text(encoding="utf-8")
        config_split_lines = config_edn_content.splitlines()
        config_split_lines = [line.strip() for line in config_split_lines if line.strip()]
        config_split_lines = [line for line in config_split_lines if not line.startswith(";;")]
        config_split_no_comments = []
        for i, line in enumerate(config_split_lines):
            comment_split = line.split(";")
            if len(comment_split) > 1:
                config_split_no_comments.append(comment_split[0].strip())
            else:
                config_split_no_comments.append(line.strip())
        config_edn_content = "\n".join(config_split_no_comments)
        count_open_brackets = config_edn_content.count("{")
        count_close_brackets = config_edn_content.count("}")

        self.config_edn_data = {
            "journal_page_title_format": "MMM do, yyyy",
            "journal_file_name_format": "yyyy_MM_dd",
            "journals_directory": "journals",
            "pages_directory": "pages",
            "whiteboards_directory": "whiteboards",
            "file_name_format": ":legacy",
        }
        self.config_edn_data["journal_page_title_format"] = (
            PATTERNS["journal_page_title_pattern"].search(config_edn_content).group(1)
        )
        self.config_edn_data["journal_file_name_format"] = (
            PATTERNS["journal_file_name_pattern"].search(config_edn_content).group(1)
        )
        self.config_edn_data["pages_directory"] = (
            PATTERNS["pages_directory_pattern"].search(config_edn_content).group(1)
        )
        self.config_edn_data["journals_directory"] = (
            PATTERNS["journals_directory_pattern"].search(config_edn_content).group(1)
        )
        self.config_edn_data["whiteboards_directory"] = (
            PATTERNS["whiteboards_directory_pattern"].search(config_edn_content).group(1)
        )
        self.config_edn_data["file_name_format"] = (
            PATTERNS["file_name_format_pattern"].search(config_edn_content).group(1)
        )

        # Check global config for overwriting configs
        if global_config_edn_file:
            with global_config_edn_file.open("r", encoding="utf-8") as f:
                content = f.read()
                keys_patterns = {
                    "journal_page_title_format": PATTERNS["journal_page_title_pattern"],
                    "journal_file_name_format": PATTERNS["journal_file_name_pattern"],
                    "pages_directory": PATTERNS["pages_directory_pattern"],
                    "journals_directory": PATTERNS["journals_directory_pattern"],
                    "whiteboards_directory": PATTERNS["whiteboards_directory_pattern"],
                    "file_name_format": PATTERNS["file_name_format_pattern"],
                }

                for key, pattern in keys_patterns.items():
                    match = pattern.search(content)
                    value = match.group(1) if match else ""
                    if value:
                        self.config_edn_data[key] = value

        config.JOURNAL_PAGE_TITLE_FORMAT = self.config_edn_data["journal_page_title_format"]
        config.JOURNAL_FILE_NAME_FORMAT = self.config_edn_data["journal_file_name_format"]
        config.NAMESPACE_FORMAT = self.config_edn_data["file_name_format"]
        if config.NAMESPACE_FORMAT == ":triple-lowbar":
            config.NAMESPACE_FILE_SEP = "___"
        config.DIR_PAGES = self.config_edn_data["pages_directory"]
        config.DIR_JOURNALS = self.config_edn_data["journals_directory"]
        config.DIR_WHITEBOARDS = self.config_edn_data["whiteboards_directory"]

        self.target_dirs = {
            config.DIR_ASSETS,
            config.DIR_DRAWS,
            config.DIR_JOURNALS,
            config.DIR_PAGES,
            config.DIR_WHITEBOARDS,
        }

    def iter_files(self):
        if not self.graph_dir.exists() or not self.graph_dir.is_dir():
            logging.warning(f"Directory does not exist or is not a directory: {self.graph_dir}")
            raise FileNotFoundError(f"Directory does not exist or is not a directory: {self.graph_dir}")

        for path in self.graph_dir.rglob("*"):
            if path.is_file():
                if self.target_dirs:
                    if path.parent.name in self.target_dirs:
                        yield path
                    else:
                        logging.info(f"Skipping file {path} outside target directories")
                else:
                    yield path
