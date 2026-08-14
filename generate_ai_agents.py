import sys
sys.path.insert(0, '/workspace/aarkaai3b')
from skills.html.docs_generator import generate_pdf

html_content = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@page {
    size: A4;
    margin: 20mm;
}
body {
    font-family: Arial, sans-serif;
    color: #333;
    line-height: 1.6;
}
.page {
    page-break-after: always;
    position: relative;
}
.page:last-child {
    page-break-after: avoid;
}
h1 {
    color: #1e3a8a;
    border-bottom: 2px solid #3b82f6;
    padding-bottom: 8px;
    margin-top: 0;
}
h2 {
    color: #1e40af;
    margin-top: 24px;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 6px;
}
p {
    line-height: 1.7;
    text-align: justify;
}
ul {
    padding-left: 20px;
}
li {
    margin-bottom: 10px;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}
th {
    background: #1e3a8a;
    color: white;
    padding: 10px;
    text-align: left;
}
td {
    padding: 9px 10px;
    border-bottom: 1px solid #e5e7eb;
}
tr:nth-child(even) td {
    background: #f8fafc;
}
.callout {
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
    padding: 14px 18px;
    margin: 16px 0;
    border-radius: 0 4px 4px 0;
}
</style>
</head>
<body>

<!-- PAGE 1: Title & Overview -->
<div class="page">
  <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%) rotate(-45deg);font-size:60px;color:rgba(200,200,200,0.15);font-weight:bold;pointer-events:none;z-index:999;">CONFIDENTIAL</div>
  <h1>AI Agents: The Next Frontier of Autonomy</h1>
  <p>AI agents represent a paradigm shift from traditional, passive software systems to proactive, goal-oriented entities. An artificial intelligence agent is an autonomous system that perceives its environment through sensors, processes information using reasoning models (such as Large Language Models), and executes actions through actuators to achieve defined objectives.</p>
  <p>By combining reasoning, tool usage, planning, and memory, modern AI agents can execute complex multi-step workflows, collaborate in teams, and adapt dynamically to feedback.</p>
  
  <div class="callout">
    <strong>Key Characteristic:</strong> Unlike chat assistants that wait for user prompts at every turn, autonomous agents are given a high-level goal and determine their own execution path, choosing when to search the web, write code, query databases, or write reports.
  </div>
</div>

<!-- PAGE 2: Types of Agents -->
<div class="page">
  <h2>Architectural Classes of AI Agents</h2>
  <p>AI agents are classified by their reasoning depth and architectural complexity:</p>
  <ul>
    <li><strong>Simple Reflex Agents:</strong> Act solely on the current perception, ignoring historical context (condition-action rules).</li>
    <li><strong>Model-Based Reflex Agents:</strong> Maintain an internal state to track aspects of the environment that cannot be viewed currently.</li>
    <li><strong>Goal-Based Agents:</strong> Combine internal state tracking with goal definitions to evaluate which actions will achieve the objective.</li>
    <li><strong>Utility-Based Agents:</strong> Go beyond binary goal achievement to optimize for a continuous utility metric (e.g., maximizing efficiency, safety, or profit).</li>
    <li><strong>Learning Agents:</strong> Feature a learning element that allows them to adapt, discover new strategies, and improve performance over time.</li>
  </ul>
</div>

<!-- PAGE 3: Applications in Healthcare -->
<div class="page">
  <h2>AI Agents in Healthcare & Medicine</h2>
  <p>In healthcare, autonomous agents act as clinical co-pilots and patient monitors, assisting professionals and improving diagnostic accuracy:</p>
  
  <div class="callout">
    <strong>Diagnostic Assistance:</strong> Agents can continuously cross-reference a patient's electronic health records (EHR), lab results, and real-time vitals with medical literature to flag early warning signs of conditions like sepsis hours before clinical symptoms manifest.
  </div>
  
  <p>Furthermore, surgical planning agents help surgeons model procedures by simulating variations in patient anatomy, while administrative agents handle insurance pre-authorizations and clinical coding, freeing up valuable face-to-face time for patients.</p>
</div>

<!-- PAGE 4: Applications in Finance -->
<div class="page">
  <h2>AI Agents in Financial Services</h2>
  <p>The financial sector benefits heavily from high-speed reasoning and real-time monitoring capabilities of AI agents:</p>
  
  <table>
    <thead>
      <tr>
        <th>Use Case</th>
        <th>Agent Behavior</th>
        <th>Business Impact</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Algorithmic Trading</strong></td>
        <td>Monitors news feeds, social sentiment, and order books to execute trades.</td>
        <td>Capitalizes on micro-second market inefficiencies.</td>
      </tr>
      <tr>
        <td><strong>Fraud Detection</strong></td>
        <td>Evaluates transaction patterns and flags anomalies in real-time.</td>
        <td>Drastically reduces chargebacks and credit losses.</td>
      </tr>
      <tr>
        <td><strong>Portfolio Management</strong></td>
        <td>Rebalances assets based on macroeconomic indicators and client risk profiles.</td>
        <td>Delivers personalized, automated wealth management at scale.</td>
      </tr>
    </tbody>
  </table>
</div>

<!-- PAGE 5: Challenges & Future -->
<div class="page">
  <h2>Current Challenges & Future Outlook</h2>
  <p>Despite their massive potential, several key hurdles must be overcome before widespread agentic adoption:</p>
  <ul>
    <li><strong>Alignment & Safety:</strong> Ensuring agents do not take harmful actions or exploit loopholes in their goal definitions (reward hacking).</li>
    <li><strong>Hallucination & Reliability:</strong> Guarding against incorrect reasoning steps or false data retrieval that could derail a multi-step workflow.</li>
    <li><strong>State Management & Memory:</strong> Managing long-term memory and context windows across extended, multi-day executions.</li>
  </ul>
  <p>The future of AI lies in multi-agent systems, where specialized agents collaborate, challenge each other's assumptions (adversarial collaboration), and orchestrate complex global operations seamlessly.</p>
</div>

</body>
</html>'''

generate_pdf(html_content, 'ai_agents.pdf')
print('PDF generated successfully')
