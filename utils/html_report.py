"""Self-contained, Extent-style HTML report (single file, no external assets).

* Dashboard: totals, pass-rate donut, per-airport table
* Per test: status, airport, TC number, steps, WARNING/ERROR log lines,
  error traceback and screenshots (embedded as base64, click to enlarge)
* One .html file -> easy to attach to e-mail, opens offline in any browser

E-mail delivery is enabled by default when valid station recipients are configured; use --no-email to disable it.
"""
import html
import json
import re
import os
import platform
import time
from datetime import datetime
from pathlib import Path

import pytest

from utils import report_context as rc

_PHASE_STATUS = {"passed": "PASSED", "failed": "FAILED", "skipped": "SKIPPED"}


def norm_tc(value) -> str:
    if not value:
        return ""
    text = re.sub(r"^TC[\s_\-]*", "", str(value).strip().upper())
    return str(int(text)) if text.isdigit() else text


def write_html(path: str | Path, document: str) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(document, encoding="utf-8")
    return destination


def write_json(path: str | Path, payload: dict) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return destination


def _tc_label(marker) -> str:
    if not marker or not marker.args:
        return ""
    number = norm_tc(marker.args[0])
    return f"TC{int(number):02d}" if number.isdigit() else f"TC-{number}"


# --------------------------------------------------------------------------- options
def pytest_addoption(parser):
    group = parser.getgroup("html-report")
    group.addoption("--report-dir", action="store", default="reports", help="Folder for the HTML report")
    group.addoption("--report-title", action="store", default="Sanity Automation Execution Report")


def pytest_configure(config):
    if hasattr(config, "workerinput"):  # xdist worker: the controller builds the report
        return
    config.pluginmanager.register(HtmlReportPlugin(config), "html-report-plugin")


# --------------------------------------------------------------------------- plugin

def cfg_station(item):
    values=[v for k,v in item.user_properties if k == "stations"]
    if values:
        return values[-1]
    from utils.email_sender import EmailSender
    proj = item.config.getoption('--project', default=None) or getattr(item.config, 'framework_project', None)
    default_st, _ = EmailSender.get_excel_station_config(proj)
    return item.config.getoption('--station', default=default_st)

