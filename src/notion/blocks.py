"""
Notion block builders for creating formatted Notion content.
Provides functions to create various Notion block types.
"""
from typing import List, Dict, Any
from loguru import logger


def create_rich_text(content: str, bold: bool = False, link: str | None = None) -> List[Dict[str, Any]]:
    """
    Create a rich text object for Notion.
    Automatically splits content if it exceeds 2000 characters (Notion API limit).

    Args:
        content: Text content
        bold: Whether to bold the text
        link: Optional URL to link to

    Returns:
        List of rich text objects
    """
    NOTION_TEXT_LIMIT = 2000

    # If content is within limit, return single rich text object
    if len(content) <= NOTION_TEXT_LIMIT:
        rich_text = {
            "type": "text",
            "text": {
                "content": content
            }
        }

        if link:
            rich_text["text"]["link"] = {"url": link}

        if bold:
            rich_text["annotations"] = {"bold": True}

        return [rich_text]

    # Split content into chunks that respect the limit
    # Try to split at sentence boundaries to maintain readability
    chunks = []
    current_chunk = ""

    # Split by sentences (looking for periods, question marks, exclamation marks)
    import re
    sentences = re.split(r'([。！？.!?])', content)

    # Re-join with punctuation
    i = 0
    while i < len(sentences):
        if i + 1 < len(sentences) and sentences[i + 1] in '。！？.!?':
            sentence = sentences[i] + sentences[i + 1]
            i += 2
        else:
            sentence = sentences[i]
            i += 1

        # If adding this sentence would exceed limit, save current chunk
        if current_chunk and len(current_chunk) + len(sentence) > NOTION_TEXT_LIMIT:
            chunks.append(current_chunk)
            current_chunk = sentence
        else:
            current_chunk += sentence

    # Add remaining content
    if current_chunk:
        chunks.append(current_chunk)

    # Create rich text objects for each chunk
    rich_texts = []
    for i, chunk in enumerate(chunks):
        rich_text = {
            "type": "text",
            "text": {
                "content": chunk
            }
        }

        # Only add link to the first chunk if link is provided
        if link and i == 0:
            rich_text["text"]["link"] = {"url": link}

        if bold:
            rich_text["annotations"] = {"bold": True}

        rich_texts.append(rich_text)

    return rich_texts


def create_heading_block(text: str, level: int = 1) -> Dict[str, Any]:
    """
    Create a heading block.

    Args:
        text: Heading text
        level: Heading level (1-3)

    Returns:
        Notion heading block
    """
    if level not in [1, 2, 3]:
        raise ValueError("Heading level must be 1, 2, or 3")

    return {
        "object": "block",
        "type": f"heading_{level}",
        f"heading_{level}": {
            "rich_text": create_rich_text(text)
        }
    }


def create_paragraph_block(text: str) -> Dict[str, Any]:
    """
    Create a paragraph block.

    Args:
        text: Paragraph text

    Returns:
        Notion paragraph block
    """
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": create_rich_text(text)
        }
    }


def create_numbered_list_item_block(text: str, bold: bool = False, link: str | None = None) -> Dict[str, Any]:
    """
    Create a numbered list item block.

    Args:
        text: Item text
        bold: Whether to bold the text
        link: Optional URL to link to

    Returns:
        Notion numbered list item block
    """
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {
            "rich_text": create_rich_text(text, bold=bold, link=link)
        }
    }


def create_toggle_block(title: str, children: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """
    Create a toggle (collapsible) block.

    Args:
        title: Toggle title
        children: Optional child blocks

    Returns:
        Notion toggle block
    """
    toggle_block = {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": create_rich_text(title)
        }
    }

    if children:
        toggle_block["toggle"]["children"] = children

    return toggle_block


def create_divider_block() -> Dict[str, Any]:
    """
    Create a divider block.

    Returns:
        Notion divider block
    """
    return {
        "object": "block",
        "type": "divider",
        "divider": {}
    }


def create_report_sections(report: 'DetailedReport') -> List[Dict[str, Any]]:
    """
    Create nested blocks for a detailed paper report.

    Args:
        report: DetailedReport object with 6 sections

    Returns:
        List of Notion blocks
    """
    from src.llm.openai_client import DetailedReport

    sections = [
        ("研究背景", report.background),
        ("核心方法", report.methods),
        ("主要创新", report.innovations),
        ("实验结果", report.results),
        ("局限性", report.limitations),
        ("应用价值", report.applications)
    ]

    blocks = []
    for section_title, content in sections:
        # Section heading
        blocks.append(create_heading_block(section_title, level=3))

        # Section content (paragraph)
        if content:
            blocks.append(create_paragraph_block(content))

    return blocks


def create_paper_blocks(
    index: int,
    title: str,
    authors: List[str],
    chinese_abstract: str,
    pdf_url: str,
    detailed_report: 'DetailedReport | None' = None
) -> List[Dict[str, Any]]:
    """
    Create Notion blocks for a paper entry.

    Args:
        index: Paper index (for numbering)
        title: Paper title
        authors: List of author names
        chinese_abstract: Chinese translated abstract
        pdf_url: URL to PDF
        detailed_report: Optional detailed report

    Returns:
        List of Notion blocks
    """
    blocks = []

    # Numbered heading with title and PDF link
    blocks.append(create_numbered_list_item_block(
        title,
        bold=True,
        link=pdf_url
    ))

    # Authors
    authors_text = f"Authors: {', '.join(authors)}"
    blocks.append(create_paragraph_block(authors_text))

    # Chinese abstract
    blocks.append(create_paragraph_block(chinese_abstract))

    # Optional: Detailed report in toggle
    if detailed_report:
        toggle_title = "📊 详细分析"
        report_blocks = create_report_sections(detailed_report)
        blocks.append(create_toggle_block(toggle_title, children=report_blocks))

    # Divider between papers (optional)
    # blocks.append(create_divider_block())

    return blocks
