"""
This module contains the main application logic for the Logseq analyzer.
"""

from pathlib import Path

from pyparsing import C

from .config_loader import get_config
from .process_properties import process_properties
from .process_dangling_links import process_dangling_links
from .compile_regex import get_patterns
from .core import (
    core_data_analysis,
    process_graph_files,
)
from .logseq_assets import handle_assets
from .logseq_move_files import create_delete_directory, handle_move_files, handle_move_directory
from .logseq_journals import extract_journals_from_dangling_links, process_journals_timelines
from .process_namespaces import process_namespace_data
from .process_summary_data import generate_sorted_summary_all, generate_summary_subsets
from .cache import get_cache
from .setup import (
    create_log_file,
    create_output_directory,
    get_logseq_analyzer_args,
    get_logseq_config_edn,
    get_logseq_target_dirs,
    get_sub_file_or_folder,
    set_logseq_config_edn_data,
    validate_path,
)

PATTERNS = get_patterns()
CONFIG = get_config()
DEF_LS_DIR = CONFIG.get("LOGSEQ_FILESYSTEM", "LOGSEQ_DIR")
DEF_REC_DIR = CONFIG.get("LOGSEQ_FILESYSTEM", "RECYCLE_DIR")
DEF_BAK_DIR = CONFIG.get("LOGSEQ_FILESYSTEM", "BAK_DIR")
CACHE = get_cache(CONFIG.get("CONSTANTS", "CACHE"))


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""

    # Setup variables
    gui_instance = kwargs.get("gui_instance")

    ###################################################################
    # Phase 01: Setup
    ###################################################################
    if gui_instance:
        gui_instance.update_progress("setup", 20)

    # Parse command line arguments or GUI arguments
    args = get_logseq_analyzer_args(**kwargs)

    # Clearing graph cache option
    if args.graph_cache:
        CACHE.cache.clear()

    # Setup output directory and logging
    create_output_directory()
    create_log_file()

    # Get graph folder and extract bak and recycle directories
    logseq_graph_dir = Path(args.graph_folder)
    validate_path(logseq_graph_dir)
    CONFIG.set("CONSTANTS", "GRAPH_DIR", str(logseq_graph_dir))
    logseq_dir = get_sub_file_or_folder(logseq_graph_dir, DEF_LS_DIR)
    recycle_dir = get_sub_file_or_folder(logseq_dir, DEF_REC_DIR)
    bak_dir = get_sub_file_or_folder(logseq_dir, DEF_BAK_DIR)

    # Get config data and target directories
    config_edn_data = get_logseq_config_edn(args, logseq_dir, PATTERNS.config)
    set_logseq_config_edn_data(config_edn_data)
    target_dirs = get_logseq_target_dirs()
    CONFIG.set("ANALYZER", "REPORT_FORMAT", args.report_format)

    if gui_instance:
        gui_instance.update_progress("setup", 100)
        gui_instance.update_progress("process_files", 20)

    ################################################################
    # Phase 02: Process files
    ################################################################
    # Check for modified files
    modded_files = CACHE.get_modified_files(logseq_graph_dir, target_dirs)

    # Check for deleted files and remove them from the database
    CACHE.clear_deleted_files()

    # Process for only modified/new graph files
    graph_meta_data, graph_content_bullets = process_graph_files(modded_files, PATTERNS.content)

    # Check for existing data
    graph_data_db = CACHE.cache.get("___meta___graph_data", {})
    graph_content_db = CACHE.cache.get("___meta___graph_content", {})

    # Update existing data with new data
    graph_data_db.update(graph_meta_data)
    graph_content_db.update(graph_content_bullets)

    # Core data analysis
    (
        alphanum_dict,
        alphanum_dict_ns,
        dangling_links,
        graph_data,
        all_refs,
    ) = core_data_analysis(graph_data_db)

    # Namespaces analysis
    summary_namespaces = process_namespace_data(graph_data, dangling_links)

    # Basic dangling links analysis
    dangling_dict = process_dangling_links(all_refs, dangling_links)

    # Basic properties analysis
    set_all_prop_values_builtin, set_all_prop_values_user, sorted_all_props_builtin, sorted_all_props_user = (
        process_properties(graph_data)
    )

    if gui_instance:
        gui_instance.update_progress("process_files", 100)
        gui_instance.update_progress("summary", 20)

    #################################################################
    # Phase 03: Process summaries
    #################################################################
    # Generate summary
    summary_data_subsets = generate_summary_subsets(graph_data)
    summary_sorted_all = generate_sorted_summary_all(graph_data)

    # TODO Process journal keys to create a timeline
    journals_dangling = extract_journals_from_dangling_links(dangling_links)
    process_journals_timelines(summary_data_subsets["___is_journal"], journals_dangling)

    if gui_instance:
        gui_instance.update_progress("summary", 100)
        gui_instance.update_progress("move_files", 20)

    #####################################################################
    # Phase 04: Move files to a delete directory (optional)
    #####################################################################
    to_delete_dir = create_delete_directory()
    assets_backlinked, assets_not_backlinked = handle_assets(graph_data, summary_data_subsets)

    moved_files = {}
    moved_files["moved_assets"] = handle_move_files(
        args.move_unlinked_assets, graph_data, assets_not_backlinked, to_delete_dir
    )
    moved_files["moved_bak"] = handle_move_directory(args.move_bak, bak_dir, to_delete_dir, DEF_BAK_DIR)
    moved_files["moved_recycle"] = handle_move_directory(args.move_recycle, recycle_dir, to_delete_dir, DEF_REC_DIR)

    if gui_instance:
        gui_instance.update_progress("move_files", 100)

    output_data = {
        # Main meta outputs
        "___meta___alphanum_dict_ns": alphanum_dict_ns,
        "___meta___alphanum_dict": alphanum_dict,
        "___meta___config_edn_data": config_edn_data,
        "___meta___config_patterns": PATTERNS.config,
        "___meta___content_patterns": PATTERNS.content,
        "___meta___graph_data": graph_data,
        "___meta___target_dirs": target_dirs,
        "all_refs": all_refs,
        "dangling_dict": dangling_dict,
        "dangling_links": dangling_links,
        # Properties
        "set_all_prop_values_builtin": set_all_prop_values_builtin,
        "set_all_prop_values_user": set_all_prop_values_user,
        "sorted_all_props_builtin": sorted_all_props_builtin,
        "sorted_all_props_user": sorted_all_props_user,
        # General summary
        "summary_data_subsets": summary_data_subsets,
        "summary_sorted_all": summary_sorted_all,
        # Namespaces summary
        "summary_namespaces": summary_namespaces,
        # Move files and assets
        "moved_files": moved_files,
        "assets_backlinked": assets_backlinked,
        "assets_not_backlinked": assets_not_backlinked,
    }

    if args.write_graph:
        output_data["___meta___graph_content"] = graph_content_db

    # Write output data to persistent storage
    shelve_output_data = {
        # Main meta outputs
        "___meta___alphanum_dict_ns": alphanum_dict_ns,
        "___meta___alphanum_dict": alphanum_dict,
        "___meta___config_edn_data": config_edn_data,
        "___meta___config_patterns": PATTERNS.config,
        "___meta___content_patterns": PATTERNS.content,
        "___meta___graph_content": graph_content_db,
        "___meta___graph_data": graph_data,
        "___meta___target_dirs": target_dirs,
        "all_refs": all_refs,
        "dangling_dict": dangling_dict,
        "dangling_links": dangling_links,
        # Properties
        "set_all_prop_values_builtin": set_all_prop_values_builtin,
        "set_all_prop_values_user": set_all_prop_values_user,
        "sorted_all_props_builtin": sorted_all_props_builtin,
        "sorted_all_props_user": sorted_all_props_user,
        # General summary
        **summary_data_subsets,
        **summary_sorted_all,
        # Namespaces summary
        **summary_namespaces,
        # Move files and assets
        "moved_files": moved_files,
        "assets_backlinked": assets_backlinked,
        "assets_not_backlinked": assets_not_backlinked,
    }

    CACHE.cache.update(shelve_output_data)
    CACHE.close()

    # TODO write config to file
    with open("user_config.ini", "w", encoding="utf-8") as config_file:
        CONFIG.write(config_file)

    return output_data