class HtmlReportPlugin:
    def __init__(self, config):
        self.config = config
        self.records: dict = {}
        self.framework_warnings: list = []
        self.started = time.time()
        self.report_path = ""
        self.capture = rc.LogCapture(level=0)

    # ---- lifecycle
    def pytest_sessionstart(self, session):
        self.started = time.time()
        self.records.clear()
        import logging
        logging.getLogger().addHandler(self.capture)

    def pytest_unconfigure(self, config):
        import logging
        logging.getLogger().removeHandler(self.capture)

    def pytest_runtest_setup(self, item):
        import logging
        logging.getLogger(__name__).info('TEST START | %s', item.nodeid)

    def pytest_runtest_teardown(self, item, nextitem):
        import logging
        logging.getLogger(__name__).info('TEST TEARDOWN | %s', item.nodeid)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_protocol(self, item, nextitem):
        params = getattr(getattr(item, "callspec", None), "params", {}) or {}
        marker = item.get_closest_marker("tc")
        raw_doc = (getattr(item.function, "__doc__", "") or "").strip()
        scenario_title, _ = extract_clean_scenario(raw_doc, item.name)

        proj_values = [v for k,v in item.user_properties if k == "project"]
        rec_project = proj_values[-1] if proj_values else (getattr(item.config, "framework_project", "") or "")

        record = rc.TestRecord(
            nodeid=item.nodeid,
            name=item.name,
            description=scenario_title,
            project=str(rec_project),
            airport=str(params.get("station") or params.get("airport") or ",".join(dict.fromkeys(v for k,v in item.user_properties if k == "stations")) or cfg_station(item) or "-"),
            tc=_tc_label(marker),
            markers=sorted({m.name for m in item.iter_markers() if m.name not in ("tc", "parametrize", "usefixtures")}),
            start=time.time(),
        )
        record.full_doc = raw_doc
        self.records[item.nodeid] = record
        station_values = [v for k,v in item.user_properties if k == "stations"]
        record.stations = [str(params["station"])] if params.get("station") else ([s for s in (station_values[-1].split(",") if station_values else []) if s] or [record.airport])
        rc.set_current(record)
        yield
        record.duration = time.time() - record.start
        if record.status == "RUNNING":
            record.status = "PASSED"
        rc.set_current(None)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        setattr(item, f"rep_{report.when}", report)  # used by fixtures to detect failures
        if report.failed:
            page = getattr(item, "_framework_page", None)
            if page is not None and not page.is_closed():
                try:
                    from pages.Common_Base_Page.Base_Page import BasePage
                    from utils import report_context
                    station_values=[v for k,v in item.user_properties if k == "stations"]
                    station=station_values[-1] if station_values else cfg_station(item)
                    proj_values=[v for k,v in item.user_properties if k == "project"]
                    proj_val=proj_values[-1] if proj_values else (item.config.getoption('--project') or getattr(item.config, 'framework_project', 'AUTOMATION'))
                    path=BasePage.capture_failure(page, project=proj_val, station=station,
                                                 test_name=item.name, report_context=report_context,
                                                 error_message=report.longreprtext)
                    if path:
                        setattr(item, "_failure_screenshot_captured", True)
                        try:
                            import allure
                            allure.attach.file(path, name=f"{item.name} failure", attachment_type=allure.attachment_type.PNG)
                        except Exception:
                            pass
                except Exception:
                    pass

        record = self.records.get(item.nodeid)
        if record is None:
            return
        if report.when == "setup" and report.failed:
            record.status, record.error = "ERROR", report.longreprtext
        elif report.when == "call":
            record.status = _PHASE_STATUS.get(report.outcome, "PASSED")
            if report.failed:
                record.error = report.longreprtext
        elif report.when == "teardown" and report.failed and record.status == "PASSED":
            record.status, record.error = "ERROR", report.longreprtext
        if report.skipped:
            record.status = "SKIPPED"
            reason = report.longrepr[2] if isinstance(report.longrepr, tuple) else str(report.longrepr)
            record.skip_reason = reason.replace("Skipped: ", "")

    def pytest_warning_recorded(self, warning_message, when, nodeid, location):
        self.framework_warnings.append(f"{warning_message.category.__name__}: {warning_message.message}")

    # ---- report
    @pytest.hookimpl
    def pytest_sessionfinish(self, session, exitstatus):
        records = list(self.records.values())
        if not records:
            return
        cfg = self.config
        from utils.email_sender import EmailSender

        # Resolve active project(s) and station mapping dynamically
        station_to_proj = getattr(cfg, "framework_station_to_project", {})
        fw_project = getattr(cfg, "framework_project", None)
        cli_project = cfg.getoption("--project", default=None)

        # Helper to reliably resolve which station a test record was executed for
        def _get_rec_station(r):
            airport = str(getattr(r, "airport", "")).strip().upper()
            if airport and airport not in ("-", "DEFAULT", "UNKNOWN", "NONE", "ALL"):
                return airport
            name_val = str(getattr(r, "name", ""))
            m = re.search(r"\[([A-Z0-9_-]+)\]", name_val)
            if m:
                return m.group(1).upper()
            node_val = str(getattr(r, "nodeid", ""))
            m = re.search(r"\[([A-Z0-9_-]+)\]", node_val)
            if m:
                return m.group(1).upper()
            st_list = [
                str(s).strip().upper() for s in getattr(r, "stations", [])
                if str(s).strip().upper() not in ("-", "DEFAULT", "UNKNOWN", "NONE", "ALL")
            ]
            if len(st_list) == 1:
                return st_list[0]
            return ""

        # Collect distinct projects and stations from executed records
        executed_projects = []
        executed_stations = []
        for r in records:
            p = getattr(r, "project", None)
            st = _get_rec_station(r)
            if not p or str(p).strip() in ("-", "None", ""):
                p = station_to_proj.get(st, {}).get("project")
            if p and p not in executed_projects:
                executed_projects.append(p)
            if st and st not in executed_stations:
                executed_stations.append(st)

        resolved_project = cli_project or (executed_projects[0] if len(executed_projects) == 1 else (", ".join(executed_projects) if executed_projects else fw_project))
        if not resolved_project or resolved_project == "-":
            resolved_project = fw_project or "AUTOMATION"

        resolved_env = cfg.getoption("--env", default=None) or getattr(cfg, "framework_env", "qa")

        excel_code, _ = EmailSender.get_excel_station_config(cli_project or (executed_projects[0] if executed_projects else fw_project))
        resolved_station = cfg.getoption("--station", default=excel_code) or excel_code
        if not resolved_station or str(resolved_station).strip().upper() in ("-", "DEFAULT", "UNKNOWN", "NONE"):
            resolved_station = excel_code or "DXB"
        resolved_station = str(resolved_station).strip().upper()
        if not getattr(cfg, "framework_stations_requested", []):
            cfg.framework_stations_requested = [resolved_station]

        meta = {
            "title": cfg.getoption("--report-title"),
            "project": resolved_project,
            "env": resolved_env,
            "browser": getattr(cfg, "_framework_execution_settings", {}).get("browser", cfg.getoption("--browser") or "chromium"),
            "airports": ", ".join(executed_stations) if executed_stations else (", ".join(getattr(cfg, "framework_stations_requested", [])) or resolved_station),
            "started": datetime.fromtimestamp(self.started).strftime("%d %b %Y %H:%M:%S"),
            "duration": time.time() - self.started,
            "ended": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
            "deselected": getattr(cfg, "framework_deselected_count", 0),
            "host": platform.node(),
            "warnings": self.framework_warnings,
            "plan_warnings": getattr(cfg, "plan_warnings", []),
        }
        summary = summarize(records)
        summary["selected"] = len(records)
        summary["deselected"] = getattr(cfg, "framework_deselected_count", 0)

        out_dir = cfg.getoption("--report-dir")
        if not os.path.isabs(out_dir):
            out_dir = os.path.join(str(cfg.rootpath), out_dir, str(meta['project']), str(meta['env']))
        os.makedirs(out_dir, exist_ok=True)
        stamp = datetime.fromtimestamp(self.started).strftime("%Y%m%d_%H%M%S")
        name = f"{str(meta['project']).upper()}_{str(meta['env']).upper()}_{stamp}.html"
        self.report_path = os.path.join(out_dir, name)
        document = build_html(meta, summary, records)
        write_html(self.report_path, document)
        write_html(os.path.join(out_dir, "latest_report.html"), document)

        # Remove any legacy comma-joined multi-station files (e.g. DXB,BFS,SZG_Report.html)
        import glob
        for comma_pattern in (
            os.path.join(str(cfg.rootpath), "reports", "*[,]*"),
            os.path.join(out_dir, "*[,]*"),
        ):
            for comma_file in glob.glob(comma_pattern):
                try:
                    os.remove(comma_file)
                except Exception:
                    pass

        # Helper to reliably resolve which station a test record was executed for
        def _get_rec_station(r):
            airport = str(getattr(r, "airport", "")).strip().upper()
            if airport and airport not in ("-", "DEFAULT", "UNKNOWN", "NONE", "ALL"):
                return airport
            name_val = str(getattr(r, "name", ""))
            m = re.search(r"\[([A-Z0-9_-]+)\]", name_val)
            if m:
                return m.group(1).upper()
            node_val = str(getattr(r, "nodeid", ""))
            m = re.search(r"\[([A-Z0-9_-]+)\]", node_val)
            if m:
                return m.group(1).upper()
            st_list = [
                str(s).strip().upper() for s in getattr(r, "stations", [])
                if str(s).strip().upper() not in ("-", "DEFAULT", "UNKNOWN", "NONE", "ALL")
            ]
            if len(st_list) == 1:
                return st_list[0]
            return ""

        # Expand records into station-specific views without mixing station results
        import copy
        station_reports = {}
        base = os.path.splitext(self.report_path)[0]
        raw_requested = getattr(cfg, "framework_stations_requested", [])
        requested = [
            s.strip().upper() for s in raw_requested
            if s and str(s).strip().upper() not in ("-", "DEFAULT", "UNKNOWN", "NONE")
        ]
        if not requested:
            requested = [resolved_station]

        for station in requested:
            subset = []
            for record in records:
                st = _get_rec_station(record)
                if st == station:
                    clone = copy.copy(record)
                    clone.airport = station
                    subset.append(clone)
                elif not st:
                    mapped = [str(s).strip().upper() for s in getattr(record, "stations", [])]
                    if station in mapped or "ALL" in mapped or not mapped:
                        clone = copy.copy(record)
                        clone.airport = station
                        subset.append(clone)

            if not subset:
                continue

            # Determine project and environment specific to this station
            st_info = station_to_proj.get(station, {})
            st_project = st_info.get("project")
            if not st_project:
                for r in subset:
                    p = getattr(r, "project", None)
                    if p and str(p).strip() not in ("-", "None", ""):
                        st_project = p
                        break
            if not st_project:
                st_project = resolved_project

            st_env = st_info.get("env") or meta.get("env", "qa")

            station_meta = dict(
                meta,
                project=st_project,
                env=st_env,
                airports=station,
                title=f"{meta['title']} - {station}",
                duration=sum(r.duration for r in subset),
            )
            station_file = os.path.join(out_dir, f"{station}_Report.html")
            root_station_file = os.path.join(str(cfg.rootpath), "reports", f"{station}_Report.html")
            station_reports[station] = root_station_file

            station_summary = summarize(subset)
            station_summary["selected"] = len(subset)
            station_summary["deselected"] = 0
            station_doc = build_html(station_meta, station_summary, subset)

            write_html(station_file, station_doc)
            write_html(root_station_file, station_doc)
            write_html(f"{base}_{station}.html", station_doc)

        # Set primary report and sync Extent_Report.html to the primary station's report
        primary_station = executed_stations[0] if executed_stations else (requested[0] if requested else resolved_station)
        primary_report = station_reports.get(primary_station, os.path.join(str(cfg.rootpath), "reports", f"{primary_station}_Report.html"))
        if os.path.exists(primary_report):
            with open(primary_report, "r", encoding="utf-8") as f:
                primary_doc = f.read()
            write_html(os.path.join(str(cfg.rootpath), "reports", "Extent_Report.html"), primary_doc)
            write_html(os.path.join(str(cfg.rootpath), "reports", "latest_report.html"), primary_doc)

        cfg._extent_report_path = primary_report
        cfg._station_reports = station_reports

        write_json(os.path.join(out_dir, "summary.json"), {
            "meta": {k: v for k, v in meta.items() if k not in ("warnings", "plan_warnings")},
            "summary": summary})

        if cfg.getoption("--no-email"):
            cfg._email_status = "Skipped (--no-email flag set)"
        elif not getattr(cfg, "_email_delivered", False):
            from utils.email_sender import EmailSender
            try:
                sender = EmailSender()
                delivered = sender.send_session_report(
                    meta=meta,
                    records=records,
                    station_reports=station_reports,
                    consolidated_report=None,
                )
                if delivered:
                    cfg._email_delivered = True
                    recipients = ", ".join(sender.receiver_emails)
                    cfg._email_status = f"Sent successfully to {recipients}"
                else:
                    cfg._email_status = "Skipped (no executed test summaries generated)"
            except Exception as error:
                err_text = f"{type(error).__name__}: {error}"
                self.framework_warnings.append(f"E-mail delivery failed: {err_text}")
                cfg._email_status = f"FAILED ({err_text})"
                print(f"\n[report] E-mail delivery problem: {err_text}")

    def pytest_terminal_summary(self, terminalreporter):
        station_reports = getattr(self.config, "_station_reports", {})
        if station_reports:
            terminalreporter.write_sep("-", "Station HTML Reports")
            for st, p in sorted(station_reports.items()):
                terminalreporter.write_line(f"{st}: {p}")
        elif self.report_path:
            terminalreporter.write_sep("-", "HTML report")
            terminalreporter.write_line(self.report_path)

        email_status = getattr(self.config, "_email_status", None)
        if email_status:
            terminalreporter.write_sep("-", "Email Delivery")
            terminalreporter.write_line(email_status)


