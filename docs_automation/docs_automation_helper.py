"""
Docs Automation Helper Module
Provides payload builders for Google Docs API batchUpdate,
Playwright browser automation shortcuts for Web Document Editors (Google Docs / Word Online),
and document design layout templates.
"""

import urllib.request
import re
from typing import Dict, Any, List, Optional

class GoogleDocsPayloadBuilder:
    """Helper to construct valid Google Docs API batchUpdate request payloads."""
    
    ALIGNMENT_MAP = {
        "center": "CENTER",
        "left": "START",
        "right": "END",
        "justify": "JUSTIFIED",
        "start": "START",
        "end": "END"
    }

    @staticmethod
    def update_paragraph_style(start_index: int, end_index: int, alignment: str = "CENTER", line_spacing: Optional[float] = None) -> Dict[str, Any]:
        align_value = GoogleDocsPayloadBuilder.ALIGNMENT_MAP.get(alignment.lower(), "CENTER")
        fields = ["alignment"]
        paragraph_style: Dict[str, Any] = {"alignment": align_value}
        
        if line_spacing is not None:
            paragraph_style["lineSpacing"] = int(line_spacing * 100)
            fields.append("lineSpacing")
            
        return {
            "updateParagraphStyle": {
                "paragraphStyle": paragraph_style,
                "fields": ",".join(fields),
                "range": {
                    "startIndex": start_index,
                    "endIndex": end_index
                }
            }
        }

    @staticmethod
    def update_text_style(start_index: int, end_index: int, font_family: Optional[str] = None, 
                          font_size_pt: Optional[int] = None, bold: Optional[bool] = None, 
                          italic: Optional[bool] = None, color_hex: Optional[str] = None) -> Dict[str, Any]:
        text_style: Dict[str, Any] = {}
        fields = []

        if font_family:
            text_style["weightedFontFamily"] = {"fontFamily": font_family}
            fields.append("weightedFontFamily")
        if font_size_pt:
            text_style["fontSize"] = {"magnitude": font_size_pt, "unit": "PT"}
            fields.append("fontSize")
        if bold is not None:
            text_style["bold"] = bold
            fields.append("bold")
        if italic is not None:
            text_style["italic"] = italic
            fields.append("italic")
        if color_hex:
            hex_clean = color_hex.lstrip("#")
            if len(hex_clean) == 6:
                r = int(hex_clean[0:2], 16) / 255.0
                g = int(hex_clean[2:4], 16) / 255.0
                b = int(hex_clean[4:6], 16) / 255.0
                text_style["foregroundColor"] = {"color": {"rgbColor": {"red": r, "green": g, "blue": b}}}
                fields.append("foregroundColor")

        return {
            "updateTextStyle": {
                "textStyle": text_style,
                "fields": ",".join(fields),
                "range": {
                    "startIndex": start_index,
                    "endIndex": end_index
                }
            }
        }

    @staticmethod
    def delete_content_range(start_index: int, end_index: int) -> Dict[str, Any]:
        return {
            "deleteContentRange": {
                "range": {
                    "startIndex": start_index,
                    "endIndex": end_index
                }
            }
        }

    @staticmethod
    def insert_table(index: int, rows: int, cols: int) -> Dict[str, Any]:
        return {
            "insertTable": {
                "rows": rows,
                "columns": cols,
                "location": {
                    "index": index
                }
            }
        }

    @staticmethod
    def replace_all_text(find_text: str, replace_text: str, match_case: bool = True) -> Dict[str, Any]:
        return {
            "replaceAllText": {
                "containsText": {
                    "text": find_text,
                    "matchCase": match_case
                },
                "replaceText": replace_text
            }
        }


class OnlineDocBrowserShortcuts:
    """Standard keyboard shortcuts & automation guides for Google Docs & Word Online."""

    @staticmethod
    def get_shortcuts_map() -> Dict[str, str]:
        return {
            "align_center": "Control+Shift+KeyE",
            "align_left": "Control+Shift+KeyL",
            "align_right": "Control+Shift+KeyR",
            "align_justify": "Control+Shift+KeyJ",
            "bold": "Control+KeyB",
            "italic": "Control+KeyI",
            "underline": "Control+KeyU",
            "heading_1": "Control+Alt+Digit1",
            "heading_2": "Control+Alt+Digit2",
            "normal_text": "Control+Alt+Digit0",
            "delete_selection": "Delete",
            "undo": "Control+KeyZ"
        }


class DocumentDesignTemplates:
    """Best practice design standards for Resumes, Cover Letters, and Technical Reports."""

    @staticmethod
    def get_resume_design_spec() -> Dict[str, Any]:
        return {
            "document_type": "Resume / Sơ Yếu Lý Lịch",
            "margins": {"top": "0.75 in", "bottom": "0.75 in", "left": "0.75 in", "right": "0.75 in"},
            "header": {
                "title_font": "Roboto",
                "title_size": 18,
                "title_bold": True,
                "alignment": "CENTER",
                "color": "#1A365D"
            },
            "section_heading": {
                "font": "Roboto",
                "size": 13,
                "bold": True,
                "alignment": "LEFT",
                "color": "#2B6CB0",
                "border_bottom": True
            },
            "body": {
                "font": "Arial",
                "size": 10.5,
                "line_spacing": 1.15,
                "alignment": "LEFT"
            }
        }


def extract_gdoc_id_from_url(url: str) -> Optional[str]:
    """Extract Google Doc ID from share URL."""
    match = re.search(r'/document/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else None


def fetch_gdoc_plain_text(doc_url_or_id: str) -> str:
    """Fetch plain text of a public Google Doc."""
    doc_id = extract_gdoc_id_from_url(doc_url_or_id) or doc_url_or_id
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    try:
        req = urllib.request.Request(export_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return f"Error fetching document text: {str(e)}"
