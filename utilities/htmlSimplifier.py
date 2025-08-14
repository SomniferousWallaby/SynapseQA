from bs4 import BeautifulSoup
from playwright.sync_api import Page
import logging

logger = logging.getLogger(__name__)

def simplify_html(page: Page) -> str:
    """
    Strips HTML down to its essential interactive elements and their attributes.
    This simplified version is easier for the LLM to process accurately.
    """
    try:
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove tags that don't contain user-facing content.
        for tag in soup(["script", "style", "meta", "link", "path", "svg"]):
            tag.decompose()

        simplified_tags = []
        # Find all potentially interactive or significant elements.
        for tag in soup.find_all(["a", "button", "input", "textarea", "select", "h1", "h2", "h3", "label", "div", "span", "p"]):
            attrs = {
                "id": tag.get("id"),
                "class": " ".join(tag.get("class", [])),
                "name": tag.get("name"),
                "placeholder": tag.get("placeholder"),
                "aria-label": tag.get("aria-label"),
                "data-testid": tag.get("data-testid"),
                "role": tag.get("role"),
                "type": tag.get("type"),
                "href": tag.get("href")
            }
            text = ' '.join(tag.stripped_strings)
            tag_name = tag.name
            clean_attrs = {k: v for k, v in attrs.items() if v}
            attr_str = " ".join([f'{k}="{v}"' for k, v in clean_attrs.items()])
            
            # Construct the simplified tag string.
            full_tag_str = f"<{tag_name} {attr_str}>"
            if text:
                full_tag_str += f"{text}</{tag_name}>"
            
            simplified_tags.append(full_tag_str)

        logger.info(f"Simplified HTML to {len(simplified_tags)} elements for AI context.")
        return "\n".join(simplified_tags)
    except Exception as e:
        logger.error(f"An error occurred during HTML simplification: {e}")
        return ""
