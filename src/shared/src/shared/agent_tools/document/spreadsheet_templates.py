"""Spreadsheet template definitions for brand strategy deliverables.

Defines 5 reusable templates with sheet structure, headers,
and Excel formula patterns. Formulas use {row} and {total_row}
placeholders resolved at build time by XLSXBuilder.
"""

from __future__ import annotations

from typing import Any

SPREADSHEET_TEMPLATES: dict[str, dict[str, Any]] = {
    "competitor_analysis": {
        "description": "Competitive landscape analysis matrix",
        "sheets": [
            {
                "name": "Overview",
                "headers": [
                    "Competitor",
                    "Category",
                    "Rating",
                    "Review Count",
                    "Price Level",
                    "Strengths",
                    "Weaknesses",
                    "Gap Analysis",
                ],
                "formulas": {
                    "Gap Analysis": (
                        '=IF(C{row}>MAX(D{row}:E{row}),"Leading",'
                        'IF(C{row}<MIN(D{row}:E{row}),"Lagging","Competitive"))'
                    ),
                },
            },
            {
                "name": "Detailed Comparison",
                "headers": [
                    "Dimension",
                    "Our Brand",
                    "Competitor 1",
                    "Competitor 2",
                    "Competitor 3",
                    "Notes",
                ],
                "formulas": {},
            },
        ],
    },
    "brand_audit": {
        "description": "Brand equity audit scorecard",
        "sheets": [
            {
                "name": "Scorecard",
                "headers": [
                    "Dimension",
                    "Weight",
                    "Current Score",
                    "Target Score",
                    "Gap",
                    "Priority",
                ],
                "formulas": {
                    "Gap": "=D{row}-C{row}",
                    "Priority": (
                        '=IF(E{row}>5,"Critical",'
                        'IF(E{row}>3,"High",'
                        'IF(E{row}>1,"Medium","Low")))'
                    ),
                },
            },
        ],
    },
    "content_calendar": {
        "description": "Monthly content planning calendar",
        "sheets": [
            {
                "name": "Monthly Plan",
                "headers": [
                    "Date",
                    "Channel",
                    "Content Type",
                    "Topic",
                    "Status",
                    "Notes",
                ],
                "formulas": {},
            },
            {
                "name": "Channel Mix",
                "headers": [
                    "Channel",
                    "Posts/Month",
                    "Avg Engagement",
                    "Frequency",
                    "Budget",
                    "Cost per Engagement",
                ],
                "formulas": {
                    "Cost per Engagement": (
                        "=IF(B{row}*C{row}*D{row}=0,0,E{row}/(B{row}*C{row}*D{row}))"
                    ),
                },
            },
        ],
    },
    "kpi_dashboard": {
        "description": "KPI tracking dashboard",
        "sheets": [
            {
                "name": "Dashboard",
                "headers": [
                    "KPI",
                    "Category",
                    "Target",
                    "Current",
                    "% Achievement",
                    "RAG Status",
                ],
                "formulas": {
                    "% Achievement": "=IF(C{row}=0,0,D{row}/C{row})",
                    "RAG Status": (
                        '=IF(E{row}>=0.9,"Green",IF(E{row}>=0.7,"Amber","Red"))'
                    ),
                },
            },
            {
                "name": "Monthly Tracking",
                "headers": [
                    "KPI",
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                    "YTD Average",
                ],
                "formulas": {
                    "YTD Average": "=AVERAGE(B{row}:M{row})",
                },
            },
        ],
    },
    "budget_plan": {
        "description": "Brand strategy budget planning",
        "sheets": [
            {
                "name": "Budget Overview",
                "headers": [
                    "Category",
                    "Q1",
                    "Q2",
                    "Q3",
                    "Q4",
                    "Annual Total",
                    "% of Total",
                ],
                "formulas": {
                    "Annual Total": "=SUM(B{row}:E{row})",
                    "% of Total": "=F{row}/F{total_row}",
                },
            },
            {
                "name": "ROI Projections",
                "headers": [
                    "Initiative",
                    "Investment",
                    "Expected Revenue",
                    "Projected ROI",
                ],
                "formulas": {
                    "Projected ROI": ("=IF(B{row}=0,0,(C{row}-B{row})/B{row})"),
                },
            },
        ],
    },
}