# --------------------------------------------------------------------------- summary
def summarize(records) -> dict:
    result = {"total": len(records), "passed": 0, "failed": 0, "skipped": 0, "warnings": 0,
              "errors_logged": 0, "airports": {}}
    for r in records:
        result[r.group] += 1
        result["warnings"] += r.warnings
        result["errors_logged"] += r.errors
        a = result["airports"].setdefault(r.airport, {"total": 0, "passed": 0, "failed": 0, "skipped": 0})
        a["total"] += 1
        a[r.group] += 1
    result["pass_rate"] = round(100 * result["passed"] / result["total"], 1) if result["total"] else 0
    return result


# --------------------------------------------------------------------------- ExtentReports 2.41.1
def _e(value) -> str:
    return html.escape(str(value), quote=True)


def _format_duration(seconds: float) -> str:
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


def _clean_test_name(name: str) -> str:
    clean = re.sub(r"\[.*?\]$", "", str(name or "")).strip()
    return clean or str(name or "")


def _clean_error_message(error: str) -> str:
    """Extract clean error detail without dumping Python code, tracebacks, or objects."""
    if not error:
        return ""
    text = str(error).strip()
    if not text:
        return ""
    # Strip Python object reprs
    text = re.sub(r"<[a-zA-Z_][\w.]*\s+object\s+at\s+0x[0-9a-fA-F]+>", "", text)
    text = re.sub(r"<Page\s+url=[^>]+>", "", text)
    text = re.sub(r"<Locator\s+frame=[^>]+>", "", text)

    m_delay = re.search(r"Delay Time in ms:\s*\d+", text)
    if m_delay:
        return m_delay.group(0)

    for pattern in (
        r"AssertionError:\s*([^\r\n]+)",
        r"(Locator expected\s+[^\r\n]+)",
        r"TimeoutError:\s*([^\r\n]+)",
        r"Exception:\s*([^\r\n]+)",
        r"Error:\s*([^\r\n]+)",
    ):
        m = re.search(pattern, text)
        if m:
            clean = m.group(1).replace("AssertionError:", "").strip()
            return clean[:150]

    lines = [
        l.strip()
        for l in text.splitlines()
        if l.strip() and not l.strip().startswith(("Traceback", "File ", "at ", "E   ", "+", "-"))
    ]
    if lines:
        return lines[-1][:150]
    return "Test execution failure"


