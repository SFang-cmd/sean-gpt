import os
import re
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import yaml
import git

@dataclass
class ObsidianDocument:
    """Represents a single Obsidian note with metadata"""
    title: str
    content: str
    file_path: str
    tags: List[str]
    links: List[str]
    frontmatter: Dict[str, Any]
    created_date: str = None
    modified_date: str = None

class ObsidianLoader:
    """Loads and parses Obsidian notes from a repository"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        
    def load_documents(self) -> List[ObsidianDocument]:
        """Load all markdown documents from the Obsidian vault"""
        documents = []
        
        # Find all .md files
        for md_file in self.repo_path.rglob("*.md"):
            try:
                doc = self._parse_markdown_file(md_file)
                documents.append(doc)
            except Exception as e:
                print(f"Error parsing {md_file}: {e}")
                continue
                
        return documents
    
    def _parse_markdown_file(self, file_path: Path) -> ObsidianDocument:
        """Parse a single markdown file into an ObsidianDocument"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract frontmatter
        frontmatter = {}
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    content = parts[2].strip()
                except yaml.YAMLError:
                    pass
        
        # Extract title (from filename or frontmatter)
        title = frontmatter.get('title', file_path.stem)
        
        # Extract tags
        tags = self._extract_tags(content, frontmatter)
        
        # Extract internal links
        links = self._extract_links(content)
        
        # Get file timestamps
        stat = file_path.stat()
        
        return ObsidianDocument(
            title=title,
            content=content,
            file_path=str(file_path.relative_to(self.repo_path)),
            tags=tags,
            links=links,
            frontmatter=frontmatter,
            created_date=str(stat.st_ctime),
            modified_date=str(stat.st_mtime)
        )
    
    def _extract_tags(self, content: str, frontmatter: Dict) -> List[str]:
        """Extract tags from content and frontmatter"""
        tags = set()
        
        # Tags from frontmatter
        if 'tags' in frontmatter:
            if isinstance(frontmatter['tags'], list):
                tags.update(frontmatter['tags'])
            else:
                tags.add(str(frontmatter['tags']))
        
        # Inline tags (#tag)
        inline_tags = re.findall(r'#([a-zA-Z0-9_-]+)', content)
        tags.update(inline_tags)
        
        return list(tags)
    
    def _extract_links(self, content: str) -> List[str]:
        """Extract internal links [[Note Title]]"""
        links = re.findall(r'\[\[([^\]]+)\]\]', content)
        return links

# Hard-coded repository configuration
DEFAULT_REPO_URL = "https://github.com/SFang-cmd/obiKnowledge"
DEFAULT_REPO_NAME = "obiKnowledge"

def clone_or_update_repo(repo_url: str = None, local_path: str = None, repo_name: str = None) -> str:
    """Clone repository or update if it exists"""
    # Use defaults if not provided
    if repo_url is None:
        repo_url = DEFAULT_REPO_URL
    if repo_name is None:
        repo_name = DEFAULT_REPO_NAME
    if local_path is None:
        # Create default path relative to this file
        backend_path = Path(__file__).parent.parent.parent
        local_path = str(backend_path / "data" / repo_name)
    
    if os.path.exists(local_path):
        # Update existing repo
        try:
            repo = git.Repo(local_path)
            repo.remotes.origin.pull()
            print(f"✅ Updated repository at {local_path}")
        except Exception as e:
            print(f"❌ Failed to update repo: {e}")
            return None
    else:
        # Clone new repo
        try:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            git.Repo.clone_from(repo_url, local_path)
            print(f"✅ Cloned repository to {local_path}")
        except Exception as e:
            print(f"❌ Failed to clone repo: {e}")
            return None
    
    return local_path

def load_default_knowledge_base():
    """Load the default hard-coded knowledge base"""
    repo_path = clone_or_update_repo()
    if repo_path:
        loader = ObsidianLoader(repo_path)
        return loader.load_documents()
    return []

# Example usage
if __name__ == "__main__":
    # Test the loader
    loader = ObsidianLoader("./data/obsidian-notes")
    documents = loader.load_documents()
    
    print(f"Loaded {len(documents)} documents")
    for doc in documents[:3]:  # Show first 3
        print(f"Title: {doc.title}")
        print(f"Tags: {doc.tags}")
        print(f"Links: {doc.links}")
        print(f"Content preview: {doc.content[:200]}...")
        print("-" * 50)