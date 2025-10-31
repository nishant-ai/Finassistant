"""
Document Chunking Utilities

Provides intelligent chunking strategies for different document types.
SEC filings use hierarchical chunking, news articles use paragraph-based chunking.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup


@dataclass
class Chunk:
    """Represents a text chunk with metadata."""
    text: str
    chunk_id: str
    chunk_type: str  # "parent" or "child"
    metadata: Dict
    parent_id: Optional[str] = None


class DocumentChunker:
    """Base class for document chunking strategies."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """
        Initialize chunker.

        Args:
            chunk_size: Target size of each chunk in tokens (approximate)
            overlap: Number of tokens to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation: 1 token ≈ 4 characters).

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return len(text) // 4

    def split_by_tokens(self, text: str, size: int, overlap: int = 0) -> List[str]:
        """
        Split text into chunks of approximately equal token size.

        Args:
            text: Text to split
            size: Target token count per chunk
            overlap: Token overlap between chunks

        Returns:
            List of text chunks
        """
        # Convert token size to character count (rough estimate)
        char_size = size * 4
        char_overlap = overlap * 4

        chunks = []
        start = 0

        while start < len(text):
            end = start + char_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end within next 200 chars
                sentence_end = text.find('. ', end, end + 200)
                if sentence_end != -1:
                    end = sentence_end + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - char_overlap

        return chunks

    def chunk_document(self, text: str, metadata: Dict) -> List[Chunk]:
        """
        Chunk a document. Override in subclasses for specific strategies.

        Args:
            text: Document text
            metadata: Document metadata

        Returns:
            List of Chunk objects
        """
        raise NotImplementedError("Subclasses must implement chunk_document")


