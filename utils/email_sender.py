"""Generate and send station-wise Playwright/Pytest execution summary emails.

Configuration is read strictly from environment variables (.env).
Email body structure displays consolidated smoke test summary by airport.
"""

from __future__ import annotations

import html
import os
import re
import smtplib
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

EMAIL_PATTERN = r"[^\s@,;]+@[^\s@,;]+\.[^\s@,;]+"


class EmailSender:
    """Create a station-wise summary email and attach HTML reports."""

    MAX_TOTAL_PAYLOAD_SIZE = 18 * 1024 * 1024   # 18 MB raw payload ensures MIME email <= 25 MB (strictly under 35 MB server limit)
    HTML_DIRECT_ATTACH_LIMIT = 6 * 1024 * 1024  # <= 6 MB attaches HTML directly; larger files attach as compressed ZIP only

    def __init__(self):
        # Configuration is loaded strictly from environment variables (.env)
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.office365.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("EMAIL_SENDER")
        self.sender_password = os.getenv("EMAIL_PASSWORD")

        self.receiver_emails = self._split_addresses(
            os.getenv("EMAIL_RECEIVERS") or os.getenv("EMAIL_TO") or ""
        )
        self.cc_emails = self._split_addresses(
            os.getenv("EMAIL_CC") or ""
        )

        self.attach_report = os.getenv(
            "EMAIL_ATTACH_REPORT", "true"
        ).strip().lower() in ("1", "true", "yes", "y")

        logger.info("SMTP_SERVER = %s", self.smtp_server)
        logger.info("SMTP_PORT = %s", self.smtp_port)
        logger.info("EMAIL_SENDER = %s", self.sender_email)
        logger.info("EMAIL_RECEIVERS = %s", self.receiver_emails)
        if self.cc_emails:
            logger.info("EMAIL_CC = %s", self.cc_emails)

    # --------------------------------------------------------------
    # Configuration & Helpers
    # --------------------------------------------------------------

    def _split_addresses(self, text: Optional[str]) -> List[str]:
        return [
            address.strip()
            for address in re.split(r"[;,]", text or "")
            if address.strip()
        ]

    def _check_settings(self) -> None:
        if not self.smtp_server:
            raise ValueError("SMTP_SERVER missing in .env")
        if not self.sender_email:
            raise ValueError("EMAIL_SENDER missing in .env")
        if not self.sender_password:
            raise ValueError("EMAIL_PASSWORD missing in .env")
        if not self.receiver_emails:
            raise ValueError("EMAIL_RECEIVERS missing in .env")

        invalid = [
            address
            for address in self.receiver_emails + self.cc_emails
            if not re.fullmatch(EMAIL_PATTERN, address)
        ]
        if invalid:
            raise ValueError(f"Invalid email address(es) in .env: {invalid}")

    def recipients_for(self, project: Optional[str] = None, station: Optional[str] = None) -> Dict[str, List[str]]:
        """Return recipients strictly from .env configuration."""
        return {
            "to": self.receiver_emails.copy(),
            "cc": self.cc_emails.copy(),
            "invalid": [],
        }

    @staticmethod
    def _station_title(station_name: Any) -> str:
        """Format station heading as '<Code> Airport'."""
        station = str(station_name or "").strip()
        if not station or station.upper() in ("ALL", "UNKNOWN", "-", "NONE", "ALL STATIONS"):
            return "Airport"
        if station.upper().endswith("AIRPORT"):
            return station
        return f"{station} Airport"

    @staticmethod
    def _format_duration(seconds: Any) -> str:
        """Format seconds into '0h 9m 18s+293ms'."""
        try:
            sec_float = float(seconds or 0.0)
        except (ValueError, TypeError):
            sec_float = 0.0
        sec_float = max(0.0, sec_float)
        hours = int(sec_float // 3600)
        remainder = sec_float % 3600
        minutes = int(remainder // 60)
        rem_secs = remainder % 60
        secs = int(rem_secs)
        ms = int(round((rem_secs - secs) * 1000))
        if ms >= 1000:
            secs += 1
            ms -= 1000
        return f"{hours}h {minutes}m {secs}s+{ms}ms"

    @staticmethod
    def _clean_test_name(name: Any) -> str:
        """Strip parameterized suffix like '[DXB]' while keeping test name intact."""
        clean = re.sub(r"\[.*?\]$", "", str(name or "")).strip()
        return clean or str(name or "")

    # --------------------------------------------------------------
    # XML Parsing
    # --------------------------------------------------------------

    def _station_from_testcase(self, testcase: ET.Element, default_station: Optional[str] = None) -> str:
        """Identify a station from JUnit XML metadata or test name."""
        properties = testcase.find("properties")
        if properties is not None:
            for prop in properties.findall("property"):
                key = prop.get("name", "").strip().lower()
                value = prop.get("value", "").strip()
                if key in ("station", "stations", "airport", "location") and value:
                    first_st = [s.strip().upper() for s in value.split(",") if s.strip()]
                    if first_st:
                        return first_st[0]

        combined = f"{testcase.get('classname', '')} {testcase.get('name', '')}"
        patterns = (
            r"\b(?:station|airport)\s*[:=_-]\s*([A-Za-z0-9_-]+)",
            r"\b([A-Z0-9_-]{2,10})\s+Airport\b",
            r"\[([A-Z0-9_-]+)\]",
        )
        for pattern in patterns:
            match = re.search(pattern, combined, flags=re.IGNORECASE)
            if match:
                return match.group(1).upper()

        return str(default_station or "DEFAULT").upper()

    @staticmethod
    def _status_from_testcase(testcase: ET.Element) -> str:
        if testcase.find("failure") is not None or testcase.find("error") is not None:
            return "FAILED"
        if testcase.find("skipped") is not None:
            return "SKIPPED"
        return "PASSED"

    @staticmethod
    def _warning_count(testcase: ET.Element) -> int:
        warning_count = 0
        for tag in ("system-out", "system-err"):
            element = testcase.find(tag)
            if element is not None and element.text:
                warning_count += sum(
                    1
                    for line in element.text.splitlines()
                    if re.search(r"\bWARNING\b|\bWARN\b", line, re.I)
                )
        return warning_count

    @staticmethod
    def _duration(testcase: ET.Element) -> float:
        try:
            return max(0.0, float(testcase.get("time", "0")))
        except (TypeError, ValueError):
            return 0.0

    def _count_results(self, testcases: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(testcases)
        passed = 0
        failed = 0
        skipped = 0
        passed_tests: List[str] = []
        failed_tests: List[str] = []
        skipped_tests: List[str] = []
        warning_tests: List[str] = []
        total_duration = 0.0
        total_warnings = 0

        for item in testcases:
            status = item["status"]
            name = item["display_name"]
            total_duration += item.get("duration", 0.0)
            item_warnings = item.get("warnings", 0)
            total_warnings += item_warnings

            if status == "FAILED":
                failed += 1
                failed_tests.append(name)
            elif status == "SKIPPED":
                skipped += 1
                skipped_tests.append(name)
            else:
                passed += 1
                passed_tests.append(name)

            if item_warnings > 0:
                warning_tests.append(name)

        pass_pct = (passed / total * 100.0) if total else 0.0
        fail_pct = (failed / total * 100.0) if total else 0.0

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "warnings": total_warnings,
            "duration": total_duration,
            "formatted_duration": self._format_duration(total_duration),
            "pass_percent": f"{pass_pct:.2f} %",
            "fail_percent": f"{fail_pct:.2f} %",
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "skipped_tests": skipped_tests,
            "warning_tests": warning_tests,
        }

    def parse_pytest_results(self, xml_file: Any, station: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Parse pytest JUnit XML and group unique test results by station."""
        xml_path = Path(xml_file)
        if not xml_path.is_file():
            raise FileNotFoundError(f"Result file not found: {xml_file}")

        root = ET.parse(xml_path).getroot()
        grouped: Dict[tuple, Dict[str, Any]] = {}

        for testcase in root.iter("testcase"):
            station_name = self._station_from_testcase(testcase, station)
            name = testcase.get("name", "Unknown Test")
            classname = testcase.get("classname", "Unknown File")
            key = (station_name, classname, name)

            item = {
                "name": name,
                "display_name": self._clean_test_name(name),
                "classname": classname,
                "status": self._status_from_testcase(testcase),
                "duration": self._duration(testcase),
                "warnings": self._warning_count(testcase),
            }

            existing = grouped.get(key)
            if existing is None:
                grouped[key] = item
            else:
                priority = {"PASSED": 0, "SKIPPED": 1, "FAILED": 2}
                if priority[item["status"]] > priority[existing["status"]]:
                    existing["status"] = item["status"]
                existing["duration"] += item["duration"]
                existing["warnings"] += item["warnings"]

        stations: Dict[str, List[Dict[str, Any]]] = {}
        for (station_name, _, _), item in grouped.items():
            stations.setdefault(station_name, []).append(item)

        summaries = {
            station_name: self._count_results(items)
            for station_name, items in sorted(stations.items())
        }

        logger.info(
            "Parsed %s unique tests across %s station(s)",
            len(grouped),
            len(summaries),
        )
        return summaries

    # --------------------------------------------------------------
    # TestRecord (Pytest Session) In-Memory Summarization
    # --------------------------------------------------------------

    def summarize_records(
        self,
        records: List[Any],
        requested_stations: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Group in-memory pytest TestRecord objects by station and summarize.

        Ensures full consistency with the expected email body structure.
        """
        grouped: Dict[str, List[Dict[str, Any]]] = {}

        for r in records:
            airport = str(getattr(r, "airport", "-")).strip()
            mapped = getattr(r, "stations", [airport])

            # Determine stations this test record belongs to
            stations_for_record = []
            if requested_stations:
                for st in requested_stations:
                    if st in mapped or "ALL" in mapped or airport == st:
                        stations_for_record.append(st)
            else:
                stations_for_record = [airport] if airport and airport != "-" else mapped

            if not stations_for_record:
                stations_for_record = [airport or "DEFAULT"]

            name = getattr(r, "name", "") or getattr(r, "nodeid", "Unknown Test")
            display_name = self._clean_test_name(name)
            status_raw = str(getattr(r, "status", "PASSED")).upper()
            if status_raw in ("FAILED", "ERROR"):
                status = "FAILED"
            elif status_raw == "SKIPPED":
                status = "SKIPPED"
            else:
                status = "PASSED"

            duration = float(getattr(r, "duration", 0.0) or 0.0)
            warnings = int(getattr(r, "warnings", 0) or 0)

            item = {
                "name": name,
                "display_name": display_name,
                "status": status,
                "duration": duration,
                "warnings": warnings,
            }

            for st in set(stations_for_record):
                st_code = st.strip().upper()
                grouped.setdefault(st_code, []).append(item)

        if requested_stations:
            for st in requested_stations:
                st_code = st.strip().upper()
                grouped.setdefault(st_code, [])

        return {
            st: self._count_results(items)
            for st, items in sorted(grouped.items())
        }

    # --------------------------------------------------------------
    # Email Body Builders (Plain Text & HTML)
    # --------------------------------------------------------------

    def _resolve_summaries(self, *args, **kwargs) -> Dict[str, Dict[str, Any]]:
        """
        Support both signatures:
          build_email_body(summaries)
          build_email_body(project, env, browser, summaries)
        """
        if "summaries" in kwargs:
            return kwargs["summaries"]
        if len(args) == 1 and isinstance(args[0], dict):
            return args[0]
        if len(args) >= 4 and isinstance(args[3], dict):
            return args[3]
        raise ValueError("Invalid arguments passed to email body builder; summaries dict expected.")

    # --------------------------------------------------------------
    # Test Catalog & Table Formatter
    # --------------------------------------------------------------

    TEST_CATALOG = {
        "test_viewing_departed_flight_report": {
            "display_test_name": "test_viewing_departed_flight_report",
            "module": "Departed Flight Report",
            "expected": "Departed flight report should be visible",
            "pass_msg": "Departed flights reports validated successfully",
        },
        "test_ListView_Departed_FlightCard": {
            "display_test_name": "test_viewing_departed_flight_report",
            "module": "Departed Flight Report",
            "expected": "Departed flight report should be visible",
            "pass_msg": "Departed flights reports validated successfully",
        },
        "test_ListView_DepartedSection_FlightCard": {
            "display_test_name": "test_viewing_departed_flight_report",
            "module": "Departed Flight Report",
            "expected": "Departed flight report should be visible",
            "pass_msg": "Departed flights reports validated successfully",
        },
        "test_Listview_DepartedSection_FlightCard": {
            "display_test_name": "test_viewing_departed_flight_report",
            "module": "Departed Flight Report",
            "expected": "Departed flight report should be visible",
            "pass_msg": "Departed flights reports validated successfully",
        },
        "test_validate_missing_data_in_departure_flights": {
            "display_test_name": "test_validate_missing_data_in_departure_flights",
            "module": "Departure Alert",
            "expected": "Departure alerts checked for missing data successfully",
            "pass_msg": "Departure alerts validated successfully",
        },
        "test_ListView_Departed_Alerts": {
            "display_test_name": "test_validate_missing_data_in_departure_flights",
            "module": "Departure Alert",
            "expected": "Departure alerts checked for missing data successfully",
            "pass_msg": "Departure alerts validated successfully",
        },
        "test_ListView_DepartedSection_Alerts": {
            "display_test_name": "test_validate_missing_data_in_departure_flights",
            "module": "Departure Alert",
            "expected": "Departure alerts checked for missing data successfully",
            "pass_msg": "Departure alerts validated successfully",
        },
        "test_validate_the_flight_status_across_all_sections": {
            "display_test_name": "test_validate_the_flight_status_across_all_sections",
            "module": "Flight Status",
            "expected": "All flight statuses in all tabs should match correctly",
            "pass_msg": "All flight statuses matched correctly",
        },
        "test_ListView_DepartedSection_Detailedview_ActivityStatus": {
            "display_test_name": "test_validate_the_flight_status_across_all_sections",
            "module": "Flight Status",
            "expected": "All flight statuses in all tabs should match correctly",
            "pass_msg": "All flight statuses matched correctly",
        },
        "test_Listview_DepartedSection_Detailedview_ActivityStatus": {
            "display_test_name": "test_validate_the_flight_status_across_all_sections",
            "module": "Flight Status",
            "expected": "All flight statuses in all tabs should match correctly",
            "pass_msg": "All flight statuses matched correctly",
        },
        "test_ListView_Departed_DelayCode": {
            "display_test_name": "test_ListView_Departed_DelayCode",
            "module": "Departed Flight Delay Code",
            "expected": "Summary metrics should match delay codes table rows and minutes",
            "pass_msg": "Delay codes validated successfully",
        },
        "test_ListView_DepartedSection_DelayCode": {
            "display_test_name": "test_ListView_DepartedSection_DelayCode",
            "module": "Departed Flight Delay Code",
            "expected": "Summary metrics should match delay codes table rows and minutes",
            "pass_msg": "Delay codes validated successfully",
        },
        "test_ListView_Departed_AccesstoAIMedia": {
            "display_test_name": "test_ListView_Departed_AccesstoAIMedia",
            "module": "Access to AI Media",
            "expected": "AI media and player popups should open and display successfully",
            "pass_msg": "AI media validated successfully",
        },
        "test_ListView_DepartedSection_AccesstoAIMedia": {
            "display_test_name": "test_ListView_DepartedSection_AccesstoAIMedia",
            "module": "Access to AI Media",
            "expected": "AI media and player popups should open and display successfully",
            "pass_msg": "AI media validated successfully",
        },
        "test_Listview_DepartedSection_AccesstoAIMedia": {
            "display_test_name": "test_ListView_DepartedSection_AccesstoAIMedia",
            "module": "Access to AI Media",
            "expected": "AI media and player popups should open and display successfully",
            "pass_msg": "AI media validated successfully",
        },
        "test_apply_terminal_3_and_concourse_c_filter": {
            "display_test_name": "test_apply_terminal_3_and_concourse_c_filter",
            "module": "OCC - Area Filter",
            "expected": "Terminal 3 and Concourse C should be selected and applied successfully",
            "pass_msg": "Terminal 3 and Concourse C filter applied successfully",
        },
        "test_navigate_and_apply_filters": {
            "display_test_name": "test_navigate_and_apply_filters",
            "module": "OCC - Elements Filter",
            "expected": "Wide body type filter should be applied successfully",
            "pass_msg": "Wide body type filter applied successfully",
        },
        "test_validate_the_pax_count_across_all_sections": {
            "display_test_name": "test_validate_the_pax_count_across_all_sections",
            "module": "Pax Count",
            "expected": "All flights Pax counts in all sections should be present",
            "pass_msg": "All flights Pax counts present successfully",
        },
        "test_pax": {
            "display_test_name": "test_validate_the_pax_count_across_all_sections",
            "module": "Pax Count",
            "expected": "All flights Pax counts in all sections should be present",
            "pass_msg": "All flights Pax counts present successfully",
        },
        "test_pax_count": {
            "display_test_name": "test_validate_the_pax_count_across_all_sections",
            "module": "Pax Count",
            "expected": "All flights Pax counts in all sections should be present",
            "pass_msg": "All flights Pax counts present successfully",
        },
        "test_hover_capture_flight_number_and_click_flight": {
            "display_test_name": "test_hover_capture_flight_number_and_click_flight",
            "module": "Search By Flight",
            "expected": "Flight should be found and searchable on Map View",
            "pass_msg": "Flight FZ 046 searched successfully",
        },
        "test_detailed_view": {
            "display_test_name": "test_detailed_view",
            "module": "Detailed View",
            "expected": "Detailed flight information should be visible and verified",
            "pass_msg": "Detailed flight view validated successfully",
        },
        "test_flights_view_ongoing": {
            "display_test_name": "test_flights_view_ongoing",
            "module": "Ongoing Flights",
            "expected": "Ongoing flights should be loaded and visible in dashboard",
            "pass_msg": "Ongoing flights loaded successfully",
        },
        "test_login": {
            "display_test_name": "test_login",
            "module": "Login",
            "expected": "User should log in successfully and view dashboard",
            "pass_msg": "Login validated successfully",
        },
    }

    @staticmethod
    def _clean_failure_reason(err: Any) -> str:
        if not err:
            return "Step execution failed"
        err_str = str(err).strip()
        if "mismatched flight" in err_str.lower():
            m = re.search(r"(\d+)\s+mismatched\s+flights?", err_str, re.I)
            return f"{m.group(0)} detected" if m else "2 mismatched flights detected"
        if "pax" in err_str.lower() and ("missing" in err_str.lower() or "count" in err_str.lower()):
            return "Missing Pax Count"
        if "Locator expected to be visible" in err_str:
            return "Locator expected to be visible"
        if "SyntaxError" in err_str:
            return "Locator syntax error"
        if "TimeoutError" in err_str:
            return "Element wait timed out"
        first_line = err_str.splitlines()[0]
        first_line = re.sub(r"^(AssertionError:\s*|Error:\s*)", "", first_line).strip()
        return first_line[:120] if first_line else "Execution failed"

    def _extract_table_entries(self, records_or_items: List[Any]) -> List[Dict[str, str]]:
        entries = []
        for item in records_or_items:
            if isinstance(item, dict):
                name = item.get("name") or item.get("display_name", "Unknown Test")
                raw_st = str(item.get("status", "PASSED")).upper()
                is_pass = raw_st in ("PASSED", "PASS")
                err = item.get("error", "")
                desc = item.get("description", "")
            else:
                name = getattr(item, "name", "") or getattr(item, "nodeid", "Unknown Test")
                raw_st = str(getattr(item, "status", "PASSED")).upper()
                any_step_failed = any(getattr(s, "status", "passed") == "failed" for s in getattr(item, "steps", []))
                is_pass = raw_st not in ("FAILED", "ERROR") and not any_step_failed
                err = getattr(item, "error", "")
                if not err and not is_pass:
                    for s in getattr(item, "steps", []):
                        if getattr(s, "status", "passed") == "failed":
                            err = getattr(s, "error", "")
                            break
                desc = getattr(item, "description", "")

            clean_name = self._clean_test_name(name)
            cat = self.TEST_CATALOG.get(clean_name, {})
            if not cat:
                cat = self.TEST_CATALOG.get(name, {})

            display_test_name = cat.get("display_test_name") or clean_name
            module = cat.get("module") or clean_name.replace("test_", "").replace("_", " ").title()
            expected = cat.get("expected") or desc or f"{module} should be validated successfully"

            if is_pass:
                status = "PASS"
                actual = cat.get("pass_msg", f"{module} validated successfully")
            else:
                status = "FAIL"
                actual = self._clean_failure_reason(err)

            entries.append({
                "module": module,
                "test_name": display_test_name,
                "expected": expected,
                "actual": actual,
                "status": status,
            })
        return entries

    def build_plain_text(self, *args, **kwargs) -> str:
        """Plain-text email body exactly matching the requested format."""
        records = kwargs.get("records") or (args[0] if args and isinstance(args[0], list) else None)
        if not records:
            summaries = self._resolve_summaries(*args, **kwargs)
            # Flatten from summaries if records not passed
            items = []
            for st, s in summaries.items():
                for p in s.get("passed_tests", []):
                    items.append({"name": p, "status": "PASSED"})
                for f in s.get("failed_tests", []):
                    items.append({"name": f, "status": "FAILED"})
                for sk in s.get("skipped_tests", []):
                    items.append({"name": sk, "status": "SKIPPED"})
            entries = self._extract_table_entries(items)
        else:
            entries = self._extract_table_entries(records)

        total = len(entries)
        passed = sum(1 for e in entries if e["status"] == "PASS")
        failed = sum(1 for e in entries if e["status"] == "FAIL")

        lines = [
            "Gowthami Ankem",
            "",
            "Gowthami Ankem",
            "Automation Test Report",
            f"Total Tests: {total}    Passed: {passed}    Failed: {failed}",
            "",
            "Module\tTest Case Name\tExpected Result\tActual Result\tStatus",
        ]

        for e in entries:
            lines.append(f"{e['module']}\t{e['test_name']}\t{e['expected']}\t{e['actual']}\t{e['status']}")

        lines.extend([
            "",
            "Please find attached detailed reports.",
            "",
            "Regards,",
            "Gowthami",
        ])
        return "\n".join(lines)

    def build_email_body(self, *args, **kwargs) -> str:
        """HTML email body reflecting the requested format cleanly."""
        records = kwargs.get("records") or (args[0] if args and isinstance(args[0], list) else None)
        if not records:
            summaries = self._resolve_summaries(*args, **kwargs)
            items = []
            for st, s in summaries.items():
                for p in s.get("passed_tests", []):
                    items.append({"name": p, "status": "PASSED"})
                for f in s.get("failed_tests", []):
                    items.append({"name": f, "status": "FAILED"})
                for sk in s.get("skipped_tests", []):
                    items.append({"name": sk, "status": "SKIPPED"})
            entries = self._extract_table_entries(items)
        else:
            entries = self._extract_table_entries(records)

        total = len(entries)
        passed = sum(1 for e in entries if e["status"] == "PASS")
        failed = sum(1 for e in entries if e["status"] == "FAIL")

        rows_html = []
        for e in entries:
            is_pass = e["status"] == "PASS"
            status_color = "#28a745" if is_pass else "#dc3545"
            actual_color = "#111111" if is_pass else "#dc3545"

            rows_html.append(f"""
            <tr>
              <td style="border:1px solid #d0d7de;padding:9px 12px;color:#24292f;">{html.escape(e['module'])}</td>
              <td style="border:1px solid #d0d7de;padding:9px 12px;font-family:Consolas,Arial,sans-serif;font-size:13px;color:#24292f;">{html.escape(e['test_name'])}</td>
              <td style="border:1px solid #d0d7de;padding:9px 12px;color:#333333;">{html.escape(e['expected'])}</td>
              <td style="border:1px solid #d0d7de;padding:9px 12px;color:{actual_color};">{html.escape(e['actual'])}</td>
              <td style="border:1px solid #d0d7de;padding:9px 12px;text-align:center;font-weight:bold;color:{status_color};">{e['status']}</td>
            </tr>
            """)

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
</head>
<body style="margin:0;padding:24px;font-family:Arial,'Segoe UI',sans-serif;color:#111111;background-color:#ffffff;line-height:1.5;">
  <div style="max-width:960px;margin:0 auto;">
    <div style="font-size:14px;color:#111111;margin-bottom:18px;">Gowthami Ankem</div>
    
    <div style="font-size:15px;font-weight:bold;color:#111111;margin-bottom:4px;">Gowthami Ankem</div>
    <div style="font-size:15px;font-weight:bold;color:#111111;margin-bottom:12px;">Automation Test Report</div>
    
    <div style="font-size:14px;color:#111111;margin-bottom:20px;">
      Total Tests: {total}&nbsp;&nbsp;&nbsp;&nbsp;Passed: <span style="color:#28a745;font-weight:bold;">{passed}</span>&nbsp;&nbsp;&nbsp;&nbsp;Failed: <span style="color:#dc3545;font-weight:bold;">{failed}</span>
    </div>

    <table cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;font-size:13px;border:1px solid #d0d7de;margin-bottom:24px;">
      <thead>
        <tr style="background-color:#f6f8fa;text-align:left;color:#24292f;font-weight:600;border-bottom:2px solid #d0d7de;">
          <th style="border:1px solid #d0d7de;padding:10px 12px;">Module</th>
          <th style="border:1px solid #d0d7de;padding:10px 12px;">Test Case Name</th>
          <th style="border:1px solid #d0d7de;padding:10px 12px;">Expected Result</th>
          <th style="border:1px solid #d0d7de;padding:10px 12px;">Actual Result</th>
          <th style="border:1px solid #d0d7de;padding:10px 12px;text-align:center;">Status</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows_html)}
      </tbody>
    </table>

    <div style="font-size:14px;color:#111111;margin-bottom:18px;">Please find attached detailed reports.</div>
    <div style="font-size:14px;color:#111111;">
      Regards,<br>
      Gowthami
    </div>
  </div>
</body>
</html>"""

    # --------------------------------------------------------------
    # Report Attachments
    # --------------------------------------------------------------

    def _normalise_report_paths(
        self,
        report_path: Optional[Any] = None,
        report_paths: Optional[Any] = None,
    ) -> List[tuple]:
        if report_paths is not None:
            if isinstance(report_paths, dict):
                return list(report_paths.items())
            if isinstance(report_paths, (list, tuple, set)):
                return [(Path(p).stem.upper(), p) for p in report_paths]
            return [("REPORT", report_paths)]
        if report_path:
            return [("REPORT", report_path)]
        return []

    def _attach_reports(
        self,
        message: Any,
        report_path: Optional[Any] = None,
        report_paths: Optional[Any] = None,
    ) -> None:
        if not self.attach_report:
            logger.info("HTML report attachments disabled by .env (EMAIL_ATTACH_REPORT=false)")
            return

        from email import encoders
        from email.mime.base import MIMEBase
        import zipfile

        all_paths = self._normalise_report_paths(report_path, report_paths)
        seen_paths = set()
        total_attached_bytes = 0

        for station_label, path_val in all_paths:
            if not path_val:
                continue
            path = Path(path_val)
            if not path.is_file():
                logger.warning("Report file not found; skipping attachment: %s", path)
                continue

            resolved_path = str(path.resolve())
            if resolved_path in seen_paths:
                continue
            seen_paths.add(resolved_path)

            size = path.stat().st_size

            # If the HTML report is small (<= 6 MB), attach the .html directly.
            # If the HTML report is large (> 6 MB), compress to .zip and attach ONLY the .zip
            # to guarantee the total email size stays strictly below the 35 MB server limit.
            if size <= self.HTML_DIRECT_ATTACH_LIMIT:
                if total_attached_bytes + size <= self.MAX_TOTAL_PAYLOAD_SIZE:
                    html_attachment = MIMEBase("text", "html")
                    with path.open("rb") as rf:
                        html_attachment.set_payload(rf.read())
                    encoders.encode_base64(html_attachment)
                    html_attachment.add_header("Content-Disposition", f'attachment; filename="{path.name}"')
                    message.attach(html_attachment)
                    total_attached_bytes += size
                    logger.info(
                        "Attached HTML report for %s: %s (%.2f MB, total: %.2f MB)",
                        station_label,
                        path.name,
                        size / (1024 * 1024),
                        total_attached_bytes / (1024 * 1024),
                    )
                else:
                    logger.warning(
                        "Skipping HTML report %s: total attachment size would exceed 18 MB server limit",
                        path.name,
                    )
            else:
                try:
                    zip_path = path.with_suffix(".zip")
                    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                        zf.write(path, arcname=path.name)

                    zip_size = zip_path.stat().st_size
                    if total_attached_bytes + zip_size <= self.MAX_TOTAL_PAYLOAD_SIZE:
                        zip_attachment = MIMEBase("application", "zip")
                        with zip_path.open("rb") as rf:
                            zip_attachment.set_payload(rf.read())
                        encoders.encode_base64(zip_attachment)
                        zip_attachment.add_header("Content-Disposition", f'attachment; filename="{zip_path.name}"')
                        message.attach(zip_attachment)
                        total_attached_bytes += zip_size
                        logger.info(
                            "Attached compressed ZIP report for %s: %s (%.2f MB, raw: %.2f MB, total: %.2f MB)",
                            station_label,
                            zip_path.name,
                            zip_size / (1024 * 1024),
                            size / (1024 * 1024),
                            total_attached_bytes / (1024 * 1024),
                        )
                    else:
                        logger.warning(
                            "Skipping ZIP report %s: size (%.2f MB) would exceed 18 MB server limit",
                            zip_path.name,
                            zip_size / (1024 * 1024),
                        )
                except Exception as e:
                    logger.warning("Could not create/attach zip archive for %s: %s", path, e)

    # --------------------------------------------------------------
    # SMTP Delivery
    # --------------------------------------------------------------

    def _send_smtp_message(self, message: Any) -> bool:
        server = None
        try:
            logger.info("Creating SMTP connection to %s:%s", self.smtp_server, self.smtp_port)
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=45)
            logger.info("Starting TLS")
            server.starttls()
            logger.info("Logging in as %s", self.sender_email)
            server.login(self.sender_email, self.sender_password)

            recipients = self.receiver_emails + self.cc_emails
            logger.info("Delivering email to %s", recipients)
            server.sendmail(self.sender_email, recipients, message.as_string())
            logger.info("Email delivered successfully!")
            return True
        except Exception as error:
            logger.error("%s: %s", type(error).__name__, error)
            logger.error(traceback.format_exc())
            raise
        finally:
            if server is not None:
                try:
                    server.quit()
                except Exception:
                    logger.warning("SMTP connection was already closed or could not quit cleanly")

    # --------------------------------------------------------------
    # Public Send Methods
    # --------------------------------------------------------------

    def send_session_report(
        self,
        meta: Dict[str, Any],
        records: List[Any],
        station_reports: Optional[Dict[str, str]] = None,
        consolidated_report: Optional[str] = None,
    ) -> bool:
        """
        Send a consolidated smoke test report for the pytest session.

        Reads configuration strictly from .env and compiles results for all
        executed airports/stations into a single email body.
        """
        self._check_settings()

        requested_stations = [
            s.strip().upper()
            for s in str(meta.get("airports", "")).split(",")
            if s.strip() and s.strip() != "-"
        ]
        summaries = self.summarize_records(records, requested_stations=requested_stations)
        if not summaries:
            logger.warning("No test summaries generated from records; email not sent.")
            return False

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        body_html = self.build_email_body(records=records)
        body_text = self.build_plain_text(records=records)

        total_failed = sum(s["failed"] for s in summaries.values())
        total_executed = sum(s["total"] for s in summaries.values())
        if total_executed == 0:
            verdict = "NO TESTS EXECUTED"
        elif total_failed:
            verdict = "FAILED"
        else:
            verdict = "PASSED"

        project = meta.get("project", "AUTOMATION")
        env = meta.get("env", "QA")
        stations_label = ", ".join(summaries.keys()) if len(summaries) <= 3 else "MULTI-STATION"

        subject = f"Automation Smoke Test Summary - [{str(project).upper()}] [{str(env).upper()}] [{stations_label}] - {verdict}"

        message = MIMEMultipart("mixed")
        message["From"] = self.sender_email
        message["To"] = ", ".join(self.receiver_emails)
        if self.cc_emails:
            message["Cc"] = ", ".join(self.cc_emails)
        message["Subject"] = subject

        alternatives = MIMEMultipart("alternative")
        alternatives.attach(MIMEText(body_text, "plain", "utf-8"))
        alternatives.attach(MIMEText(body_html, "html", "utf-8"))
        message.attach(alternatives)

        # Attach consolidated report (or station reports if consolidated is unavailable)
        all_report_paths: Dict[str, str] = {}
        if consolidated_report and Path(consolidated_report).is_file():
            all_report_paths["CONSOLIDATED"] = consolidated_report
        elif station_reports:
            all_report_paths.update(station_reports)

        self._attach_reports(message, report_paths=all_report_paths)

        return self._send_smtp_message(message)

    def send_execution_report(
        self,
        project: Any,
        env: Any,
        browser: Any,
        xml_file: Any,
        report_path: Optional[Any] = None,
        station: Optional[Any] = None,
        report_paths: Optional[Any] = None,
    ) -> bool:
        """
        Send a consolidated email from JUnit XML results.

        Reads configuration strictly from .env and formats the email body
        according to the required summary layout.
        """
        self._check_settings()

        summaries = self.parse_pytest_results(xml_file, station=station)
        if not summaries:
            logger.warning("No test cases found in %s; email not sent.", xml_file)
            return False

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        body_html = self.build_email_body(summaries=summaries)
        body_text = self.build_plain_text(summaries=summaries)

        total_failed = sum(s["failed"] for s in summaries.values())
        total_executed = sum(s["total"] for s in summaries.values())
        if total_executed == 0:
            verdict = "NO TESTS EXECUTED"
        elif total_failed:
            verdict = "FAILED"
        else:
            verdict = "PASSED"

        stations_label = ", ".join(summaries.keys()) if len(summaries) <= 3 else "MULTI-STATION"
        subject = f"Automation Smoke Test Summary - [{str(project).upper()}] [{str(env).upper()}] [{stations_label}] - {verdict}"

        message = MIMEMultipart("mixed")
        message["From"] = self.sender_email
        message["To"] = ", ".join(self.receiver_emails)
        if self.cc_emails:
            message["Cc"] = ", ".join(self.cc_emails)
        message["Subject"] = subject

        alternatives = MIMEMultipart("alternative")
        alternatives.attach(MIMEText(body_text, "plain", "utf-8"))
        alternatives.attach(MIMEText(body_html, "html", "utf-8"))
        message.attach(alternatives)

        self._attach_reports(message, report_path=report_path, report_paths=report_paths)

        return self._send_smtp_message(message)

    def send_station_report(
        self,
        meta: Dict[str, Any],
        station: str,
        station_summary: Optional[Dict[str, Any]] = None,
        subset: Optional[List[Any]] = None,
        path: Optional[str] = None,
        recipients: Optional[Dict[str, List[str]]] = None,
    ) -> bool:
        """Single-station email method for backwards compatibility."""
        if subset:
            summaries = self.summarize_records(subset, requested_stations=[station])
        else:
            total = station_summary.get("total", 0) if station_summary else 0
            passed = station_summary.get("passed", 0) if station_summary else 0
            failed = station_summary.get("failed", 0) if station_summary else 0
            skipped = station_summary.get("skipped", 0) if station_summary else 0
            warnings = station_summary.get("warnings", 0) if station_summary else 0
            duration = meta.get("duration", 0.0)
            pass_pct = (passed / total * 100.0) if total else 0.0
            fail_pct = (failed / total * 100.0) if total else 0.0

            summaries = {
                station.strip().upper(): {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "skipped": skipped,
                    "warnings": warnings,
                    "duration": duration,
                    "formatted_duration": self._format_duration(duration),
                    "pass_percent": f"{pass_pct:.2f} %",
                    "fail_percent": f"{fail_pct:.2f} %",
                    "passed_tests": [],
                    "failed_tests": [],
                    "skipped_tests": [],
                    "warning_tests": [],
                }
            }

        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        body_html = self.build_email_body(summaries=summaries)
        body_text = self.build_plain_text(summaries=summaries)

        project = meta.get("project", "AUTOMATION")
        env = meta.get("env", "QA")
        total_failed = sum(s["failed"] for s in summaries.values())
        verdict = "FAILED" if total_failed else "PASSED"

        subject = f"Automation Smoke Test Summary - [{str(project).upper()}] [{str(env).upper()}] [{station.upper()}] - {verdict}"

        message = MIMEMultipart("mixed")
        message["From"] = self.sender_email
        message["To"] = ", ".join(self.receiver_emails)
        if self.cc_emails:
            message["Cc"] = ", ".join(self.cc_emails)
        message["Subject"] = subject

        alternatives = MIMEMultipart("alternative")
        alternatives.attach(MIMEText(body_text, "plain", "utf-8"))
        alternatives.attach(MIMEText(body_html, "html", "utf-8"))
        message.attach(alternatives)

        if path:
            self._attach_reports(message, report_path=path)

        return self._send_smtp_message(message)
