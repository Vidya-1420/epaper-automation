import os
import re
from datetime import datetime
from pathlib import Path
import requests


class AawsatAgent:
    HOME_URL = "https://aawsat.com/"
    SITE_NAME = "aawsat"
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    def __init__(self, download_dir=None, timeout=30):
        if download_dir is None:
            project_root = Path(__file__).resolve().parent.parent
            self.download_dir = project_root / "downloads"
        else:
            self.download_dir = Path(download_dir)
        self.timeout = timeout

    def get_today_issue_number(self) -> str:
        """Fetch homepage and extract today's issue number using regex."""
        print("Fetching Aawsat homepage...")
        try:
            response = requests.get(
                self.HOME_URL,
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch Aawsat homepage: {e}") from e

        match = re.search(r"/files/pdf/issue(\d+)/", response.text)
        if not match:
            raise ValueError("Could not find today's issue number on homepage HTML")

        issue_number = match.group(1)
        print(f"Found today's issue number: {issue_number}")
        return issue_number

    def get_pdf_url(self, issue_number: str) -> str:
        """Construct the direct PDF download URL for a given issue number."""
        return (
            f"https://aawsat.com/files/pdf/issue{issue_number}/"
            f"files/assets/common/downloads/issue{issue_number}.pdf"
        )

    def download_pdf(self, issue_number: str = None) -> Path:
        """Download today's Aawsat PDF and save it with the YYMMDDaawsat.pdf format."""
        if issue_number is None:
            issue_number = self.get_today_issue_number()

        pdf_url = self.get_pdf_url(issue_number)
        print(f"PDF URL: {pdf_url}")

        # Ensure download directory exists
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename: YYMMDD<sitename>.pdf (e.g. 260922aawsat.pdf)
        date_str = datetime.now().strftime("%y%m%d")
        filename = f"{date_str}{self.SITE_NAME}.pdf"
        output_path = self.download_dir / filename

        # Check whether PDF already exists
        already_exists = output_path.exists()

        if already_exists:
            print("PDF already exists. Downloading again...")
        else:
            print(f"Downloading PDF from: {pdf_url}")

        try:
            response = requests.get(
                pdf_url,
                headers=self.DEFAULT_HEADERS,
                timeout=120
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to download PDF from {pdf_url}: {e}") from e

        # Save / overwrite binary data
        with open(output_path, "wb") as f:
            f.write(response.content)

        size_mb = output_path.stat().st_size / (1024 * 1024)

        if already_exists:
            print("Downloaded again successfully.")
        else:
            print("Downloaded successfully.")

        print(f"Saved to: {output_path.resolve()}")
        print(f"File size: {size_mb:.1f} MB")

        return output_path