def _clean_log_text(msg: str) -> str:
    """Clean log message of raw Python objects, Base64 strings, and internal noise."""
    if not msg:
        return ""
    s = str(msg).strip()
    s = re.sub(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]{50,}", "[IMAGE_DATA]", s)
    s = re.sub(r"<[a-zA-Z_][\w.]*\s+object\s+at\s+0x[0-9a-fA-F]+>", "", s)
    s = re.sub(r"<Page\s+url=[^>]+>", "", s)
    s = re.sub(r"<Locator\s+frame=[^>]+>", "", s)
    return s.strip()


def extract_clean_scenario(raw_doc: str, fallback_name: str) -> tuple[str, str]:
    """
    Extracts a clean scenario title and secondary details/steps from a docstring.
    Guarantees:
      - Never repeats the scenario title inside the details block.
      - Strips decorative banners like '=== INTRODUCTION ===' or '=== TEST OVERVIEW ==='.
      - Strips 'What this test does:' or 'Test Scenario:' headers.
      - Returns (clean_scenario_title, clean_details_text).
    """
    if not raw_doc or not raw_doc.strip():
        return fallback_name, ""

    lines = [line.strip() for line in raw_doc.strip().splitlines()]
    content_lines = []
    for line in lines:
        if not line:
            content_lines.append("")
            continue
        # Remove divider lines like "==============  INTRODUCTION ================"
        if re.match(r"^[=\-*~#]{3,}.*[=\-*~#]{3,}$", line):
            continue
        content_lines.append(line)

    scenario_title = ""
    scenario_idx = -1
    for i, line in enumerate(content_lines):
        clean_l = line.strip()
        if not clean_l:
            continue
        low = clean_l.lower()
        if low.startswith("test scenario:"):
            scenario_title = clean_l[14:].strip()
            scenario_idx = i
            break
        elif low.startswith("scenario:"):
            scenario_title = clean_l[9:].strip()
            scenario_idx = i
            break
        elif low.startswith("what this test does:"):
            for j in range(i + 1, len(content_lines)):
                next_l = content_lines[j].strip()
                if next_l:
                    scenario_title = next_l
                    scenario_idx = j
                    break
            if scenario_title:
                break

    # If still not found, pick the first descriptive line
    if not scenario_title:
        for i, line in enumerate(content_lines):
            clean_l = line.strip()
            if not clean_l:
                continue
            low = clean_l.lower()
            if any(low.startswith(k) for k in ("introduction", "test overview", "author", "created", "modified")):
                continue
            scenario_title = clean_l
            scenario_idx = i
            break

    if not scenario_title:
        scenario_title = fallback_name

    # Clean up multi-line scenario title if ending in colon
    if scenario_title.endswith(":"):
        scenario_title = scenario_title[:-1].strip()

    # Now extract details/steps (if any), strictly excluding the scenario title
    details_lines = []
    start_collecting = False
    for i, line in enumerate(content_lines):
        clean_l = line.strip()
        if not clean_l:
            if start_collecting and details_lines and details_lines[-1] != "":
                details_lines.append("")
            continue
        if i <= scenario_idx:
            continue
        low = clean_l.lower()
        if low.startswith("what this test does:") or low.startswith("test scenario:"):
            continue
        if clean_l == scenario_title:
            continue
        if low.startswith("it checks the entire workflow") or low.startswith("steps:"):
            start_collecting = True
            details_lines.append(clean_l)
            continue
        if start_collecting or re.match(r"^\d+[\.\)]", clean_l) or clean_l.startswith(("-", "*", "•")):
            start_collecting = True
            details_lines.append(clean_l)

    clean_details = "\n".join(details_lines).strip()
    return scenario_title, clean_details


