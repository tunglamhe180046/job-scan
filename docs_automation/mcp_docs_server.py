"""
Online Docs Automation MCP Server (mcp_docs_server.py)
Implements Model Context Protocol (MCP) Tools for Online Document Editors (Google Docs & Word Online).
Compatible with mcp 2.0.0 (MCPServer) and FastMCP.
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import helper module from current directory
sys.path.append(os.path.dirname(__file__))

from docs_automation_helper import (
    GoogleDocsPayloadBuilder,
    OnlineDocBrowserShortcuts,
    DocumentDesignTemplates,
    fetch_gdoc_plain_text,
    extract_gdoc_id_from_url
)

HAS_MCP = False
mcp = None

try:
    from mcp.server.mcpserver import MCPServer
    mcp = MCPServer("Online Docs Automation MCP Server")
    HAS_MCP = True
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP
        mcp = FastMCP("Online Docs Automation MCP Server")
        HAS_MCP = True
    except ImportError:
        HAS_MCP = False


def read_online_document(doc_url_or_id: str) -> str:
    """Fetch content and text from a Google Doc URL or Document ID."""
    return fetch_gdoc_plain_text(doc_url_or_id)

def generate_alignment_payload(start_index: int, end_index: int, alignment: str = "CENTER") -> str:
    """Generate Google Docs API payload to format text alignment (CENTER, LEFT, RIGHT, JUSTIFIED)."""
    payload = GoogleDocsPayloadBuilder.update_paragraph_style(start_index, end_index, alignment)
    return json.dumps(payload, indent=2, ensure_ascii=False)

def generate_text_style_payload(start_index: int, end_index: int, font_family: str = "Roboto",
                                font_size: int = 12, bold: bool = False, color_hex: str = "#000000") -> str:
    """Generate Google Docs API payload for text styling (Font, size, bold, color)."""
    payload = GoogleDocsPayloadBuilder.update_text_style(
        start_index, end_index, font_family=font_family, font_size_pt=font_size, bold=bold, color_hex=color_hex
    )
    return json.dumps(payload, indent=2, ensure_ascii=False)

def generate_delete_element_payload(start_index: int, end_index: int) -> str:
    """Generate Google Docs API payload to delete an element (image, table, or text range)."""
    payload = GoogleDocsPayloadBuilder.delete_content_range(start_index, end_index)
    return json.dumps(payload, indent=2, ensure_ascii=False)

def generate_full_batch_update(doc_id: str, requests_json: str) -> str:
    """Construct full batchUpdate JSON request body for Google Docs API."""
    try:
        req_list = json.loads(requests_json)
        body = {"requests": req_list}
        return json.dumps({"documentId": doc_id, "body": body}, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Invalid JSON input: {str(e)}"})

def get_browser_automation_shortcuts() -> str:
    """Get keyboard shortcuts and commands for Playwright browser automation on Web Editors."""
    shortcuts = OnlineDocBrowserShortcuts.get_shortcuts_map()
    return json.dumps(shortcuts, indent=2, ensure_ascii=False)

def get_resume_design_spec() -> str:
    """Get best practice design specs (margins, font hierarchy, colors) for Resumes/CVs on Docs."""
    spec = DocumentDesignTemplates.get_resume_design_spec()
    return json.dumps(spec, indent=2, ensure_ascii=False)


# Register tools if MCP SDK is available
if HAS_MCP and mcp is not None:
    mcp.tool()(read_online_document)
    mcp.tool()(generate_alignment_payload)
    mcp.tool()(generate_text_style_payload)
    mcp.tool()(generate_delete_element_payload)
    mcp.tool()(generate_full_batch_update)
    mcp.tool()(get_browser_automation_shortcuts)
    mcp.tool()(get_resume_design_spec)


def run_cli_demo():
    print("=== Online Docs Automation MCP Server ===")
    print("MCP SDK Status: Loaded Successfully" if HAS_MCP else "MCP SDK Status: Fallback CLI Mode")
    print("\n--- Available Tools & Samples ---")
    print("1. get_resume_design_spec():")
    print(get_resume_design_spec())
    print("\n2. get_browser_automation_shortcuts():")
    print(get_browser_automation_shortcuts())
    print("\n3. generate_alignment_payload(1, 20, 'center'):")
    print(generate_alignment_payload(1, 20, "center"))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        run_cli_demo()
    elif HAS_MCP and mcp is not None:
        mcp.run()
    else:
        run_cli_demo()
