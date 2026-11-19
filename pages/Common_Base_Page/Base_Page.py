
# Author : Tilak Badsheshi
# Created Date : 2026-10-22
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-10

"""
==============  INTRODUCTION ================
Page Object / Component: BasePage (Common Foundation)
Description: Reusable synchronous Playwright actions and Page Object Model foundation for AviLeap.
             Provides resilient locator interactions, error logging, screenshot attachments,
             and explicit waiting strategies. Locators remain owned by individual Page Objects.

Scenario & Workflow Capabilities:
1. Navigation & Page Lifecycle: Open application URL, wait for DOM/networkidle load states, reload.
2. Synchronized Element Interaction: Click, double-click, hover, fill/type text, clear, select dropdown options.
3. Element State Inquiries: Check visibility, enabled state, count elements, extract inner text and attributes.
4. Resilient Scrolling & Waiting: Scroll into view, wait for locators, retry mechanisms.
5. Evidence & Reporting: Capture viewport and full-page screenshots, attach failure artifacts to Allure and Extent reports.
"""
from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Iterable

from playwright.sync_api import Locator, Page, expect
from utils.logger import get_logger

logger = get_logger(__name__)


class BasePage:
    def __init__(self, page: Page, base_url: str | None = None):
        self.page = page
        self.base_url = base_url

    def _locator(self, target: str | Locator) -> Locator:
        return target if isinstance(target, Locator) else self.page.locator(target)

    def _run(self, action: str, target: str | Locator, fn, *args, **kwargs):
        loc = self._locator(target)
        label = str(target)
        logger.info("ACTION start | %s | locator=%s", action, label)
        try:
            result = fn(loc, *args, **kwargs)
            logger.info("ACTION success | %s | locator=%s", action, label)
            return result
        except Exception:
            try:
                setattr(self.page, "_last_failed_locator", loc)
            except Exception:
                pass
            logger.exception("ACTION failed | %s | locator=%s | url=%s", action, label, self.page.url)
            raise

    # -------------------------------------------------------------------------
    # Navigation & Page Lifecycle
    # -------------------------------------------------------------------------

    def open_application(self, url: str | None = None):
        target = url or self.base_url
        if not target:
            raise ValueError(
                "Application URL not found. Pass a URL to open_application() or configure project/environment URL."
            )
        logger.info("Navigating to application: %s", target)
        try:
            self.page.goto(target, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            logger.warning("Initial navigation to %s encountered %s, retrying...", target, e)
            self.page.goto(target, wait_until="domcontentloaded", timeout=60000)

    def goto(self, url, **kwargs):
        return self.page.goto(url, **kwargs)

    def back(self, **kwargs):
        return self.page.go_back(**kwargs)

    def forward(self, **kwargs):
        return self.page.go_forward(**kwargs)

    def reload(self, **kwargs):
        return self.page.reload(**kwargs)

    def wait_for_load_state(self, state="domcontentloaded", timeout=None):
        return self.page.wait_for_load_state(state, timeout=timeout)

    def wait_for(self, target, state="visible", timeout=None):
        return self._locator(target).wait_for(state=state, timeout=timeout)

    def wait_for_element(self, target, state="visible", timeout=None):
        return self.wait_for(target, state=state, timeout=timeout)

    def login(self, username: str | None = None, password: str | None = None):
        """
        Prerequisite method to authenticate / log into the application.

        What this function does:
        Creates an instance of the LoginPage object and runs the login_user() workflow.
        This provides a convenient shorthand for any page object or test that needs to ensure
        the user is authenticated before proceeding.
        """
        from pages.Login.Login_Page import LoginPage
        login_page = LoginPage(self.page, self.base_url)
        return login_page.login_user(username, password)

    # -------------------------------------------------------------------------
    # Basic User Actions
    # -------------------------------------------------------------------------

    def click(self, locator, **kwargs):
        return self._run("click", locator, lambda l: l.click(**kwargs))

    def double_click(self, locator, **kwargs):
        return self._run("double_click", locator, lambda l: l.dblclick(**kwargs))

    def right_click(self, locator, **kwargs):
        return self._run("right_click", locator, lambda l: l.click(button="right", **kwargs))

    def hover(self, locator, **kwargs):
        return self._run("hover", locator, lambda l: l.hover(**kwargs))

    def move_mouse_to_element(self, locator):
        return self._run("move_mouse", locator, lambda l: l.hover())

    def send_text(self, locator, text, **kwargs):
        return self._run("fill", locator, lambda l: l.fill(str(text), **kwargs))

    def fill(self, locator, text, **kwargs):
        return self.send_text(locator, text, **kwargs)

    def type_text(self, locator, text, **kwargs):
        return self._run("type", locator, lambda l: l.press_sequentially(str(text), **kwargs))

    def clear(self, locator):
        return self._run("clear", locator, lambda l: l.fill(""))

    def press(self, locator, key, **kwargs):
        return self._run("press", locator, lambda l: l.press(key, **kwargs))

    def focus(self, locator):
        return self._run("focus", locator, lambda l: l.focus())

    def select_text(self, locator, **kwargs):
        return self._run("select_text", locator, lambda l: l.select_text(**kwargs))

    def check(self, locator, **kwargs):
        return self._run("check", locator, lambda l: l.check(**kwargs))

    def uncheck(self, locator, **kwargs):
        return self._run("uncheck", locator, lambda l: l.uncheck(**kwargs))

    def select_radio(self, locator, **kwargs):
        return self._run("select_radio", locator, lambda l: l.check(**kwargs))

    def select_option(self, locator, option, **kwargs):
        return self._run("select_option", locator, lambda l: l.select_option(option, **kwargs))

    def select_multiple(self, locator, options, **kwargs):
        return self._run("select_multiple", locator, lambda l: l.select_option(options, **kwargs))

    def upload_file(self, locator, files, **kwargs):
        return self._run("upload_file", locator, lambda l: l.set_input_files(files, **kwargs))

    def scroll_into_view(self, locator, **kwargs):
        return self._run("scroll_into_view", locator, lambda l: l.scroll_into_view_if_needed(**kwargs))

    def scroll_page(self, x=0, y=500):
        self.page.mouse.wheel(x, y)

    # -------------------------------------------------------------------------
    # Getters & State Checks
    # -------------------------------------------------------------------------

    def get_text(self, locator):
        return self._run("get_text", locator, lambda l: l.inner_text())

    def get_input_value(self, locator):
        return self._run("get_input_value", locator, lambda l: l.input_value())

    def get_attribute(self, locator, name):
        return self._run("get_attribute", locator, lambda l: l.get_attribute(name))

    def exists(self, locator):
        return self._locator(locator).count() > 0

    def is_visible(self, locator):
        return self._locator(locator).is_visible()

    def is_hidden(self, locator):
        return self._locator(locator).is_hidden()

    def is_enabled(self, locator):
        return self._locator(locator).is_enabled()

    def is_disabled(self, locator):
        return self._locator(locator).is_disabled()

    def is_checked(self, locator):
        return self._locator(locator).is_checked()

    def is_editable(self, locator):
        return self._locator(locator).is_editable()

    def count(self, locator):
        return self._locator(locator).count()

    def get_all_text(self, locator):
        return self._locator(locator).all_text_contents()

    def get_all_attributes(self, locator, name):
        return [self._locator(locator).nth(i).get_attribute(name) for i in range(self.count(locator))]

    def get_title(self):
        return self.page.title()

    def get_page_title(self):
        return self.page.title()

    def get_url(self):
        return self.page.url

    # -------------------------------------------------------------------------
    # Assertions
    # -------------------------------------------------------------------------

    def assert_visible(self, locator, timeout=None):
        loc = self._locator(locator)
        try:
            expect(loc).to_be_visible(timeout=timeout)
        except Exception:
            try:
                setattr(self.page, "_last_failed_locator", loc)
            except Exception:
                pass
            raise

    def assert_not_visible(self, locator, timeout=None):
        loc = self._locator(locator)
        try:
            expect(loc).not_to_be_visible(timeout=timeout)
        except Exception:
            try:
                setattr(self.page, "_last_failed_locator", loc)
            except Exception:
                pass
            raise

    def assert_enabled(self, locator, timeout=None):
        loc = self._locator(locator)
        try:
            expect(loc).to_be_enabled(timeout=timeout)
        except Exception:
            try:
                setattr(self.page, "_last_failed_locator", loc)
            except Exception:
                pass
            raise

    def assert_disabled(self, locator, timeout=None):
        loc = self._locator(locator)
        try:
            expect(loc).to_be_disabled(timeout=timeout)
        except Exception:
            try:
                setattr(self.page, "_last_failed_locator", loc)
            except Exception:
                pass
            raise

    def assert_present(self, locator, timeout=None):
        loc = self._locator(locator)
        try:
            loc.wait_for(state="attached", timeout=timeout)
        except Exception as exc:
            try:
                setattr(self.page, "_last_failed_locator", loc)
            except Exception:
                pass
            raise AssertionError(
                f"Expected element to be present; locator={locator!s}; url={self.page.url}; cause={exc}"
            ) from exc

    def assert_absent(self, locator, timeout=None):
        try:
            self._locator(locator).wait_for(state="detached", timeout=timeout)
        except Exception as exc:
            raise AssertionError(
                f"Expected element to be absent; locator={locator!s}; url={self.page.url}; cause={exc}"
            ) from exc

    def assert_text(self, locator, expected, timeout=None):
        loc = self._locator(locator)
        try:
            expect(loc).to_have_text(expected, timeout=timeout)
        except Exception as exc:
            try:
                setattr(self.page, "_last_failed_locator", loc)
            except Exception:
                pass
            raise AssertionError(
                f"Text assertion failed; locator={locator!s}; expected={expected!r}; url={self.page.url}"
            ) from exc

    def assert_text_contains(self, locator, expected, timeout=None):
        loc = self._locator(locator)
        try:
            expect(loc).to_contain_text(expected, timeout=timeout)
        except Exception as exc:
            try:
                setattr(self.page, "_last_failed_locator", loc)
            except Exception:
                pass
            raise AssertionError(
                f"Text containment failed; locator={locator!s}; expected substring={expected!r}; url={self.page.url}"
            ) from exc

    def assert_url(self, expected, contains=False, timeout=None):
        pattern = re.compile(re.escape(expected)) if contains else expected
        try:
            expect(self.page).to_have_url(pattern, timeout=timeout)
        except AssertionError as exc:
            mode = "to contain " if contains else ""
            raise AssertionError(
                f"URL assertion failed; expected {mode}{expected!r}; actual={self.page.url!r}"
            ) from exc

    def assert_title(self, expected, contains=False, timeout=None):
        pattern = re.compile(re.escape(expected)) if contains else expected
        try:
            expect(self.page).to_have_title(pattern, timeout=timeout)
        except AssertionError as exc:
            mode = "to contain " if contains else ""
            raise AssertionError(
                f"Page title assertion failed; expected {mode}{expected!r}; actual={self.page.title()!r}; url={self.page.url}"
            ) from exc

    def handle_new_page(self, action):
        with self.page.context.expect_page() as page_info:
            action()
        return page_info.value

    def open_new_tab(self, action):
        return self.handle_new_page(action)

    # -------------------------------------------------------------------------
    # Red Border Box Highlighting & Screenshot Capture (Self-Contained in POM)
    # -------------------------------------------------------------------------

    @classmethod
    def _extract_locator_from_error(cls, error_text: str) -> str | None:
        """Extract failing locator/selector or domain element from error tracebacks."""
        if not error_text:
            return None
        text = str(error_text)

        # 1. Playwright: waiting for locator("...") or selector('...')
        m = re.search(r'(?:locator|selector)\((["\'])(.*?)\1\)', text, re.DOTALL)
        if m:
            return m.group(2).strip()

        # 2. Playwright expect: Locator: locator("...")
        m = re.search(r'Locator:\s*locator\((["\'])(.*?)\1\)', text, re.DOTALL)
        if m:
            return m.group(2).strip()

        # 3. Playwright expect with get_by_*: Locator: get_by_role("button", name="...")
        m = re.search(r'Locator:\s*([^\r\n]+)', text)
        if m:
            raw_loc = m.group(1).strip()
            m_inner = re.search(r'\((["\'])(.*?)\1', raw_loc)
            if m_inner:
                return m_inner.group(2).strip()
            return raw_loc

        # 4. Flight failure: Flight '<flight_no>'
        m_flight = re.search(r"[Ff]light\s*['\"]([A-Za-z0-9_\s\-]+)['\"]", text)
        if m_flight:
            flight_str = m_flight.group(1).strip()
            token = flight_str.split()[0].strip() if flight_str else flight_str
            return f"//div[contains(@class, 'flight-card') and .//*[contains(text(), '{token}')]] | //*[contains(text(), '{token}')]"

        # 5. Activity group failure: Activity group '<group_name>'
        m_group = re.search(r"[Aa]ctivity\s+group\s*['\"]([^'\"]+)['\"]", text)
        if m_group:
            group_str = m_group.group(1).strip()
            return f"//div[contains(@class,'grp-button') and normalize-space()='{group_str}'] | //*[contains(text(), '{group_str}')]"

        # 6. Logger or action failed log: locator=...
        m = re.search(r'locator=([^\s|\r\n]+)', text)
        if m:
            return m.group(1).strip()

        # 7. Look for XPath or CSS selector in error text
        m = re.search(r'(?://[a-zA-Z0-9_\-\[\]@=\'\"\s\.\*\(\)]+|[#.][a-zA-Z0-9_-]+)', text)
        if m:
            cand = m.group(0).strip()
            if len(cand) > 2:
                return cand

        return None

    @classmethod
    def highlight_element(cls, page: Page | None, locator: Any = None, error_message: str = "") -> None:
        """
        Highlight target failed element with a prominent 3px solid red outline, 2px red border,
        and glowing red box-shadow before capturing failure screenshot.

        1. Clears any previous highlight borders or banners.
        2. Resolves target locator from passed locator, page._last_failed_locator,
           or by parsing error_message / stack trace.
        3. If target element exists in DOM:
           - Scrolls element into view.
           - Applies '3px solid red' outline and '2px solid red' border with !important.
        4. If target element is not in DOM:
           - Injects a red overlay banner at top of viewport displaying the missing locator.
        """
        try:
            if page is None or page.is_closed():
                return

            # 1. Clear previous failure highlights and banners
            try:
                page.evaluate("""() => {
                    const banner = document.getElementById('__pw_failure_banner__');
                    if (banner) banner.remove();
                    document.querySelectorAll('.__pw_failed_element__').forEach(el => {
                        el.style.removeProperty('outline');
                        el.style.removeProperty('border');
                        el.style.removeProperty('box-shadow');
                        el.style.removeProperty('background-color');
                        el.classList.remove('__pw_failed_element__');
                    });
                }""")
            except Exception:
                pass

            target = None
            extracted_loc_str = ""

            # 2. Determine target locator
            if locator is not None:
                target = locator if hasattr(locator, "first") else page.locator(str(locator))
                extracted_loc_str = str(locator)
            elif getattr(page, "_last_failed_locator", None) is not None:
                target = page._last_failed_locator
                extracted_loc_str = str(getattr(target, "_selector", "") or target)
            elif error_message:
                extracted = cls._extract_locator_from_error(error_message)
                if extracted:
                    extracted_loc_str = extracted
                    try:
                        target = page.locator(extracted)
                    except Exception:
                        target = None

            # 3. Apply highlighting
            if target is not None:
                try:
                    count = target.count()
                    if count > 0:
                        elem = target.first
                        elem.scroll_into_view_if_needed(timeout=2000)
                        elem.evaluate("""el => {
                            try { el.scrollIntoView({ behavior: 'instant', block: 'center', inline: 'nearest' }); } catch(e){}
                            el.classList.add('__pw_failed_element__');
                            el.style.setProperty('outline', '3px solid #ff0000', 'important');
                            el.style.setProperty('outline-offset', '2px', 'important');
                            el.style.setProperty('border', '2px solid #ff0000', 'important');
                            el.style.setProperty('box-shadow', '0 0 16px 4px rgba(255, 0, 0, 0.85)', 'important');
                            el.style.setProperty('background-color', 'rgba(255, 0, 0, 0.08)', 'important');
                        }""")
                        logger.info("Highlighted failed element with red border: %s", extracted_loc_str)
                        return
                except Exception as ex:
                    logger.debug("Could not highlight element in DOM: %s", ex)

            # 4. If element was not found in DOM or locator failed to match an existing node,
            # display a red failure banner across the viewport so the missing element is immediately obvious.
            if extracted_loc_str:
                try:
                    clean_msg = extracted_loc_str.replace("`", "'").replace("\\", "\\\\")[:120]
                    page.evaluate(f"""() => {{
                        const banner = document.createElement('div');
                        banner.id = '__pw_failure_banner__';
                        banner.innerHTML = '&#10060; FAILED LOCATOR NOT FOUND: <span style="font-family:monospace;background:#fff;color:#c00;padding:2px 6px;border-radius:4px;margin-left:6px;">{clean_msg}</span>';
                        banner.style.cssText = 'position:fixed;top:10px;left:50%;transform:translateX(-50%);z-index:2147483647;background:#dc3545;color:#ffffff;padding:10px 20px;border:2px solid #721c24;border-radius:6px;font-family:Arial,sans-serif;font-size:13px;font-weight:bold;box-shadow:0 4px 12px rgba(0,0,0,0.4);text-align:center;max-width:92%;';
                        document.body.appendChild(banner);
                    }}""")
                except Exception:
                    pass
        except Exception:
            logger.debug("Element highlight failed; continuing with screenshot", exc_info=True)

    @classmethod
    def capture_failure(
        cls,
        page: Page | None,
        *,
        project: str,
        station: str,
        test_name: str,
        report_context=None,
        output_dir="reports/screenshots",
        error_message="",
        locator=None,
    ) -> str | None:
        """
        Capture a PNG screenshot with red border element highlighting.
        Used by pytest hooks and framework reporters. Returns saved path or None.
        """
        try:
            if page is None or page.is_closed():
                return None
            safe = lambda s: "".join(c if c.isalnum() or c in "._-" else "_" for c in str(s))[:100]
            path = Path(output_dir) / safe(project) / safe(station) / f"{safe(test_name)}_{time.strftime('%Y%m%d_%H%M%S')}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            cls.highlight_element(page, locator=locator, error_message=error_message)
            data = page.screenshot(path=str(path), full_page=True, animations="disabled")
            if report_context is not None:
                report_context.attach_screenshot(data, path.name, error_message, "image/png")
            logger.error("Failure screenshot captured | path=%s | url=%s", path, getattr(page, "url", "unknown"))
            return str(path)
        except Exception:
            logger.exception("Failure screenshot capture failed; preserving original test failure.")
            return None

    def highlight_failed_element(self, locator=None, error_message=""):
        """Instance method: marks failed element with red border."""
        self.highlight_element(self.page, locator=locator, error_message=error_message)

    def capture_failure_screenshot(self, locator=None, flight_name="Failure", error_message=""):
        """Instance method for page objects: marks failed element with red border and saves screenshot."""
        try:
            if self.page.is_closed():
                return None
            self.highlight_failed_element(locator=locator, error_message=error_message)
            from utils import report_context

            data = self.page.screenshot(full_page=True, animations="disabled")
            report_context.attach_screenshot(data, f"{flight_name} Failure Screenshot", error_message, "image/png")
            try:
                import allure

                allure.attach(data, name=f"{flight_name} Failure Screenshot", attachment_type=allure.attachment_type.PNG)
                if error_message:
                    allure.attach(error_message, name=f"{flight_name} Error", attachment_type=allure.attachment_type.TEXT)
            except Exception:
                logger.debug("Allure screenshot attachment unavailable", exc_info=True)
            return data
        except Exception:
            logger.exception("Unable to capture failure screenshot | url=%s", getattr(self.page, "url", "unknown"))
            return None

    # -------------------------------------------------------------------------
    # Flight Card Attribute Extractions (Flight Number, Arrival & Departure)
    # -------------------------------------------------------------------------
    FLIGHTNO_COL = ".flightno-col, //div[contains(@class,'flightno-col')]"
    ARRIVAL_AND_DEPARTURE_FLIGHT_NUMBER = (
        "//div[contains(@class,'flightno-col')]//p[@mattooltip='Flight Arrival Departure Numbers'] | "
        "//div[contains(@class,'flightno-col')] | "
        "//p[@mattooltip='Flight Arrival Departure Numbers']"
    )

    def get_arrival_and_departure_flight_numbers(self, flight_card: Locator | None = None) -> tuple[str, str]:
        """
        Extracts both the Arrival Flight Number and Departure Flight Number from a flight card.

        What this function does:
        1. Finds the flight number container element (class="flightno-col") within the flight card.
        2. Extracts the text content or child elements (including tooltip paragraphs).
        3. Parses and returns the separate Arrival and Departure flight numbers.

        Inputs:
            flight_card (Locator, optional): The flight card web element. If None, queries the page.

        Returns:
            tuple[str, str]: (arrival_flight_number, departure_flight_number).
        """
        target = flight_card if flight_card is not None else self.page
        try:
            # 1. Primary check: class="flightno-col"
            col = target.locator(".flightno-col, //div[contains(@class,'flightno-col')]").first
            raw_text = ""
            if col.count() > 0:
                # Check for child paragraph with tooltip inside flightno-col
                p_elem = col.locator("p[mattooltip='Flight Arrival Departure Numbers'], p").first
                if p_elem.count() > 0:
                    raw_text = p_elem.inner_text().strip()
                if not raw_text:
                    raw_text = col.inner_text().strip()

            # 2. Secondary check: mattooltip locator directly
            if not raw_text:
                tooltip_elem = target.locator("//p[@mattooltip='Flight Arrival Departure Numbers']").first
                if tooltip_elem.count() > 0:
                    raw_text = tooltip_elem.inner_text().strip()

            if raw_text:
                # Normalize spaces and newlines
                clean_text = " ".join(raw_text.split())
                # Handle separator: ' - ' or ' / ' or '-'
                if " - " in clean_text:
                    parts = clean_text.split(" - ", 1)
                    arr = parts[0].strip()
                    dep = parts[1].strip() if len(parts) > 1 else ""
                    return (arr if arr != "-" else ""), (dep if dep != "-" else "")
                elif " / " in clean_text:
                    parts = clean_text.split(" / ", 1)
                    arr = parts[0].strip()
                    dep = parts[1].strip() if len(parts) > 1 else ""
                    return (arr if arr != "-" else ""), (dep if dep != "-" else "")
                elif "-" in clean_text and not clean_text.startswith("FZ-") and not clean_text.startswith("EK-"):
                    parts = clean_text.split("-", 1)
                    arr = parts[0].strip()
                    dep = parts[1].strip() if len(parts) > 1 else ""
                    return (arr if arr != "-" else ""), (dep if dep != "-" else "")
                else:
                    return clean_text, ""
        except Exception as e:
            logger.warning("Error fetching arrival and departure flight numbers: %s", e)
        return "", ""

    def get_flight_number(self, flight_card: Locator | None = None) -> str:
        """
        Extracts and formats the flight number from the dashboard / flight card.

        What this function does:
        Fetches both the Arrival Flight Number and Departure Flight Number from class="flightno-col",
        and returns a clean, human-readable flight number string to display in test steps and reports.
        - If both arrival and departure numbers are present: '8500 - 863' or 'FZ-0215 - FZ-0216'
        - If only arrival number is present: 'FZ-0215'
        - If only departure number is present: 'FZ-0216'

        Inputs:
            flight_card (Locator, optional): The flight card web element.

        Returns:
            str: The flight number string (e.g. '8500 - 863' or 'FZ-0215').
        """
        arr, dep = self.get_arrival_and_departure_flight_numbers(flight_card)
        if arr and dep:
            return f"{arr} - {dep}"
        if arr:
            return arr
        if dep:
            return dep

        # Fallback to direct text if splitting didn't yield values
        target = flight_card if flight_card is not None else self.page
        try:
            col = target.locator(".flightno-col, //div[contains(@class,'flightno-col')]").first
            if col.count() > 0:
                txt = col.inner_text().strip()
                if txt and txt != "-":
                    return " ".join(txt.split())
            tooltip_elem = target.locator("//p[@mattooltip='Flight Arrival Departure Numbers']").first
            if tooltip_elem.count() > 0:
                txt = tooltip_elem.inner_text().strip()
                if txt and txt != "-":
                    return " ".join(txt.split())
        except Exception:
            pass
        return "Unknown Flight"
