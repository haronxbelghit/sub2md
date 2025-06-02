import json
from typing import List, Optional
from pathlib import Path
from dataclasses import dataclass

from sub2md.utils.Exceptions import ValidationError

@dataclass
class Post:
    """Data class representing a blog post."""
    title: str
    date: str
    like_count: str
    subtitle: str = ""
    is_paid: bool = False
    file_link: Optional[str] = None
    html_link: Optional[str] = None

    @property
    def is_paid_post(self) -> bool:
        """Check if the post is paid based on title, subtitle, and is_paid flag."""
        # First check the is_paid flag from the scraper
        if self.is_paid:
            return True
            
        return False

    @property
    def paid_indicator_html(self) -> str:
        """Get HTML for paid post indicator with emoji."""
        if self.is_paid_post:
            return '<span class="paid-indicator">🔒 Premium</span>'
        return ''

    @property
    def paid_indicator_md(self) -> str:
        """Get Markdown for paid post indicator with emoji."""
        if self.is_paid_post:
            return "🔒 Premium Article"
        return ""

class ThemeManager:
    """Manages theme-related functionality for the HTML generator."""
    
    @staticmethod
    def get_theme_css() -> str:
        """Get the CSS for both light and dark themes with premium styling."""
        return """
            :root {
                --bg-primary: #ffffff;
                --bg-secondary: #f8f8f8;
                --text-primary: #000000;
                --text-secondary: #555555;
                --border-color: #eeeeee;
                --accent-color: #007aff;
                --card-bg: #ffffff;
                --card-border: #e0e0e0;
                --card-hover-border: #d0d0d0;
                --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06);
                --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
                --radius-sm: 6px;
                --radius-md: 10px;
                --transition: all 0.2s ease-in-out;
                --spacing-unit: 1rem;
            }

            [data-theme="dark"] {
                --bg-primary: #000000;
                --bg-secondary: #111111;
                --text-primary: #ffffff;
                --text-secondary: #888888;
                --border-color: #333333;
                --accent-color: #0a84ff;
                --card-bg: #111111;
                --card-border: #333333;
                --card-hover-border: #444444;
                --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
                --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
            }

            body {
                font-family: 'Inter', sans-serif;
                line-height: 1.6;
                max-width: 900px;
                margin: 0 auto;
                padding: calc(var(--spacing-unit) * 4) var(--spacing-unit);
                color: var(--text-primary);
                background-color: var(--bg-primary);
                transition: var(--transition);
                font-size: 1rem;
                min-height: 100vh;
            }

            .header {
                text-align: center;
                margin-bottom: calc(var(--spacing-unit) * 4);
            }

            .header h1 {
                font-size: 2rem;
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: var(--spacing-unit);
                letter-spacing: -0.02em;
            }

            .header p {
                color: var(--text-secondary);
                font-size: 0.875rem;
            }

            .controls {
                display: flex;
                flex-direction: column;
                gap: var(--spacing-unit);
                margin-bottom: calc(var(--spacing-unit) * 3);
            }

            @media (min-width: 640px) {
                .controls {
                    flex-direction: row;
                    justify-content: center;
                }
            }

            .tabs {
                display: flex;
                background: var(--bg-secondary);
                border-radius: var(--radius-md);
                padding: 0.25rem;
                width: 100%;
                max-width: 20rem;
            }

            .tab {
                flex: 1;
                padding: 0.5rem 1rem;
                text-align: center;
                border-radius: var(--radius-sm);
                cursor: pointer;
                transition: var(--transition);
                color: var(--text-secondary);
                font-size: 0.875rem;
                font-weight: 500;
            }

            .tab.active {
                background: var(--bg-primary);
                color: var(--text-primary);
                box-shadow: var(--shadow-sm);
            }

            .select {
                position: relative;
                width: 100%;
                max-width: 20rem;
            }

            .select-trigger {
                width: 100%;
                padding: 0.5rem 1rem;
                background: var(--bg-secondary);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                color: var(--text-primary);
                font-size: 0.875rem;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .select-content {
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: var(--bg-primary);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-md);
                margin-top: 0.25rem;
                box-shadow: var(--shadow-md);
                z-index: 10;
            }

            .select-item {
                padding: 0.5rem 1rem;
                cursor: pointer;
                color: var(--text-primary);
                font-size: 0.875rem;
                transition: var(--transition);
            }

            .select-item:hover {
                background: var(--bg-secondary);
            }

            .post-list {
                display: flex;
                flex-direction: column;
                gap: calc(var(--spacing-unit) * 2);
            }

            .post {
                border-bottom: 1px solid var(--border-color);
                padding-bottom: calc(var(--spacing-unit) * 2);
            }

            .post:last-child {
                border-bottom: none;
            }

            .post-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: var(--spacing-unit);
            }

            .post-title {
                font-size: 1.25rem;
                font-weight: 500;
                color: var(--text-primary);
                margin: 0;
                flex: 1;
                margin-right: var(--spacing-unit);
            }

            .post-title a {
                color: inherit;
                text-decoration: none;
                transition: var(--transition);
            }

            .post-title a:hover {
                color: var(--accent-color);
            }

            .premium-badge {
                background: #ffdb58;
                color: #4a3300;
                padding: 0.25rem 0.5rem;
                border-radius: var(--radius-sm);
                font-size: 0.75rem;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                gap: 0.25rem;
            }

            .post-excerpt {
                color: var(--text-secondary);
                margin-bottom: var(--spacing-unit);
                font-size: 0.875rem;
                line-height: 1.5;
            }

            .post-meta {
                display: flex;
                justify-content: space-between;
                align-items: center;
                color: var(--text-secondary);
                font-size: 0.875rem;
            }

            .post-meta-item {
                display: flex;
                align-items: center;
                gap: 0.25rem;
            }

            .post-meta-item svg {
                width: 1rem;
                height: 1rem;
            }

            .read-more {
                margin-top: var(--spacing-unit);
                color: var(--text-primary);
                text-decoration: none;
                font-size: 0.875rem;
                display: inline-flex;
                align-items: center;
                gap: 0.25rem;
                transition: var(--transition);
            }

            .read-more:hover {
                color: var(--accent-color);
            }

            .theme-toggle {
                position: fixed;
                top: var(--spacing-unit);
                right: var(--spacing-unit);
                background: var(--bg-secondary);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                cursor: pointer;
                padding: 0.5rem;
                border-radius: 50%;
                transition: var(--transition);
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: var(--shadow-sm);
                z-index: 1000;
            }

            .theme-toggle:hover {
                transform: rotate(90deg);
                box-shadow: var(--shadow-md);
            }

            .theme-toggle svg {
                width: 1.25rem;
                height: 1.25rem;
            }

            .empty-state {
                text-align: center;
                padding: calc(var(--spacing-unit) * 3) 0;
                color: var(--text-secondary);
            }

            @media (max-width: 640px) {
                body {
                    padding: calc(var(--spacing-unit) * 2) var(--spacing-unit);
                }

                .header h1 {
                    font-size: 1.75rem;
                }

                .post-title {
                    font-size: 1.125rem;
                }

                .theme-toggle {
                    top: calc(var(--spacing-unit) * 0.75);
                    right: calc(var(--spacing-unit) * 0.75);
                }
            }
        """

    @staticmethod
    def get_theme_js() -> str:
        """Get the JavaScript for theme handling."""
        return """
            // Theme handling
            const themeToggle = document.querySelector('.theme-toggle');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');

            function setTheme(theme) {
                document.documentElement.setAttribute('data-theme', theme);
                localStorage.setItem('theme', theme);
            }

            function toggleTheme() {
                const currentTheme = document.documentElement.getAttribute('data-theme');
                setTheme(currentTheme === 'dark' ? 'light' : 'dark');
            }

            // Initialize theme
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {
                setTheme(savedTheme);
            } else {
                setTheme(prefersDark.matches ? 'dark' : 'light');
            }

            // Tab handling
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    const sortBy = tab.dataset.sort;
                    sortPosts(sortBy);
                });
            });

            // Select handling
            const selectTrigger = document.querySelector('.select-trigger');
            const selectContent = document.querySelector('.select-content');
            const selectItems = document.querySelectorAll('.select-item');

            selectTrigger.addEventListener('click', () => {
                selectContent.style.display = selectContent.style.display === 'block' ? 'none' : 'block';
            });

            selectItems.forEach(item => {
                item.addEventListener('click', () => {
                    const filter = item.dataset.filter;
                    filterPosts(filter);
                    selectTrigger.textContent = item.textContent;
                    selectContent.style.display = 'none';
                });
            });

            // Close select when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.select')) {
                    selectContent.style.display = 'none';
                }
            });

            // Sort and filter functions
            function sortPosts(sortBy) {
                const container = document.querySelector('.post-list');
                const posts = Array.from(container.children);
                
                posts.sort((a, b) => {
                    if (sortBy === 'likes') {
                        const likesA = parseInt(a.querySelector('.likes').textContent) || 0;
                        const likesB = parseInt(b.querySelector('.likes').textContent) || 0;
                        return likesB - likesA;
                    } else {
                        const dateA = new Date(a.querySelector('.date').textContent);
                        const dateB = new Date(b.querySelector('.date').textContent);
                        return dateB - dateA;
                    }
                });

                container.innerHTML = '';
                posts.forEach(post => container.appendChild(post));
            }

            function filterPosts(filter) {
                const posts = document.querySelectorAll('.post');
                posts.forEach(post => {
                    const isPremium = post.querySelector('.premium-badge') !== null;
                    if (filter === 'all' || 
                        (filter === 'premium' && isPremium) || 
                        (filter === 'free' && !isPremium)) {
                        post.style.display = '';
                    } else {
                        post.style.display = 'none';
                    }
                });

                // Show empty state if no posts are visible
                const visiblePosts = document.querySelectorAll('.post:not([style*="display: none"])');
                const emptyState = document.querySelector('.empty-state');
                if (emptyState) {
                    emptyState.style.display = visiblePosts.length === 0 ? 'block' : 'none';
                }
            }

            // Initial sort by date
            document.addEventListener('DOMContentLoaded', () => {
                sortPosts('date');
            });
        """

