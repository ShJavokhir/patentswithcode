import os
from typing import List, Dict, Any
import httpx

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from e2b import Sandbox
from openai import OpenAI
import dotenv

print("[ps] Loading environment from ../.env.local", flush=True)
dotenv.load_dotenv("./.env.local")
print("[ps] Environment loaded. EXA_API_KEY present:", "EXA_API_KEY" in os.environ, flush=True)

app = FastAPI(title="Patent Search API")

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global persistent sandbox - created once on startup
_sandbox = None
_mcp_url = None
_mcp_token = None

def get_sandbox():
    """Get or create the persistent sandbox"""
    global _sandbox, _mcp_url, _mcp_token
    
    if _sandbox is None:
        print("[ps] Creating persistent sandbox with MCP 'exa' and 'firecrawl'", flush=True)
        _sandbox = Sandbox.create(
            mcp={
                "exa": {
                    "apiKey": os.environ["EXA_API_KEY"],
                },
                "firecrawl": {
                    "apiKey": os.environ["FIRECRAWL_API_KEY"],
                },
            },
            timeout=3600,
        )
        _mcp_url = _sandbox.get_mcp_url()
        _mcp_token = _sandbox.get_mcp_token()
        print("[ps] Persistent sandbox created", flush=True)
    
    return _sandbox, _mcp_url, _mcp_token

# Request/Response models
class SearchQuery(BaseModel):
    query: str

class ScrapeURL(BaseModel):
    url: str

class SearchResult(BaseModel):
    results: List[Dict[str, Any]]

class PatentText(BaseModel):
    text: str

class SpecsResponse(BaseModel):
    specs: str

class CodeResponse(BaseModel):
    code: str
    specs: str

class E2BPreviewResponse(BaseModel):
    url: str
    sandbox_id: str

class SandboxKillRequest(BaseModel):
    sandbox_id: str

# Store active sandboxes
active_sandboxes: Dict[str, Any] = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Patent Search API is running"}

