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
        """Fetch Aawsat homepage and find today's issue number."""

        print("Fetching Aawsat homepage...")

        try:
            response = requests.get(
                self.HOME_URL,
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout
            )

            response.raise_for_status()

        except requests.RequestException as e:
            raise RuntimeError(
                f"Failed to fetch Aawsat homepage: {e}"
            ) from e

        match = re.search(
            r"/files/pdf/issue(\d+)/",
            response.text
        )

        if not match:
            raise RuntimeError(
                "Today's Aawsat issue number was not found on the homepage."
            )

        issue_number = match.group(1)

        print(f"Found today's issue number: {issue_number}")

        return issue_number

    def get_pdf_url(self, issue_number: str) -> str:
        """Construct the PDF URL for the issue."""

        return (
            f"https://aawsat.com/files/pdf/issue{issue_number}/"
            f"files/assets/common/downloads/issue{issue_number}.pdf"
        )

    def download_pdf(self, issue_number: str = None) -> Path:
        """
        Download today's Aawsat PDF.

        The workflow should fail if:
        - today's issue cannot be found
        - PDF request fails
        - response is empty
        - response is not actually a PDF
        - downloaded file is suspiciously small
        """

        print("\n=== Downloading Aawsat E-Paper ===")

        # --------------------------------------------------
        # STEP 1: Find today's issue
        # --------------------------------------------------

        if issue_number is None:
            issue_number = self.get_today_issue_number()

        # --------------------------------------------------
        # STEP 2: Create PDF URL
        # --------------------------------------------------

        pdf_url = self.get_pdf_url(issue_number)

        print(f"PDF URL: {pdf_url}")

        # --------------------------------------------------
        # STEP 3: Create downloads folder
        # --------------------------------------------------

        self.download_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # --------------------------------------------------
        # STEP 4: Create filename
        # --------------------------------------------------

        date_str = datetime.now().strftime("%y%m%d")

        filename = f"{date_str}{self.SITE_NAME}.pdf"

        output_path = self.download_dir / filename

        # --------------------------------------------------
        # STEP 5: Download PDF
        # --------------------------------------------------

        if output_path.exists():
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
            raise RuntimeError(
                f"Failed to download PDF from {pdf_url}: {e}"
            ) from e

        # --------------------------------------------------
        # STEP 6: Validate downloaded response
        # --------------------------------------------------

        if not response.content:
            raise RuntimeError(
                "Downloaded PDF is empty."
            )

        # A real PDF normally starts with %PDF
        if not response.content.startswith(b"%PDF"):
            raise RuntimeError(
                "Downloaded file is not a valid PDF."
            )

        # --------------------------------------------------
        # STEP 7: Save PDF
        # --------------------------------------------------

        with open(output_path, "wb") as file:
            file.write(response.content)

        # --------------------------------------------------
        # STEP 8: Validate saved file
        # --------------------------------------------------

        file_size = output_path.stat().st_size

        if file_size < 10_000:
            raise RuntimeError(
                f"Downloaded PDF is unexpectedly small: "
                f"{file_size} bytes."
            )

        size_mb = file_size / (1024 * 1024)

        print("Downloaded successfully.")
        print(f"Saved to: {output_path.resolve()}")
        print(f"File size: {size_mb:.1f} MB")

        print(
            f"Download completed successfully: "
            f"{output_path.resolve()}"
        )

        return output_path