class SECFilingChunker(DocumentChunker):
    """
    Hierarchical chunker for SEC filings.
    Creates parent chunks (section summaries) and child chunks (detailed content).
    """

    # SEC filing section patterns
    SECTION_PATTERNS = [
        (r'ITEM\s+1[.\s]+BUSINESS', 'Item 1 - Business'),
        (r'ITEM\s+1A[.\s]+RISK\s+FACTORS', 'Item 1A - Risk Factors'),
        (r'ITEM\s+1B[.\s]+UNRESOLVED\s+STAFF\s+COMMENTS', 'Item 1B - Unresolved Staff Comments'),
        (r'ITEM\s+2[.\s]+PROPERTIES', 'Item 2 - Properties'),
        (r'ITEM\s+3[.\s]+LEGAL\s+PROCEEDINGS', 'Item 3 - Legal Proceedings'),
        (r'ITEM\s+4[.\s]+MINE\s+SAFETY', 'Item 4 - Mine Safety Disclosures'),
        (r'ITEM\s+5[.\s]+MARKET\s+FOR', 'Item 5 - Market for Registrant'),
        (r'ITEM\s+6[.\s]+SELECTED\s+FINANCIAL', 'Item 6 - Selected Financial Data'),
        (r'ITEM\s+7[.\s]+MANAGEMENT.?S\s+DISCUSSION', 'Item 7 - MD&A'),
        (r'ITEM\s+7A[.\s]+QUANTITATIVE\s+AND\s+QUALITATIVE', 'Item 7A - Market Risk'),
        (r'ITEM\s+8[.\s]+FINANCIAL\s+STATEMENTS', 'Item 8 - Financial Statements'),
        (r'ITEM\s+9[.\s]+CHANGES\s+IN\s+AND\s+DISAGREEMENTS', 'Item 9 - Disagreements'),
        (r'ITEM\s+9A[.\s]+CONTROLS\s+AND\s+PROCEDURES', 'Item 9A - Controls and Procedures'),
        (r'ITEM\s+9B[.\s]+OTHER\s+INFORMATION', 'Item 9B - Other Information'),
        (r'ITEM\s+10[.\s]+DIRECTORS', 'Item 10 - Directors and Officers'),
        (r'ITEM\s+11[.\s]+EXECUTIVE\s+COMPENSATION', 'Item 11 - Executive Compensation'),
        (r'ITEM\s+12[.\s]+SECURITY\s+OWNERSHIP', 'Item 12 - Security Ownership'),
        (r'ITEM\s+13[.\s]+CERTAIN\s+RELATIONSHIPS', 'Item 13 - Related Transactions'),
        (r'ITEM\s+14[.\s]+PRINCIPAL\s+ACCOUNTANT', 'Item 14 - Accountant Fees'),
        (r'ITEM\s+15[.\s]+EXHIBITS', 'Item 15 - Exhibits'),
    ]

    def __init__(self, parent_size: int = 800, child_size: int = 400, overlap: int = 50):
        """
        Initialize SEC filing chunker.

        Args:
            parent_size: Token size for parent (summary) chunks
            child_size: Token size for child (detail) chunks
            overlap: Token overlap between chunks
        """
        super().__init__(chunk_size=child_size, overlap=overlap)
        self.parent_size = parent_size
        self.child_size = child_size

    def extract_sections(self, text: str) -> List[Tuple[str, str, int]]:
        """
        Extract sections from SEC filing based on Item numbers.

        Args:
            text: Full filing text

        Returns:
            List of (section_name, section_text, start_position) tuples
        """
        sections = []

        # Find all section headers
        section_matches = []
        for pattern, name in self.SECTION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                section_matches.append((match.start(), name, pattern))

        # Sort by position
        section_matches.sort(key=lambda x: x[0])

        # Extract text between sections
        for i, (start, name, _) in enumerate(section_matches):
            # Determine end position (start of next section or end of document)
            if i + 1 < len(section_matches):
                end = section_matches[i + 1][0]
            else:
                end = len(text)

            section_text = text[start:end].strip()

            if section_text and len(section_text) > 100:  # Minimum section length
                sections.append((name, section_text, start))

        return sections

    def create_parent_chunk(self, section_name: str, section_text: str,
                           metadata: Dict, section_position: int) -> Chunk:
        """
        Create a parent (summary) chunk for a section.

        Args:
            section_name: Name of the section
            section_text: Full section text
            metadata: Base metadata
            section_position: Position in document

        Returns:
            Parent Chunk object
        """
        # Take first N tokens as summary
        summary_text = section_text[:self.parent_size * 4]  # Rough char estimate

        # Try to end at sentence boundary
        last_period = summary_text.rfind('. ')
        if last_period > self.parent_size * 2:  # At least half the target size
            summary_text = summary_text[:last_period + 1]

        chunk_id = f"{metadata.get('ticker', 'UNK')}_{metadata.get('filing_type', 'UNK')}_" \
                  f"{metadata.get('filing_year', 'UNK')}_{section_name.replace(' ', '_')}_PARENT"

        parent_metadata = {
            **metadata,
            'section': section_name,
            'chunk_type': 'parent',
            'section_position': section_position,
            'is_summary': True
        }

        return Chunk(
            text=f"[Section: {section_name}]\n\n{summary_text}",
            chunk_id=chunk_id,
            chunk_type='parent',
            metadata=parent_metadata,
            parent_id=None
        )

    def create_child_chunks(self, section_name: str, section_text: str,
                           parent_chunk_id: str, metadata: Dict) -> List[Chunk]:
        """
        Create child (detail) chunks for a section.

        Args:
            section_name: Name of the section
            section_text: Full section text
            parent_chunk_id: ID of parent chunk
            metadata: Base metadata

        Returns:
            List of child Chunk objects
        """
        # Split section into smaller chunks
        text_chunks = self.split_by_tokens(section_text, self.child_size, self.overlap)

        child_chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_id = f"{parent_chunk_id}_CHILD_{i:03d}"

            child_metadata = {
                **metadata,
                'section': section_name,
                'chunk_type': 'child',
                'chunk_index': i,
                'total_chunks': len(text_chunks),
                'is_summary': False
            }

            child_chunks.append(Chunk(
                text=chunk_text,
                chunk_id=chunk_id,
                chunk_type='child',
                metadata=child_metadata,
                parent_id=parent_chunk_id
            ))

        return child_chunks

    def chunk_document(self, text: str, metadata: Dict) -> List[Chunk]:
        """
        Chunk SEC filing into hierarchical parent and child chunks.

        Args:
            text: Full filing text
            metadata: Filing metadata (ticker, filing_type, year, etc.)

        Returns:
            List of Chunk objects (parents and children)
        """
        all_chunks = []

        # Extract sections
        sections = self.extract_sections(text)

        if not sections:
            # If no sections found, fall back to simple chunking
            print("Warning: No sections found in filing, using simple chunking")
            text_chunks = self.split_by_tokens(text, self.child_size, self.overlap)

            for i, chunk_text in enumerate(text_chunks):
                chunk_id = f"{metadata.get('ticker', 'UNK')}_CHUNK_{i:03d}"
                all_chunks.append(Chunk(
                    text=chunk_text,
                    chunk_id=chunk_id,
                    chunk_type='child',
                    metadata={**metadata, 'chunk_index': i},
                    parent_id=None
                ))

            return all_chunks

        # Process each section
        for section_name, section_text, section_position in sections:
            # Create parent chunk
            parent_chunk = self.create_parent_chunk(
                section_name, section_text, metadata, section_position
            )
            all_chunks.append(parent_chunk)

            # Create child chunks
            child_chunks = self.create_child_chunks(
                section_name, section_text, parent_chunk.chunk_id, metadata
            )
            all_chunks.extend(child_chunks)

        return all_chunks