class PostSorter:
    """Handles post sorting functionality."""
    
    @staticmethod
    def get_sort_js() -> str:
        """Get the JavaScript for sorting functionality."""
        return """
            function sortByDate() {
                const container = document.getElementById('essays');
                const essays = Array.from(container.children);
                essays.sort((a, b) => {
                    const dateA = new Date(a.querySelector('.date').textContent);
                    const dateB = new Date(b.querySelector('.date').textContent);
                    // Handle invalid dates by placing them at the end
                    if (isNaN(dateA.getTime()) && isNaN(dateB.getTime())) return 0;
                    if (isNaN(dateA.getTime())) return 1;
                    if (isNaN(dateB.getTime())) return -1;
                    return dateB - dateA; // Descending order
                });
                // Clear existing content and append sorted essays
                container.innerHTML = '';
                essays.forEach(essay => container.appendChild(essay));
            }

            function sortByLikes() {
                const container = document.getElementById('essays');
                const essays = Array.from(container.children);
                essays.sort((a, b) => {
                    const likesA = parseInt(a.querySelector('.likes').textContent.replace('❤️ ', '') || '0');
                    const likesB = parseInt(b.querySelector('.likes').textContent.replace('❤️ ', '') || '0');
                    return likesB - likesA; // Descending order
                });
                // Clear existing content and append sorted essays
                container.innerHTML = '';
                essays.forEach(essay => container.appendChild(essay));
            }

            // Initial sort by date on page load
            window.addEventListener('load', sortByDate);
        """

