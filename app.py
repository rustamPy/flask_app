from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from starlette.background import BackgroundTask
from fastapi.templating import Jinja2Templates
from io import StringIO
from threading import Thread
from typing import Dict, Any
import time
import asyncio
import uuid
from fastapi import HTTPException

from hello import hello

import tempfile
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")


CONTEXT = {}

# Define the function parameters with more details
function_params = {
    "function_1": {
        "description": "This function performs a basic calculation using two parameters.",
        "params": {
            "a": {
                "type": "number",
                "description": "A numeric value for the calculation"
            },
            "b": {
                "type": "text",
                "description": "A text value for the calculation"
            }
        }
    },
    "function_2": {
        "description": "This function processes text and numeric input for advanced operations.",
        "params": {
            "x": {
                "type": "text",
                "description": "A text input for processing"
            },
            "y": {
                "type": "number",
                "description": "A numeric input for processing"
            }
        }
    },
    "run_context_table": {
        "description": "run_context_table description",
        "params": {
            "table": {
                "type": "text",
                "description": "A text input for processing"
            },
            "scenarios": {
                "type": "list",
                "description": "The list of scenarios"
            }
        }
    }
}

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate_payload", response_class=HTMLResponse)
async def handle_form(request: Request):
    global CONTEXT
    form_data = await request.form()
    
    # Process chapters, sub-chapters, and sub-sub-chapters
    chapters_data = []
    cover_data = {}
    cob = ''
    current_chapter = None
    current_sub_chapter = None

    for key, value in form_data.items():
        if key.startswith('chapter'):
            current_chapter = {"chapter": value, "sub_chapters": []}
            chapters_data.append(current_chapter)
        elif key.startswith('subChapter'):
            current_sub_chapter = {"sub_chapter": value, "sub_sub_chapters": []}
            current_chapter["sub_chapters"].append(current_sub_chapter)
        elif key.startswith('subSubChapter'):
            sub_sub_chapter_index = key.replace('subSubChapter', '')
            function_key = f'function{sub_sub_chapter_index}'
            print(function_key)
            function_value = form_data.get(function_key, '')
            
            sub_sub_chapter = {
                "sub_sub_chapter": value,
                "function": function_value,
                "params": {}
            }
            
            if function_value in function_params:
                for param, details in function_params[function_value]["params"].items():
                    param_key = f'{function_value}_{param}{sub_sub_chapter_index}'
                    if details['type'] == 'list':
                        sub_sub_chapter["params"][param] = list(map(lambda x: x.strip(), form_data.get(param_key, '').split(',')))
                        
                    else:
                        sub_sub_chapter["params"][param] = form_data.get(param_key, '')
            
            current_sub_chapter["sub_sub_chapters"].append(sub_sub_chapter)
        elif key.startswith('report'):
            cover_data[key] = value
        elif key == 'cob':
            cob = value

    CONTEXT = {
        "cob": cob,
        "cover_data": cover_data,
        "chapters_data": chapters_data
    }
    return JSONResponse(content=CONTEXT)

@app.get("/get_function_params")
async def get_function_params():
    return JSONResponse(content=function_params)

report_cache = {}


@app.get("/run_report")
async def run_report(request: Request):
    # Simulate a long-running task
    await asyncio.sleep(1)
    res = hello()

    # Generate HTML content
    html_content = generate_html_content("dasda")

    # Create a unique filename
    filename = f"report_{uuid.uuid4().hex}.html"

    # Store the content in the cache
    report_cache[filename] = html_content

    return JSONResponse(content={"status": "completed", "filename": filename})

@app.get("/download/{filename}")
async def download_file(filename: str):
    if filename not in report_cache:
        raise HTTPException(status_code=404, detail="Report not found")
    
    content = report_cache[filename]
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as temp_file:
        temp_file.write(content)
        temp_file_path = temp_file.name

    return FileResponse(temp_file_path, media_type="text/html", filename=filename)



def generate_html_content(res):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Report Result</title>
    </head>
    <body>
        <h1>Report Result</h1>
        <p>{res}</p>
    </body>
    </html>
    """
    return html_content





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)