"""
This module contains the main application logic for the Logseq analyzer.
"""

from enum import Enum
from pathlib import Path

from .filesystem import File
from .regex_patterns import RegexPatterns
from .logseq_analyzer_config import LogseqAnalyzerConfig
from .logseq_analyzer import LogseqAnalyzer, LogseqAnalyzerArguments
from .logseq_graph_config import LogseqGraphConfig
from .cache import Cache
from .logseq_graph import LogseqGraph
from .logseq_file_mover import LogseqFileMover
from .logseq_journals import LogseqJournals
from .logseq_namespaces import LogseqNamespaces
from .report_writer import ReportWriter
import logging

ANALYZER_CONFIG = LogseqAnalyzerConfig()
ANALYZER = LogseqAnalyzer()
GRAPH_CONFIG = LogseqGraphConfig()
CACHE = Cache()
PATTERNS = RegexPatterns()
PATTERNS.compile_re_content()
PATTERNS.compile_re_content_double_curly_brackets()
PATTERNS.compile_re_content_advanced_command()
PATTERNS.compile_re_ext_links()
PATTERNS.compile_re_emb_links()
PATTERNS.compile_re_code()
PATTERNS.compile_re_dblparen()


class Phase(Enum):
    GUI_INSTANCE = "gui_instance"
    PROGRESS = "progress"


class Output(Enum):
    DANGLING_JOURNALS = "dangling_journals"
    PROCESSED_KEYS = "processed_keys"
    COMPLETE_TIMELINE = "complete_timeline"
    MISSING_KEYS = "missing_keys"
    TIMELINE_STATS = "timeline_stats"
    DANGLING_JOURNALS_PAST = "dangling_journals_past"
    DANGLING_JOURNALS_FUTURE = "dangling_journals_future"
    META_UNIQUE_LINKED_REFS = "___meta___unique_linked_refs"
    META_UNIQUE_LINKED_REFS_NS = "___meta___unique_linked_refs_ns"
    GRAPH_DATA = "___meta___graph_data"
    GRAPH_CONTENT = "___meta___graph_content"
    ALL_REFS = "all_refs"
    DANGLING_LINKS = "dangling_links"
    GRAPH_HASHED_FILES = "graph_hashed_files"
    GRAPH_NAMES_TO_HASHES = "graph_names_to_hashes"
    GRAPH_MASKED_BLOCKS = "graph_masked_blocks"
    NAMESPACE_DATA = "___meta___namespace_data"
    NAMESPACE_PARTS = "___meta___namespace_parts"
    UNIQUE_NAMESPACE_PARTS = "unique_namespace_parts"
    NAMESPACE_DETAILS = "namespace_details"
    UNIQUE_NAMESPACES_PER_LEVEL = "unique_namespaces_per_level"
    NAMESPACE_QUERIES = "namespace_queries"
    NAMESPACE_HIERARCHY = "namespace_hierarchy"
    CONFLICTS_NON_NAMESPACE = "conflicts_non_namespace"
    CONFLICTS_DANGLING = "conflicts_dangling"
    CONFLICTS_PARENT_DEPTH = "conflicts_parent_depth"
    CONFLICTS_PARENT_UNIQUE = "conflicts_parent_unique"
    MOVED_FILES = "moved_files"
    ASSETS_BACKLINKED = "assets_backlinked"
    ASSETS_NOT_BACKLINKED = "assets_not_backlinked"


class GUIInstanceDummy:
    """Dummy class to simulate a GUI instance for testing purposes."""

    def __init__(self):
        """Initialize dummy GUI instance."""
        self.progress = {}

    def update_progress(self, phase, percentage):
        """Simulate updating progress in a GUI."""
        logging.info("Updating progress: %s - %d%%", phase, percentage)


