"""
Cron schedule descriptions.
Returns schedules in a readable format.
"""

import calendar
import datetime
import re


class ExpressionDescriptor:

    """
    Converts a Cron Expression into a human readable string
    """

    _special_characters = ["/", "-", ",", "*"]

    def __init__(
        self,
        cron_year,
        cron_month,
        cron_week,
        cron_day,
        cron_week_day,
        cron_hour,
        cron_min,
        cron_sec,
    ) -> None:
        """Initializes a new instance of the ExpressionDescriptor

        Args:
           cron parts

        """
        self.cron_year = cron_year
        self.cron_month = cron_month
        self.cron_week = cron_week
        self.cron_day = cron_day
        self.cron_week_day = cron_week_day
        self.cron_hour = cron_hour
        self.cron_min = cron_min
        self.cron_sec = cron_sec

        if self.cron_sec is None or self.cron_sec == "":
            self.cron_sec = "0"
        if self.cron_min is None or self.cron_min == "":
            self.cron_min = "0"
        if self.cron_hour is None or self.cron_hour == "":
            self.cron_hour = "0"
        if self.cron_month is None or self.cron_month == "":
            self.cron_month = "*"
        if self.cron_year is None or self.cron_year == "":
            self.cron_year = "*"
        if self.cron_day is None or self.cron_day == "":
            self.cron_day = "*"
        if self.cron_week_day is None or self.cron_week_day == "":
            self.cron_week_day = "*"

    def get_full_description(self):
        """Generates the FULL description

        Returns:
            The FULL description
        Raises:
            FormatException: if formatting fails

        """

        try:
            time_segment = self.get_time_of_day_description()
            day_of_month_desc = self.get_day_of_month_description()
            month_desc = self.get_month_description()
            day_of_week_desc = self.get_day_of_week_description()
            week_desc = self.get_week_number_description()
            year_desc = self.get_year_description()

            description = f"{time_segment}{day_of_month_desc}{day_of_week_desc}{month_desc}{week_desc}{year_desc}"

            description = self.transform_verbosity(description, True)
            description = (
                f"{description[0].upper()}{description[1:]}"  # sentence casing
            )
        except Exception:
            description = "An error occurred when generating the expression description.  Check the cron expression syntax."

            raise ValueError(description)

        return description

    def get_time_of_day_description(self):
        """Generates a description for only the TIMEOFDAY portion of the expression

        Returns:
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
            and any(exp in seconds_expression for exp in self._special_characters)
            is False
        ):
            # specific time of day (i.e. 10 14)
            description = f"At {self.format_time(hour_expression, minute_expression, seconds_expression)} "

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
            and any(exp in minute_expression for exp in self._special_characters)
            is False
        ):
            # hours list with single minute (o.e. 30 6,14,16)
            hour_parts = hour_expression.split(",")
            description = "At"
            for i, hour_part in enumerate(hour_parts):
                description = description + " "
                description = (
                    description + f"{self.format_time(hour_part, minute_expression)}"
                )

                if i < (len(hour_parts) - 2):
                    description = description + ","

                if i == len(hour_parts) - 2:
                    description = description + " and"
        else:
            # default time description
            seconds_description = self.get_seconds_description()
            minutes_description = self.get_minutes_description()
            hours_description = self.get_hours_description()

            description = seconds_description

            if description and minutes_description:
                description = description + ", "

            description = description + minutes_description

            if description and hours_description:
                description = description + ", "

            description = description + hours_description
        return str(description)

    def get_seconds_description(self):
        """Generates a description for only the SECONDS portion of the expression

        Returns:
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

    def get_minutes_description(self):
        """Generates a description for only the MINUTE portion of the expression

        Returns:
            The MINUTE description

        """
        return self.get_segment_description(
            self.cron_min,
            "every minute",
            lambda s: s,
            lambda s: f"every {s} minutes",
            lambda s: "minutes {0} through {1} past the hour",
            lambda s: ""
            if s == "0" and self.cron_sec == ""
            else "at {0} minutes past the hour",
            lambda s: ", {0} through {1}",
        )

    def get_hours_description(self):
        """Generates a description for only the HOUR portion of the expression

        Returns:
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

    def get_day_of_week_description(self):
        """Generates a description for only the DAYOFWEEK portion of the expression

        Returns:
            The DAYOFWEEK description

        """
        if self.cron_week_day == "*":
            # DOW is specified as * so we will not generate a description and defer to DOM part.
            # Otherwise, we could get a contradiction like "on day 1 of the month, every day"
            # or a dupe description like "every day, every day".
            return ""

        def get_day_name(s):
            exp = s
            day_choices = {
                "mon": 0,
                "tue": 1,
                "wed": 2,
                "thu": 3,
                "fri": 4,
                "sat": 5,
                "sun": 6,
            }
            try:
                return self.number_to_day(int(day_choices.get(exp.lower(), exp)))
            except:
                return exp

        return self.get_segment_description(
            self.cron_week_day,
            ", every day",
            lambda s: get_day_name(s),
            lambda s: f", every {s} days of the week",
            lambda s: ", {0} through {1}",
            lambda s: ", only on {0}",
            lambda s: ", {0} through {1}",
        )

    def get_week_number_description(self):
        """Generates a description for only the week number portion of the expression

        Returns:
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

    def get_month_description(self):
        """Generates a description for only the MONTH portion of the expression

        Returns:
            The MONTH description

        """

        def get_month_number(s):
            exp = s

            try:
                return list(calendar.month_abbr).index(exp.title())
            except:
                return exp

        return self.get_segment_description(
            self.cron_month,
            "",
            lambda s: datetime.date(
                datetime.date.today().year, int(get_month_number(s)), 1
            ).strftime("%B"),
            lambda s: f", every {s} months",
            lambda s: ", {0} through {1}",
            lambda s: ", only in {0}",
            lambda s: ", {0} through {1}",
        )

    def get_day_format(s):
        if re.match(r"^\d{1}(nd|st|rd|th)", s):
            day_of_week_of_month = s[0]

            try:
                day_of_week_of_month_number = int(day_of_week_of_month)
                choices = {
                    1: "first",
                    2: "second",
                    3: "third",
                    4: "forth",
                    5: "fifth",
                }
                day_of_week_of_month_description = choices.get(
                    day_of_week_of_month_number, ""
                )
            except ValueError:
                day_of_week_of_month_description = ""

            formatted = f", on the {day_of_week_of_month_description}{0} of the month"
        elif "last" in s.lower():
            formatted = ", on the last {0} of the month"
        else:
            formatted = ", only on {0}"

        return formatted

    def get_day_of_month_description(self):
        """Generates a description for only the DAYOFMONTH portion of the expression

        Returns:
            The DAYOFMONTH description

        """

        def get_day_name(s):
            exp = s
            day_choices = {
                "mon": 0,
                "tue": 1,
                "wed": 2,
                "thu": 3,
                "fri": 4,
                "sat": 5,
                "sun": 6,
            }
            try:
                return self.number_to_day(int(day_choices.get(exp.lower(), exp)))
            except:
                return exp

        exp = self.cron_day
        if re.match(r"\d{1}(nd|st|rd|th)\s\D{3}$", exp, re.IGNORECASE):
            parts = exp.split()
            description = f", on the {parts[0].lower()} {get_day_name(parts[1].upper())} of the month"
        elif exp.lower() == "last":
            description = ", on the last day of the month"
        elif re.match(r"last\s\D{3}$", exp, re.IGNORECASE):
            parts = exp.split()
            description = f", on the last {parts[1].upper()} of the month"

        else:
            description = self.get_segment_description(
                exp,
                ", every day" if self.cron_week_day == "*" else "",
                lambda s: s,
                lambda s: ", every day" if s == "1" else ", every {0} days",
                lambda s: ", between day {0} and {1} of the month",
                lambda s: " on the {0} day of the month"
                if s.isdigit()
                else " on the {0} of the month",
                lambda s: ", {0} through {1}",
            )

        return description

    def get_year_description(self):
        """Generates a description for only the YEAR portion of the expression

        Returns:
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
        expression,
        all_description,
        get_single_item_description,
        get_interval_description_format,
        get_between_description_format,
        get_description_format,
        get_range_format,
    ):
        """Returns segment description
        Args:
            expression: Segment to descript
            all_description: *
            get_single_item_description: 1
            get_interval_description_format: 1/2
            get_between_description_format: 1-2
            get_description_format: format get_single_item_description
            get_range_format: function that formats range expressions depending on cron parts
        Returns:
            segment description

        """
        day_choices = {
            "mon": 0,
            "tue": 1,
            "wed": 2,
            "thu": 3,
            "fri": 4,
            "sat": 5,
            "sun": 6,
        }

        description = None
        if expression is None or expression == "":
            description = ""
        elif expression == "*":
            description = all_description
        elif any(ext in expression for ext in ["/", "-", ","]) is False:
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
            elif any(ext in segments[0] for ext in ["*", ","]) is False:
                range_item_description = get_description_format(segments[0]).format(
                    get_single_item_description(segments[0])
                )
                range_item_description = range_item_description.replace(", ", "")

                description += f", starting {range_item_description}"
        elif "," in expression:
            segments = expression.split(",")
            for i in range(len(segments)):
                segments[i] = segments[i].strip()
                daypart = segments[i].split()
                if len(daypart) > 1 and daypart[1].lower() in day_choices:
                    segments[
                        i
                    ] = f"{daypart[0]} {self.number_to_day(day_choices.get(daypart[1].lower()))}"
            description_content = ""

            for i, segment in enumerate(segments):
                if i > 0 and len(segments) > 2:
                    description_content += ","

                    if i < len(segments) - 1:
                        description_content += " "

                if (
                    i > 0
                    and len(segments) > 1
                    and (i == len(segments) - 1 or len(segments) == 2)
                ):
                    description_content += " and "

                if "-" in segment:
                    between_segment_description = (
                        self.generate_between_segment_description(
                            segment, get_range_format, get_single_item_description
                        )
                    )

                    between_segment_description = between_segment_description.replace(
                        ", ", ""
                    )

                    description_content += between_segment_description
                else:
                    description_content += get_single_item_description(segment)

            description = get_description_format(expression).format(description_content)
        elif "-" in expression:
            description = self.generate_between_segment_description(
                expression, get_between_description_format, get_single_item_description
            )

        return description

    def generate_between_segment_description(
        self,
        between_expression,
        get_between_description_format,
        get_single_item_description,
    ):
        """
        Generates the between segment description
        :param between_expression:
        :param get_between_description_format:
        :param get_single_item_description:
        :return: The between segment description
        """
        description = ""
        between_segments = between_expression.split("-")
        between_segment_1_description = get_single_item_description(between_segments[0])
        between_segment_2_description = get_single_item_description(between_segments[1])
        between_segment_2_description = between_segment_2_description.replace(
            ":00", ":59"
        )

        between_description_format = get_between_description_format(between_expression)
        description += between_description_format.format(
            between_segment_1_description, between_segment_2_description
        )

        return description

    def format_time(self, hour_expression, minute_expression, second_expression=""):
        """Given time parts, will construct a formatted time description
        Args:
            hour_expression: Hours part
            minute_expression: Minutes part
            second_expression: Seconds part
        Returns:
            Formatted time description

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

    def transform_verbosity(self, description, use_verbose_format):
        """Transforms the verbosity of the expression description by stripping verbosity from original description
        Args:
            description: The description to transform
            use_verbose_format: If True, will leave description as it, if False, will strip verbose parts
        Returns:
            The transformed description with proper verbosity

        """
        if use_verbose_format is False:
            description = description.replace(", every minute", "")
            description = description.replace(", every hour", "")
            description = description.replace(", every day", "")
            description = re.sub(r", ?$", "", description)
        return description

    @staticmethod
    def number_to_day(day_number):
        """Returns localized day name by its CRON number

        Args:
            day_number: Number of a day
        Returns:
            Day corresponding to day_number
        Raises:
            IndexError: When day_number is not found
        """
        try:
            return [
                calendar.day_name[0],
                calendar.day_name[1],
                calendar.day_name[2],
                calendar.day_name[3],
                calendar.day_name[4],
                calendar.day_name[5],
                calendar.day_name[6],
            ][day_number]
        except IndexError:
            raise IndexError(f"Day {day_number} is out of range!")

    def __str__(self):
        return self.get_full_description()

    def __repr__(self):
        return self.get_full_description()


def get_description(expression):
    """Generates a human readable string for the Cron Expression
    Args:
        expression: The cron expression string
    Returns:
        The cron expression description

    """
    descriptor = ExpressionDescriptor(expression)
    return descriptor.get_full_description()
