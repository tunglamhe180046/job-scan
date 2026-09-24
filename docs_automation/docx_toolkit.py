"""
DocxToolkit - Bộ công cụ đa năng tự động hóa & chỉnh sửa tài liệu Word (.docx / .doc)
Tích hợp toàn bộ thao tác: điền form mẫu, tô viền ô, căn giữa header, tạo ô ký tay, đánh lại số thứ tự, và tối ưu trang.
"""

import os
import sys
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


class DocxToolkit:
    """Multi-functional toolkit for Word Document (.docx) creation, editing & layout optimization."""

    def __init__(self, doc_path: str):
        self.doc_path = os.path.abspath(doc_path)
        self.doc = Document(self.doc_path) if os.path.exists(self.doc_path) else Document()

    def save(self, output_path: str = None) -> str:
        target = os.path.abspath(output_path) if output_path else self.doc_path
        
        # Auto-close open Word instances locking the file if on Windows
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            for d in word.Documents:
                if os.path.basename(target).lower() in d.Name.lower():
                    d.Close()
            word.Quit()
        except Exception:
            pass

        self.doc.save(target)
        print(f"[DocxToolkit] Saved document to: {target}")
        return target

    # --- 1. TÔ VIỀN ĐEN BẢNG (BLACK CELL BORDERS) ---
    def set_table_borders(self, table_index: int = None, color: str = "000000", sz: str = "4"):
        """Add sharp borders to specified table or data tables (skipping header table 0)."""
        if table_index is not None:
            tables = [self.doc.tables[table_index]]
        else:
            # Skip table 0 (Header/Photo table) and format data tables
            tables = self.doc.tables[1:] if len(self.doc.tables) > 1 else self.doc.tables

        for t in tables:
            tblPr = t._tbl.tblPr
            for child in list(tblPr):
                if child.tag.endswith('tblBorders'):
                    tblPr.remove(child)
            tblBorders = OxmlElement('w:tblBorders')
            for b in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                node = OxmlElement(f'w:{b}')
                node.set(qn('w:val'), 'single')
                node.set(qn('w:sz'), sz)
                node.set(qn('w:space'), '0')
                node.set(qn('w:color'), color)
                tblBorders.append(node)
            tblPr.append(tblBorders)
        print(f"[DocxToolkit] Applied black borders to {len(tables)} table(s).")
        return self

    # --- 2. THAY THẾ CHUỖI TỰ ĐỘNG (TEXT REPLACEMENT) ---
    def replace_text(self, replacements: dict):
        """Replace dictionary of {old_text: new_text} across all paragraphs and tables."""
        for old, new in replacements.items():
            # Paragraphs
            for p in self.doc.paragraphs:
                if old in p.text:
                    p.text = p.text.replace(old, new)
            # Tables
            for t in self.doc.tables:
                for r in t.rows:
                    for c in r.cells:
                        for p in c.paragraphs:
                            if old in p.text:
                                p.text = p.text.replace(old, new)
        print(f"[DocxToolkit] Replaced {len(replacements)} text patterns.")
        return self

    # --- 3. XÓA MỤC & ĐÁNH LẠI SỐ THỨ TỰ (REMOVE & RENUMBER) ---
    def remove_and_renumber(self, remove_prefixes: list, renumber_map: dict):
        """Remove paragraphs starting with prefixes and renumber remaining items."""
        to_remove = []
        for p in self.doc.paragraphs:
            p_text = p.text.strip()
            # Check removal
            for rem in remove_prefixes:
                if p_text.startswith(rem):
                    to_remove.append(p)
                    break
            # Check renumbering
            for old_prefix, new_val in renumber_map.items():
                if p_text.startswith(old_prefix):
                    p.text = new_val
                    for run in p.runs:
                        run.font.name = "Times New Roman"
                        run.font.size = Pt(11)
                    break

        for p in to_remove:
            p._element.getparent().remove(p._element)
        print(f"[DocxToolkit] Removed {len(to_remove)} paragraph(s) and renumbered remaining items.")
        return self

    # --- 4. Ô KÝ TAY TRỐNG (BLANK HANDWRITTEN SIGNATURE) ---
    def setup_handwritten_signature(self, table_index: int = -1, blank_lines: int = 5):
        """Configure signature box with spacious blank lines for physical handwriting."""
        if self.doc.tables:
            t = self.doc.tables[table_index]
            cell_sig = t.cell(0, 1) if len(t.columns) > 1 else t.cell(0, 0)
            blank_spaces = "\n" * blank_lines
            cell_sig.text = f"Người khai\n(ký và ghi rõ họ tên){blank_spaces}"
            for p in cell_sig.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(10.5)
            print("[DocxToolkit] Configured signature box for physical handwriting.")
        return self

    # --- 5. TỐI ƯU TRANG & LỀ VĂN BẢN (OPTIMIZE MARGINS & SPACING) ---
    def optimize_page_fit(self, top_bottom_inch: float = 0.5, left_right_inch: float = 0.65, line_spacing: float = 1.05):
        """Tighten margins and paragraph spacing to prevent page overflow."""
        for s in self.doc.sections:
            s.top_margin = Inches(top_bottom_inch)
            s.bottom_margin = Inches(top_bottom_inch)
            s.left_margin = Inches(left_right_inch)
            s.right_margin = Inches(left_right_inch)

        for p in self.doc.paragraphs:
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = line_spacing
            
        print("[DocxToolkit] Optimized page margins and paragraph spacing.")
        return self


