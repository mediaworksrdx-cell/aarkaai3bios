"""
AARKAAI – Agent Coordinator
Manages the ReAct (Reasoning and Acting) loop using aarkaa_engine.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Dict, Any

from modules import aarkaa_engine
from modules.tools import registry

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are AARKAAI, an advanced multilingual agentic coordinator based on Claude Code. 
You can break down tasks and use external tools to read, write, and execute code.
Always provide your Final Answer in the same language the user writes in.

You have access to the following tools:
{tools}

You must solve the user's request using a strict Thought/Action/Observation loop.
Whenever you want to use a tool, you must output exactly this format:

Thought: <explain what you're thinking and why you need a tool>
Action: <ToolName>
Action Input: {{"param": "value"}} (IMPORTANT: This must be a single line of valid JSON with NO literal newlines)

You will then receive an "Observation" with the result of the tool execution. 
Repeat this process until you have gathered all necessary context or finished all edits.

When you are completely finished, provide the final response to the user using this format:

Thought: <explain how the task is complete>
Final Answer: <your final answer to the user>

IMPORTANT: 
1. Do NOT output the text "Observation:" yourself. You must stop after "Action Input:".
2. When answering calculation or math requests, you MUST use calculation tools (like running python in BashTool) to perform the math.
3. In your "Final Answer", you must explain the calculation in full detail step-by-step (e.g. showing CAGR formulas, long-hand multiplication layouts, tax rate steps) and use the exact values computed by the tools. Do not shorten or skip the explanations.
4. If the required numbers, exchange rates, or values are already provided in the "Context:" section of the prompt (e.g. stock prices or exchange rates), you MUST copy those values EXACTLY with all digits and decimal positions intact (do NOT round, truncate, or shift decimal points, e.g. if context says 25.85, you must write 25.85, not 2.58) directly into your calculation tool (e.g. `python -c 'print(1000 * 25.85)'`) instead of trying to write complex scripts to fetch them again.
5. SKILL TOOLS: When the task involves file formats (PDF, DOCX, XLSX, PPTX, Word, Excel, PowerPoint), document creation, web UI design, or any specialised domain, you SHOULD call ListSkillsTool first to discover available skills, then call GetSkillTool with the matching skill name to fetch detailed instructions. Follow the skill's instructions to complete the task.
6. WRITING SCRIPTS: When generating files using Python (such as HTML/weasyprint for PDF, python-docx for DOCX, or xlsxwriter/openpyxl for Excel), NEVER try to execute complex inline python blocks with `python3 -c` using BashTool. This fails due to shell quote escaping. Also, NEVER write Python code into a path ending in `.pdf`, `.docx`, `.xlsx`, or `.pptx` (e.g., `invoice.pdf`). Instead:
   a. Write the python code into a script file ending in `.py` (e.g., `generate_report.py`) using FileEditTool first.
   b. Execute that script file using BashTool (e.g., Action Input: {{"command": "python3 generate_report.py"}}).
7. FILE DOWNLOAD LINKS: When you successfully create a file (e.g. `report.pdf`, `data.xlsx`) in the workspace, you MUST provide a relative download link in the format `[Download report.pdf](/download/report.pdf)` (using the relative path `/download/{{{{filename}}}}`) in your Final Answer. Do NOT expose absolute server file paths (e.g. /home/ubuntu/.../workspace/report.pdf) or the server's public IP address. Do NOT output a placeholder download link if the script execution failed or has not run successfully.
8. HANDLING ERRORS: If a command execution or tool call fails, read the error output carefully, modify/fix your script using FileEditTool, and execute it again. Do NOT give up and return a placeholder or incomplete answer.
9. DOCUMENT FILENAMES: Always name the generated document (e.g. PDF, Word document, Excel spreadsheet, PowerPoint slides) and its generator script dynamically based on the specific topic or search keywords of the user's query (converted to lowercase, using underscores instead of spaces, e.g. if request is to create a PDF of AI startup research, name the script `generate_ai_startups.py` and the output document `ai_startups.pdf` instead of generic names like `report.pdf` or `invoice.pdf`). Derive this name dynamically from the user's request.
10. PDF CREATION — CRITICAL RULE: NEVER use `reportlab` to create PDFs. ReportLab produces plain, ugly PDFs with no real content. ALWAYS use the html skill + docs_generator.py approach (weasyprint). For ANY PDF task, your Python script MUST follow this exact pattern:

import sys
sys.path.insert(0, '/home/ubuntu/aarkaai3b')
from skills.html.docs_generator import generate_pdf

html_content = \"\"\"<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>Title</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; color: #222; }}
h1 {{ color: #1e3a8a; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; }}
h2 {{ color: #1e40af; margin-top: 28px; }}
p {{ line-height: 1.7; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th {{ background: #1e3a8a; color: white; padding: 10px; text-align: left; }}
td {{ padding: 9px 10px; border-bottom: 1px solid #e5e7eb; }}
tr:nth-child(even) td {{ background: #f8fafc; }}
.callout {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 14px 18px; margin: 16px 0; }}
</style></head>
<body>
<h1>Document Title Here</h1>
<p>Introduction paragraph with actual content...</p>
<h2>Section 1</h2>
<p>Section content here...</p>
<div class='callout'>Key insight or highlight box here.</div>
<h2>Data Table</h2>
<table><tr><th>Column A</th><th>Column B</th><th>Column C</th></tr>
<tr><td>Row 1A</td><td>Row 1B</td><td>Row 1C</td></tr>
</table>
</body></html>\"\"\"

generate_pdf(html_content, 'output_name.pdf')
print('PDF generated successfully')

Replace the content inside the html_content string with REAL, DETAILED content about the user's topic. The HTML MUST contain multiple sections, paragraphs, and tables — not just a heading.

11. CHARTS & IMAGES IN PDF: If the user's query requests charts or visual data, your Python script MUST use `matplotlib` (always call `import matplotlib; matplotlib.use('Agg')` at the very beginning of the script) to generate and save chart image files. To ensure the images render successfully in the final PDF, your script MUST read the generated chart image files, encode them into Base64 format (using `base64.b64encode`), and embed them directly inside the HTML using inline data URLs (e.g., `<img class='chart-img' src='data:image/png;base64,{{chart_base64_data}}'>`).
12. MULTI-PAGE & FONT SIZE REQUIREMENTS: If the user requests a minimum page count (e.g., 'minimum 6 pages'), your HTML code MUST partition the pages explicitly using a CSS page-break class (e.g., `.page {{ page-break-after: always; }}`) and wrap each page's content inside a `<div class='page'>` container. Ensure the font sizes are set to a highly readable level: body text `11.5px` to `12.5px`, headings `16px` to `22px`, and table elements `10.5px`. Write long, comprehensive paragraphs for each section so that the content naturally fills the page layout.
13. PYTHON ESCAPE NEWLINES: When writing Python scripts via FileEditTool that generate strings with newlines (e.g. `\n`), ALWAYS escape the newline as double-slash `\\n` (so it prints as `\n` in the script file) instead of a literal newline, to prevent Python SyntaxErrors.

--- Example Interaction ---
User Request: Calculate 2 + 2 by running python.

Thought: I need to write a quick python script to calculate 2+2 and run it.
Action: BashTool
Action Input: {{"command": "python -c 'print(2+2)'"}}
Observation: [stdout]
4
Exit code: 0

Thought: The command worked and the output is 4. I can now provide the final answer.
Final Answer: The result of 2 + 2 is 4.
---------------------------

--- Example PDF Skill Interaction ---
User Request: Create a PDF report about Python programming.

Thought: I need to create a PDF. I must use docs_generator.py (html skill) — NOT reportlab. I will write the script now.
Action: FileEditTool
Action Input: {{"path": "generate_python_report.py", "content": "import sys\\nsys.path.insert(0, '/home/ubuntu/aarkaai3b')\\nfrom skills.html.docs_generator import generate_pdf\\nhtml_content = '''<!DOCTYPE html><html><head><meta charset=\\"utf-8\\"><title>Python Report</title><style>body{{font-family:Arial,sans-serif;margin:40px;color:#222}}h1{{color:#1e3a8a;border-bottom:2px solid #3b82f6;padding-bottom:8px}}h2{{color:#1e40af;margin-top:28px}}p{{line-height:1.7}}table{{width:100%;border-collapse:collapse;margin:20px 0}}th{{background:#1e3a8a;color:white;padding:10px;text-align:left}}td{{padding:9px 10px;border-bottom:1px solid #e5e7eb}}tr:nth-child(even) td{{background:#f8fafc}}.callout{{background:#eff6ff;border-left:4px solid #3b82f6;padding:14px 18px;margin:16px 0}}</style></head><body><h1>Python Programming Report</h1><p>Python is a high-level, general-purpose programming language known for its simplicity and versatility. Created by Guido van Rossum in 1991, Python has become one of the most popular languages worldwide.</p><h2>Key Features</h2><div class=\\"callout\\">Python emphasizes readability and simplicity, making it ideal for beginners and experts alike.</div><p>Python supports multiple programming paradigms including procedural, object-oriented, and functional programming. It has a rich standard library and a vibrant ecosystem of third-party packages.</p><h2>Popular Libraries</h2><table><tr><th>Library</th><th>Purpose</th><th>Version</th></tr><tr><td>NumPy</td><td>Numerical computing</td><td>1.26</td></tr><tr><td>Pandas</td><td>Data analysis</td><td>2.0</td></tr><tr><td>Flask</td><td>Web framework</td><td>3.0</td></tr><tr><td>TensorFlow</td><td>Machine learning</td><td>2.15</td></tr></table><h2>Conclusion</h2><p>Python continues to dominate in data science, web development, automation, and AI/ML applications due to its clear syntax and powerful ecosystem.</p></body></html>'''\\ngenerate_pdf(html_content, 'python_report.pdf')\\nprint('PDF generated successfully')"}}
Observation: Successfully wrote to generate_python_report.py

Thought: Now I will run the script to generate the PDF using BashTool.
Action: BashTool
Action Input: {{"command": "python3 generate_python_report.py"}}
Observation: PDF generated successfully
Exit code: 0

Thought: The PDF was generated successfully. I will provide the download link.
Final Answer: I have created a professional PDF report about Python programming. Download it here: [Download python_report.pdf](/download/python_report.pdf)
---------------------------
"""

