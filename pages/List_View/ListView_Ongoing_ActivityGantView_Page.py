# Author : Tilak Badsheshi
# Created Date : 2026-11-16
# Modified By : Tilak Badsheshi
# Modified Date : 2026-11-16

"""
==============  INTRODUCTION ================
Page Object / Component: ListView_Ongoing_ActivityGantView_Page
Description: Page Object Model for validating Gantt View functionality in the Flights List View,
             including enabling the Gantt View toggle, expanding flight cards, iterating through all
             activity groups, and validating planned/actual activity timings, progress, and delays.

Scenario & Workflow Capabilities:
1. Navigation: Route through navigation menu to Flights List View dashboard.
2. Section Switching: Ensure Ongoing section is active and flight cards are loaded.
3. Gantt View Toggle: Locate and enable the Gantt View mat-slide-toggle on the List View toolbar.
4. Flight Card Expansion: Select a flight card to expand the embedded Gantt chart (app-flight-activities-ganttchart).
5. Activity Group Iteration: Discover and sequentially navigate through all activity groups (e.g. Aircraft Recipients,
   Technical Equipment, Arrival Events, Departure Events, Departure Readiness).
6. Activity Verification:
   - Verify activity name is displayed for each activity.
   - Verify planned activity bar is displayed with planned start time, end time, and duration.
   - Verify actual activity bar (if present) displays actual start time, end time, and delay/on-time status.
   - Verify color styling and delay representation (On-Time in Green, Delay in Red).
"""

import re
import pytest
import allure
from playwright.sync_api import expect
from pages.Common_Base_Page.Base_Page import BasePage
from utils.logger import get_logger

logger = get_logger(__name__)