def normalize_step_name(name: str) -> str:
    """Normalize step text for deduplication comparison."""
    s = re.sub(r"^(step\s*\d+[\.\d*]*\s*:\s*|prerequisite\s*:\s*)", "", str(name).strip(), flags=re.IGNORECASE)
    s = re.sub(r"[\s_-]+", " ", s).strip().lower()
    return s


def build_html(meta: dict, summary: dict, records) -> str:
    """Generate modern, self-contained ExtentReports HTML report."""
    template_file = Path(__file__).resolve().parent / "extent_template.html"
    if not template_file.is_file():
        raise FileNotFoundError(f"ExtentReports template not found: {template_file}")

    template = template_file.read_text(encoding="utf-8")

    started_val = meta.get("started")
    if isinstance(started_val, (int, float)):
        started_dt = datetime.fromtimestamp(started_val)
    else:
        try:
            started_dt = datetime.strptime(str(started_val), "%d %b %Y %H:%M:%S")
        except Exception:
            started_dt = datetime.now()

    started_str = started_dt.strftime("%Y-%m-%d %H:%M:%S")
    ended_dt = datetime.now()
    ended_str = ended_dt.strftime("%Y-%m-%d %H:%M:%S")
    total_duration_str = _format_duration(meta.get("duration", 0.0))

    user_name = os.getenv("USERNAME") or os.getenv("USER") or "avileap"
    os_name = f"{platform.system()} {platform.release()}"
    python_version = platform.python_version()
    host_name = platform.node()
    raw_project = meta.get("project")
    project = str(raw_project if raw_project and raw_project != "-" else "AUTOMATION").upper()
    raw_env = meta.get("env")
    env = str(raw_env if raw_env and raw_env != "-" else "QA").upper()
    browser = str(meta.get("browser", "chromium")).capitalize()

    total_count = summary.get("total", len(records))
    pass_count = summary.get("passed", 0)
    fail_count = summary.get("failed", 0)
    skip_count = summary.get("skipped", 0)
    pass_rate = f"{summary.get('pass_rate', 0)}%"

    overall_status = "PASSED" if fail_count == 0 else "FAILED"
    overall_status_class = "pass" if fail_count == 0 else "fail"

    nav_items = []
    detail_panes = []

    now_ts = datetime.now().timestamp()
    for idx, r in enumerate(records):
        test_id = f"test_{idx}"
        name = _clean_test_name(getattr(r, "name", "Unknown Test"))
        st_raw = str(getattr(r, "status", "PASSED")).upper()
        if st_raw in ("FAILED", "ERROR"):
            status = "fail"
            status_label = "FAILED"
        elif st_raw == "SKIPPED":
            status = "skip"
            status_label = "SKIPPED"
        else:
            status = "pass"
            status_label = "PASSED"

        # Scenario extraction
        scenario_title, scenario_details = extract_clean_scenario(
            getattr(r, "full_doc", "") or getattr(r, "description", ""),
            name
        )

        rec_start = getattr(r, "start", 0.0)
        if not rec_start or rec_start < 86400:
            rec_start = now_ts
        rec_dur = max(float(getattr(r, "duration", 0.0) or 0.0), 0.0)
        rec_start_dt = datetime.fromtimestamp(rec_start)
        rec_end_dt = datetime.fromtimestamp(rec_start + rec_dur)

        r_start_str = rec_start_dt.strftime("%Y-%m-%d %H:%M:%S")
        r_end_str = rec_end_dt.strftime("%Y-%m-%d %H:%M:%S")
        r_dur_str = _format_duration(rec_dur)

        markers = getattr(r, "markers", [])
        tags_html = "".join(f"<span class='meta-badge' style='margin-left:4px;'>#{_e(m)}</span>" for m in markers)

        # Left Navigator Item
        nav_item_html = f"""<div class="test-nav-item" data-id="{test_id}" data-status="{status}" data-text="{_e(name)} {_e(scenario_title)}" onclick="selectTest('{test_id}')">
  <div class="test-nav-head">
    <span class="badge {status}">{status_label}</span>
    <span class="test-nav-duration">{r_dur_str}</span>
  </div>
  <div class="test-nav-title">{_e(name)}</div>
  <div class="test-nav-scenario">{_e(scenario_title)}</div>
</div>"""
        nav_items.append(nav_item_html)

        # Right Detail Pane - Scenario details block (only when distinct details exist)
        scenario_details_html = ""
        if scenario_details:
            scenario_details_html = f"<div class='scenario-details'>{_e(scenario_details)}</div>"

        # Failure banner (if failed)
        failure_alert_html = ""
        if status == "fail":
            err_msg = _clean_error_message(getattr(r, "error", ""))
            raw_err = getattr(r, "error", "")
            traceback_block = ""
            if raw_err and raw_err != err_msg:
                traceback_block = f"""<details class='failure-traceback-details'>
  <summary>View Complete Traceback</summary>
  <pre>{_e(raw_err)}</pre>
</details>"""
            failure_alert_html = f"""<div class="failure-alert-box">
  <div class="failure-alert-title">❌ Test Execution Failure</div>
  <div class="failure-alert-msg">{_e(err_msg or 'Execution failed')}</div>
  {traceback_block}
</div>"""

        # Steps Table with intelligent deduplication
        rendered_screenshot_names = set()
        step_rows = []
        raw_steps = getattr(r, "steps", None) or []

        if raw_steps:
            processed_steps = []
            for s in raw_steps:
                s_name = getattr(s, "name", "").strip()
                if not s_name:
                    continue

                if processed_steps:
                    prev = processed_steps[-1]
                    norm_curr = normalize_step_name(s_name)
                    norm_prev = normalize_step_name(prev.name)

                    # Exact duplicate check (e.g. repeated method call or child having exact same name)
                    if norm_curr == norm_prev:
                        # Transfer any screenshots to previous step
                        for shot in getattr(s, "screenshots", []):
                            if not any(x.name == shot.name for x in prev.screenshots):
                                prev.screenshots.append(shot)
                        # Transfer any attachments to previous step
                        for att in getattr(s, "attachments", []):
                            if not any(x.name == att.name for x in getattr(prev, "attachments", [])):
                                getattr(prev, "attachments", []).append(att)
                        # Transfer failure status/error
                        if s.status == "failed" and prev.status != "failed":
                            prev.status = "failed"
                            prev.error = s.error
                        continue

                processed_steps.append(s)

            for s in processed_steps:
                s_time = datetime.fromtimestamp(getattr(s, "start", rec_start)).strftime("%H:%M:%S")
                s_name = _e(getattr(s, "name", ""))
                s_status = getattr(s, "status", "passed")
                is_step_failed = (s_status == "failed")
                step_badge_cls = "fail" if is_step_failed else "pass"
                step_badge_txt = "FAIL" if is_step_failed else "PASS"

                depth = getattr(s, "depth", 0)
                indent_px = min(depth * 20, 60)
                indent_prefix = '<span class="step-tree-indicator">↳ </span>' if depth > 0 else ""
                row_cls = f"step-row step-level-{min(depth, 3)}"

                step_err_html = ""
                if is_step_failed:
                    step_err = _clean_error_message(getattr(s, "error", "") or getattr(r, "error", ""))
                    if step_err:
                        step_err_html = f"<div class='step-error-desc'>{_e(step_err)}</div>"

