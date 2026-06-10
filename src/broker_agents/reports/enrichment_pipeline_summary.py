"""Markdown summary for the unified Backoffice enrichment pipeline."""

from broker_agents.backoffice.enrichment_pipeline import EnrichmentPipelineResult


def generate_enrichment_pipeline_summary(
    result: EnrichmentPipelineResult,
) -> str:
    """Render one enrichment result as a concise Markdown audit summary."""
    source_rows = [
        *(f"| {source} | Applied |" for source in result.applied_sources),
        *(f"| {source} | Skipped |" for source in result.skipped_sources),
    ]
    warnings = result.warnings or ["No warnings."]
    lines = [
        "# Backoffice Enrichment Pipeline Summary",
        "",
        "## 1. Important Disclaimer",
        "",
        "This summary is not a recommendation, ranking, vote, average score, or consensus. It only documents data enrichment and source quality changes.",
        "",
        "## 2. Pipeline Inputs",
        "",
        "| Input Pack | Output Pack | Ticker |",
        "| --- | --- | --- |",
        f"| {result.input_path} | {result.output_path} | {result.ticker} |",
        "",
        "## 3. Applied Sources",
        "",
        "| Source | Status |",
        "| --- | --- |",
        *source_rows,
        "",
        "## 4. Source Quality Change",
        "",
        "| Overall Before | Overall After |",
        "| --- | --- |",
        f"| {result.overall_source_quality_before} | {result.overall_source_quality_after} |",
        "",
        "## 5. Section Quality Changes",
        "",
        "| Section | Before | After |",
        "| --- | --- | --- |",
        *[
            f"| {change['section']} | {change['before']} | {change['after']} |"
            for change in result.section_quality_changes
        ],
        "",
        "## 6. Source Log Change",
        "",
        "| Before | After |",
        "| --- | --- |",
        f"| {result.source_log_count_before} | {result.source_log_count_after} |",
        "",
        "## 7. Warnings",
        "",
        *[f"- {warning}" for warning in warnings],
        "",
    ]
    return "\n".join(lines)