class LiveWordController:
    """Controls a live, visible MS Word Application instance on the user's desktop."""

    def __init__(self, doc_path: str):
        import win32com.client
        self.doc_path = os.path.abspath(doc_path)
        try:
            self.word = win32com.client.GetActiveObject("Word.Application")
        except Exception:
            self.word = win32com.client.Dispatch("Word.Application")
        
        self.word.Visible = True
        
        # Find active document or open it
        self.doc = None
        for d in self.word.Documents:
            if os.path.basename(self.doc_path).lower() in d.Name.lower():
                self.doc = d
                break
                
        if not self.doc:
            self.doc = self.word.Documents.Open(self.doc_path)
            
        self.doc.Activate()
        print(f"[LiveWordController] Connected to live MS Word window: {self.doc.Name}")

    def live_replace_text(self, find_text: str, replace_text: str):
        """Find and replace text live on screen in MS Word."""
        sel = self.word.Selection
        sel.HomeKey(Unit=6) # wdStory
        find = sel.Find
        find.ClearFormatting()
        find.Replacement.ClearFormatting()
        find.Text = find_text
        find.Replacement.Text = replace_text
        find.Execute(Replace=2) # 2 = wdReplaceAll
        print(f"[LiveWordController] Replaced '{find_text}' -> '{replace_text}' live on screen.")
        return self

    def live_save(self):
        """Save active document without closing Word."""
        if self.doc:
            self.doc.Save()
            print("[LiveWordController] Document saved live.")
        return self


# --- CONVERT DOC TO DOCX HELPER ---
def convert_doc_to_docx(doc_path: str, output_docx_path: str = None) -> str:
    """Convert legacy Word .doc to modern .docx format via Word COM."""
    import win32com.client
    doc_path = os.path.abspath(doc_path)
    output_docx_path = os.path.abspath(output_docx_path) if output_docx_path else doc_path + "x"
    
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    try:
        doc = word.Documents.Open(doc_path)
        doc.SaveAs2(output_docx_path, FileFormat=16) # 16 = wdFormatXMLDocument
        doc.Close()
        print(f"[DocxToolkit] Converted {doc_path} -> {output_docx_path}")
        return output_docx_path
    finally:
        word.Quit()


def main():
    print("=== DocxToolkit Multi-functional Word Automation Suite ===")
    sample_file = r"E:\job-scan\Ly_Lich_Trich_Ngang_Nguyen_Tung_Lam.docx"
    if os.path.exists(sample_file):
        toolkit = DocxToolkit(sample_file)
        toolkit.set_table_borders() \
               .optimize_page_fit() \
               .save()
        print("DocxToolkit executed successfully on sample document.")

if __name__ == "__main__":
    main()
