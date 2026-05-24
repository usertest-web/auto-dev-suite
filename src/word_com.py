import win32com.client as client


class WordApp:
    """Wrapper around Word COM application. Mimics professional Word user operations."""

    def __init__(self, visible: bool = False):
        self.visible = visible
        self.app = None

    def __enter__(self):
        self.app = client.Dispatch("Word.Application")
        self.app.Visible = self.visible
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.app:
            try:
                self.app.Quit()
            except Exception:
                pass
        return False

    def open_document(self, path: str):
        self.app.Documents.Open(path)
        return self.app.ActiveDocument

    def save_as(self, path: str):
        self.app.ActiveDocument.SaveAs(path)

    def close_document(self):
        self.app.ActiveDocument.Close()

    @property
    def selection(self):
        return self.app.Selection

    @property
    def active_document(self):
        return self.app.ActiveDocument

    def apply_style(self, style_name: str):
        doc = self.active_document
        self.selection.Style = doc.Styles(style_name)

    def type_text(self, text: str):
        self.selection.TypeText(text)

    def type_paragraph(self):
        self.selection.TypeParagraph()

    def insert_page_break(self):
        self.selection.InsertBreak(Type=7)  # wdPageBreak

    def insert_section_break_next_page(self):
        self.selection.InsertBreak(Type=2)  # wdSectionBreakNextPage

    def make_superscript(self, start: int, end: int):
        rng = self.active_document.Range(start, end)
        rng.Font.Superscript = True

    def insert_toc(self):
        doc = self.active_document
        rng = self.selection.Range
        doc.TablesOfContents.Add(Range=rng, UseHeadingStyles=True,
                                  LowerHeadingLevel=3, UpperHeadingLevel=1)

    def update_all_fields(self):
        self.active_document.Fields.Update()

    def set_page_header(self, text: str, section_index: int = 1):
        doc = self.active_document
        section = doc.Sections(section_index)
        header = section.Headers(1)  # wdHeaderFooterPrimary
        header.Range.Text = text

    def set_page_footer_page_numbers(self, section_index: int = 1, start_at: int = 1):
        doc = self.active_document
        section = doc.Sections(section_index)
        footer = section.Footers(1)
        footer.PageNumbers.Add()
        footer.PageNumbers.StartingNumber = start_at
