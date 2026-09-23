import sys

from agents.aawsat_agent import AawsatAgent
from notifications.notifier import notify_failure
from services.sftp_service import SFTPService


def main():
    downloaded_file = None

    print("=== Step 1: Downloading Aawsat E-Paper ===")
    try:
        agent = AawsatAgent()
        downloaded_file = agent.download_pdf()
        print(f"Download completed successfully: {downloaded_file}")
    except Exception as e:
        print(f"Error during download: {e}", file=sys.stderr)
        notify_failure("Download", e)
        sys.exit(1)

    print("\n=== Step 2: Uploading to SFTP ===")
    try:
        sftp_service = SFTPService()

        missing_configs = []
        if not sftp_service.host:
            missing_configs.append("SFTP_HOST")
        if not sftp_service.username:
            missing_configs.append("SFTP_USERNAME")
        if not sftp_service.password:
            missing_configs.append("SFTP_PASSWORD")

        if missing_configs:
            raise RuntimeError(
                "SFTP upload cannot be performed because credentials are "
                f"not configured. Missing: {', '.join(missing_configs)}"
            )

        remote_path = sftp_service.upload_file(downloaded_file)
        print(f"SFTP upload completed successfully: {remote_path}")

    except Exception as e:
        print(f"SFTP upload failed: {e}", file=sys.stderr)
        notify_failure("SFTP Upload", e, extra=f"Local file: {downloaded_file}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unexpected fatal error: {e}", file=sys.stderr)
        notify_failure("Unexpected crash", e)
        sys.exit(1)