def stream_task(query: str, context: str = ""):
    """Run an agent loop until completion or max iterations, yielding status updates."""
    # 1. Build tool descriptions
    tool_descs = []
    for name, tool in registry.tools.items():
        tool_descs.append(f"- {name}: {tool.description}")
    
    prompt = SYSTEM_PROMPT.format(tools="\n".join(tool_descs))
    
    if context:
        prompt += f"\n\nContext:\n{context}\n"
    
    prompt += f"\nRequest: {query}\n"
    
    MAX_LOOPS = 10
    executed_actions = set()
    next_prefix = ""
    
    for loop in range(MAX_LOOPS):
        logger.info(f"Coordinator loop {loop+1}/{MAX_LOOPS}")
        yield "status", f"Thinking... (Step {loop+1})"
        
        # Stop generation when the model implies it's waiting for observation or template breakout
        response = aarkaa_engine.generate_raw(
            prompt=prompt + "\nThought: " + next_prefix, 
            max_new_tokens=2048,
            stop=["Observation:", "---------------------------", "User Request:", "\nUser Request:", "---"]
        )
        
        # Format the model's output cleanly. Check if it already wrote "Thought:"
        raw_resp = response.strip()
        if next_prefix:
            full_response = "Thought: " + next_prefix + raw_resp
            next_prefix = ""
        else:
            if raw_resp.lower().startswith("thought:"):
                full_response = raw_resp
            else:
                full_response = "Thought: " + raw_resp
            
        logger.info(f"Model generated: {full_response}")
        
        # Check if we reached final answer or it's the last loop
        full_lower = full_response.lower()
        
        # 1. Did it output Final Answer?
        if "final answer:" in full_lower:
            match = re.search(r"final answer:\s*(.*)", full_response, re.IGNORECASE | re.DOTALL)
            ans = match.group(1).strip() if match else full_response
            for delimiter in [
                "\nThought:", "\nAction:", "Observation:", "\nthought:", "\naction:", 
                "\n--", "\nUser:", "\nAARKAA:", "\nRequest:", "[Recent Conversation]",
                "---------------------------", "User Request:", "---"
            ]:
                if delimiter.lower() in ans.lower():
                    ans = re.split(delimiter, ans, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            yield "final", ans
            return
            
        action_name = None
        action_match = re.search(r"Action:\s*(\w+)", full_response, re.IGNORECASE)
        if action_match:
            action_candidate = action_match.group(1).strip()
            # Try exact match first
            for t in registry.tools.keys():
                if t.lower() == action_candidate.lower():
                    action_name = t
                    break
            # Fallback to fuzzy substring match if exact match fails
            if not action_name:
                for t in registry.tools.keys():
                    t_low = t.lower()
                    c_low = action_candidate.lower()
                    if c_low in t_low or t_low in c_low:
                        action_name = t
                        break
                
        # 3. If no tool is mentioned, the 3B model is just talking. 
        # Return what it said instead of forcing an error loop.
        if not action_name:
            if loop >= 1: # If it failed to use tools or is just outputting text, let's treat it as the final answer
                ans = full_response.replace("Thought:", "").strip()
                yield "final", ans
                return
            else:
                prompt += f"\n{full_response}\nObservation: Error: You must specify an Action (e.g. Action: BashTool) or a Final Answer.\n"
                continue

        # 4. Try to find JSON for the tool
        # Start searching for '{' only AFTER 'Action Input:' to avoid matching python code in Thoughts
        action_input_idx = full_lower.find("action input:")
        if action_input_idx != -1:
            start = full_response.find("{", action_input_idx)
        else:
            start = full_response.find("{")
            
        end = full_response.rfind("}")
        
        params = None
        raw_json = ""
        if start != -1 and end != -1 and start < end:
            raw_json = full_response[start:end+1]
            # Self-heal double curly braces if generated by the model
            if raw_json.startswith("{{") and raw_json.endswith("}}"):
                raw_json = raw_json[1:-1]
            try:
                params = json.loads(raw_json)
            except Exception:
                try:
                    import ast
                    params = ast.literal_eval(raw_json)
                    if not isinstance(params, dict):
                        raise ValueError()
                except Exception as e:
                    pass
                    
        if params is None:
            if action_name == "BashTool":
                # Fallback for unescaped newlines in BashTool commands
                m = re.search(r'"command"\s*:\s*"(.*?)"\s*\}?$', raw_json, re.DOTALL)
                if m:
                    params = {"command": m.group(1).replace('\\"', '"').replace('\\n', '\n')}
            elif action_name == "FileEditTool":
                # Fallback for unescaped quotes inside FileEditTool content
                path_match = re.search(r'"path"\s*:\s*"([^"]+)"', raw_json)
                if path_match:
                    path = path_match.group(1)
                    # Locate "content": "
                    content_start_match = re.search(r'"content"\s*:\s*"', raw_json)
                    if content_start_match:
                        start_idx = content_start_match.end()
                        # Check if path is before content
                        path_idx = raw_json.find('"path"')
                        if path_idx != -1 and path_idx < start_idx:
                            remaining = raw_json[start_idx:].strip()
                            if remaining.endswith("}"):
                                remaining = remaining[:-1].strip()
                            if remaining.endswith('"') or remaining.endswith("'"):
                                remaining = remaining[:-1]
                            content = remaining.replace('\\"', '"').replace('\\n', '\n')
                            params = {"path": path, "content": content}
                        else:
                            # Path is after content
                            m_end = re.search(r',\s*"path"', raw_json[start_idx:])
                            if m_end:
                                end_idx = start_idx + m_end.start()
                            else:
                                end_idx = -1
                            if end_idx != -1:
                                remaining = raw_json[start_idx:end_idx].strip()
                                if remaining.endswith('"') or remaining.endswith("'"):
                                    remaining = remaining[:-1]
                                content = remaining.replace('\\"', '"').replace('\\n', '\n')
                                params = {"path": path, "content": content}

        if params is None:
            observation = "Error: Invalid JSON object format. Action Input must be a valid JSON dictionary on a single line."
            prompt += f"\n{full_response}\nObservation: {observation}\n"
            continue
            
        # Prevent infinite repetition of the same action across the history
        action_key = (action_name, json.dumps(params, sort_keys=True))
        if action_key in executed_actions and action_name not in ["BashTool", "FileReadTool"]:
            if action_name == "GetSkillTool":
                observation = "Error: You already loaded this skill document. DO NOT call GetSkillTool or ListSkillsTool again. Proceed to write and execute the Python code to generate the file using BashTool."
                next_prefix = "I already loaded the skill instructions. I will now write the python script using FileEditTool to generate the file. "
            elif action_name == "ListSkillsTool":
                observation = "Error: You already listed the skills. You know the 'pdf' skill exists. Call GetSkillTool or write the Python code to make the file using BashTool."
                next_prefix = "I already listed the skills. I will now use FileEditTool to generate the file. "
            elif action_name == "FileEditTool":
                observation = "Error: You already edited/created this file with this exact content. Writing the same content again will not change anything. Write a python script using FileEditTool first, and then execute it via BashTool to generate the document."
                next_prefix = "I already wrote this file. I will now run it using BashTool. "
            else:
                observation = "Error: You already executed this exact Action and Action Input in a previous step. To prevent infinite loops, you are blocked from repeating it. Please change your approach (e.g. check for errors, write a proper python script to a file instead of inline, or run a different command)."
                next_prefix = "I already tried that action. I will change my approach and "
            prompt += f"\n{full_response}\nObservation: {observation}\n"
            continue
            
        executed_actions.add(action_key)
            
        yield "status", f"Running {action_name}..."
        logger.info(f"Executing tool {action_name} with params {params}")
        observation = registry.execute_tool(action_name, params)
        logger.info(f"Observation length: {len(observation)}")
        
        # Constrain observation size to prevent context window overflow
        if len(observation) > 1000:
            observation = observation[:1000] + "\n...[truncated for length]"
            
        # VERY IMPORTANT: Update prompt context with the Thought + Action + Observation correctly
        prompt += f"\n{full_response}\nObservation: {observation}\n"
        
    # Final fallback if loops exhausted
    clean_ans = full_response.replace("Thought:", "").strip()
    if "final answer:" in clean_ans.lower():
        clean_ans = re.sub(r'(?i)final answer:\s*', '', clean_ans).strip()
    yield "final", clean_ans



def process_task(query: str, context: str = "") -> str:
    """Run an agent loop until completion or max iterations and return final answer."""
    final_ans = ""
    for event_type, data in stream_task(query, context):
        if event_type == "final":
            final_ans = data
    return final_ans
