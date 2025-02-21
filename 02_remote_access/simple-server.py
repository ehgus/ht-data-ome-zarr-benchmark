import os
import json
import argparse
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from typing import List
from fastapi import Request

# Directory to serve
directory = None

def startup_event():
    global directory
    if not directory:
        raise RuntimeError("Server requires a directory path to serve files.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # When service starts.
    startup_event()
    yield
    # When service is stopped.
    pass

app = FastAPI(lifespan=lifespan)

@app.api_route("/", methods=["GET", "HEAD"])
async def list_files(request: Request) -> List[str]:
    """List available files in the directory, supporting both GET and HEAD."""
    if request.method == "HEAD":
        return JSONResponse(content=None, status_code=200)

    if not os.path.exists(directory):
        raise HTTPException(status_code=404, detail="Directory not found")

    files = [f.name for f in Path(directory).iterdir() if f.is_file()]
    return files

@app.get("/{file_path:path}")
async def get_file(file_path: str):
    """Serve a file from the directory, preserving subdirectories."""
    full_path = Path(directory) / file_path

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    # Serve JSON files as structured data
    text_extensions = ('.zattrs', '.zgroup', '.zarray', '.json')
    if full_path.name.endswith(text_extensions):
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = json.load(f)
            return JSONResponse(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid JSON format")

    # Serve other files as downloads
    return FileResponse(full_path, filename=full_path.name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FastAPI file server with HTTP/2 support")
    parser.add_argument("directory", type=str, help="Directory to serve")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--cert", type=str, default="cert.pem", help="SSL certificate file")
    parser.add_argument("--key", type=str, default="key.pem", help="SSL key file")
    args = parser.parse_args()

    directory = args.directory
    port = args.port
    cert_file = args.cert
    key_file = args.key

    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory")
        exit(1)

    import hypercorn.asyncio
    from hypercorn.config import Config

    config = Config()
    config.bind = [f"0.0.0.0:{port}"]
    config.alpn_protocols = ["h2", "http/1.1"]  # Enable HTTP/2 and fallback to HTTP/1.1
    config.accesslog = '-'

    import asyncio
    asyncio.run(hypercorn.asyncio.serve(app, config))