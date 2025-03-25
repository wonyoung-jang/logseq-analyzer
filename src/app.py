"""
This module contains the main application logic for the Logseq analyzer.
"""

# import sys
from pathlib import Path

from .config_loader import get_config
from .process_properties import process_properties
from .process_dangling_links import process_dangling_links
from .compile_regex import compile_re_config, compile_re_content
from .core import (
    core_data_analysis,
    generate_global_summary,
    generate_sorted_summary_all,
    generate_summary_subsets,
    process_graph_files,
)
from .logseq_assets import handle_assets
from .logseq_move_files import create_delete_directory, handle_move_files
from .process_namespaces import process_namespace_data
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

CONFIG = get_config()


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""

    # Setup variables
    gui_inst = "gui_instance"
    setup_phase = "setup"
    process_files_phase = "process_files"
    summary_phase = "summary"
    move_files_phase = "move_files"
    gui_instance = kwargs.get(gui_inst)

    ###################################################################
    # Phase 01: Setup
    ###################################################################
    if gui_instance:
        gui_instance.update_progress(setup_phase, 20)

    # Parse command line arguments or GUI arguments
    args = get_logseq_analyzer_args(**kwargs)

    # Setup output directory and logging
    create_output_directory()
    create_log_file()

    # Get graph folder and extract bak and recycle directories
    logseq_graph_dir = Path(args.graph_folder)
    validate_path(logseq_graph_dir)
    def_ls_dir = CONFIG.get("LOGSEQ_STRUCTURE", "LOGSEQ_DIR")
    def_rec_dir = CONFIG.get("LOGSEQ_STRUCTURE", "RECYCLE_DIR")
    def_bak_dir = CONFIG.get("LOGSEQ_STRUCTURE", "BAK_DIR")
    logseq_dir = get_sub_file_or_folder(logseq_graph_dir, def_ls_dir)
    recycle_dir = get_sub_file_or_folder(logseq_dir, def_rec_dir)
    bak_dir = get_sub_file_or_folder(logseq_dir, def_bak_dir)

    # Compile regex patterns
    content_patterns = compile_re_content()
    config_patterns = compile_re_config()

    # Get config data and target directories
    config_edn_data = get_logseq_config_edn(args, logseq_dir, config_patterns)
    set_logseq_config_edn_data(config_edn_data)
    target_dirs = get_logseq_target_dirs()
    CONFIG.set("REPORTING", "REPORT_FORMAT", args.report_format)
    # with open("config_user.ini", "w") as cf:
    #     CONFIG.config.write(cf)

    if gui_instance:
        gui_instance.update_progress(setup_phase, 100)
        gui_instance.update_progress(process_files_phase, 20)

    ################################################################
    # Phase 02: Process files
    ################################################################
    # Process graph files
    graph_data, graph_content_bullets = process_graph_files(logseq_graph_dir, content_patterns, target_dirs)

    # Core data analysis
    (
        alphanum_dict,
        alphanum_dict_ns,
        dangling_links,
        graph_data,
        all_refs,
    ) = core_data_analysis(graph_data)

    # Namespaces analysis
    summary_namespaces, summary_global_namespaces = process_namespace_data(graph_data, dangling_links)

    # TODO Test dangling links
    dangling_dict = process_dangling_links(all_refs, dangling_links)

    # TODO Test properties
    set_all_prop_values_builtin, set_all_prop_values_user, sorted_all_props_builtin, sorted_all_props_user = (
        process_properties(graph_data)
    )

    if gui_instance:
        gui_instance.update_progress(process_files_phase, 100)
        gui_instance.update_progress(summary_phase, 20)

    #################################################################
    # Phase 03: Process summaries
    #################################################################
    # Generate summary
    summary_data_subsets = generate_summary_subsets(graph_data)
    summary_global = generate_global_summary(summary_data_subsets)
    summary_sorted_all = generate_sorted_summary_all(graph_data)

    if gui_instance:
        gui_instance.update_progress(summary_phase, 100)
        gui_instance.update_progress(move_files_phase, 20)

    #####################################################################
    # Phase 04: Move files to a delete directory (optional)
    #####################################################################
    to_delete_dir = create_delete_directory()
    assets_backlinked, assets_not_backlinked = handle_assets(graph_data, summary_data_subsets)
    moved_files = handle_move_files(args, graph_data, assets_not_backlinked, bak_dir, recycle_dir, to_delete_dir)

    if gui_instance:
        gui_instance.update_progress(move_files_phase, 100)

    output_data = {
        # Main meta outputs
        "alphanum_dict": alphanum_dict,
        "alphanum_dict_ns": alphanum_dict_ns,
        "dangling_links": dangling_links,
        "config_edn_data": config_edn_data,
        "target_dirs": target_dirs,
        "graph_data": graph_data,
        "content_patterns": content_patterns,
        "config_patterns": config_patterns,
        "all_refs": all_refs,
        "dangling_dict": dangling_dict,
        # Properties
        "set_all_prop_values_builtin": set_all_prop_values_builtin,
        "set_all_prop_values_user": set_all_prop_values_user,
        "sorted_all_props_builtin": sorted_all_props_builtin,
        "sorted_all_props_user": sorted_all_props_user,
        # General summary
        "___summary_global": summary_global,
        "summary_data_subsets": summary_data_subsets,
        "summary_sorted_all": summary_sorted_all,
        # Namespaces summary
        "___summary_global_namespaces": summary_global_namespaces,
        "summary_namespaces": summary_namespaces,
        # Move files and assets
        "moved_files": moved_files,
        "assets_backlinked": assets_backlinked,
        "assets_not_backlinked": assets_not_backlinked,
    }

    if args.write_graph:
        output_data["graph_content"] = graph_content_bullets

    return output_data
