"""
Structural Edit Classification.
Assigns an EditEvent to broad structural categories based on heuristic signals.
"""
from __future__ import annotations
import re

from .normalizer import EditEvent

# Classification targets matching user specs
CLS_ARTICLE_CREATE      = "article_creation"
CLS_ARTICLE_EXPAND      = "article_expansion"
CLS_COPYEDIT_CLEANUP    = "copyedit_cleanup"
CLS_LEAD_REWRITE        = "lead_rewrite"
CLS_CHRONOLOGY_UPDATE   = "chronology_update"
CLS_INFOBOX_UPDATE      = "infobox_update"
CLS_CATEGORY_WORK       = "category_work"
CLS_TEMPLATE_WORK       = "template_work"
CLS_REFERENCE_WORK      = "reference_or_citation_work"
CLS_STRUCTURED_DATA     = "structured_data_work"
CLS_MEDIA_WORK          = "media_or_file_work"
CLS_REVERT_UNDO         = "revert_or_undo"
CLS_MINOR_POLISH        = "minor_polish"
CLS_MANUAL_REVIEW       = "manual_review_required"
CLS_SUMMARY_UNKNOWN     = "summary_unknown"
CLS_TALK_WORK           = "talk_page_discussion"
CLS_MAINTENANCE         = "project_maintenance"


def classify_edit(event: EditEvent) -> str:
    """Classify an EditEvent using structural signals."""
    ns = event.page.namespace_id
    comment = event.comment.lower()
    sdiff = event.sizediff

    # 1. Non-Main Namespace filtering
    if ns == 6:  # File:
        return CLS_MEDIA_WORK
    if ns == 14: # Category:
        return CLS_CATEGORY_WORK
    if ns == 10: # Template:
        return CLS_TEMPLATE_WORK
    if ns % 2 == 1: # Odd namespaces are talk pages (1=Talk, 3=User talk, etc.)
        return CLS_TALK_WORK
    if ns in (2, 3, 4, 12): # User, Wikipedia, Help
        return CLS_MAINTENANCE
    if event.project == "wikidata":
        # Almost all edits on Wikidata main ns are structured data
        return CLS_STRUCTURED_DATA

    # 2. Main Namespace (ns = 0) Signals
    # Exact flag signals
    if event.is_new:
        return CLS_ARTICLE_CREATE

    # Undo / Revert operations
    if "revert" in comment or "undo" in comment or "undid" in comment:
        return CLS_REVERT_UNDO

    # Specific Wikipedia summary conventions
    if re.search(r'\b(cite|ref|citation|sources)\b', comment):
        return CLS_REFERENCE_WORK
    if re.search(r'\b(cat|categories|categorize|categorise)\b', comment):
        return CLS_CATEGORY_WORK
    if re.search(r'\b(infobox|ibox)\b', comment):
        return CLS_INFOBOX_UPDATE
    if re.search(r'\b(lead|intro|lede)\b', comment):
        return CLS_LEAD_REWRITE
    if re.search(r'\b(update|current|now|history|year)\b', comment):
        return CLS_CHRONOLOGY_UPDATE
    if re.search(r'\b(ce|copyedit|grammar|typo|spelling|wording|cleanup|\+)\b', comment):
        if sdiff < 500:
            return CLS_COPYEDIT_CLEANUP
            
    # Sizediff based signals if comment is ambiguous
    if sdiff > 1500:
        return CLS_ARTICLE_EXPAND
    
    if event.is_minor or (0 <= sdiff < 200 and not comment):
        return CLS_MINOR_POLISH
        
    if not comment:
        return CLS_SUMMARY_UNKNOWN

    # Default fallback
    return CLS_MANUAL_REVIEW
