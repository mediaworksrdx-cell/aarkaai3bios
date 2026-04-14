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
Action Input: {{"param": "value"}}

You will then receive an "Observation" with the result of the tool execution. 
Repeat this process until you have gathered all necessary context or finished all edits.

When you are completely finished, provide the final response to the user using this format:

Thought: <explain how the task is complete>
Final Answer: <your final answer to the user>

IMPORTANT: Do NOT output the text "Observation:" yourself. You must stop after "Action Input:".

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
"""

def process_task(query: str, context: str = "") -> str:
    """Run an agent loop until completion or max iterations."""
    
    # 1. Build tool descriptions
    tool_descs = []
    for name, tool in registry.tools.items():
        tool_descs.append(f"- {name}: {tool.description}")
    
    prompt = SYSTEM_PROMPT.format(tools="\n".join(tool_descs))
    
    if context:
        prompt += f"\n\nContext:\n{context}\n"
    
    prompt += f"\nRequest: {query}\n"
    
    MAX_LOOPS = 8
    last_action = {"name": None, "params": None}
    
    for loop in range(MAX_LOOPS):
        logger.info(f"Coordinator loop {loop+1}/{MAX_LOOPS}")
        
        # Stop generation when the model implies it's waiting for observation
        # Llama cpp will stop strictly when it encounters "Observation:"
        response = aarkaa_engine.generate_raw(
            prompt=prompt + "\nThought: ", 
            max_new_tokens=300,
            stop=["Observation:"]
        )
        
        full_response = "Thought: " + response.strip()
        logger.info(f"Model generated: {full_response}")
        
        # Check if we reached final answer or it's the last loop
        full_lower = full_response.lower()
        
        # 1. Did it output Final Answer?
        if "final answer:" in full_lower:
            match = re.search(r"final answer:\s*(.*)", full_response, re.IGNORECASE | re.DOTALL)
            ans = match.group(1).strip() if match else full_response
            for delimiter in [
                "\nThought:", "\nAction:", "Observation:", "\nthought:", "\naction:", 
                "\n--", "\nUser:", "\nAARKAA:", "\nRequest:", "[Recent Conversation]"
            ]:
                if delimiter.lower() in ans.lower():
                    ans = re.split(delimiter, ans, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            return ans
            
        # 2. Try to find a tool mention
        action_name = None
        for t in registry.tools.keys():
            if t.lower() in full_lower:
                action_name = t
                break
                
        # 3. If no tool is mentioned, the 3B model is just talking. 
        # Return what it said instead of forcing an error loop.
        if not action_name:
            if loop >= 2: # If it failed to use tools a few times, just return its text
                ans = full_response.replace("Thought:", "").strip()
                return ans
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
        if start != -1 and end != -1 and start < end:
            raw_json = full_response[start:end+1]
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
            observation = "Error: Invalid JSON object format. Action Input must be a valid JSON dictionary."
            prompt += f"\n{full_response}\nObservation: {observation}\n"
            continue
            
        # Prevent infinite repetition of exactly the same action
        if action_name == last_action["name"] and params == last_action["params"]:
            observation = "Error: You just tried this exact same action and got the previous observation. You MUST try something else or provide a Final Answer."
            prompt += f"\n{full_response}\nObservation: {observation}\n"
            continue
            
        last_action["name"] = action_name
        last_action["params"] = params
            
        logger.info(f"Executing tool {action_name} with params {params}")
        observation = registry.execute_tool(action_name, params)
        logger.info(f"Observation length: {len(observation)}")
        
        # Constrain observation size aggressively to prevent 4096 context window overflow
        if len(observation) > 800:
            observation = observation[:800] + "\n...[truncated for length]"
            
        prompt += f"\n{full_response}\nObservation: {observation}\n"
        
    return full_response.replace("Thought:", "").strip()  # Return best effort instead of "Task stopped"
