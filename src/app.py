import logging
import src.config as config
from pathlib import Path
from src.compile_regex import *
from src.namespace import *
from src.setup import *
from src.core import *
from src.helpers import *
from src.reporting import *


def run_app(**kwargs):
    """
    Main function to run the Logseq analyzer.
    """
    args = get_logseq_analyzer_args(**kwargs)

    # Setup output directory and logging
    output_dir = create_output_directory()
    create_log_file(output_dir)

    # Get graph folder and extract bak and recycle directories
    logseq_graph_dir = Path(args.graph_folder)
    logseq_dir = get_sub_file_or_folder(logseq_graph_dir, config.DEFAULT_LOGSEQ_DIR)
    recycle_dir = get_sub_file_or_folder(logseq_dir, config.DEFAULT_RECYCLE_DIR)
    bak_dir = get_sub_file_or_folder(logseq_dir, config.DEFAULT_BAK_DIR)

    # Compile regex patterns
    content_patterns = compile_re_content()
    config_patterns = compile_re_config()

    # Get configs
    config_edn_data = get_logseq_config_edn(args, logseq_dir, config_patterns)

    # Get target directories
    target_dirs = get_logseq_target_dirs(config_edn_data)
    write_output(output_dir, "target_dirs", target_dirs, config.OUTPUT_DIR_META)  # TODO: Remove this line

    # Process graph files
    graph_meta_data, logseq_graph_content, meta_primary_bullet, meta_content_bullets = process_graph_files(
        logseq_graph_dir, content_patterns, target_dirs
    )
    write_output(
        output_dir, "meta_primary_bullet", meta_primary_bullet, config.OUTPUT_DIR_META
    )  # TODO: Remove this line
    write_output(
        output_dir, "meta_content_bullets", meta_content_bullets, config.OUTPUT_DIR_META
    )  # TODO: Remove this line

    # Core data analysis
    (
        alphanum_dictionary,
        dangling_links,
        graph_content_data,
        graph_summary_data,
    ) = core_data_analysis(content_patterns, graph_meta_data, logseq_graph_content)

    # Generate summary subsets
    summary_data_subsets = generate_summary_subsets(output_dir, graph_summary_data)

    # Write initial outputs
    write_initial_outputs(
        args,
        output_dir,
        alphanum_dictionary,
        dangling_links,
        logseq_graph_content,
        graph_meta_data,
        graph_content_data,
        graph_summary_data,
    )

    # Generate global summary
    generate_global_summary(output_dir, summary_data_subsets)

    # Handle assets
    handle_assets(args, output_dir, graph_meta_data, graph_content_data, graph_summary_data, summary_data_subsets)

    # Handle bak and recycle directories
    handle_bak_recycle(args, bak_dir, recycle_dir)

    # Namespaces analysis
    process_namespace_data(output_dir, graph_content_data, dangling_links)

    logging.info("Logseq Analyzer completed.")
