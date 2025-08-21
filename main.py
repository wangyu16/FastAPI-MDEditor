import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from pathlib import Path

# --- Configuration & Setup ---

# Define the directory where notes will be stored.
NOTES_DIRECTORY = Path("notes")
# Ensure the notes directory exists.
NOTES_DIRECTORY.mkdir(exist_ok=True)

# Define the directory for HTML templates.
TEMPLATE_DIRECTORY = "templates"
STATIC_DIRECTORY = "static"

# Create the main FastAPI application instance.
app = FastAPI(
    title="Markdown Editor API",
    description="An API for a simple markdown editor.",
    version="1.0.0"
)

# Mount the static directory to serve CSS, JS, etc.
app.mount(f"/{STATIC_DIRECTORY}", StaticFiles(directory=STATIC_DIRECTORY), name="static")

# Set up the Jinja2 environment to load templates.
env = Environment(loader=FileSystemLoader(TEMPLATE_DIRECTORY))
template = env.get_template("index.html")

# Pydantic model for validating the content sent from the frontend when saving a file.
class FileContent(BaseModel):
    content: str

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serves the main HTML page of the application.
    """
    # Renders the index.html template and returns it as the response.
    return HTMLResponse(content=template.render(), status_code=200)

@app.get("/api/files")
async def get_file_list():
    """
    Gets the list of all markdown (.md) files in the NOTES_DIRECTORY.
    """
    try:
        # List all files in the directory, filtering for those that end with .md
        files = [f.name for f in NOTES_DIRECTORY.iterdir() if f.is_file() and f.name.endswith(".md")]
        return {"files": files}
    except Exception as e:
        # If there's an error reading the directory, raise an HTTP exception.
        raise HTTPException(status_code=500, detail=f"Error reading files: {str(e)}")

@app.get("/api/files/{filename}")
async def get_file_content(filename: str):
    """
    Gets the content of a specific markdown file.
    """
    file_path = NOTES_DIRECTORY / filename
    # Security check: ensure the file is within the intended directory.
    if not file_path.is_file() or not str(file_path.resolve()).startswith(str(NOTES_DIRECTORY.resolve())):
        raise HTTPException(status_code=404, detail="File not found or access denied.")

    try:
        content = file_path.read_text(encoding="utf-8")
        return {"filename": filename, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@app.post("/api/files/{filename}")
async def save_file_content(filename: str, file_data: FileContent):
    """
    Saves or updates the content of a specific markdown file.
    """
    # Basic validation for the filename.
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = NOTES_DIRECTORY / f"{filename}.md" if not filename.endswith(".md") else NOTES_DIRECTORY / filename

    try:
        file_path.write_text(file_data.content, encoding="utf-8")
        return {"message": f"File '{file_path.name}' saved successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """
    Deletes a specific markdown file.
    """
    file_path = NOTES_DIRECTORY / filename
    # Security check: ensure the file is within the intended directory and is a valid file.
    if not file_path.is_file() or not str(file_path.resolve()).startswith(str(NOTES_DIRECTORY.resolve())):
        raise HTTPException(status_code=404, detail="File not found or access denied.")
    
    try:
        file_path.unlink() # Deletes the file
        return {"message": f"File '{filename}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")


# --- Initial File Creation (for demonstration) ---
# Create a default file if the notes directory is empty to give the user something to see.
if not any(NOTES_DIRECTORY.iterdir()):
    (NOTES_DIRECTORY / "welcome.md").write_text("# Welcome to your new Markdown Editor!\n\nStart typing here.")