@app.post("/search", response_model=SearchResult)
async def search_patents(query: SearchQuery):
    """Search for patents using Exa API directly, return top 10 results"""
    print(f"[ps] /search endpoint called with query: {query.query}", flush=True)
    
    # Prefix query with "google patent" to ensure only Google Patents results
    search_query = f"google patent {query.query}"
    print(f"[ps] Prefixed search query: {search_query}", flush=True)
    
    try:
        # Call Exa API directly for faster results
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.exa.ai/search",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": os.environ["EXA_API_KEY"],
                },
                json={
                    "query": search_query,
                    "num_results": 10,
                    "type": "keyword",
                    "include_domains": ["patents.google.com"],
                    "contents": {
                        "text": {"max_characters": 200}
                    }
                },
                timeout=30.0,
            )
            
            if response.status_code != 200:
                print(f"[ps] Exa API error: {response.status_code} - {response.text}", flush=True)
                raise HTTPException(status_code=response.status_code, detail=f"Exa API error: {response.text}")
            
            data = response.json()
            print(f"[ps] Got {len(data.get('results', []))} results from Exa", flush=True)
            
            # Format results
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", "Untitled"),
                    "url": item.get("url", ""),
                    "snippet": item.get("text", "") or item.get("snippet", "")
                })
            
            return SearchResult(results=results)
    
    except httpx.HTTPError as e:
        print(f"[ps] HTTP error in /search: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        print(f"[ps] ERROR in /search: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search-and-scrape", response_model=PatentText)
async def search_and_scrape_patent(query: SearchQuery):
    """Search for patent and scrape full text from Google Patents"""
    print(f"[ps] /search-and-scrape endpoint called with query: {query.query}", flush=True)
    
    # Use persistent sandbox
    sandbox, mcp_url, mcp_token = get_sandbox()
    
    try:
        client = OpenAI()
        
        with client.responses.stream(
            model="gpt-5.1",
            tools=[
                {
                    "type": "mcp",
                    "server_label": "exa",
                    "server_url": mcp_url,
                    "require_approval": "never",
                    "headers": {
                        "Authorization": f"Bearer {mcp_token}",
                    },
                },
                {
                    "type": "mcp",
                    "server_label": "firecrawl",
                    "server_url": mcp_url,
                    "require_approval": "never",
                    "headers": {
                        "Authorization": f"Bearer {mcp_token}",
                    },
                }
            ],
            input=(
                "You have access to Exa (for search) and Firecrawl (for scraping) MCP tools.\n\n"
                f'1. Use Exa search to find the Google Patents page for: "{query.query}". '
                "Search for patents.google.com URLs.\n"
                "2. Once you find the Google Patents URL (patents.google.com/patent/...), use Firecrawl's "
                "firecrawl_scrape tool to extract the full content from that URL. "
                "Use formats=['markdown'] and onlyMainContent=true for best results.\n"
                "3. From the scraped content, extract and return the patent information including: "
                "patent number, title, abstract, description, and claims.\n"
                "4. Format the output clearly in order (e.g., TITLE, ABSTRACT, DESCRIPTION, CLAIMS) but do not add any explanations, questions, or extra commentary.\n"
                "5. Return only the extracted patent text. Do not include any opening text, closing text, meta-discussion, or questions to the user."
            ),
        ) as stream:
            for event in stream:
                event_name = getattr(event, 'type', type(event))
                if "output_text" not in event_name:
                    print(f"[ps] EVENT: {event_name}", flush=True)
            
            final_response = stream.get_final_response()
            output_text = final_response.output_text
            print(f"[ps] Patent text extracted (length: {len(output_text)})", flush=True)
            return PatentText(text=output_text)
    
    except Exception as e:
        print(f"[ps] ERROR in /search-and-scrape: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape", response_model=PatentText)
async def scrape_url(scrape_request: ScrapeURL):
    """Scrape patent content from a given URL using Firecrawl API directly"""
    print(f"[ps] /scrape endpoint called with url: {scrape_request.url}", flush=True)
    
    try:
        # Call Firecrawl API directly for faster scraping
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ['FIRECRAWL_API_KEY']}",
                },
                json={
                    "url": scrape_request.url,
                    "formats": ["markdown"],
                    "onlyMainContent": True,
                },
                timeout=60.0,
            )
            
            if response.status_code != 200:
                print(f"[ps] Firecrawl API error: {response.status_code} - {response.text}", flush=True)
                raise HTTPException(status_code=response.status_code, detail=f"Firecrawl API error: {response.text}")
            
            data = response.json()
            markdown_content = data.get("data", {}).get("markdown", "")
            
            if not markdown_content:
                print("[ps] Warning: No markdown content returned from Firecrawl", flush=True)
                markdown_content = data.get("data", {}).get("content", "No content extracted")
            
            print(f"[ps] Scraped content (length: {len(markdown_content)})", flush=True)
            return PatentText(text=markdown_content)
    
    except httpx.HTTPError as e:
        print(f"[ps] HTTP error in /scrape: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        print(f"[ps] ERROR in /scrape: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/patent-to-specs", response_model=SpecsResponse)
async def patent_to_specs(patent: PatentText):
    """Convert patent text to implementation specs using OpenAI"""
    print(f"[ps] /patent-to-specs endpoint called (patent length: {len(patent.text)})", flush=True)
    
    try:
        # Read the patent2specs prompt
        with open("prompts/patent2specs.md", "r") as f:
            system_prompt = f.read()
        
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Convert this patent into implementation specs:\n\n{patent.text}"}
            ],
            temperature=0.7,
        )
        
        specs = response.choices[0].message.content
        print(f"[ps] Generated specs (length: {len(specs)})", flush=True)
        
        return SpecsResponse(specs=specs)
    
    except Exception as e:
        print(f"[ps] ERROR in /patent-to-specs: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/specs-to-code", response_model=CodeResponse)
async def specs_to_code(specs_input: SpecsResponse):
    """Convert specs to React code using OpenAI"""
    print(f"[ps] /specs-to-code endpoint called (specs length: {len(specs_input.specs)})", flush=True)
    
    try:
        # Read the specs2code prompt
        with open("prompts/specs2code.md", "r") as f:
            system_prompt = f.read()
        
        client = OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Convert these specs into React code:\n\n{specs_input.specs}"}
            ],
            temperature=0.7,
        )
        
        code = response.choices[0].message.content
        print(f"[ps] Generated code (length: {len(code)})", flush=True)
        
        return CodeResponse(code=code, specs=specs_input.specs)
    
    except Exception as e:
        print(f"[ps] ERROR in /specs-to-code: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/run-in-e2b", response_model=E2BPreviewResponse)