class LogseqAnalyzerPathValidator:
    """Class to validate paths in the Logseq analyzer."""

    _instance = None

    def __new__(cls):
        """Ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the path validator."""
        if not hasattr(self, "_initialized"):
            self._initialized = True

            self.dir_graph = None

            self.dir_logseq = None
            self.dir_recycle = None
            self.dir_bak = None

            self.dir_assets = None
            self.dir_draws = None
            self.dir_journals = None
            self.dir_pages = None
            self.dir_whiteboards = None

            self.dir_output = None

            self.dir_delete = None
            self.dir_delete_bak = None
            self.dir_delete_recycle = None
            self.dir_delete_assets = None

            self.file_config_global = None
            self.file_config = None
            self.file_cache = None
            self.file_log = None

    def initialize(self):
        self.dir_graph = File(ANALYZER_CONFIG.config["ANALYZER"]["GRAPH_DIR"])
        self.dir_logseq = File(ANALYZER_CONFIG.config["CONST"]["LOGSEQ_DIR"])
        self.dir_recycle = File(ANALYZER_CONFIG.config["CONST"]["RECYCLE_DIR"])
        self.dir_bak = File(ANALYZER_CONFIG.config["CONST"]["BAK_DIR"])

        self.dir_assets = File(ANALYZER_CONFIG.config["TARGET_DIRS"]["ASSETS_DIR"])
        self.dir_draws = File(ANALYZER_CONFIG.config["TARGET_DIRS"]["DRAWS_DIR"])
        self.dir_journals = File(ANALYZER_CONFIG.config["TARGET_DIRS"]["JOURNALS_DIR"])
        self.dir_pages = File(ANALYZER_CONFIG.config["TARGET_DIRS"]["PAGES_DIR"])
        self.dir_whiteboards = File(ANALYZER_CONFIG.config["TARGET_DIRS"]["WHITEBOARDS_DIR"])

        self.dir_output = File(ANALYZER_CONFIG.config["CONST"]["OUTPUT_DIR"])
        self.dir_delete = File(ANALYZER_CONFIG.config["CONST"]["TO_DELETE_DIR"])
        self.dir_delete_bak = File(ANALYZER_CONFIG.config["CONST"]["TO_DELETE_BAK_DIR"])
        self.dir_delete_recycle = File(ANALYZER_CONFIG.config["CONST"]["TO_DELETE_RECYCLE_DIR"])
        self.dir_delete_assets = File(ANALYZER_CONFIG.config["CONST"]["TO_DELETE_ASSETS_DIR"])

        self.file_config_global = File(ANALYZER_CONFIG.config["LOGSEQ_FILESYSTEM"]["GLOBAL_CONFIG_FILE"])
        self.file_config = File(ANALYZER_CONFIG.config["CONST"]["CONFIG_FILE"])
        self.file_cache = File(ANALYZER_CONFIG.config["CONST"]["CACHE"])
        self.file_log = File(ANALYZER_CONFIG.config["CONST"]["LOG_FILE"])


def check_all_files():
    """Check all files in the Logseq graph."""
    args = LogseqAnalyzerArguments()
    graph_dir = File(args.graph_folder)
    graph_dir.validate()

    cache = File(ANALYZER_CONFIG.config["CONST"]["CACHE"])
    cache.get_or_create()

    to_delete_dir = File(ANALYZER_CONFIG.config["CONST"]["TO_DELETE_DIR"])
    to_delete_dir.get_or_create()


def setup_gui(**kwargs):
    """Setup the GUI for the Logseq analyzer."""
    gui = kwargs.get(Phase.GUI_INSTANCE.value, GUIInstanceDummy())
    gui.update_progress(Phase.PROGRESS.value, 5)
    return gui


def setup_args(**kwargs):
    """Setup the command line arguments for the Logseq analyzer."""
    args = LogseqAnalyzerArguments()
    if kwargs:
        args.set_gui_args(**kwargs)
    else:
        args.set_cli_args()
    return args


