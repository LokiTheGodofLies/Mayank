import html
import json
import re
from urllib.parse import quote_plus, urljoin
import aiohttp
from parsel import Selector

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Lightweight cache (max 500 items) to avoid scraping the same book title twice
_BOOK_CACHE: dict[str, dict] = {}


def clean_filename_for_search(file_name: str) -> str:
    """Cleans a messy Telegram filename into a clean book search query."""
    if not file_name:
        return ""
    # Strip file extension
    name = re.sub(r"\.[a-zA-Z0-9]{2,5}$", "", file_name)
    # Remove common release tags in brackets/parentheses
    name = re.sub(r"\[.*?\]|\(.*?\)", " ", name)
    # Remove common noise words
    noise = r"\b(z-lib\.org|z-library|annas-archive|libgen|epub|pdf|azw3|kfx|mp3|m4b|aax|audiobook|unabridged|64kbps|128kbps)\b"
    name = re.sub(noise, " ", name, flags=re.IGNORECASE)
    # Replace underscores, dots, and dashes with spaces
    name = re.sub(r"[_\.\-]+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _find_book_ld_json(sel: Selector) -> dict:
    """Extracts the @type == 'Book' JSON-LD block from a Goodreads book page."""
    for script in sel.xpath('//script[@type="application/ld+json"]/text()').getall():
        try:
            data = json.loads(script)
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") == "Book":
            return data
    return {}


def _parse_book_html(html_text: str, fallback_stub: dict) -> dict:
    """Parses Goodreads book page HTML using JSON-LD and scoped data-testid selectors."""
    sel = Selector(text=html_text)
    ld = _find_book_ld_json(sel)
    rating_block = ld.get("aggregateRating") or {}
    authors = ld.get("author") or []

    title = (
        sel.css('h1[data-testid="bookTitle"]::text').get()
        or ld.get("name")
        or fallback_stub.get("title")
        or "Unknown Title"
    )
    author_name = (
        (authors[0].get("name") if authors and isinstance(authors[0], dict) else None)
        or fallback_stub.get("author")
        or "Unknown Author"
    )

    desc_parts = [
        t.strip()
        for t in sel.css('div[data-testid="description"] .Formatted::text').getall()
        if t.strip()
    ]
    description = " ".join(desc_parts) if desc_parts else "No description available."
    if len(description) > 320:
        description = description[:317].rsplit(" ", 1)[0] + "..."

    genres = [
        g.strip()
        for g in sel.css(
            'div[data-testid="genresList"] span.BookPageMetadataSection__genreButton a '
            "span.Button__labelItem::text"
        ).getall()
        if g.strip()
    ]
    genres_str = ", ".join(genres[:5]) if genres else "N/A"

    avg_rating = rating_block.get("ratingValue") or fallback_stub.get("avg_rating") or "N/A"
    ratings_count = rating_block.get("ratingCount") or fallback_stub.get("ratings_count")
    if isinstance(ratings_count, int) or (isinstance(ratings_count, str) and ratings_count.isdigit()):
        ratings_count_str = f"{int(ratings_count):,}"
    else:
        ratings_count_str = str(ratings_count) if ratings_count else "0"

    published = sel.css('p[data-testid="publicationInfo"]::text').get() or "N/A"
    num_pages = ld.get("numberOfPages") or "N/A"
    isbn = ld.get("isbn") or "N/A"
    language = ld.get("inLanguage") or "N/A"
    cover_url = (
        ld.get("image")
        or sel.xpath('//meta[@property="og:image"]/@content').get()
        or fallback_stub.get("image_url")
        or ""
    )
    canonical_url = (
        sel.xpath('//link[@rel="canonical"]/@href').get()
        or fallback_stub.get("book_url")
        or ""
    )

    return {
        "book_title": str(title).strip(),
        "book_author": str(author_name).strip(),
        "book_rating": str(avg_rating),
        "book_ratings_count": ratings_count_str,
        "book_genres": genres_str,
        "book_pages": str(num_pages),
        "book_isbn": str(isbn),
        "book_language": str(language),
        "book_published": str(published).strip(),
        "book_description": description,
        "book_url": canonical_url,
        "book_cover": cover_url,
    }


def _default_book_meta(clean_title: str) -> dict:
    """Fallback metadata dictionary when a book is not found on Goodreads."""
    return {
        "book_title": clean_title or "Unknown Title",
        "book_author": "N/A",
        "book_rating": "N/A",
        "book_ratings_count": "0",
        "book_genres": "N/A",
        "book_pages": "N/A",
        "book_isbn": "N/A",
        "book_language": "N/A",
        "book_published": "N/A",
        "book_description": "N/A",
        "book_url": "",
        "book_cover": "",
    }


async def fetch_goodreads_metadata(file_name: str) -> dict:
    """
    Searches Goodreads using the cleaned filename and scrapes the book's metadata.
    Never raises an exception—returns safe fallback strings if offline or not found.
    """
    clean_query = clean_filename_for_search(file_name)
    if not clean_query:
        return _default_book_meta(file_name)

    cache_key = clean_query.lower()
    if cache_key in _BOOK_CACHE:
        return _BOOK_CACHE[cache_key]

    timeout = aiohttp.ClientTimeout(total=8)
    try:
        async with aiohttp.ClientSession(headers=HEADERS, timeout=timeout) as session:
            # Try full cleaned query first, then first 5 words if no match
            words = clean_query.split()
            candidate_queries = [clean_query]
            if len(words) > 5:
                candidate_queries.append(" ".join(words[:5]))

            stub_data = None
            for q in candidate_queries:
                auto_url = f"https://www.goodreads.com/book/auto_complete?format=json&q={quote_plus(q)}"
                async with session.get(auto_url) as resp:
                    if resp.status == 200:
                        items = await resp.json(content_type=None)
                        if isinstance(items, list) and len(items) > 0:
                            first = items[0]
                            book_path = first.get("bookUrl", "")
                            author_obj = first.get("author") or {}
                            stub_data = {
                                "title": first.get("title"),
                                "author": author_obj.get("name") if isinstance(author_obj, dict) else None,
                                "avg_rating": first.get("avgRating"),
                                "ratings_count": first.get("ratingsCount"),
                                "image_url": first.get("imageUrl"),
                                "book_url": urljoin("https://www.goodreads.com", book_path).split("?")[0],
                            }
                            break

            if not stub_data or not stub_data.get("book_url"):
                return _default_book_meta(clean_query)

            # Fetch the actual Goodreads book page to extract JSON-LD, Genres, and Description
            async with session.get(stub_data["book_url"]) as page_resp:
                if page_resp.status == 200:
                    html_text = await page_resp.text()
                    parsed = _parse_book_html(html_text, stub_data)
                else:
                    parsed = _parse_book_html("", stub_data)

            if len(_BOOK_CACHE) >= 500:
                _BOOK_CACHE.clear()
            _BOOK_CACHE[cache_key] = parsed
            return parsed

    except Exception as e:
        print(f"[GOODREADS SCRAPER WARNING] Could not scrape '{clean_query}': {e}")
        return _default_book_meta(clean_query)


def format_index_channel_caption(
    file_name: str,
    file_size_str: str,
    duration_str: str,
    extension: str,
    file_type: str,
    book_meta: dict,
) -> str:
    """
    Formats the rich HTML caption placed on the file in INDEX_CHANNEL_ID,
    combining file details (name, size, duration) with scraped Goodreads metadata.
    Guaranteed to stay <= 1024 characters for Telegram media captions.
    """
    esc_file_name = html.escape(file_name or "Unknown")
    esc_title = html.escape(book_meta.get("book_title") or "Unknown")
    esc_author = html.escape(book_meta.get("book_author") or "N/A")
    esc_rating = html.escape(book_meta.get("book_rating") or "N/A")
    esc_ratings_count = html.escape(book_meta.get("book_ratings_count") or "0")
    esc_genres = html.escape(book_meta.get("book_genres") or "N/A")
    esc_pages = html.escape(book_meta.get("book_pages") or "N/A")
    esc_published = html.escape(book_meta.get("book_published") or "N/A")
    esc_desc = html.escape(book_meta.get("book_description") or "N/A")
    book_url = book_meta.get("book_url") or ""

    title_display = (
        f'<a href="{html.escape(book_url)}">{esc_title}</a>' if book_url else esc_title
    )

    lines = [
        f"📚 <b>Book:</b> {title_display}",
        f"✍️ <b>Author:</b> <code>{esc_author}</code>",
        f"⭐ <b>Rating:</b> <code>{esc_rating}</code> (<code>{esc_ratings_count}</code> ratings)",
        f"🏷 <b>Genres:</b> <code>{esc_genres}</code>",
        f"📄 <b>Pages:</b> <code>{esc_pages}</code> | 📅 <code>{esc_published}</code>",
        "",
        f"📁 <b>File Name:</b> <code>{esc_file_name}</code>",
        f"📦 <b>Size:</b> <code>{html.escape(file_size_str)}</code> | <b>Type:</b> <code>{html.escape(file_type)} (.{html.escape(extension)})</code>",
    ]
    if duration_str and duration_str != "N/A":
        lines.append(f"⏱ <b>Duration:</b> <code>{html.escape(duration_str)}</code>")

    if esc_desc and esc_desc != "N/A":
        lines.append(f"\n📝 <b>Summary:</b>\n<blockquote expandable>{esc_desc}</blockquote>")

    caption = "\n".join(lines)
    return caption[:1020]
