import re

RE_MULTILINE_COMMENT = re.compile(r"-:.*:-", flags=re.S)
RE_SINGLELINE_COMMENT = re.compile(r"::.*")


def remove_comments(segment: str) -> str:
    """Removes comments from a modfile"""
    segment = RE_MULTILINE_COMMENT.sub(segment, "")
    segment = RE_SINGLELINE_COMMENT.sub(segment, "")

    return segment
