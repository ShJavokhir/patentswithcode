import os
import asyncio

from e2b import Sandbox
from openai import OpenAI
import dotenv

print("[ps] Loading environment from ../.env.local", flush=True)
dotenv.load_dotenv("../.env.local")
print("[ps] Environment loaded. EXA_API_KEY present:", "EXA_API_KEY" in os.environ, flush=True)

query = "Google Autocomplete/Suggestions"

async def main():
    print("[ps] Starting main()", flush=True)
    print("[ps] Creating Sandbox with MCP 'exa' and 'firecrawl'", flush=True)
    sandbox = Sandbox.create(
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
    print("[ps] Sandbox created", flush=True)

    try:
        print("[ps] Fetching MCP URL and token", flush=True)
        mcp_url = sandbox.get_mcp_url()
        mcp_token = sandbox.get_mcp_token()
        print("[ps] Got MCP URL and token", flush=True)

        print("[ps] Initializing OpenAI client", flush=True)
        client = OpenAI()
        print("[ps] OpenAI client initialized, sending responses.stream request", flush=True)

        # Use Responses API streaming + MCP tools (Exa for search, Firecrawl for scraping)
        with client.responses.stream(
            model="gpt-5-mini",
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
                f'1. Use Exa search to find the Google Patents page for the original "{query}" patent. '
                "Search for 'google patent multi touch original' or similar to find patents.google.com URLs.\n"
                "2. Once you find the Google Patents URL (patents.google.com/patent/...), use Firecrawl's "
                "firecrawl_scrape tool to extract the full content from that URL. "
                "Use formats=['markdown'] and onlyMainContent=true for best results.\n"
                "3. From the scraped content, extract and return the patent information including: "
                "patent number, title, abstract, description, and claims.\n"
                "4. Format the output clearly in order (e.g., TITLE, ABSTRACT, DESCRIPTION, CLAIMS) but do not add any explanations, questions, or extra commentary.\n"
                "5. Return only the extracted patent text. Do not include any opening text, closing text, meta-discussion, or questions to the user."
            ),
        ) as stream:
            print("[ps] Stream opened, iterating over events for progress", flush=True)
            for event in stream:
                # This will include tool call / tool result / output events
                event_name = getattr(event, 'type', type(event))
                if "output_text" not in event_name:
                    print(f"[ps] EVENT: {event_name}", flush=True)

            print("[ps] Stream completed, fetching final response", flush=True)
            final_response = stream.get_final_response()
            output_text = final_response.output_text
            print("[ps] Printing final output text", flush=True)
            print(output_text)
            with open("output.txt", "w") as f:
                f.write(output_text)

    except Exception as e:
        print(f"[ps] ERROR: {type(e).__name__}: {e}", flush=True)
        raise

    finally:
        # Clean up the sandbox
        print("[ps] Killing sandbox", flush=True)
        sandbox.kill()
        print("[ps] Sandbox killed, exiting main()", flush=True)


if __name__ == "__main__":
    print("[ps] __main__ entry, running asyncio.run(main())", flush=True)
    asyncio.run(main())
