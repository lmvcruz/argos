"""
Scout command argument validation utilities.

Validates that commands have been invoked with proper arguments.
"""


def validate_fetch_args(args) -> str:
    """
    Validate fetch command arguments.

    Returns:
        Error message if invalid, empty string if valid
    """
    # Check that at least one mode is specified
    if not args.fetch_all and args.fetch_last is None and not args.workflow_name:
        return (
            "Error: Must specify one of: --fetch-all, --fetch-last N, "
            "--workflow-name (for single fetch)"
        )

    # If fetch-last without workflow-name, that's ok (fetch all)
    # If fetch-last with workflow-name, that's ok (filter by workflow)
    # If fetch-all with workflow-name, workflow should be ignored
    # If workflow-name without fetch-all/fetch-last, need case identifier

    if args.workflow_name and not args.fetch_all and args.fetch_last is None:
        # Single execution fetch - need case identifier
        if not args.run_id and not args.execution_number:
            return "Error: When using --workflow-name, must provide --run-id or --execution-number"
        if not args.job_id and not args.action_name:
            return "Error: When using --workflow-name, must provide --job-id or --action-name"

    return ""


def validate_parse_args(args) -> str:
    """
    Validate parse command arguments.

    Returns:
        Error message if invalid, empty string if valid
    """
    # Must provide either --input or --workflow-name
    if not args.input and not args.workflow_name:
        return "Error: Must specify either --input (file) or --workflow-name (from database)"

    # If using --workflow-name, need case identifier
    if args.workflow_name:
        if not args.run_id and not args.execution_number:
            return "Error: When using --workflow-name, must provide --run-id or --execution-number"
        if not args.job_id and not args.action_name:
            return "Error: When using --workflow-name, must provide --job-id or --action-name"

    return ""


def validate_sync_args(args) -> str:
    """
    Validate sync command arguments.

    Returns:
        Error message if invalid, empty string if valid
    """
    # Check that at least one mode is specified
    if not args.fetch_all and args.fetch_last is None and not args.workflow_name:
        return (
            "Error: Must specify one of: --fetch-all, --fetch-last N, "
            "--workflow-name (for single sync)"
        )

    # If workflow-name without fetch-all/fetch-last, need case identifier
    if args.workflow_name and not args.fetch_all and args.fetch_last is None:
        if not args.run_id and not args.execution_number:
            return "Error: When using --workflow-name, must provide --run-id or --execution-number"
        if not args.job_id and not args.action_name:
            return "Error: When using --workflow-name, must provide --job-id or --action-name"

    # Validate skip options make sense
    if args.skip_fetch and args.skip_save_ci and args.skip_parse and args.skip_save_analysis:
        return "Error: Cannot skip all stages"

    # If skip_fetch without caching, error will occur during execution
    # That's fine - we'll handle it in the command handler

    return ""