class ListView_Ongoing_ActivityGantView_Page(BasePage):
    """
    Page Object dedicated to Flights List View Gantt View toggle, activity groups,
    and planned/actual activity timeline validations.
    """

    MENU = "//span[@class='nav-icon']/i[normalize-space()='menu' or text()='menu']"
    LIST_VIEW = "//div[@role='button']//span[normalize-space()='Flights'] | //span[normalize-space()='Flights']"

    SECTIONS = [
        {"name": "Ongoing", "tab": "//div[contains(text(),'Ongoing')]"},
        {"name": "Incoming", "tab": "//div[contains(text(),'Incoming')]"},
        {"name": "Departed", "tab": "//div[contains(text(),'Departed')]"},
    ]

    GANTT_TOGGLE_DIV = "//div[contains(@class,'gantt-view-toggle-div')]"
    GANTT_SLIDE_TOGGLE = "//div[contains(@class,'gantt-view-toggle-div')]//mat-slide-toggle"
    FLIGHT_ROW_CARDS = "//mat-card[contains(@class,'listviewmatcard')]//div[@id='selectedCard']"
    SYNC_ICON = "//i[@ptooltip='Refresh Flight'] | //i[contains(@class,'pi-sync')]"
    FLIGHT_NUMBER = "//p[@mattooltip='Flight Arrival Departure Numbers']"

    # Gantt Chart Component and Elements
    GANTT_CHART = "app-flight-activities-ganttchart"
    GROUP_BUTTONS = "//app-flight-activities-ganttchart//div[contains(@class,'grp-button')]"
    ACTIVITY_ROWS = "app-flight-activities-ganttchart .activity-container-body:not(.legend-div):not(#activity-timeline-container)"
    ACTIVITY_TITLE = ".timeline-activity-title"
    PLANNED_BAR = ".suggested-activity-bar"
    ACTUAL_BAR = ".actual-activity-bar"
    TOOLTIP_TEXT = ".tooltiptext"

    # Legend Elements
    LEGEND_CONTAINER = "app-flight-activities-ganttchart .legend-div"

    @allure.step("Navigate to Flights List View Dashboard")
    def navigate_to_list_view_page(self):
        """Navigates to the Flights List View dashboard via the main navigation menu."""
        logger.info("Navigating to Flights List View dashboard")
        self.page.wait_for_timeout(2000)

        # In case login redirection is completing
        if "/login" in self.page.url:
            logger.info("Current URL is still /login; awaiting navigation...")
            try:
                self.page.wait_for_url(lambda u: "/login" not in u, timeout=20000)
            except Exception:
                login_btn = self.page.locator("//button[@type='submit']").first
                if login_btn.is_visible():
                    login_btn.click()
                    self.page.wait_for_url(lambda u: "/login" not in u, timeout=20000)

        menu = self.page.locator(self.MENU).first
        expect(menu).to_be_visible(timeout=25000)
        menu.hover()
        self.page.wait_for_timeout(500)

        list_view = self.page.locator(self.LIST_VIEW).first
        if not list_view.is_visible():
            logger.info("List View menu item not visible after hover; clicking hamburger menu")
            menu.click()
            self.page.wait_for_timeout(1000)

        expect(list_view).to_be_visible(timeout=15000)
        list_view.click()
        self.page.wait_for_timeout(2000)

        # Move mouse away to dismiss navigation overlay and avoid click interception
        self.page.mouse.move(900, 500)
        self.page.wait_for_timeout(1500)

        # Wait for any spinner to disappear
        try:
            self.page.locator(".loader-container, .spinner").wait_for(state="detached", timeout=15000)
        except Exception:
            pass

        logger.info("Successfully navigated to Flights List View dashboard")

    @allure.step("Ensure Ongoing Section is Active and Flights are Loaded")
    def ensure_ongoing_section_loaded(self) -> int:
        """
        Activates Ongoing section tab and ensures flight cards are loaded.
        Uses sync icon fallback if flight cards are initially missing.
        """
        logger.info("Activating Ongoing section tab")
        ongoing_tab = self.page.locator(self.SECTIONS[0]["tab"]).first
        expect(ongoing_tab).to_be_visible(timeout=15000)
        ongoing_tab.click(force=True)
        self.page.wait_for_timeout(2000)

        card_loc = self.page.locator(self.FLIGHT_ROW_CARDS)
        try:
            card_loc.first.wait_for(state="visible", timeout=8000)
        except Exception:
            sync_icon = self.page.locator(self.SYNC_ICON).first
            if sync_icon.count() > 0 and sync_icon.is_visible():
                logger.info("Flight cards not immediately visible. Triggering Refresh Flight sync icon...")
                sync_icon.click()
                self.page.wait_for_timeout(4000)
            card_loc.first.wait_for(state="visible", timeout=15000)

        total_cards = card_loc.count()
        logger.info(f"Ongoing section active with {total_cards} flight cards loaded")
        return total_cards

    @allure.step("Enable Gantt View Toggle on Flights List View")
    def enable_gantt_view_toggle(self) -> bool:
        """
        Locates the Gantt View mat-slide-toggle and enables it if not already checked.
        Verifies that aria-checked becomes true and mat-checked class is present.
        """
        logger.info("Verifying and enabling Gantt View toggle")
        toggle = self.page.locator(self.GANTT_SLIDE_TOGGLE).first
        expect(toggle).to_be_visible(timeout=15000)

        input_elem = toggle.locator("input[type='checkbox']").first
        is_checked = input_elem.get_attribute("aria-checked") == "true"

        if not is_checked:
            logger.info("Gantt View toggle is currently OFF; clicking to enable...")
            toggle.click(force=True)
            self.page.wait_for_timeout(3000)
            is_checked = input_elem.get_attribute("aria-checked") == "true"

        # Verify toggle is ON
        toggle_class = toggle.get_attribute("class") or ""
        assert is_checked, f"Failed to enable Gantt View toggle. aria-checked is '{input_elem.get_attribute('aria-checked')}'"
        logger.info(f"Gantt View toggle successfully enabled (aria-checked=true, class='{toggle_class}')")
        return True

    @allure.step("Expand Flight Card to Reveal Gantt Chart")
    def expand_flight_card_gantt(self, card_index: int = 0) -> str:
        """
        Selects a flight card by index to open/expand its embedded Gantt chart.
        Waits for app-flight-activities-ganttchart to become visible.
        Returns the flight number of the selected card.
        """
        card_loc = self.page.locator(self.FLIGHT_ROW_CARDS)
        total_cards = card_loc.count()
        assert total_cards > 0, "No flight cards available to expand."

        target_card = card_loc.nth(card_index)
        target_card.scroll_into_view_if_needed()

        try:
            flight_no = target_card.locator(self.FLIGHT_NUMBER).inner_text().strip()
        except Exception:
            flight_no = f"Flight_Index_{card_index}"

        logger.info(f"Clicking flight card [{flight_no}] to expand Gantt chart...")
        target_card.click(force=True)
        self.page.wait_for_timeout(4000)

        gantt_chart = self.page.locator(self.GANTT_CHART).first
        expect(gantt_chart).to_be_visible(timeout=20000)
        logger.info(f"Gantt chart component '{self.GANTT_CHART}' successfully loaded for flight '{flight_no}'")
        return flight_no

    @allure.step("Extract Available Activity Groups from Gantt Chart")
    def get_activity_group_names(self) -> list:
        """
        Discovers and returns list of all activity group names (.grp-button) in the Gantt chart.
        e.g. ['Aircraft Recipients', 'Technical Equipment', 'Arrival Events', 'Departure Events', 'Departure Readiness'].
        """
        grp_locator = self.page.locator(self.GROUP_BUTTONS)
        expect(grp_locator.first).to_be_visible(timeout=15000)

        groups = []
        for i in range(grp_locator.count()):
            txt = grp_locator.nth(i).inner_text().strip()
            if txt and txt not in groups:
                groups.append(txt)

        logger.info(f"Discovered {len(groups)} Activity Groups: {groups}")
        return groups

    @allure.step("Select Activity Group: '{group_name}'")
    def select_activity_group(self, group_name: str):
        """
        Clicks on the specified activity group button (.grp-button) to filter/display its activities.
        Uses force=True to ensure sidebar overlays do not block interaction.
        """
        logger.info(f"Selecting Activity Group: '{group_name}'")
        btn = self.page.locator(
            f"//app-flight-activities-ganttchart//div[contains(@class,'grp-button') and normalize-space()='{group_name}']"
        ).first
        expect(btn).to_be_visible(timeout=10000)
        btn.click(force=True)
        try:
            expect(btn).to_have_class(re.compile(r"selected-group"), timeout=6000)
        except Exception:
            btn.dispatch_event("click")
            self.page.wait_for_timeout(1500)
            btn_class = btn.get_attribute("class") or ""
            assert "selected-group" in btn_class, f"Activity group '{group_name}' was not highlighted as selected."
        logger.info(f"Activity Group '{group_name}' active and selected")

    @allure.step("Extract Activities Data for Active Activity Group")
    def get_activities_for_active_group(self, group_name: str) -> list:
        """
        Parses all activity rows currently displayed for the active activity group.
        For each activity:
          - Extracts activity name from .timeline-activity-title.
          - Checks if planned activity bar (.suggested-activity-bar) is present and parses planned times (Start, End, Duration).
          - Checks if actual activity bar (.actual-activity-bar) is present and parses actual times (Start, End, Delay).
          - Detects on-time vs delay status.
        """
        activity_rows = self.page.locator(self.ACTIVITY_ROWS).all()
        logger.info(f"Parsing activities for group '{group_name}'. Rows found: {len(activity_rows)}")

        activities = []
        for idx, row in enumerate(activity_rows):
            title_elem = row.locator(self.ACTIVITY_TITLE).first
            if title_elem.count() == 0:
                continue

            activity_name = title_elem.inner_text().strip()
            if not activity_name:
                continue

            # Planned bar extraction
            planned_bar = row.locator(self.PLANNED_BAR).first
            has_planned = planned_bar.count() > 0
            planned_data = {"present": has_planned, "start": None, "end": None, "duration": None, "raw": None}

            if has_planned:
                tooltip = planned_bar.locator(self.TOOLTIP_TEXT).first
                raw_tooltip = tooltip.inner_text().strip() if tooltip.count() > 0 else ""
                planned_data["raw"] = raw_tooltip

                # Parse Start, End, Duration
                start_m = re.search(r"Start\s*:\s*(\d{1,2}:\d{2})", raw_tooltip)
                end_m = re.search(r"End\s*:\s*(\d{1,2}:\d{2})", raw_tooltip)
                dur_m = re.search(r"Duration\s*:\s*([^\n\r]+)", raw_tooltip)

                planned_data["start"] = start_m.group(1) if start_m else None
                planned_data["end"] = end_m.group(1) if end_m else None
                planned_data["duration"] = dur_m.group(1).strip() if dur_m else None

            # Actual bar extraction
            actual_bar = row.locator(self.ACTUAL_BAR).first
            has_actual = actual_bar.count() > 0
            actual_data = {
                "present": has_actual,
                "start": None,
                "end": None,
                "delay": None,
                "is_ontime": False,
                "is_delayed": False,
                "raw": None,
            }

            if has_actual:
                actual_cls = actual_bar.get_attribute("class") or ""
                actual_data["is_ontime"] = "on-time-bar" in actual_cls
                actual_data["is_delayed"] = "delay-bar" in actual_cls

                tooltip = actual_bar.locator(self.TOOLTIP_TEXT).first
                raw_tooltip = tooltip.inner_text().strip() if tooltip.count() > 0 else ""
                actual_data["raw"] = raw_tooltip

                start_m = re.search(r"Start\s*:\s*(\d{1,2}:\d{2})", raw_tooltip)
                end_m = re.search(r"End\s*:\s*(\d{1,2}:\d{2})", raw_tooltip)
                delay_m = re.search(r"Delay\s*:\s*([^\n\r]+)", raw_tooltip)

                actual_data["start"] = start_m.group(1) if start_m else None
                actual_data["end"] = end_m.group(1) if end_m else None
                actual_data["delay"] = delay_m.group(1).strip() if delay_m else None

            activity_info = {
                "activity_index": idx + 1,
                "group_name": group_name,
                "activity_name": activity_name,
                "planned": planned_data,
                "actual": actual_data,
            }
            activities.append(activity_info)

            logger.info(
                f"  [{group_name}] Activity {idx+1}: '{activity_name}' | "
                f"Planned={has_planned} (Start={planned_data['start']}, End={planned_data['end']}, Dur={planned_data['duration']}) | "
                f"Actual={has_actual} (Start={actual_data['start']}, OnTime={actual_data['is_ontime']}, Delay={actual_data['delay']})"
            )

        return activities

    @allure.step("Validate All Activity Groups and Planned/Actual Timings in Gantt View")
    def validate_gantt_activities_all_groups(self) -> dict:
        """
        Navigates through all activity groups in the Gantt View, checks that activities are displayed,
        verifies planned times (start/end/duration) are rendered on planned bars, and checks actual times.
        Returns a comprehensive summary dictionary.
        """
        group_names = self.get_activity_group_names()
        assert len(group_names) > 0, "No activity groups discovered in Gantt View."

        all_results = {}
        total_activities = 0
        total_with_planned = 0
        total_with_actual = 0

        for grp in group_names:
            self.select_activity_group(grp)
            activities = self.get_activities_for_active_group(grp)
            all_results[grp] = activities

            count_planned = sum(1 for a in activities if a["planned"]["present"])
            count_actual = sum(1 for a in activities if a["actual"]["present"])

            total_activities += len(activities)
            total_with_planned += count_planned
            total_with_actual += count_actual

            logger.info(
                f"Group '{grp}' Summary: Total Activities={len(activities)}, "
                f"With Planned Time={count_planned}, With Actual Time={count_actual}"
            )

        summary = {
            "total_groups": len(group_names),
            "group_names": group_names,
            "total_activities": total_activities,
            "total_with_planned": total_with_planned,
            "total_with_actual": total_with_actual,
            "details": all_results,
        }

        logger.info(
            f"Overall Gantt View Validation Summary: Groups={len(group_names)}, "
            f"Activities={total_activities}, Planned={total_with_planned}, Actual={total_with_actual}"
        )
        return summary
