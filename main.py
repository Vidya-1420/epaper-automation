import sys
from agents.aawsat_agent import AawsatAgent
from services.sftp_service import SFTPService


def main():
    print("=== Step 1: Downloading Aawsat E-Paper ===")
    try:
        agent = AawsatAgent()
        downloaded_file = agent.download_pdf()
        print(f"Download completed successfully: {downloaded_file}")
    except Exception as e:
        print(f"Error during download: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n=== Step 2: Uploading to SFTP ===")
    sftp_service = SFTPService()

    # Check if credentials are provided in environment / .env
    missing_configs = []
    if not sftp_service.host:
        missing_configs.append("SFTP_HOST")
    if not sftp_service.username:
        missing_configs.append("SFTP_USERNAME")
    if not sftp_service.password:
        missing_configs.append("SFTP_PASSWORD")

    if missing_configs:
        print("SFTPService successfully imported and initialized.")
        print(
            "Notice: SFTP upload cannot be performed because credentials are not configured.\n"
            f"Missing configuration: {', '.join(missing_configs)} in .env\n"
            "To test actual SFTP upload, configure SFTP_HOST, SFTP_USERNAME, SFTP_PASSWORD (and optional SFTP_PORT, SFTP_REMOTE_PATH) in .env."
        )
        return

    try:
        remote_path = sftp_service.upload_file(downloaded_file)
        print(f"SFTP upload completed successfully: {remote_path}")
    except Exception as e:
        print(f"SFTP upload failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
