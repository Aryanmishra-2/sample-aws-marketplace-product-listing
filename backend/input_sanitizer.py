# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""
Input sanitization for user-provided text before sending to Amazon Bedrock.
Strips common prompt injection / instruction-override patterns.
"""

import re

# Patterns that attempt to override system instructions
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|above|prior)\s+(instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.IGNORECASE),
    re.compile(r"new\s+instructions?:", re.IGNORECASE),
    re.compile(r"system\s*prompt:", re.IGNORECASE),
    re.compile(r"<\s*/?\s*system\s*>", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"\[/INST\]", re.IGNORECASE),
    re.compile(r"<<\s*SYS\s*>>", re.IGNORECASE),
    re.compile(r"<<\s*/SYS\s*>>", re.IGNORECASE),
]


def sanitize_prompt_input(text: str) -> str:
    """Remove known prompt-injection patterns from user-supplied text.

    This is a defense-in-depth measure. For production workloads,
    configure Amazon Bedrock Guardrails with prompt-attack filters
    for more comprehensive protection.
    """
    if not text:
        return text
    sanitized = text
    for pattern in _INJECTION_PATTERNS:
        sanitized = pattern.sub("", sanitized)
    # Collapse multiple whitespace left by removals
    sanitized = re.sub(r"  +", " ", sanitized).strip()
    return sanitized