class ContentGenerator:
    """Generates HTML and Markdown content for posts."""
    
    def __init__(self, author_name: str, output_dir: str = "output"):
        self.author_name = author_name
        self.output_dir = Path(output_dir).resolve()
        self.posts: List[Post] = []
        
    def _validate_path(self, path: Path) -> None:
        """Validate that a path is within the output directory."""
        try:
            path = path.resolve()
            if not str(path).startswith(str(self.output_dir)):
                raise ValidationError(f"Path {path} is outside the output directory")
        except Exception as e:
            raise ValidationError(f"Invalid path: {str(e)}")
        
    def load_posts(self) -> None:
        """Load posts from JSON data."""
        json_paths = [
            self.output_dir / "data" / f"{self.author_name}_essays.json",
            self.output_dir / "data" / f"{self.author_name}.json"
        ]
        
        for json_path in json_paths:
            if json_path.exists():
                # Validate the path is within output directory
                self._validate_path(json_path)
                
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.posts = [
                        Post(
                            title=post['title'],
                            date=post['date'],
                            like_count=post['like_count'],
                            subtitle=post.get('subtitle', ''),
                            is_paid=post.get('is_paid', False),
                            file_link=post.get('file_link'),
                            html_link=post.get('html_link')
                        )
                        for post in data
                        if all(key in post for key in ['title', 'date', 'like_count'])
                    ]
                break
                
        # Sort posts by date
        self.posts.sort(key=lambda x: x.date, reverse=True)
        
    def generate_html_content(self) -> str:
        """Generate HTML content for all posts with premium styling and correct links."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{self.author_name}'s Blog</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
            <style>
                {ThemeManager.get_theme_css()}
            </style>
        </head>
        <body>
            <button class="theme-toggle" onclick="toggleTheme()" aria-label="Toggle theme">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"></path>
                </svg>
            </button>

            <div class="header">
                <h1>{self.author_name}'s Substack</h1>
            </div>

            <div class="controls">
                <div class="tabs">
                    <div class="tab active" data-sort="date">By Date</div>
                    <div class="tab" data-sort="likes">By Likes</div>
                </div>

                <div class="select">
                    <div class="select-trigger">All Articles</div>
                    <div class="select-content" style="display: none;">
                        <div class="select-item" data-filter="all">All Articles</div>
                        <div class="select-item" data-filter="free">Free Articles</div>
                        <div class="select-item" data-filter="premium">Premium Articles</div>
                    </div>
                </div>
            </div>

            <div class="post-list">
        """
        
        for post in self.posts:
            # Skip if no links available
            if not post.file_link and not post.html_link:
                continue
                
            # Construct the correct relative path for links
            md_filename = Path(post.file_link).name if post.file_link else None
            html_filename = Path(post.html_link).name if post.html_link else None

            # Use the author name subdirectory for markdown files
            md_relative_path = f"../substack_md_files/{self.author_name}/{md_filename}" if md_filename else None
            html_relative_path = f"./{html_filename}" if html_filename else None

            # Determine the link to use for the title (prefer HTML)
            title_link_href = html_relative_path or md_relative_path

            html_content += f"""
                <article class="post">
                    <div class="post-header">
                        <h2 class="post-title">
                            <a href="{title_link_href}">{post.title}</a>
                        </h2>
                        {f'<div class="premium-badge"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/></svg>Premium</div>' if post.is_paid_post else ''}
                    </div>

                    <p class="post-excerpt">{post.subtitle}</p>

                    <div class="post-meta">
                        <div class="post-meta-item date">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                                <line x1="16" y1="2" x2="16" y2="6"></line>
                                <line x1="8" y1="2" x2="8" y2="6"></line>
                                <line x1="3" y1="10" x2="21" y2="10"></line>
                            </svg>
                            {post.date}
                        </div>

                        <div class="post-meta-item likes">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
                            </svg>
                            {post.like_count}
                        </div>
                    </div>

                    <a href="{title_link_href}" class="read-more">
                        {f"Read premium article" if post.is_paid_post else "Read article"}
                        <span>→</span>
                    </a>
                </article>
            """
        
        html_content += """
            </div>

            <div class="empty-state" style="display: none;">
                <p>No articles found for the selected filter.</p>
            </div>

            <script>
                """
        html_content += ThemeManager.get_theme_js()
        html_content += """
            </script>
        </body>
        </html>
        """
        
        return html_content
        
    def generate_markdown_content(self) -> str:
        """Generate markdown content for all posts."""
        md_content = f"# {self.author_name}'s Blog\n\n"
        md_content += "## Posts\n\n"
        
        for post in self.posts:
            if not post.file_link and not post.html_link:
                continue
                
            md_filename = post.file_link.split('/')[-1] if post.file_link else None
            html_filename = post.html_link.split('/')[-1] if post.html_link else None
            
            md_content += f"### {post.title}\n\n"
            if md_filename:
                md_content += f"[Markdown]({md_filename})  \n"
            if html_filename:
                md_content += f"[HTML]({html_filename})  \n"
                
            if post.subtitle:
                md_content += f"_{post.subtitle}_\n\n"
            md_content += f"**Date:** {post.date}  \n"
            md_content += f"**Likes:** {post.like_count}  \n"
            if post.is_paid_post:
                md_content += f"**{post.paid_indicator_md}**  \n"
            md_content += "\n---\n\n"
            
        return md_content

