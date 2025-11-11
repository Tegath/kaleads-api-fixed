The Boring Stuff That Automation Pros Don’t Share (But Should)
Tutorial
After burning through an obscene amount of token costs in my first month building client automations, I had no choice but to take token optimization seriously. These 8 insider strategies now save my clients thousands monthly while actually improving workflow performance - stuff that experienced builders know but rarely talk about openly.
Let’s use an email processing automation workflow by way of example:1. The Modular Agent Architecture
What most people do wrong: Build one massive AI Agent that does everything - analyzes, classifies, formats, and outputs in one $0.15 call.
What you should do instead: Break complex tasks into specialized micro-agents.
Before (expensive):Single AI Agent: "Analyze this email, determine 1) priority, 2) extract key info, 3) format response and suggest next actions"
Cost: $0.15 per email × 1000 emails = $150
After (optimized):Agent 1: "Is this urgent? Yes/No" (gpt-3.5-turbo, $0.02)
Agent 2: "Extract: sender, subject, key points" (gpt-4o-mini, $0.03)
Agent 3: "Format as JSON" (gpt-3.5-turbo, $0.01)
Total: $0.06 per email × 1000 emails = $60
Why this works: Each agent uses the cheapest model capable of its specific task. Plus, if one step fails, you only re-run that piece, not the entire expensive analysis.
Modular agents are easier to debug, test, and improve independently.2. The Token Preprocessing Technique
The problem: Feeding raw, bloated data into AI models burns tokens on irrelevant information.
The solution: Clean your data BEFORE it hits the AI.
My 3-step preprocessing pipeline:
Step 1: Eliminate irrelevant fields// Code node before AI Agent
const cleanData = items.map(item => ({
  content: item.body,           // Keep
  timestamp: item.created_at,   // Keep
  priority: item.priority       // Keep
  // Remove: metadata, internal_ids, formatting, etc.
}));
Step 2: Classify for model routing// Basic classification to route to appropriate model
if (item.content.length > 4000) {
  // Route to higher context model
  return { model: "gpt-4-turbo", data: item };
} else {
  // Use cheaper model for simple content
  return { model: "gpt-3.5-turbo", data: item };
}
Step 3: Summarize when possible
For long documents, use a cheap summarization pass first:Summarize Chain: "Extract key points in 100 words" → Main AI Agent
Instead of: Raw 2000-word document → Main AI Agent
Real impact: Reduced average tokens per call from 3,500 to 1,200. That's $0.10 to $0.035 per call.3. Batch Processing Magic
What beginners do: Process items one by one, repeating the system prompt each time.
What pros do: Batch items to amortize the system prompt cost.
The math that changed everything:
System prompt: 200 tokens
Processing 10 items individually: 200 × 10 = 2,000 tokens wasted
Processing 10 items in one batch: 200 × 1 = 200 tokens
The sweet spot on how many batch items per run really depends on your data and AI model used. The key is to strike a balance between context overload and token efficiency.
I speak more in-depth about it here.4. JSON Output Enforcement
Structured output is much more efficient than natural language for multi-step workflows.
Before (expensive):AI Output: "The email appears to be urgent based on the subject line containing 'ASAP' and the sender being from the CEO's office. I would recommend escalating this to high priority and routing it to the executive support team..."

Tokens: ~150
Next AI Agent: Has to parse this whole explanation
After (optimized):AI Output: {"urgency": "high", "reason": "CEO request", "route": "exec_support", "confidence": 0.95}

Tokens: ~25
Next AI Agent: Gets clean, structured input
Implementation using Structured Output Parser:System Prompt: "Return ONLY valid JSON. No explanations."
User Prompt: "Analyze email: [content]"
Output Schema: {
  "priority": "string",
  "category": "string",
  "action_needed": "boolean",
  "confidence": "number"
}
Compounding effect: Each subsequent AI Agent in your workflow processes the structured data faster and cheaper.5. Track Your Tokens
The nightmare scenario: Your AI Agent goes rogue and racks up a $500 OpenAI bill overnight.
The solution: Built-in cost tracking for every AI node.
What I track:
Tokens used per execution
Cost per workflow run
Daily/monthly spending limits
Model performance metrics
TLDR: Client appreciates cost transparency.
I walk you through how to track your tokens in this video6. Prompt Engineering for Cheaper Models
Most tasks can run on gpt-5-mini with the right prompting, instead of defaulting to gpt-5.
My model downgrade process:
Step 1: Build with gpt-5 to get desired output quality
Step 2: Copy that exact output as an example
Step 3: Rewrite prompt for gpt-5-mini using the gpt-5 output as a template
Example transformation:
Original gpt-5 prompt:"Analyze this customer feedback and provide insights"
Optimized gpt-5-mini prompt:"Act as a customer feedback analyst. Follow this exact format:

SENTIMENT: [Positive/Negative/Neutral]
KEY_ISSUES: [bullet list, max 3]
PRIORITY: [High/Medium/Low]
ACTION: [specific next step]

Example:
SENTIMENT: Negative
KEY_ISSUES:
• Slow response time
• Confusing interface
• Missing feature request
PRIORITY: High
ACTION: Escalate to product team within 24h

Now analyze: [feedback]"
Results: 85% of tasks now run successfully on gpt-5-mini at 1/10th the cost.7. Dynamic Model Selection
The game-changer: Use a cheap model to determine complexity, then route to the appropriate expensive model only when needed.
My 2-step routing system:
Step 1: Complexity Assessment (Basic LLM Chain)Prompt: "Rate complexity 1-10: [content preview]"
Model: gpt-5-mini ($0.001)
Output: Just a number
Step 2: Dynamic Routing (Set node + IF logic)// Set node determines model based on complexity
if (complexity <= 3) {
  return { model: "gpt-5-nano" };        // $0.001
} else if (complexity <= 7) {
  return { model: "gpt-5-mini" };          // $0.01
} else {
  return { model: "gpt-5" };          // $0.1
}
Real results: 70% of tasks now use the cheapest model, 20% use mid-tier, 10% use premium.
OpenRouter tip: Use their model routing API to automatically select the cheapest model that meets your quality threshold.
PS - I deep dive into these methods with concrete examples + show you how you can implement them here.