def setup_logging(log_file: Path):
    """Setup logging configuration for the Logseq Analyzer."""
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    logging.debug("Logging initialized to %s", log_file)
    logging.info("Logseq Analyzer started.")


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""
    gui = setup_gui(**kwargs)
    args = setup_args(**kwargs)
    gui.update_progress(Phase.PROGRESS.value, 10)

    logseq_paths = LogseqAnalyzerPathValidator()

    output_dir = File(ANALYZER_CONFIG.config["CONST"]["OUTPUT_DIR"])
    output_dir.initialize_dir()
    ANALYZER.output_dir = output_dir.path

    log_file = File(ANALYZER_CONFIG.config["CONST"]["LOG_FILE"])
    log_file.initialize_file()
    setup_logging(log_file.path)

    ANALYZER_CONFIG.set("ANALYZER", "GRAPH_DIR", args.graph_folder)
    GRAPH_CONFIG.initialize_graph_structure()
    GRAPH_CONFIG.initialize_config_edns(args.global_config)

    ANALYZER_CONFIG.get_built_in_properties()
    ANALYZER_CONFIG.get_datetime_token_map()
    ANALYZER_CONFIG.get_datetime_token_pattern()
    ANALYZER_CONFIG.set("ANALYZER", "REPORT_FORMAT", args.report_format)
    ANALYZER_CONFIG.set_logseq_config_edn_data(GRAPH_CONFIG.ls_config)
    ANALYZER_CONFIG.get_logseq_target_dirs()
    ANALYZER_CONFIG.set_journal_py_formatting()

    if args.graph_cache:
        CACHE.clear()
    else:
        CACHE.clear_deleted_files()

    gui.update_progress(Phase.PROGRESS.value, 20)

    graph = LogseqGraph()
    graph.process_graph_files()
    gui.update_progress(Phase.PROGRESS.value, 30)

    graph.update_graph_files_with_cache()
    gui.update_progress(Phase.PROGRESS.value, 40)

    graph.post_processing_content()
    gui.update_progress(Phase.PROGRESS.value, 50)

    graph.process_summary_data()
    gui.update_progress(Phase.PROGRESS.value, 60)

    graph.generate_summary_file_subsets()
    gui.update_progress(Phase.PROGRESS.value, 70)

    graph.generate_summary_data_subsets()
    gui.update_progress(Phase.PROGRESS.value, 80)

    graph_namespaces = LogseqNamespaces()
    graph_namespaces.init_ns_parts()
    graph_namespaces.analyze_ns_queries()
    graph_namespaces.detect_non_ns_conflicts()
    graph_namespaces.detect_parent_depth_conflicts()
    gui.update_progress(Phase.PROGRESS.value, 85)

    graph_journals = LogseqJournals()
    graph_journals.process_journals_timelines()
    gui.update_progress(Phase.PROGRESS.value, 90)

    graph_assets_handler = LogseqFileMover()
    graph.handle_assets()
    graph_assets_handler.moved_files["moved_assets"] = (graph_assets_handler.handle_move_files(),)
    graph_assets_handler.moved_files["moved_bak"] = graph_assets_handler.handle_move_directory(
        args.move_bak,
        GRAPH_CONFIG.bak_dir,
        ANALYZER_CONFIG.config["CONST"]["BAK_DIR"],
    )
    graph_assets_handler.moved_files["moved_recycle"] = graph_assets_handler.handle_move_directory(
        args.move_recycle,
        GRAPH_CONFIG.recycle_dir,
        ANALYZER_CONFIG.config["CONST"]["RECYCLE_DIR"],
    )

    gui.update_progress(Phase.PROGRESS.value, 95)

    # Output writing
    # Meta
    meta_reports = {
        Output.META_UNIQUE_LINKED_REFS.value: graph.unique_linked_references,
        Output.META_UNIQUE_LINKED_REFS_NS.value: graph.unique_linked_references_ns,
        Output.GRAPH_DATA.value: graph.data,
        Output.ALL_REFS.value: graph.all_linked_references,
        Output.DANGLING_LINKS.value: graph.dangling_links,
        Output.GRAPH_HASHED_FILES.value: graph.hashed_files,
        Output.GRAPH_NAMES_TO_HASHES.value: graph.names_to_hashes,
        Output.GRAPH_MASKED_BLOCKS.value: graph.masked_blocks,
    }
    if args.write_graph:
        meta_reports[Output.GRAPH_CONTENT.value] = graph.content_bullets
    for name, data in meta_reports.items():
        ReportWriter(name, data, ANALYZER_CONFIG.config["OUTPUT_DIRS"]["META"]).write()
    # Journals
    journals_report = {
        Output.DANGLING_JOURNALS.value: graph_journals.dangling_journals,
        Output.PROCESSED_KEYS.value: graph_journals.processed_keys,
        Output.COMPLETE_TIMELINE.value: graph_journals.complete_timeline,
        Output.MISSING_KEYS.value: graph_journals.missing_keys,
        Output.TIMELINE_STATS.value: graph_journals.timeline_stats,
        Output.DANGLING_JOURNALS_PAST.value: graph_journals.dangling_journals_past,
        Output.DANGLING_JOURNALS_FUTURE.value: graph_journals.dangling_journals_future,
    }
    for name, data in journals_report.items():
        ReportWriter(name, data, ANALYZER_CONFIG.config["OUTPUT_DIRS"]["LOGSEQ_JOURNALS"]).write()
    # Summary
    for name, data in graph.summary_file_subsets.items():
        ReportWriter(name, data, ANALYZER_CONFIG.config["OUTPUT_DIRS"]["SUMMARY"]).write()
    for name, data in graph.summary_data_subsets.items():
        ReportWriter(name, data, "summary_content_data").write()
    # Namespace
    namespace_reports = {
        Output.NAMESPACE_DATA.value: graph_namespaces.namespace_data,
        Output.NAMESPACE_PARTS.value: graph_namespaces.namespace_parts,
        Output.UNIQUE_NAMESPACE_PARTS.value: graph_namespaces.unique_namespace_parts,
        Output.NAMESPACE_DETAILS.value: graph_namespaces.namespace_details,
        Output.UNIQUE_NAMESPACES_PER_LEVEL.value: graph_namespaces.unique_namespaces_per_level,
        Output.NAMESPACE_QUERIES.value: graph_namespaces.namespace_queries,
        Output.NAMESPACE_HIERARCHY.value: graph_namespaces.tree,
        Output.CONFLICTS_NON_NAMESPACE.value: graph_namespaces.conflicts_non_namespace,
        Output.CONFLICTS_DANGLING.value: graph_namespaces.conflicts_dangling,
        Output.CONFLICTS_PARENT_DEPTH.value: graph_namespaces.conflicts_parent_depth,
        Output.CONFLICTS_PARENT_UNIQUE.value: graph_namespaces.conflicts_parent_unique,
    }
    for name, data in namespace_reports.items():
        ReportWriter(name, data, ANALYZER_CONFIG.config["OUTPUT_DIRS"]["NAMESPACE"]).write()
    # Move files and assets
    moved_files_reports = {
        Output.MOVED_FILES.value: graph_assets_handler.moved_files,
        Output.ASSETS_BACKLINKED.value: graph.assets_backlinked,
        Output.ASSETS_NOT_BACKLINKED.value: graph.assets_not_backlinked,
    }
    for name, data in moved_files_reports.items():
        ReportWriter(name, data, ANALYZER_CONFIG.config["OUTPUT_DIRS"]["ASSETS"]).write()
    # Write output data to persistent storage
    shelve_output_data = {
        # Main meta outputs
        Output.META_UNIQUE_LINKED_REFS.value: graph.unique_linked_references,
        Output.META_UNIQUE_LINKED_REFS_NS.value: graph.unique_linked_references_ns,
        Output.GRAPH_DATA.value: graph.data,
        Output.ALL_REFS.value: graph.all_linked_references,
        Output.DANGLING_LINKS.value: graph.dangling_links,
        Output.GRAPH_HASHED_FILES.value: graph.hashed_files,
        Output.GRAPH_NAMES_TO_HASHES.value: graph.names_to_hashes,
        Output.GRAPH_MASKED_BLOCKS.value: graph.masked_blocks,
        # General summary
        **graph.summary_file_subsets,
        **graph.summary_data_subsets,
        # Namespaces summary
        **namespace_reports,
        # Move files and assets
        Output.MOVED_FILES.value: graph_assets_handler.moved_files,
        Output.ASSETS_BACKLINKED.value: graph.assets_backlinked,
        Output.ASSETS_NOT_BACKLINKED.value: graph.assets_not_backlinked,
    }
    try:
        CACHE.update(shelve_output_data)
        CACHE.close()
    finally:
        ANALYZER_CONFIG.write_to_file()
    gui.update_progress(Phase.PROGRESS.value, 100)