#                 # Attachments for this step
#                 step_atts = getattr(s, "attachments", [])
#                 step_atts_html = ""
#                 if step_atts:
#                     att_cards = []
#                     for att in step_atts:
#                         att_cards.append(f"""<details class="step-attachment-details">
#   <summary><span class="att-icon">📎</span> <span class="att-name">{_e(att.name)}</span></summary>
#   <pre class="att-content">{_e(att.content)}</pre>
# </details>""")
#                     step_atts_html = f"<div class='step-attachments-container'>{''.join(att_cards)}</div>"

                # Screenshots for this step
                step_shots = getattr(s, "screenshots", [])
                step_shots_html = ""
                if step_shots:
                    cards = []
                    for shot in step_shots:
                        rendered_screenshot_names.add(shot.name)
                        cards.append(f"""<div class="screenshot-card">
  <div class="screenshot-thumb-wrapper" onclick="openLightbox('data:{shot.mime};base64,{shot.data_b64}', '{_e(shot.name)}')">
    <img class="screenshot-thumb" src="data:{shot.mime};base64,{shot.data_b64}" alt="{_e(shot.name)}" />
    <div class="screenshot-zoom-overlay">🔍 Enlarge</div>
  </div>
  <div class="screenshot-caption" title="{_e(shot.name)}">{_e(shot.name)}</div>
</div>""")
                    step_shots_html = f"<div class='screenshots-row'>{''.join(cards)}</div>"

                step_rows.append(f"""<tr class="{row_cls}">
  <td class="step-col-status"><span class="badge {step_badge_cls}">{step_badge_txt}</span></td>
  <td class="step-col-time">{s_time}</td>
  <td class="step-col-details" style="padding-left: {14 + indent_px}px;">
    <div class="step-title">{indent_prefix}{s_name}</div>
    {step_err_html}
    {step_shots_html}
  </td>
</tr>""")

        else:
            # Fallback: display execution info or logs
            for l in getattr(r, "logs", []):
                msg = _clean_log_text(l.message)
                if not msg or any(p in msg for p in ("TEST START |", "TEST TEARDOWN |")):
                    continue
                l_time = datetime.fromtimestamp(l.ts).strftime("%H:%M:%S")
                l_status = "fail" if l.level in ("ERROR", "CRITICAL") else ("skip" if l.level == "WARNING" else "info")
                l_badge = "FAIL" if l_status == "fail" else ("WARN" if l_status == "skip" else "INFO")
                step_rows.append(f"""<tr>
  <td class="step-col-status"><span class="badge {l_status}">{l_badge}</span></td>
  <td class="step-col-time">{l_time}</td>
  <td class="step-col-details">{_e(msg)}</td>
</tr>""")

            if not step_rows:
                step_rows.append(f"""<tr>
  <td class="step-col-status"><span class="badge {status}">{status_label}</span></td>
  <td class="step-col-time">{rec_end_dt.strftime('%H:%M:%S')}</td>
  <td class="step-col-details">Test completed with status: <strong>{status_label}</strong></td>
</tr>""")

        # Additional Test Screenshots (screenshots on record not yet displayed in a step)
        remaining_shots = [s for s in getattr(r, "screenshots", []) if s.name not in rendered_screenshot_names]
        additional_gallery_html = ""
        if remaining_shots:
            cards = []
            for shot in remaining_shots:
                cards.append(f"""<div class="screenshot-card">
  <div class="screenshot-thumb-wrapper" onclick="openLightbox('data:{shot.mime};base64,{shot.data_b64}', '{_e(shot.name)}')">
    <img class="screenshot-thumb" src="data:{shot.mime};base64,{shot.data_b64}" alt="{_e(shot.name)}" />
    <div class="screenshot-zoom-overlay">🔍 Enlarge</div>
  </div>
  <div class="screenshot-caption" title="{_e(shot.name)}">{_e(shot.name)}</div>
</div>""")
            additional_gallery_html = f"""<div class="screenshots-gallery">
  <div class="section-heading">📸 Attached Test Screenshots ({len(remaining_shots)})</div>
  <div class="screenshots-row">{''.join(cards)}</div>
</div>"""

        # Execution Logs Block - deduplicated from steps and STEP: prefixes
        logs_html = ""
        log_lines = getattr(r, "logs", [])
        if log_lines:
            log_entries = []
            all_step_texts = set()
            for s in (getattr(r, "steps", []) or []):
                s_name = getattr(s, "name", "").strip()
                if s_name:
                    all_step_texts.add(s_name.lower())
                    norm_s = normalize_step_name(s_name)
                    if norm_s:
                        all_step_texts.add(norm_s)

            for l in log_lines:
                msg = _clean_log_text(l.message)
                if not msg:
                    continue
                # Skip internal report step logger outputs
                if msg.startswith("STEP: "):
                    continue
                # Skip pytest protocol / teardown markers
                if any(p in msg for p in ("TEST START |", "TEST TEARDOWN |")):
                    continue

                # Skip logs that merely echo an allure step title
                msg_lower = msg.strip().lower()
                norm_msg = normalize_step_name(msg)
                if msg_lower in all_step_texts or (norm_msg and norm_msg in all_step_texts):
                    continue

                t_str = datetime.fromtimestamp(l.ts).strftime("%H:%M:%S")
                log_entries.append(f"<div class='log-line {l.level}'>[{t_str}] [{l.level}] {_e(msg)}</div>")
            if log_entries:
                logs_html = f"""<details class="logs-accordion">
  <summary>📋 Execution Logs ({len(log_entries)} events)</summary>
  <div class="logs-content">
    {''.join(log_entries)}
  </div>
</details>"""

        detail_pane_html = f"""<div class="test-detail-card" id="{test_id}">
  <div class="detail-header">
    <div class="detail-title-row">
      <div class="detail-test-name">{_e(name)}</div>
      <div class="detail-status-pill {status}">{status_label}</div>
    </div>
    <div class="detail-meta-row">
      <div class="detail-meta-item">Started: <strong>{r_start_str}</strong></div>
      <div class="detail-meta-item">Ended: <strong>{r_end_str}</strong></div>
      <div class="detail-meta-item">Duration: <strong>{r_dur_str}</strong></div>
      {tags_html}
    </div>
  </div>

  <div class="scenario-box">
    <div class="scenario-header">📋 TEST SCENARIO</div>
    <div class="scenario-title">{_e(scenario_title)}</div>
    {scenario_details_html}
  </div>

  {failure_alert_html}

  <div class="section-heading">🔄 Execution Steps & Results</div>
  <table class="steps-table">
    <thead>
      <tr>
        <th>Status</th>
        <th>Time</th>
        <th>Step Details & Screenshots</th>
      </tr>
    </thead>
    <tbody>
      {''.join(step_rows)}
    </tbody>
  </table>

  {additional_gallery_html}
  {logs_html}
</div>"""
        detail_panes.append(detail_pane_html)

    doc = (template
           .replace("{{TITLE}}", _e(meta.get("title", "QA Automation Execution Report")))
           .replace("{{PROJECT}}", _e(project))
           .replace("{{ENV}}", _e(env))
           .replace("{{BROWSER}}", _e(browser))
           .replace("{{STARTED_TIME}}", started_str)
           .replace("{{ENDED_TIME}}", ended_str)
           .replace("{{TOTAL_DURATION}}", total_duration_str)
           .replace("{{TOTAL_TESTS}}", str(total_count))
           .replace("{{PASSED_TESTS}}", str(pass_count))
           .replace("{{FAILED_TESTS}}", str(fail_count))
           .replace("{{SKIPPED_TESTS}}", str(skip_count))
           .replace("{{PASS_RATE}}", pass_rate)
           .replace("{{OVERALL_STATUS}}", overall_status)
           .replace("{{OVERALL_STATUS_CLASS}}", overall_status_class)
           .replace("{{USER_NAME}}", _e(user_name))
           .replace("{{OS_NAME}}", _e(os_name))
           .replace("{{PYTHON_VERSION}}", _e(python_version))
           .replace("{{HOST_NAME}}", _e(host_name))
           .replace("{{TEST_LIST_HTML}}", "\n".join(nav_items))
           .replace("{{TEST_DETAILS_HTML}}", "\n".join(detail_panes))
    )
    return doc