async def run_in_e2b(code_input: CodeResponse):
    """Run generated code in E2B sandbox and return preview URL"""
    print(f"[ps] /run-in-e2b endpoint called (code length: {len(code_input.code)})", flush=True)
    
    try:
        # Extract code from markdown if needed
        import re
        jsx_code = code_input.code
        code_block_match = re.search(r'```(?:jsx?|typescript|javascript)?\n([\s\S]*?)```', jsx_code)
        if code_block_match:
            jsx_code = code_block_match.group(1)
        
        # Create HTML template
        HTML_TEMPLATE = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Patent Demo</title>
    <style>
      body {{
        margin: 0;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #f8fafc;
        color: #1e293b;
        display: flex;
        align-items: stretch;
        min-height: 100vh;
      }}
      #root {{
        flex: 1;
        padding: 24px;
      }}
      .banner {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        padding: 8px 16px;
        background: rgba(255, 255, 255, 0.95);
        border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        font-size: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 10;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
      }}
      .banner span {{
        opacity: 0.7;
        color: #64748b;
      }}
      .banner strong {{
        font-weight: 600;
        color: #0f172a;
      }}
    </style>
    <script src="https://unpkg.com/react@18/umd/react.development.js" crossorigin></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js" crossorigin></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  </head>
  <body>
    <div class="banner">
      <span><strong>Patent Demo</strong> – Live Preview</span>
    </div>
    <div id="root" style="margin-top: 32px;"></div>
    <script type="text/babel">
{jsx_code}
      const rootElement = document.getElementById('root');
      if (typeof App === 'undefined') {{
        rootElement.innerHTML = "<pre style='color:#f97373'>Error: App component is not defined.</pre>";
      }} else {{
        const root = ReactDOM.createRoot(rootElement);
        root.render(React.createElement(App));
      }}
    </script>
  </body>
</html>
"""
        
        # Indent JSX code
        indented_jsx = "\n".join("      " + line for line in jsx_code.splitlines())
        html = HTML_TEMPLATE.format(jsx_code=indented_jsx)
        
        # Create E2B sandbox with 1 hour timeout
        import uuid
        sbx = Sandbox.create(timeout=3600)  # 1 hour
        sandbox_id = str(uuid.uuid4())
        print(f"[ps] Created sandbox {sandbox_id}", flush=True)
        
        # Write HTML file
        sbx.files.write("/home/user/index.html", html)
        
        # Start HTTP server in background (no timeout - let it run indefinitely)
        import time
        sbx.commands.run(
            "cd /home/user && python -m http.server 3000",
            background=True,
        )
        
        # Give the server a moment to start
        time.sleep(2)
        
        # Get public URL
        host = sbx.get_host(3000)
        url = f"https://{host}"
        
        # Store sandbox reference to keep it alive
        active_sandboxes[sandbox_id] = sbx
        print(f"[ps] Stored sandbox {sandbox_id} in active_sandboxes", flush=True)
        print(f"[ps] Active sandboxes count: {len(active_sandboxes)}", flush=True)
        print(f"[ps] E2B preview live at {url}", flush=True)
        
        return E2BPreviewResponse(url=url, sandbox_id=sandbox_id)
    
    except Exception as e:
        print(f"[ps] ERROR in /run-in-e2b: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/kill-sandbox")
async def kill_sandbox(request: SandboxKillRequest):
    """Kill an active E2B sandbox"""
    print(f"[ps] /kill-sandbox endpoint called for {request.sandbox_id}", flush=True)
    
    try:
        if request.sandbox_id in active_sandboxes:
            sbx = active_sandboxes[request.sandbox_id]
            sbx.kill()
            del active_sandboxes[request.sandbox_id]
            print(f"[ps] Killed sandbox {request.sandbox_id}", flush=True)
            return {"status": "killed", "sandbox_id": request.sandbox_id}
        else:
            return {"status": "not_found", "sandbox_id": request.sandbox_id}
    
    except Exception as e:
        print(f"[ps] ERROR in /kill-sandbox: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("[ps] Starting FastAPI server on http://0.0.0.0:8000", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
