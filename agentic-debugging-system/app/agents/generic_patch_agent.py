import re


class GenericPatchAgent:
    def generate_candidates(self, buggy_code: str):
        candidates = []

        def add(code, explanation):
            if code != buggy_code and code not in [c["code"] for c in candidates]:
                candidates.append({"code": code, "explanation": explanation})

        rules = [
            ("+", "-", "Replace + with -"),
            ("-", "+", "Replace - with +"),
            ("+", "*", "Replace + with *"),
            ("*", "+", "Replace * with +"),
            ("<=", "<", "Replace <= with <"),
            (">=", ">", "Replace >= with >"),
            ("<", "<=", "Replace < with <="),
            (">", ">=", "Replace > with >="),
            ("==", "!=", "Replace == with !="),
            ("!=", "==", "Replace != with =="),
            ("and", "or", "Replace and with or"),
            ("or", "and", "Replace or with and"),
            ("True", "False", "Replace True with False"),
            ("False", "True", "Replace False with True"),
            ("min(", "max(", "Replace min with max"),
            ("max(", "min(", "Replace max with min"),
        ]

        for old, new, explanation in rules:
            for match in re.finditer(re.escape(old), buggy_code):
                start, end = match.span()
                patched = buggy_code[:start] + new + buggy_code[end:]
                add(patched, explanation)

        # Safe exponent repair: single * to **
        for match in re.finditer(r"(?<!\*)\*(?!\*)", buggy_code):
            start, end = match.span()
            patched = buggy_code[:start] + "**" + buggy_code[end:]
            add(patched, "Replace * with **")

        return candidates