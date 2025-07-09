import re
from typing import List, Dict, Any
from dataclasses import dataclass
from .obsidian_loader import ObsidianDocument

@dataclass
class DocumentChunk:
    """Represents a chunk of text with metadata"""
    content: str
    source_file: str
    source_title: str
    chunk_index: int
    headers: List[str]  # Hierarchy of headers (h1, h2, h3, etc.)
    tags: List[str]
    links: List[str]
    metadata: Dict[str, Any]

class MarkdownTextSplitter:
    """Splits markdown documents into semantically meaningful chunks"""
    
    def __init__(self, 
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 respect_headers: bool = True):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.respect_headers = respect_headers
    
    def split_documents(self, documents: List[ObsidianDocument]) -> List[DocumentChunk]:
        """Split multiple documents into chunks"""
        all_chunks = []
        
        for doc in documents:
            chunks = self.split_document(doc)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def split_document(self, document: ObsidianDocument) -> List[DocumentChunk]:
        """Split a single document into chunks"""
        if self.respect_headers:
            return self._split_by_headers(document)
        else:
            return self._split_by_size(document)
    
    def _split_by_headers(self, document: ObsidianDocument) -> List[DocumentChunk]:
        """Split document by markdown headers while respecting size limits"""
        chunks = []
        sections = self._extract_sections(document.content)
        
        for i, section in enumerate(sections):
            # If section is too large, split it further
            if len(section['content']) > self.chunk_size:
                sub_chunks = self._split_large_section(section, document, i)
                chunks.extend(sub_chunks)
            else:
                chunk = DocumentChunk(
                    content=section['content'],
                    source_file=document.file_path,
                    source_title=document.title,
                    chunk_index=i,
                    headers=section['headers'],
                    tags=document.tags,
                    links=self._extract_links_from_text(section['content']),
                    metadata={
                        'frontmatter': document.frontmatter,
                        'created_date': document.created_date,
                        'modified_date': document.modified_date
                    }
                )
                chunks.append(chunk)
        
        return chunks
    
    def _extract_sections(self, content: str) -> List[Dict[str, Any]]:
        """Extract sections based on markdown headers"""
        sections = []
        current_section = {'content': '', 'headers': []}
        header_stack = []
        
        lines = content.split('\n')
        
        for line in lines:
            # Check if line is a header
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            
            if header_match:
                # Save previous section if it has content
                if current_section['content'].strip():
                    sections.append(current_section)
                
                # Start new section
                level = len(header_match.group(1))
                header_text = header_match.group(2)
                
                # Update header stack
                header_stack = header_stack[:level-1] + [header_text]
                
                current_section = {
                    'content': line + '\n',
                    'headers': header_stack.copy()
                }
            else:
                current_section['content'] += line + '\n'
        
        # Add final section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _split_large_section(self, section: Dict[str, Any], 
                           document: ObsidianDocument, 
                           base_index: int) -> List[DocumentChunk]:
        """Split a large section into smaller chunks"""
        chunks = []
        content = section['content']
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        current_chunk = ""
        chunk_index = base_index
        
        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                # Create chunk
                chunk = DocumentChunk(
                    content=current_chunk.strip(),
                    source_file=document.file_path,
                    source_title=document.title,
                    chunk_index=chunk_index,
                    headers=section['headers'],
                    tags=document.tags,
                    links=self._extract_links_from_text(current_chunk),
                    metadata={
                        'frontmatter': document.frontmatter,
                        'created_date': document.created_date,
                        'modified_date': document.modified_date
                    }
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                current_chunk = self._get_overlap_text(current_chunk) + paragraph
                chunk_index += 1
            else:
                current_chunk += paragraph + '\n\n'
        
        # Add final chunk
        if current_chunk.strip():
            chunk = DocumentChunk(
                content=current_chunk.strip(),
                source_file=document.file_path,
                source_title=document.title,
                chunk_index=chunk_index,
                headers=section['headers'],
                tags=document.tags,
                links=self._extract_links_from_text(current_chunk),
                metadata={
                    'frontmatter': document.frontmatter,
                    'created_date': document.created_date,
                    'modified_date': document.modified_date
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_by_size(self, document: ObsidianDocument) -> List[DocumentChunk]:
        """Simple size-based splitting"""
        chunks = []
        content = document.content
        
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            
            # Try to break at word boundary
            if end < len(content):
                last_space = content.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk_content = content[start:end]
            
            chunk = DocumentChunk(
                content=chunk_content,
                source_file=document.file_path,
                source_title=document.title,
                chunk_index=chunk_index,
                headers=[],
                tags=document.tags,
                links=self._extract_links_from_text(chunk_content),
                metadata={
                    'frontmatter': document.frontmatter,
                    'created_date': document.created_date,
                    'modified_date': document.modified_date
                }
            )
            chunks.append(chunk)
            
            start = end - self.chunk_overlap
            chunk_index += 1
        
        return chunks
    
    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of a chunk"""
        if len(text) <= self.chunk_overlap:
            return text
        
        # Try to break at sentence boundary
        sentences = text.split('. ')
        if len(sentences) > 1:
            overlap = '. '.join(sentences[-2:])
            if len(overlap) <= self.chunk_overlap:
                return overlap
        
        # Fallback to character-based overlap
        return text[-self.chunk_overlap:]
    
    def _extract_links_from_text(self, text: str) -> List[str]:
        """Extract internal links from text chunk"""
        return re.findall(r'\[\[([^\]]+)\]\]', text)

# Example usage
if __name__ == "__main__":
    from obsidian_loader import ObsidianLoader
    
    # Test the splitter
    loader = ObsidianLoader("./data/obsidian-notes")
    documents = loader.load_documents()
    
    splitter = MarkdownTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
    
    print(f"Split {len(documents)} documents into {len(chunks)} chunks")
    for chunk in chunks[:3]:  # Show first 3
        print(f"File: {chunk.source_file}")
        print(f"Headers: {' > '.join(chunk.headers)}")
        print(f"Content: {chunk.content[:200]}...")
        print("-" * 50)