import pytest
from unittest.mock import patch, MagicMock
from src.stage6_verifier import verify_format, VerificationReport, Issue

def test_verify_format_returns_report():
    template_config = {
        "page": {"size": "A4", "margin_top_cm": 2.5, "margin_bottom_cm": 2.5,
                 "margin_left_cm": 3.0, "margin_right_cm": 2.5},
        "styles": {
            "heading_1": {"font": "黑体", "size_pt": 16, "bold": True},
            "body": {"font": "宋体", "size_pt": 12, "line_spacing": 1.5},
        },
    }

    report = verify_format("fake_output.docx", template_config)
    assert isinstance(report, VerificationReport)
    assert report.total_checks > 0


def test_issue_severity_ordering():
    issues = [
        Issue(severity="warning", dimension="引用", detail="test1", location="", auto_fixable=False),
        Issue(severity="error", dimension="字体", detail="test2", location="", auto_fixable=True),
        Issue(severity="info", dimension="结构", detail="test3", location="", auto_fixable=False),
    ]
    severity_order = {"error": 0, "warning": 1, "info": 2}
    sorted_issues = sorted(issues, key=lambda i: severity_order.get(i.severity, 99))
    assert sorted_issues[0].severity == "error"
    assert sorted_issues[1].severity == "warning"
    assert sorted_issues[2].severity == "info"


def test_verification_report_pass():
    report = VerificationReport(total_checks=10, passed=10, failed=0, issues=[])
    assert report.pass_ is True
