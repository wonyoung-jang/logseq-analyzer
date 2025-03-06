import logging
from src.compile_regex import compile_re_content
from src.namespace import process_namespace_data
from src.reporting import write_output
from src.setup import setup_logseq_analyzer_args, setup_logging_and_output, get_logseq_config_edn, get_logseq_bak_recycle
from src.core import (
    process_graph_files,
    core_data_analysis,
    write_initial_outputs,
    generate_summary_subsets,
    generate_global_summary,
    handle_assets,
    handle_bak_recycle,
)


def run():
    """
    Main function to run the Logseq analyzer.
    """
    # Setup command line arguments
    args = setup_logseq_analyzer_args()

    # Setup logging and output directory
    logseq_graph_folder, output_dir = setup_logging_and_output(args)

    # Extract Logseq configuration and directories
    target_dirs, config_edn_data = get_logseq_config_edn(logseq_graph_folder, args)

    write_output(
        output_dir,
        "config_edn_data",
        config_edn_data,
        type_output="config",
    )

    # Extract bak and recycle directories
    recycle_dir, bak_dir = get_logseq_bak_recycle(logseq_graph_folder)

    # Compile regex patterns
    content_patterns = compile_re_content()

    # Process graph files
    graph_meta_data, meta_graph_content = process_graph_files(logseq_graph_folder, content_patterns, target_dirs)

    # Core data analysis
    (
        meta_alphanum_dictionary,
        meta_dangling_links,
        graph_content_data,
        graph_summary_data,
    ) = core_data_analysis(content_patterns, graph_meta_data, meta_graph_content)

    # Generate summary subsets
    summary_data_subsets = generate_summary_subsets(output_dir, graph_summary_data)

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
    )

    # Generate global summary
    generate_global_summary(output_dir, summary_data_subsets)

    # Handle assets
    handle_assets(args, output_dir, graph_meta_data, graph_content_data, graph_summary_data, summary_data_subsets)

    # Handle bak and recycle directories
    handle_bak_recycle(args, bak_dir, recycle_dir)

    # Namespaces analysis
    process_namespace_data(output_dir, graph_content_data, meta_dangling_links)

    logging.info("Logseq Analyzer completed.")