class Generator:
    """Main generator class for creating HTML and Markdown files."""
    
    @classmethod
    def generate(cls, author_name: str, output_dir: str = "output") -> None:
        """Generate all necessary files.
        
        Args:
            author_name: The name of the author/blog to generate files for.
            output_dir: Base directory for all outputs.
        """
        generator = cls(author_name, output_dir)
        generator._generate_files()
    
    def __init__(self, author_name: str, output_dir: str = "output"):
        self.author_name = author_name
        self.output_dir = Path(output_dir).resolve()
        self.content_generator = ContentGenerator(author_name, str(self.output_dir))
        
    def _validate_path(self, path: Path) -> None:
        """Validate that a path is within the output directory."""
        try:
            path = path.resolve()
            if not str(path).startswith(str(self.output_dir)):
                raise ValidationError(f"Path {path} is outside the output directory")
        except Exception as e:
            raise ValidationError(f"Invalid path: {str(e)}")
        
    def _generate_files(self) -> None:
        """Internal method to generate all necessary files."""
        # Load posts
        self.content_generator.load_posts()
        
        # Generate and save HTML files in output/substack_html_pages/author_name
        html_dir = self.output_dir / "substack_html_pages" / self.author_name
        html_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate the path is within output directory
        self._validate_path(html_dir)
        
        html_content = self.content_generator.generate_html_content()
        blog_path = html_dir / "index.html"
        with open(blog_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Generated html index at {blog_path}")
        
        # Generate and save markdown files in output/substack_md_files/author_name
        md_dir = self.output_dir / "substack_md_files" / self.author_name
        md_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate the path is within output directory
        self._validate_path(md_dir)
        
        md_content = self.content_generator.generate_markdown_content()
        md_path = md_dir / "index.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

def generate(author_name: str, output_dir: str = "output") -> None:
    """Main entry point for generating HTML and Markdown files."""
    Generator.generate(author_name, output_dir) 