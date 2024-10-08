"""
Cron schedule descriptions.

Returns schedules in a readable format.
"""

import calendar
import datetime
import re
from typing import Any, Callable, ClassVar, List, Optional


class ExpressionDescriptor:
    """Converts a Cron Expression into a human readable string."""

    _cron_days: ClassVar[dict[str, int]] = {
        v.upper(): k for (k, v) in enumerate(calendar.day_abbr)
    }
    _special_characters: ClassVar[List[str]] = ["/", "-", ",", "*"]

    def __init__(
        self,
        cron_year: str = "*",
        cron_month: str = "*",
        cron_week: str = "*",
        cron_day: str = "*",
        cron_week_day: str = "*",
        cron_hour: str = "0",
        cron_min: str = "0",
        cron_sec: str = "0",
    ) -> None:
        """Initializes a new instance of the ExpressionDescriptor."""
        self.cron_year = "*" if cron_year is None or cron_year == "" else cron_year
        self.cron_month = "*" if cron_month is None or cron_month == "" else cron_month
        self.cron_week = "*" if cron_week is None or cron_week == "" else cron_week
        self.cron_day = "*" if cron_day is None or cron_day == "" else cron_day
        self.cron_week_day = "*" if cron_week_day is None or cron_week_day == "" else cron_week_day
        self.cron_hour = "0" if cron_hour is None or cron_hour == "" else cron_hour
        self.cron_min = "0" if cron_min is None or cron_min == "" else cron_min
        self.cron_sec = "0" if cron_sec is None or cron_sec == "" else cron_sec

    def get_full_description(self) -> str:
        """Generates the FULL description.

        Returns
        -------
            The FULL description
        Raises:
            FormatException: if formatting fails

        """

        def remove_adjacent_duplicates(sentence: str) -> str:
            """Remove duplicate words that might pop up such as week week."""
            words = sentence.split()
            unique_words = [words[0]]  # Initialize unique words list with the first word
            for word in words[1:]:
                if (
                    word != unique_words[-1]
                ):  # Check if the current word is different from the previous word
                    unique_words.append(word)
            return " ".join(unique_words)

        try:
            time_segment = self.get_time_of_day_description()
            day_of_month_desc = self.get_day_of_month_description()
            month_desc = self.get_month_description()
            day_of_week_desc = self.get_day_of_week_description()
            week_desc = self.get_week_number_description()
            year_desc = self.get_year_description()

            description = f"{time_segment}{day_of_month_desc}{day_of_week_desc}{month_desc}{week_desc}{year_desc}"
            description = remove_adjacent_duplicates(description)
            description = f"{description[0].upper()}{description[1:]}"

        except Exception as e:
            description = (
                f"An error occurred when generating the expression description.  error is {e}"
            )

            raise ValueError(description) from e

        return description

    def get_time_of_day_description(self) -> str:
        """Generates a description for only the TIMEOFDAY portion of the expression.

        Returns
        -------
            The TIMEOFDAY description

        """
        seconds_expression = self.cron_sec
        minute_expression = self.cron_min
        hour_expression = self.cron_hour
        description = ""

        # handle special cases first
        if (
            any(exp in minute_expression for exp in self._special_characters) is False
            and any(exp in hour_expression for exp in self._special_characters) is False
            and any(exp in seconds_expression for exp in self._special_characters) is False
        ):
            # specific time of day (i.e. 10 14)
            description = (
                f"At {self.format_time(hour_expression, minute_expression, seconds_expression)} "
            )

        elif (
            seconds_expression == ""
            and "-" in minute_expression
            and "," not in minute_expression
            and any(exp in hour_expression for exp in self._special_characters) is False
        ):
            # minute range in single hour (i.e. 0-10 11)
            minute_parts = minute_expression.split("-")
            description = f"Every minute between {self.format_time(hour_expression, minute_parts[0])} and {self.format_time(hour_expression, minute_parts[1])} "

        elif (
            seconds_expression == ""
            and "," in hour_expression
            and "-" not in hour_expression
            and any(exp in minute_expression for exp in self._special_characters) is False
        ):
            # hours list with single minute (o.e. 30 6,14,16)
            hour_parts = hour_expression.split(",")
            description = "At" + "".join(
                f" {self.format_time(hour_part, minute_expression)}"
                + (
                    ","
                    if i < len(hour_parts) - 2
                    else (" and" if i == len(hour_parts) - 2 else "")
                )
                for i, hour_part in enumerate(hour_parts)
            )

        else:
            # default time description
            seconds_description = self.get_seconds_description()
            minutes_description = self.get_minutes_description()
            hours_description = self.get_hours_description()

            description = str(seconds_description)

            if description and minutes_description:
                description += ", "

            description += str(minutes_description)

            if description and hours_description:
                description += ", "

            description += str(hours_description)
        return description

    def get_seconds_description(self) -> Optional[str]:
        """Generates a description for only the SECONDS portion of the expression.

        Returns
        -------
            The SECONDS description

        """
        return self.get_segment_description(
            self.cron_sec,
            "every second",
            lambda s: s,
            lambda s: f"every {s} seconds",
            lambda s: "seconds {0} through {1} past the minute",
            lambda s: "" if s == "0" else "at {0} seconds past the minute",
            lambda s: ", {0} through {1}",
        )

    def get_minutes_description(self) -> Optional[str]:
        """Generates a description for only the MINUTE portion of the expression.

        Returns
        -------
            The MINUTE description

        """
        return self.get_segment_description(
            self.cron_min,
            "every minute",
            lambda s: s,
            lambda s: f"every {s} minutes",
            lambda s: "minutes {0} through {1} past the hour",
            lambda s: "" if s == "0" and self.cron_sec == "" else "at {0} minutes past the hour",
            lambda s: ", {0} through {1}",
        )

    def get_hours_description(self) -> Optional[str]:
        """Generates a description for only the HOUR portion of the expression.

        Returns
        -------
            The HOUR description

        """
        return self.get_segment_description(
            self.cron_hour,
            "every hour",
            lambda s: self.format_time(s, "0"),
            lambda s: f"every {s} hours",
            lambda s: "between {0} and {1}",
            lambda s: "at {0}",
            lambda s: ", {0} through {1}",
        )

    def get_day_of_week_description(self) -> Optional[str]:
        """Generates a description for only the DAYOFWEEK portion of the expression.

        Returns
        -------
            The DAYOFWEEK description

        """
        if self.cron_week_day == "*":
            # DOW is specified as * so we will not generate a description and defer to DOM part.
            # Otherwise, we could get a contradiction like "on day 1 of the month, every day"
            # or a dupe description like "every day, every day".
            return ""

        def get_day_name(s: str) -> str:
            try:
                return calendar.day_name[int(s)]
            except (IndexError, ValueError):
                pass
            try:
                return calendar.day_name[list(calendar.day_abbr).index(s.title())]
            except ValueError:
                pass
            return s

        return self.get_segment_description(
            self.cron_week_day,
            ", every day",
            lambda s: get_day_name(s),
            lambda s: f", every {s} days of the week",
            lambda s: ", {0} through {1}",
            lambda s: ", only on {0}",
            lambda s: ", {0} through {1}",
        )

    def get_week_number_description(self) -> Optional[str]:
        """Generates a description for only the week number portion of the expression.

        Returns
        -------
            The week description

        """
        return self.get_segment_description(
            self.cron_week,
            "",
            lambda s: s,
            lambda s: f", every {s} weeks",
            lambda s: ", week {0} through {1}",
            lambda s: ", only on week {0} of the year",
            lambda s: ", week {0} through {1}",
        )

    def get_month_description(self) -> Optional[str]:
        """Generates a description for only the MONTH portion of the expression.

        Returns
        -------
            The MONTH description

        """

        def get_month_name(s: str) -> str:
            try:
                return calendar.month_name[int(s)]
            except (IndexError, ValueError):
                pass
            try:
                return calendar.month_name[list(calendar.month_abbr).index(s.title())]
            except ValueError:
                pass
            return s

        return self.get_segment_description(
            self.cron_month,
            "",
            lambda s: get_month_name(s),
            lambda s: f", every {s} months",
            lambda s: ", {0} through {1}",
            lambda s: ", only in {0}",
            lambda s: ", {0} through {1}",
        )

    def get_day_of_month_description(self) -> str:
        """Generates a description for only the DAYOFMONTH portion of the expression.

        Returns
        -------
            The DAYOFMONTH description

        """

        def _add_suffix(day: str) -> str:
            try:
                d = int(day)
                if 10 <= d % 100 <= 20:
                    suffix = "th"
                else:
                    suffix = {1: "st", 2: "nd", 3: "rd"}.get(d % 10, "th")
                return str(d) + suffix + " day"
            except ValueError:
                return day

        exp = self.cron_day
        if exp.lower() == "last":
            description = ", on the last day of the month"
        elif re.match(r"^last\s\D{3}$", exp, re.IGNORECASE):
            parts = exp.split()
            description = f", on the last {calendar.day_name[self._cron_days[parts[1].upper()]]} of the month"

        else:
            description = str(
                self.get_segment_description(
                    exp,
                    ", every day" if self.cron_week_day == "*" else "",
                    lambda s: _add_suffix(s),
                    lambda s: ", every day" if s == "1" else ", every {0}",
                    lambda s: ", between {0} and {1} day of the month",
                    lambda s: " on the {0} of the month",
                    lambda s: ", {0} through {1}",
                )
            )

        return description

    def get_year_description(self) -> Optional[str]:
        """Generates a description for only the YEAR portion of the expression.

        Returns
        -------
            The YEAR description

        """
        return self.get_segment_description(
            self.cron_year,
            "",
            lambda s: s,
            lambda s: f", every {s} years",
            lambda s: ", year {0} through year {1}",
            lambda s: ", only in {0}",
            lambda s: ", year {0} through year {1}",
        )

    def get_segment_description(
        self,
        expression: str,
        all_description: str,
        get_single_item_description: Callable[[Any], str],
        get_interval_description_format: Callable[[Any], str],
        get_between_description_format: Callable[[Any], str],
        get_description_format: Callable[[Any], str],
        get_range_format: Callable[[Any], str],
    ) -> Optional[str]:
        """Returns segment description.

        Args:
        ----
            expression: Segment to descript
            all_description: if everything then description for it.
            get_single_item_description: single item description such as Monday.
            get_interval_description_format: description for an interval such as 1/2.
            get_between_description_format: description for a between such as 1-2.
            get_description_format: Format get_single_item_description.
            get_range_format: Function that formats range expressions depending on cron parts.

        Returns:
        -------
            segment description.

        """
        description = None
        expression = expression.strip()
        if expression is None or expression == "":
            description = ""
        elif expression == "*":
            description = all_description
        elif not any(ext in expression for ext in ["/", "-", ",", " "]):
            description = get_description_format(expression).format(
                get_single_item_description(expression)
            )
        elif "," in expression:
            segments = expression.split(",")
            description_content = ""
            for i, seg in enumerate(segments):
                seg = seg.strip()
                if i > 0 and len(segments) > 2:
                    description_content += ", "

                    if i < len(segments) - 1:
                        description_content += " "

                if i > 0 and len(segments) > 1 and (i == len(segments) - 1 or len(segments) == 2):
                    description_content += " and "
                description_content += str(
                    self.get_segment_description(
                        seg,
                        all_description,
                        get_single_item_description,
                        get_interval_description_format,
                        get_between_description_format,
                        get_single_item_description,
                        get_range_format,
                    )
                )
                # replace weirdness
                description_content = description_content.replace("and ,", "and")
                description_content = description_content.replace("of the month", "")

            description = get_description_format(expression).format(description_content)
        elif " " in expression and not any(ext in expression for ext in ["/", "-", ","]):
            daypart = expression.split()
            if len(daypart) > 1 and daypart[1].lower() in map(str.lower, calendar.day_abbr):
                expression = (
                    f"{daypart[0]} {calendar.day_name[self._cron_days[daypart[1].upper()]]}"
                )
            description = get_description_format(expression).format(
                get_single_item_description(expression)
            )
        elif "/" in expression:
            segments = expression.split("/")
            description = get_interval_description_format(segments[1]).format(
                get_single_item_description(segments[1])
            )

            # interval contains 'between' piece (i.e. 2-59/3 )
            if "-" in segments[0]:
                between_segment_description = self.generate_between_segment_description(
                    segments[0],
                    get_between_description_format,
                    get_single_item_description,
                )
                if not between_segment_description.startswith(", "):
                    description += ", "

                description += between_segment_description
            elif not any(ext in segments[0] for ext in ["*", ","]):
                range_item_description = get_description_format(segments[0]).format(
                    get_single_item_description(segments[0])
                )
                range_item_description = range_item_description.replace(", ", "")

                description += f", starting {range_item_description}"
        elif "-" in expression:
            description = self.generate_between_segment_description(
                expression, get_between_description_format, get_single_item_description
            )

        return description

    def generate_between_segment_description(
        self,
        between_expression: str,
        get_between_description_format: Callable[[Any], str],
        get_single_item_description: Callable[[Any], str],
    ) -> str:
        """
        Generates the between segment description.

        :param between_expression: the expression that is passed in.
        :param get_between_description_format: a format for how to describe the between expression.
        :param get_single_item_description: if it is one item, then this is the expression.

        :return: The between segment description.
        """
        description = ""
        between_segments = between_expression.split("-")
        between_segment_1_description = get_single_item_description(between_segments[0])
        between_segment_2_description = get_single_item_description(between_segments[1])
        between_segment_2_description = between_segment_2_description.replace(":00", ":59")

        between_description_format = get_between_description_format(between_expression)
        description += between_description_format.format(
            between_segment_1_description, between_segment_2_description
        )

        return description

    def format_time(
        self, hour_expression: str, minute_expression: str, second_expression: str = ""
    ) -> str:
        """Given time parts, will construct a formatted time description.

        Args:
        ----
            hour_expression: This is the Hours part of the time.
            minute_expression: Minutes part of time.
            second_expression: Seconds part of time.

        Returns:
        -------
            Formatted time description.

        """
        hour = int(hour_expression)

        period = ""

        period = "PM" if (hour >= 12) else "AM"
        if period:
            # add preceding space
            period = " " + period

        if hour > 12:
            hour -= 12

        if hour == 0:
            hour = 12

        minute = str(int(minute_expression))  # Removes leading zero if any
        second = ""
        if second_expression is not None and second_expression:
            second = f":{str(int(second_expression)).zfill(2)}"

        return f"{str(hour).zfill(2)}:{minute.zfill(2)}{second}{period}"

    def __str__(self) -> str:
        """Call the full description if this method is called."""
        return self.get_full_description()

    def __repr__(self) -> str:
        """Call the full description if this method is called."""
        return self.get_full_description()
