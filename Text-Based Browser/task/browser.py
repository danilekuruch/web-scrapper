import argparse
import os
from collections import deque
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import colorama


class CacheManager:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(self.path, exist_ok=True)
        self._memory_cache = {}

    def _file_path(self, key: str) -> str:
        return os.path.join(self.path, key)

    def save(self, key: str, content: str) -> None:
        with open(self._file_path(key), "w", encoding="utf-8") as f:
            f.write(content)
        self._memory_cache[key] = content

    def load(self, key: str) -> str | None:
        if key in self._memory_cache:
            return self._memory_cache[key]
        try:
            with open(self._file_path(key), "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return None


class History:
    def __init__(self):
        self._stack = deque()

    def push(self, url: str) -> None:
        self._stack.append(url)

    def back(self) -> str | None:
        if len(self._stack) > 1:
            self._stack.pop()
            return self._stack[-1]
        return None


class Renderer:
    @staticmethod
    def extract_text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        lines = []
        for tag in soup.find_all():
            text = tag.get_text(strip=True)
            if not text:
                continue
            if tag.name == "a":
                text = colorama.Fore.BLUE + text + colorama.Style.RESET_ALL
            lines.append(text)
        return "\n".join(lines)


class Browser:
    def __init__(self, cache_path: str):
        self.cache = CacheManager(cache_path)
        self.history = History()

    def normalize_url(self, url: str) -> str:
        if not urlparse(url).scheme:
            url = "https://" + url
        return url

    def cache_key(self, url: str) -> str:
        return urlparse(url).netloc

    def fetch_page(self, url: str) -> str:
        key = self.cache_key(url)
        cached = self.cache.load(key)
        if cached:
            return cached

        response = requests.get(url)
        response.raise_for_status()
        text = Renderer.extract_text(response.text)
        self.cache.save(key, text)
        return text

    def print_page(self, url: str) -> None:
        try:
            url = self.normalize_url(url)
            text = self.fetch_page(url)
        except Exception as e:
            print(f"Error: {e}")
            return

        print(text)
        self.history.push(url)

    def back(self) -> None:
        prev = self.history.back()
        if prev:
            self.print_page(prev)

    def run(self):
        while user_input := input("> "):
            if user_input == "exit":
                break
            elif user_input == "back":
                self.back()
            else:
                self.print_page(user_input)


def parse_args() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument("cache_path")
    return parser.parse_args().cache_path


if __name__ == "__main__":
    browser = Browser(parse_args())
    browser.run()
