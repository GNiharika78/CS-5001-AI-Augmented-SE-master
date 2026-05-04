import re
from typing import Optional, Dict, Tuple


def make_bug_info(code, buggy_code, bug_type, original, mutated, description):
    if buggy_code == code:
        return None

    return {
        "buggy_code": buggy_code,
        "bug_type": bug_type,
        "original": original,
        "mutated": mutated,
        "description": description,
    }


def inject_simple_bug(code: str) -> Optional[Dict]:
    mutation_rules = [
        # arithmetic / operators
        (r"\*\*", "*", "operator_pow_to_mul", "**", "*", "Replace exponentiation with multiplication"),
        (r"(?<!\*)\*(?!\*)", "+", "operator_mul_to_plus", "*", "+", "Replace multiplication with addition"),
        (r"\+", "-", "operator_plus_to_minus", "+", "-", "Replace addition with subtraction"),
        (r"(?<![=!])==(?![=])", "!=", "operator_eq_to_neq", "==", "!=", "Replace equality with inequality"),
        (r"!=", "==", "operator_neq_to_eq", "!=", "==", "Replace inequality with equality"),

        # boundary bugs
        (r"<=", "<", "boundary_lte_to_lt", "<=", "<", "Tighten <= to <"),
        (r">=", ">", "boundary_gte_to_gt", ">=", ">", "Tighten >= to >"),
        (r"(?<!<)<(?![=<])", "<=", "boundary_lt_to_lte", "<", "<=", "Relax < to <="),
        (r"(?<!>)>(?![=>])", ">=", "boundary_gt_to_gte", ">", ">=", "Relax > to >="),

        # boolean logic
        (r"\band\b", "or", "boolean_and_to_or", "and", "or", "Replace and with or"),
        (r"\bor\b", "and", "boolean_or_to_and", "or", "and", "Replace or with and"),
        (r"\bTrue\b", "False", "boolean_true_to_false", "True", "False", "Replace True with False"),
        (r"\bFalse\b", "True", "boolean_false_to_true", "False", "True", "Replace False with True"),

        # builtins
        (r"\bmin\s*\(", "max(", "builtin_min_to_max", "min", "max", "Replace min with max"),
        (r"\bmax\s*\(", "min(", "builtin_max_to_min", "max", "min", "Replace max with min"),
        (r"reverse\s*=\s*True", "reverse=False", "sort_reverse_true_to_false", "reverse=True", "reverse=False", "Flip sort reverse flag"),
        (r"reverse\s*=\s*False", "reverse=True", "sort_reverse_false_to_true", "reverse=False", "reverse=True", "Flip sort reverse flag"),

        # loop / off-by-one
        (r"range\(([^,\)\n]+)\)", r"range(\1 - 1)", "loop_range_n_to_n_minus_1", "range(n)", "range(n-1)", "Off-by-one loop range"),
        (r"len\(([^)]+)\)", r"len(\1) - 1", "len_to_len_minus_1", "len(x)", "len(x)-1", "Off-by-one length"),
    ]

    for pattern, replacement, bug_type, original, mutated, description in mutation_rules:
        buggy_code, count = re.subn(pattern, replacement, code, count=1)
        if count > 0:
            return make_bug_info(
                code=code,
                buggy_code=buggy_code,
                bug_type=bug_type,
                original=original,
                mutated=mutated,
                description=description,
            )

    return None


# Compatibility wrapper for older experiment scripts
# Returns tuple: (buggy_code, bug_type)
def inject_bug(code: str, seed=None, **kwargs) -> Tuple[Optional[str], Optional[str]]:
    bug_info = inject_simple_bug(code)

    if bug_info is None:
        return None, None

    return bug_info["buggy_code"], bug_info["bug_type"]