import src.config as config
from pathlib import Path

from src.compile_regex import compile_re_content, compile_re_config
from src.namespace import process_namespace_data
from src.setup import (
    get_logseq_analyzer_args,
    create_output_directory,
    create_log_file,
    get_logseq_config_edn,
    get_logseq_target_dirs,
    set_logseq_config_edn_data,
    validate_path,
    get_sub_file_or_folder,
)
from src.core import (
    create_delete_directory,
    handle_assets,
    handle_move_files,
    process_graph_files,
    core_data_analysis,
    write_initial_outputs,
    generate_summary_subsets,
    generate_global_summary,
)
from src.helpers import merge_dicts


def run_app(**kwargs):
    """Main function to run the Logseq analyzer."""

    # Setup variables
    gui_inst = "gui_instance"
    setup_phase = "setup"
    process_files_phase = "process_files"
    reporting_phase = "reporting"
    namespaces_phase = "namespaces"
    move_files_phase = "move_files"
    gui_instance = kwargs.get(gui_inst)

    ###################################################################
    # Phase 01: Setup
    ###################################################################
    if gui_instance:
        gui_instance.update_progress(setup_phase, 20)

    # Parse command line arguments or GUI arguments
    args = get_logseq_analyzer_args(**kwargs)
    move_bak = args.move_bak
    move_recycle = args.move_recycle
    move_assets = args.move_unlinked_assets
    move = any([move_bak, move_recycle, move_assets])

    # Setup output directory and logging
    output_dir = create_output_directory()
    create_log_file(output_dir)

    # Get graph folder and extract bak and recycle directories
    logseq_graph_dir = Path(args.graph_folder)
    validate_path(logseq_graph_dir)
    logseq_dir = get_sub_file_or_folder(logseq_graph_dir, config.DEFAULT_LOGSEQ_DIR)
    recycle_dir = get_sub_file_or_folder(logseq_dir, config.DEFAULT_RECYCLE_DIR)
    bak_dir = get_sub_file_or_folder(logseq_dir, config.DEFAULT_BAK_DIR)

    # Compile regex patterns
    content_patterns = compile_re_content()
    config_patterns = compile_re_config()

    # Get config data and target directories
    config_edn_data = get_logseq_config_edn(args, logseq_dir, config_patterns)
    set_logseq_config_edn_data(config_edn_data)
    target_dirs = get_logseq_target_dirs()

    if gui_instance:
        gui_instance.update_progress(setup_phase, 100)
        gui_instance.update_progress(process_files_phase, 20)
    ################################################################
    # Phase 02: Process files
    ################################################################
    # Process graph files
    graph_meta_data, meta_graph_content, meta_primary_bullet, meta_content_bullets = process_graph_files(
        logseq_graph_dir, content_patterns, target_dirs
    )

    # Core data analysis
    (
        meta_alphanum_dictionary,
        meta_dangling_links,
        graph_content_data,
        graph_summary_data,
    ) = core_data_analysis(content_patterns, graph_meta_data, meta_graph_content, meta_primary_bullet)

    # Merge all graph data into a single dictionary
    graph_all_data = merge_dicts(graph_meta_data, graph_content_data, graph_summary_data)

    if gui_instance:
        gui_instance.update_progress(process_files_phase, 100)
        gui_instance.update_progress(reporting_phase, 20)
    #################################################################
    # Phase 03: Reporting/writing outputs
    #################################################################
    # Write initial outputs
    write_initial_outputs(
        args,
        output_dir,
        meta_alphanum_dictionary,
        meta_dangling_links,
        meta_graph_content,
        graph_meta_data,
        graph_content_data,
        graph_summary_data,
        target_dirs,
        meta_primary_bullet,
        meta_content_bullets,
        graph_all_data,
    )

    # Generate summary
    summary_data_subsets = generate_summary_subsets(output_dir, graph_all_data)
    generate_global_summary(output_dir, summary_data_subsets)

    if gui_instance:
        gui_instance.update_progress(reporting_phase, 100)
        gui_instance.update_progress(namespaces_phase, 20)
    ################################################################
    # Phase 04: Process namespaces
    ################################################################
    # Namespaces analysis
    process_namespace_data(output_dir, graph_content_data, meta_dangling_links)

    if gui_instance:
        gui_instance.update_progress(namespaces_phase, 100)
        gui_instance.update_progress(move_files_phase, 20)
    #####################################################################
    # Phase 05: Move files to a delete directory (optional)
    #####################################################################
    if move:
        # Create delete directory
        to_delete_dir = create_delete_directory()

        # Handle assets
        summary_is_asset_not_backlinked = handle_assets(output_dir, graph_all_data, summary_data_subsets, to_delete_dir)

        # Handle bak and recycle directories
        handle_move_files(args, graph_meta_data, summary_is_asset_not_backlinked, bak_dir, recycle_dir, to_delete_dir)

    if gui_instance:
        gui_instance.update_progress(move_files_phase, 100)
