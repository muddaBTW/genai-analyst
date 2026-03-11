"""
Report Router — generates and serves downloadable reports (Markdown or PDF).
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response
from services import data_service, ai_service, report_service
from routers.upload import get_current_df

router = APIRouter()


@router.get("/report")
async def generate_report(format: str = Query("markdown", pattern="^(markdown|pdf)$")):
    """Generate a report and return it as a downloadable file.

    Query params:
        format: 'markdown' (default) or 'pdf'
    """
    df = get_current_df()
    if df is None:
        raise HTTPException(status_code=400, detail="No dataset uploaded yet")

    try:
        # Build the summary from data_service
        summary = data_service.build_llm_summary(df)
        stats = data_service.get_summary_stats(df)

        # Get AI-generated content
        insights = ai_service.generate_insights(summary)
        report_content = ai_service.generate_report_content(summary, insights)

        if format == "pdf":
            pdf_bytes = report_service.generate_pdf_report(
                summary_text=summary,
                stats=stats,
                insights=insights,
                report_content=report_content,
            )
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": "attachment; filename=analysis_report.pdf"
                },
            )

        # Default: Markdown
        md_report = report_service.generate_markdown_report(
            summary_text=summary,
            stats=stats,
            insights=insights,
            report_content=report_content,
        )
        return PlainTextResponse(
            content=md_report,
            media_type="text/markdown",
            headers={
                "Content-Disposition": "attachment; filename=analysis_report.md"
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Report generation failed: {str(e)}"
        )

