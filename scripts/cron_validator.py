import re


class CronValidator:
    """Group of functions to make sure each cron field is correct"""

    _cron_days = {0: "SUN", 1: "MON", 2: "TUE", 3: "WED", 4: "THU", 5: "FRI", 6: "SAT"}
    _cron_months = {
        1: "JAN",
        2: "FEB",
        3: "MAR",
        4: "APR",
        5: "MAY",
        6: "JUN",
        7: "JUL",
        8: "AUG",
        9: "SEP",
        10: "OCT",
        11: "NOV",
        12: "DEC",
    }

    def __init__(
        self,
        cron,
        cron_year,
        cron_month,
        cron_week,
        cron_day,
        cron_week_day,
        cron_hour,
        cron_min,
        cron_sec,
    ) -> None:
        if not cron:
            pass
        else:
            self.cron_year = cron_year
            self.cron_month = cron_month
            self.cron_week = cron_week
            self.cron_day = cron_day
            self.cron_week_day = cron_week_day
            self.cron_hour = cron_hour
            self.cron_min = cron_min
            self.cron_sec = cron_sec

    def validate(self):
        if self.cron_year:
            self.year(self.cron_year, "Year")
        if self.cron_month:
            self.month(self.cron_month, "Month")
        if self.cron_week:
            self.week(self.cron_week, "Week")
        if self.cron_day:
            self.dayofmonth(self.cron_day, "Day")
        if self.cron_week_day:
            self.dayofweek(self.cron_week_day, "Week Day")
        if self.cron_hour:
            self.hour(self.cron_hour, "Hour")
        if self.cron_min:
            self.second_minute(self.cron_min, "Minute")
        if self.cron_sec:
            self.second_minute(self.cron_sec, "Second")

    def second_minute(self, expr: str, prefix: str):
        """sec/min expressions (n : Number, s: String)
        *
        nn (1~59)
        nn-nn
        nn/nn
        nn-nn/nn
        */nn
        nn,nn,nn (Maximum 24 elements)
        """
        mi, mx = (0, 59)
        if re.match(r"\d{1,2}$", expr):
            self.check_range(expr=expr, mi=mi, mx=mx, prefix=prefix)

        elif re.search(r"[-*,/]", expr):
            if "*" == expr:
                pass

            elif re.match(r"\d{1,2}-\d{1,2}$", expr):
                parts = expr.split("-")
                self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range(expr=parts[1], mi=mi, mx=mx, prefix=prefix)
                self.compare_range(
                    st=parts[0], ed=parts[1], mi=mi, mx=mx, prefix=prefix
                )

            elif re.match(r"\d{1,2}/\d{1,2}$", expr):
                parts = expr.split("/")
                self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range("interval", expr=parts[1], mi=mi, mx=mx, prefix=prefix)

            elif re.match(r"\d{1,2}-\d{1,2}/\d{1,2}$", expr):
                parts = expr.split("/")
                fst_parts = parts[0].split("-")
                self.check_range(expr=fst_parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range(expr=fst_parts[1], mi=mi, mx=mx, prefix=prefix)
                self.compare_range(
                    st=fst_parts[0], ed=fst_parts[1], mi=mi, mx=mx, prefix=prefix
                )
                self.check_range("interval", expr=parts[1], mi=mi, mx=mx, prefix=prefix)

            elif re.match(r"\*/\d{1,2}$", expr):
                parts = expr.split("/")
                self.check_range("interval", expr=parts[1], mi=mi, mx=mx, prefix=prefix)

            elif "," in expr:
                limit = 60
                expr_ls = expr.split(",")
                if len(expr_ls) > limit:
                    msg = "({0}) Exceeded maximum number({1}) of specified value. '{2}' is provided".format(
                        prefix, limit, len(expr_ls)
                    )
                    raise ValueError(msg)
                else:
                    for n in expr_ls:
                        self.second_minute(expr=n.strip(), prefix=prefix)
            else:
                msg = "({0}) Illegal Expression Format '{1}'".format(prefix, expr)
                raise ValueError(msg)

        else:
            msg = "({0}) Illegal Expression Format '{1}'".format(prefix, expr)

    def hour(self, expr: str, prefix: str):
        """hour expressions (n : Number, s: String)
        *
        nn (1~23)
        nn-nn
        nn/nn
        nn-nn/nn
        */nn
        nn,nn,nn (Maximum 24 elements)
        """
        mi, mx = (0, 23)
        if re.match(r"\d{1,2}$", expr):
            self.check_range(expr=expr, mi=mi, mx=mx, prefix=prefix)

        elif re.search(r"[-*,/]", expr):
            if "*" == expr:
                pass

            elif re.match(r"\d{1,2}-\d{1,2}$", expr):
                parts = expr.split("-")
                self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range(expr=parts[1], mi=mi, mx=mx, prefix=prefix)
                self.compare_range(
                    st=parts[0], ed=parts[1], mi=mi, mx=mx, prefix=prefix
                )

            elif re.match(r"\d{1,2}/\d{1,2}$", expr):
                parts = expr.split("/")
                self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range("interval", expr=parts[1], mi=mi, mx=mx, prefix=prefix)

            elif re.match(r"\d{1,2}-\d{1,2}/\d{1,2}$", expr):
                parts = expr.split("/")
                fst_parts = parts[0].split("-")
                self.check_range(expr=fst_parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range(expr=fst_parts[1], mi=mi, mx=mx, prefix=prefix)
                self.compare_range(
                    st=fst_parts[0], ed=fst_parts[1], mi=mi, mx=mx, prefix=prefix
                )
                self.check_range("interval", expr=parts[1], mi=mi, mx=mx, prefix=prefix)

            elif re.match(r"\*/\d{1,2}$", expr):
                parts = expr.split("/")
                self.check_range("interval", expr=parts[1], mi=mi, mx=mx, prefix=prefix)

            elif "," in expr:
                limit = 24
                expr_ls = expr.split(",")
                if len(expr_ls) > limit:
                    msg = "({0}) Exceeded maximum number({1}) of specified value. '{2}' is provided".format(
                        prefix, 24, len(limit)
                    )
                    raise ValueError(msg)
                else:
                    for n in expr_ls:
                        self.hour(expr=n.strip(), prefix=prefix)
            else:
                msg = "({0}) Illegal Expression Format '{1}'".format(prefix, expr)
                raise ValueError(msg)
        else:
            msg = "({0}) Illegal Expression Format '{1}'".format(prefix, expr)
            raise ValueError(msg)

    def dayofmonth(self, expr: str, prefix: str):
        """DAYOfMonth expressions (n : Number, s: String)
        *
        ?
        nn (1~31)
        nn-nn
        nn/nn
        nn-nn/nn
        */nn
        nn,nn,nn, nth sss, last sss, last (Maximum 31 elements)
        last
        nth sss
        last sss
        """
        mi, mx = (1, 31)
        if re.match(r"\d{1,2}$", expr):
            self.check_range(expr=expr, mi=mi, mx=mx, prefix=prefix)
        elif re.search(r"[-*,/?]", expr):
            if "*" == expr:
                pass

            elif "?" == expr:
                pass

            elif re.match(r"\d{1,2}-\d{1,2}$", expr):
                parts = expr.split("-")
                self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range(expr=parts[1], mi=mi, mx=mx, prefix=prefix)
                self.compare_range(
                    st=parts[0], ed=parts[1], mi=mi, mx=mx, prefix=prefix
                )

            elif re.match(r"\d{1,2}/\d{1,2}$", expr):
                parts = expr.split("/")
                self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range("interval", expr=parts[1], mi=0, mx=mx, prefix=prefix)

            elif re.match(r"\d{1,2}-\d{1,2}/\d{1,2}$", expr):
                parts = expr.split("/")
                fst_parts = parts[0].split("-")
                self.check_range(expr=fst_parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range(expr=fst_parts[1], mi=mi, mx=mx, prefix=prefix)
                self.compare_range(
                    st=fst_parts[0], ed=fst_parts[1], mi=mi, mx=mx, prefix=prefix
                )
                self.check_range("interval", expr=parts[1], mi=0, mx=mx, prefix=prefix)

            elif re.match(r"\*/\d{1,2}$", expr):
                parts = expr.split("/")
                self.check_range("interval", expr=parts[1], mi=0, mx=mx, prefix=prefix)

            elif "," in expr:
                limit = 31
                expr_ls = expr.split(",")
                if len(expr_ls) > 31:
                    msg = "({0}) Exceeded maximum number({1}) of specified value. '{2}' is provided".format(
                        prefix, limit, len(expr_ls)
                    )
                    raise ValueError(msg)
                else:
                    for dayofmonth in expr_ls:
                        self.dayofmonth(expr=dayofmonth.strip(), prefix=prefix)
            elif re.match(r"^(L|l)-(\d{1,2})$", expr):
                parts = expr.split("-")
                self.check_range(expr=parts[1], mi=mi, mx=mx, prefix=prefix)
            else:
                msg = "Illegal Expression Format '{0}'".format(expr)
                raise ValueError(msg)

        elif "last" == expr.lower():
            pass
        elif re.match(r"\d{1}(nd|st|rd|th)\s\D{3}$", expr, re.IGNORECASE):
            parts = expr.split()
            parts[0] = re.sub("[nd|st|rd|th]", "", parts[0])
            cron_days = {v: k for (k, v) in self._cron_days.items()}
            try:
                st_day = cron_days[parts[1].upper()]
            except KeyError:
                msg = "({0}) Invalid value '{1}'".format(prefix, expr)
                raise ValueError(msg)
            self.check_range(expr=parts[0], mi=mi, mx=5, prefix=prefix, type="day")
        elif re.match(r"last\s\D{3}$", expr, re.IGNORECASE):
            parts = expr.split()
            cron_days = {v: k for (k, v) in self._cron_days.items()}
            try:
                st_day = cron_days[parts[1].upper()]
            except KeyError:
                msg = "({0}) Invalid value '{1}'".format(prefix, expr)
                raise ValueError(msg)
        elif re.match(r"^(\d{1,2})(w{1}|W{1})$", expr):
            self.check_range(expr=expr[:-1], mi=mi, mx=mx, prefix=prefix)

        elif re.match(r"^(w{1}|W{1})(\d{1,2})$", expr):
            self.check_range(expr=expr[1:], mi=mi, mx=mx, prefix=prefix)

        else:
            msg = "({0}) Illegal Expression Format '{1}'".format(prefix, expr)
            raise ValueError(msg)

    def month(self, expr: str, prefix: str):
        """month expressions (n : Number, s: String)
        *
        nn (1~12)
        sss (JAN~DEC)
        nn-nn
        sss-sss
        nn/nn
        nn-nn/nn
        */nn
        nn,nn,nn,nn-nn,sss-sss (Maximum 12 elements)
        """
        mi, mx = (1, 12)
        if re.match(r"\d{1,2}$", expr):
            self.check_range(expr=expr, mi=mi, mx=mx, prefix=prefix)

        elif re.match(r"\D{3}$", expr):
            matched_month = [m for m in self._cron_months.values() if expr == m]
            if len(matched_month) == 0:
                msg = "Invalid Month value '{}'".format(expr)
                raise ValueError(msg)

        elif re.search(r"[-*,/]", expr):
            if "*" == expr:
                pass

            elif re.match(r"\d{1,2}-\d{1,2}$", expr):
                parts = expr.split("-")
                self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range(expr=parts[1], mi=mi, mx=mx, prefix=prefix)
                self.compare_range(
                    st=parts[0], ed=parts[1], mi=mi, mx=mx, prefix=prefix
                )

            elif re.match(r"\D{3}-\D{3}$", expr):
                parts = expr.split("-")
                cron_months = {v: k for (k, v) in self._cron_months.items()}
                st_not_exist = parts[0] not in cron_months
                ed_not_exist = parts[1] not in cron_months
                if st_not_exist or ed_not_exist:
                    msg = "Invalid Month value '{}'".format(expr)
                    raise ValueError(msg)
                self.compare_range(
                    st=cron_months[parts[0]],
                    ed=cron_months[parts[1]],
                    mi=mi,
                    mx=mx,
                    prefix=prefix,
                )

            elif re.match(r"\d{1,2}/\d{1,2}$", expr):
                parts = expr.split("/")
                self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range("interval", expr=parts[1], mi=0, mx=mx, prefix=prefix)

            elif re.match(r"\d{1,2}-\d{1,2}/\d{1,2}$", expr):
                parts = expr.split("/")
                fst_parts = parts[0].split("-")
                self.check_range(expr=fst_parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range(expr=fst_parts[1], mi=mi, mx=mx, prefix=prefix)
                self.compare_range(
                    st=fst_parts[0], ed=fst_parts[1], mi=mi, mx=mx, prefix=prefix
                )
                self.check_range("interval", expr=parts[1], mi=0, mx=12, prefix=prefix)

            elif re.match(r"\*/\d{1,2}$", expr):
                parts = expr.split("/")
                self.check_range("interval", expr=parts[1], mi=0, mx=12, prefix=prefix)

            elif "," in expr:
                """
                get values with a comma and then run each part through months again.
                """
                limit = 12
                expr_ls = expr.split(",")
                if len(expr_ls) > limit:
                    msg = "({0}) Exceeded maximum number({1}) of specified value. '{2}' is provided".format(
                        prefix, limit, len(expr_ls)
                    )
                    raise ValueError(msg)
                else:
                    for mon in expr_ls:
                        self.month(expr=mon.strip(), prefix=prefix)
            else:
                msg = "({0}) Illegal Expression Format '{1}'".format(prefix, expr)
                raise ValueError(msg)
        else:
            msg = "({0}) Illegal Expression Format '{1}'".format(prefix, expr)
            raise ValueError(msg)

    def week(self, expr: str, prefix: str):
        """week expressions (n : Number)
        *
        ?
        n (1~53) - 1 and 53 for up to 53 weeks a year
        n/n
        n-n/n
        */n
        n-n
        n-n,n (maximum 53 elements)
        """
        mi, mx = (1, 53)

        if "*" == expr:
            pass

        elif "?" == expr:
            pass

        elif re.match(r"\d{1,2}", expr):
            self.check_range(expr=expr, mi=mi, mx=mx, prefix=prefix)

        elif re.match(r"\d{1}/\d{1}$", expr):
            parts = expr.split("/")
            self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
            self.check_range("interval", expr=parts[1], mi=0, mx=mx, prefix=prefix)

        elif re.match(r"\d{1}-\d{1}/\d{1}$", expr):
            parts = expr.split("/")
            fst_parts = parts[0].split("-")
            self.check_range(expr=fst_parts[0], mi=mi, mx=mx, prefix=prefix)
            self.check_range(expr=fst_parts[1], mi=mi, mx=mx, prefix=prefix)
            self.compare_range(
                st=fst_parts[0], ed=fst_parts[1], mi=mi, mx=mx, prefix=prefix
            )
            self.check_range("interval", expr=parts[1], mi=0, mx=mx, prefix=prefix)

        elif re.match(r"[*]/\d{1}$", expr):
            parts = expr.split("/")
            self.check_range("interval", expr=parts[1], mi=0, mx=mx, prefix=prefix)
        elif "," in expr:
            parts = expr.split(",")
            if len(parts) > 53:
                msg = "({0}) Exceeded maximum number({1}) of specified value. '{2}' is provided".format(
                    prefix, mx, len(parts)
                )
                raise ValueError(msg)
            else:
                for w in parts:
                    self.week(expr=w.strip(), prefix=prefix)

    def dayofweek(self, expr: str, prefix: str):
        """DAYOfWeek expressions (n : Number, s: String)
        *
        ?
        n (0~7) - 0 and 7 used interchangeable as Sunday
        sss (SUN~SAT)
        n/n
        n-n/n
        */n
        n-n
        sss-sss
        n-n,sss-sss (maximum 7 elements)
        """
        mi, mx = (0, 7)

        if "*" == expr:
            pass

        elif "?" == expr:
            pass

        elif re.match(r"\d{1}$", expr):
            self.check_range(expr=expr, mi=mi, mx=mx, prefix=prefix)

        elif re.match(r"\D{3}$", expr):
            cron_days = {v: k for (k, v) in self._cron_days.items()}
            if expr.upper() in cron_days:
                pass
            else:
                msg = "Invalid value '{}'".format(expr)
                raise ValueError(msg)

        elif re.match(r"\d{1}/\d{1}$", expr):
            parts = expr.split("/")
            self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
            self.check_range("interval", expr=parts[1], mi=0, mx=mx, prefix=prefix)

        elif re.match(r"\d{1}-\d{1}/\d{1}$", expr):
            parts = expr.split("/")
            fst_parts = parts[0].split("-")
            self.check_range(expr=fst_parts[0], mi=mi, mx=mx, prefix=prefix)
            self.check_range(expr=fst_parts[1], mi=mi, mx=mx, prefix=prefix)
            self.compare_range(
                st=fst_parts[0], ed=fst_parts[1], mi=mi, mx=mx, prefix=prefix
            )
            self.check_range("interval", expr=parts[1], mi=0, mx=mx, prefix=prefix)

        elif re.match(r"[*]/\d{1}$", expr):
            parts = expr.split("/")
            self.check_range("interval", expr=parts[1], mi=0, mx=mx, prefix=prefix)

        elif re.match(r"\d{1}-\d{1}$", expr):
            parts = expr.split("-")
            self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
            self.check_range(expr=parts[1], mi=mi, mx=mx, prefix=prefix)
            self.compare_range(st=parts[0], ed=parts[1], mi=mi, mx=mx, prefix=prefix)

        elif re.match(r"\D{3}-\D{3}$", expr):
            parts = expr.split("-")
            cron_days = {v: k for (k, v) in self._cron_days.items()}
            try:
                st_day = cron_days[parts[0].upper()]
                ed_day = cron_days[parts[1].upper()]
            except KeyError:
                msg = "({0}) Invalid value '{1}'".format(prefix, expr)
                raise ValueError(msg)
            self.compare_range(
                st=st_day, ed=ed_day, mi=mi, mx=mx, prefix=prefix, type="dow"
            )

        elif "," in expr:
            limit = 7
            expr_ls = expr.split(",")
            if len(expr_ls) > limit:
                msg = "({0}) Exceeded maximum number({1}) of specified value. '{2}' is provided".format(
                    prefix, limit, len(expr_ls)
                )
                raise ValueError(msg)
            else:
                for day in expr_ls:
                    self.dayofweek(expr=day.strip(), prefix=prefix)

        else:
            msg = "({0}) Illegal Expression Format '{1}'".format(prefix, expr)
            raise ValueError(msg)

    def year(self, expr: str, prefix: str):
        """Year - valid expression (n : Number)
        *
        nnnn(1970~2099) - 4 digits number
        nnnn-nnnn(1970~2099)
        nnnn/nnn(0~129)
        */nnn(0~129)
        nnnn,nnnn,nnnn(1970~2099) - maximum 86 elements
        """
        mi, mx = (1970, 2099)
        if re.match(r"\d{4}$", expr):
            self.check_range(expr=expr, mi=mi, mx=mx, prefix=prefix)

        elif re.search(r"[-*,/]", expr):
            if "*" == expr:
                pass

            elif re.match(r"\d{4}-\d{4}$", expr):
                parts = expr.split("-")
                self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range(expr=parts[1], mi=mi, mx=mx, prefix=prefix)
                self.compare_range(
                    st=parts[0], ed=parts[1], mi=mi, mx=mx, prefix=prefix
                )

            elif re.match(r"\d{4}/\d{1,3}$", expr):
                parts = expr.split("/")
                self.check_range(expr=parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range("interval", expr=parts[1], mi=0, mx=129, prefix=prefix)

            elif re.match(r"\d{4}-\d{4}/\d{1,3}$", expr):
                parts = expr.split("/")
                fst_parts = parts[0].split("-")
                self.check_range(expr=fst_parts[0], mi=mi, mx=mx, prefix=prefix)
                self.check_range(expr=fst_parts[1], mi=mi, mx=mx, prefix=prefix)
                self.compare_range(
                    st=fst_parts[0], ed=fst_parts[1], mi=mi, mx=mx, prefix=prefix
                )
                self.check_range("interval", expr=parts[1], mi=0, mx=129, prefix=prefix)

            elif re.match(r"\*/\d{1,3}$", expr):
                parts = expr.split("/")
                self.check_range("interval", expr=parts[1], mi=0, mx=129, prefix=prefix)

            elif re.match(r"\d{1}/\d{1,3}$", expr):
                parts = expr.split("/")
                self.check_range(expr=parts[0], mi=0, mx=129, prefix=prefix)
                self.check_range("interval", expr=parts[1], mi=0, mx=129, prefix=prefix)

            elif "," in expr:
                limit = 84
                expr_ls = expr.split(",")
                if len(expr_ls) > limit:
                    msg = "({0}) Exceeded maximum number({1}) of specified value. '{2}' is provided".format(
                        prefix, limit, len(expr_ls)
                    )
                    raise ValueError(msg)
                else:
                    for year in expr_ls:
                        self.year(expr=year.strip(), prefix=prefix)
            else:
                msg = "({0}) Illegal Expression Format '{1}'".format(prefix, expr)
                raise ValueError(msg)
        else:
            msg = "({0}) Illegal Expression Format '{1}'".format(prefix, expr)
            raise ValueError(msg)

    def check_range(self, type=None, **kwargs):
        """
        check if expression value within range of specified limit
        """
        prefix = kwargs["prefix"]
        mi = kwargs["mi"]
        mx = kwargs["mx"]
        expr = kwargs["expr"]
        if int(expr) < mi or mx < int(expr):
            if type is None:
                msg = "{0} values must be between {1} and {2} but '{3}' is provided".format(
                    prefix, mi, mx, expr
                )
            elif type == "interval":
                msg = "({0}) Accepted increment value range is {1}~{2} but '{3}' is provided".format(
                    prefix, mi, mx, expr
                )
            elif type == "dow":
                msg = (
                    "({0}) Accepted week value is {1}~{2} but '{3}' is provided".format(
                        prefix, mi, mx, expr
                    )
                )
            raise ValueError(msg)
        else:
            pass

    def compare_range(self, type=None, **kwargs):
        """check 2 expression values size
        does not allow {st} value to be greater than {ed} value
        """
        prefix = kwargs["prefix"]
        st = kwargs["st"]
        ed = kwargs["ed"]
        mi = kwargs["mi"]
        mx = kwargs["mx"]
        if int(st) > int(ed):
            if type is None:
                msg = "({0}) Invalid range '{1}-{2}'. Accepted range is {3}-{4}".format(
                    prefix, st, ed, mi, mx
                )
            elif type == "dow":
                msg = "({0}) Invalid range '{1}-{2}'. Accepted range is {3}-{4}".format(
                    prefix, self._cron_days[st], self._cron_days[ed], mi, mx
                )
            raise ValueError(msg)
