import os
from pathlib import Path
from typing import Optional, Union
import paramiko


def load_env_file(dotenv_path: Optional[Union[str, Path]] = None) -> None:
    """Load key-value pairs from .env into os.environ if not already set."""
    if dotenv_path is None:
        dotenv_path = Path(__file__).resolve().parent.parent / ".env"
    else:
        dotenv_path = Path(dotenv_path)

    if not dotenv_path.is_file():
        return

    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = val


class SFTPService:
    """Service for uploading local files to an SFTP server."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        remote_path: Optional[str] = None,
    ):
        # Automatically load environment variables from .env if present
        load_env_file()

        self.host = host or os.getenv("SFTP_HOST", "").strip()
        port_raw = port if port is not None else os.getenv("SFTP_PORT", "22").strip()
        try:
            self.port = int(port_raw) if port_raw else 22
        except ValueError:
            self.port = 22

        self.username = username or os.getenv("SFTP_USERNAME", "").strip()
        self.password = password or os.getenv("SFTP_PASSWORD", "").strip()
        self.remote_path = remote_path or os.getenv("SFTP_REMOTE_PATH", "").strip()

    def _validate_config(self) -> None:
        """Ensure all required SFTP configuration values are present."""
        missing = []
        if not self.host:
            missing.append("SFTP_HOST")
        if not self.username:
            missing.append("SFTP_USERNAME")
        if not self.password:
            missing.append("SFTP_PASSWORD")

        if missing:
            raise ValueError(
                f"Missing required SFTP configuration: {', '.join(missing)}. "
                "Please configure these in your .env file or environment variables."
            )

    def upload_file(self, local_file_path: Union[str, Path]) -> str:
        """Upload a local file to the SFTP server using the same filename.

        Args:
            local_file_path: Path to the local file to upload.

        Returns:
            The remote path where the file was uploaded.
        """
        local_path = Path(local_file_path).resolve()

        if not local_path.exists():
            raise FileNotFoundError(f"Local file does not exist: {local_path}")
        if not local_path.is_file():
            raise ValueError(f"Path is not a regular file: {local_path}")

        # Validate configuration before attempting connection
        self._validate_config()

        filename = local_path.name
        if self.remote_path:
            remote_dir = self.remote_path.rstrip("/\\").replace("\\", "/")
            remote_file_path = f"{remote_dir}/{filename}"
        else:
            remote_file_path = filename

        transport = None
        sftp = None

        print("Connecting to SFTP...")
        try:
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.username, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            print("SFTP connection successful.")
        except Exception as e:
            if transport:
                try:
                    transport.close()
                except Exception:
                    pass
            raise ConnectionError(
                f"Failed to connect to SFTP server {self.host}:{self.port} - {e}"
            ) from e

        try:
            print(f"Uploading: {filename}")
            sftp.put(str(local_path), remote_file_path)
            print("Upload successful.")
            print(f"Remote path: {remote_file_path}")
            return remote_file_path
        except Exception as e:
            raise RuntimeError(
                f"Failed to upload {filename} to {remote_file_path}: {e}"
            ) from e
        finally:
            if sftp:
                try:
                    sftp.close()
                except Exception:
                    pass
            if transport:
                try:
                    transport.close()
                except Exception:
                    pass