class NewsArticleChunker(DocumentChunker):
    """
    Paragraph-based chunker for news articles.
    Simpler than SEC filing chunker - splits by paragraphs.
    """

    def __init__(self, chunk_size: int = 300, overlap: int = 20):
        """
        Initialize news article chunker.

        Args:
            chunk_size: Target token size per chunk
            overlap: Token overlap between chunks
        """
        super().__init__(chunk_size=chunk_size, overlap=overlap)

    def extract_paragraphs(self, text: str) -> List[str]:
        """
        Extract paragraphs from article text.

        Args:
            text: Article text

        Returns:
            List of paragraph strings
        """
        # Split by double newline or <p> tags
        if '<p>' in text:
            soup = BeautifulSoup(text, 'html.parser')
            paragraphs = [p.get_text().strip() for p in soup.find_all('p')]
        else:
            paragraphs = [p.strip() for p in text.split('\n\n')]

        # Filter out empty paragraphs
        return [p for p in paragraphs if p and len(p) > 50]

    def chunk_document(self, text: str, metadata: Dict) -> List[Chunk]:
        """
        Chunk news article by paragraphs.

        Args:
            text: Article text
            metadata: Article metadata (title, url, date, etc.)

        Returns:
            List of Chunk objects
        """
        paragraphs = self.extract_paragraphs(text)

        if not paragraphs:
            # Fallback to token-based splitting
            paragraphs = self.split_by_tokens(text, self.chunk_size, self.overlap)

        chunks = []
        current_chunk_text = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self.estimate_tokens(para)

            # If single paragraph is too large, split it
            if para_tokens > self.chunk_size * 1.5:
                # Save current chunk if it exists
                if current_chunk_text:
                    chunk_id = f"{metadata.get('source', 'news')}_{len(chunks):03d}"
                    chunks.append(Chunk(
                        text='\n\n'.join(current_chunk_text),
                        chunk_id=chunk_id,
                        chunk_type='child',
                        metadata={**metadata, 'chunk_index': len(chunks)},
                        parent_id=None
                    ))
                    current_chunk_text = []
                    current_tokens = 0

                # Split large paragraph
                para_chunks = self.split_by_tokens(para, self.chunk_size, self.overlap)
                for pc in para_chunks:
                    chunk_id = f"{metadata.get('source', 'news')}_{len(chunks):03d}"
                    chunks.append(Chunk(
                        text=pc,
                        chunk_id=chunk_id,
                        chunk_type='child',
                        metadata={**metadata, 'chunk_index': len(chunks)},
                        parent_id=None
                    ))

            elif current_tokens + para_tokens > self.chunk_size:
                # Current chunk is full, save it and start new one
                chunk_id = f"{metadata.get('source', 'news')}_{len(chunks):03d}"
                chunks.append(Chunk(
                    text='\n\n'.join(current_chunk_text),
                    chunk_id=chunk_id,
                    chunk_type='child',
                    metadata={**metadata, 'chunk_index': len(chunks)},
                    parent_id=None
                ))
                current_chunk_text = [para]
                current_tokens = para_tokens

            else:
                # Add to current chunk
                current_chunk_text.append(para)
                current_tokens += para_tokens

        # Save final chunk
        if current_chunk_text:
            chunk_id = f"{metadata.get('source', 'news')}_{len(chunks):03d}"
            chunks.append(Chunk(
                text='\n\n'.join(current_chunk_text),
                chunk_id=chunk_id,
                chunk_type='child',
                metadata={**metadata, 'chunk_index': len(chunks)},
                parent_id=None
            ))

        return chunks


if __name__ == "__main__":
    # Test chunking
    sample_sec_text = """
    ITEM 1. BUSINESS

    Our company operates in the technology sector...

    ITEM 1A. RISK FACTORS

    Market Competition: We face intense competition from major players...
    Regulatory Risks: Changes in data privacy regulations could impact...

    ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS

    Revenue for the year increased by 15%...
    """

    chunker = SECFilingChunker()
    metadata = {'ticker': 'TEST', 'filing_type': '10-K', 'filing_year': 2024}
    chunks = chunker.chunk_document(sample_sec_text, metadata)

    print(f"Created {len(chunks)} chunks")
    for chunk in chunks[:3]:
        print(f"\n{chunk.chunk_type.upper()} - {chunk.chunk_id}")
        print(f"Text preview: {chunk.text[:100]}...")
