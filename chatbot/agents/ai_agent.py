"""
Advanced AI Agent for Smart Finance Chatbot
Uses LLM as the main decision-maker and executor
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..tools.function_tools import ChatbotTools
from ..llm.gemini_client import gemini_client
from ..llm.ollama_client import ollama_client
from accounts.models import CURRENCY_SYMBOLS
import logging

logger = logging.getLogger(__name__)


class AIFinancialAgent:
    """AI-powered financial agent using LLM for decision making and execution"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.tools = ChatbotTools(user_id)
        self.conversation_history = []
        self.max_retries = 3

    def get_system_prompt(self) -> str:
        """Get the comprehensive system prompt for the LLM"""
        tools_list = self._format_tools_for_prompt()
        currency_code = getattr(self.tools.user, 'preferred_currency', 'USD')
        currency_sym = CURRENCY_SYMBOLS.get(currency_code, '$')

        return f"""You are an expert financial assistant AI. Your role is to help users manage their finances intelligently.

## IMPORTANT: Currency Settings
The user's currency is **{currency_code}** and the symbol is **{currency_sym}**.
You MUST use '{currency_sym}' for ALL monetary amounts in ALL your responses. Never use '$' unless the user's currency is USD.

## Your Core Responsibilities:
1. **Understand** what the user is asking for or requesting
2. **Decide** whether it's a question to answer or a task to perform
3. **Execute** if it's a task - use the available tools to complete it
4. **Respond** with clear, helpful information

## Available Tools:

You have access to these financial tools. When the user asks for something that requires a tool, USE IT IMMEDIATELY:

{tools_list}

## How to Use Tools:

When you need to use a tool, respond with ONLY the following format. Do not include any conversational text, emojis, or markdown code blocks around it:

TOOL_CALL
{{
  "tool_name": "tool_function_name",
  "parameters": {{"param1": value1, "param2": value2}}
}}
END_TOOL_CALL

You can make multiple tool calls in one response by including multiple blocks.

## Important Rules:

1. **ALWAYS execute tasks** - If user asks you to "add 300 to bike fund", don't just acknowledge it, USE THE TOOL
2. **Parse ambiguous requests** - Understand intent even if wording is unclear
3. **Provide context** - After executing tasks, explain what you did
4. **Ask for clarification** - Only if absolutely necessary
5. **Be proactive** - If a request seems incomplete, make reasonable assumptions and explain them

6. **Greeting** - If the user says "hi" or "hello", warmly introduce yourself as their Smart Finance Assistant and briefly list what you can do.

## Examples:

User: "add 300 to bike funds"
→ First call get_all_goals() to find goal IDs, then call add_goal_contribution with goal_name="bike" and amount=300
→ Or directly: add_goal_contribution(goal_name="bike", amount=300)
→ RESPOND: "✅ Added ₹300 to your bike fund. New total: ₹5,300 (60% complete)"

User: "Show my spending"
→ USE: get_spending_breakdown()
→ RESPOND: with formatted breakdown

User: "I want to save 5000 for a laptop"
→ USE: create_savings_goal(name="laptop", amount=5000)
→ RESPOND: "✅ Goal created! You need to save $5000 - that's about $416/month for 12 months"

User: "Find my bills"
→ USE: get_bills(days_ahead=30)
→ RESPOND: "You have 2 bills coming up: Electric ($50) due in 3 days, and Internet ($80) due in 10 days."

User: "Pay my electric bill"
→ USE: pay_bill(bill_id=123)
→ RESPOND: "✅ Successfully paid your Electric bill of $50."

User: "I spent $50 on food today"
→ USE: add_transaction(amount=50, transaction_type="expense", category_name="Food")
→ RESPOND: "✅ Added an expense of $50 for Food."

User: "I earned 1000 from freelance work"
→ USE: add_transaction(amount=1000, transaction_type="income", category_name="Freelance")
→ RESPOND: "✅ Awesome! I've logged $1000 as income under Freelance."

## Current User Financial Context:
"""

    def _format_tools_for_prompt(self) -> str:
        """Format available tools for the LLM prompt"""
        tools = self.tools.get_available_tools()
        formatted = ""

        for tool in tools:
            formatted += f"\n### {tool['name']}\n"
            formatted += f"**Description**: {tool['description']}\n"
            if tool["parameters"]:
                formatted += (
                    f"**Parameters**: {json.dumps(tool['parameters'], indent=2)}\n"
                )

        return formatted

    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response — handles multiple output formats."""
        tool_calls = []
        seen = set()  # deduplicate

        # ── Format 1: Strict TOOL_CALL { ... } END_TOOL_CALL block ──────────
        pattern_json = r"TOOL_CALL\s*(\{.*?\})\s*END_TOOL_CALL"
        for match in re.findall(pattern_json, response, re.DOTALL | re.IGNORECASE):
            try:
                tool_data = json.loads(match.strip())
                if "tool_name" in tool_data and "parameters" in tool_data:
                    key = (tool_data["tool_name"], str(sorted(tool_data["parameters"].items())))
                    if key not in seen:
                        seen.add(key)
                        tool_calls.append({"name": tool_data["tool_name"], "params": tool_data["parameters"]})
                        logger.debug(f"[Parser] JSON block → {tool_data['tool_name']}")
            except json.JSONDecodeError as e:
                logger.warning(f"[Parser] JSON parse error: {e}")

        # ── Format 2: Ollama/Mistral narrative: → USE: func(key=val, ...) ────
        # Matches patterns like:
        #   → USE: create_savings_goal(name="PC", target_amount=120000, ...)
        #   USE: func(...)
        pattern_use = r"(?:→\s*)?USE:\s*([a-zA-Z_]+)\s*\(([^)]*)\)"
        for m in re.finditer(pattern_use, response, re.IGNORECASE):
            func_name = m.group(1).strip()
            args_str = m.group(2).strip()
            params = {}
            # Parse key=value pairs, handling quoted strings and numbers
            for kv in re.finditer(r'(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[\w.,-]+)', args_str):
                k = kv.group(1)
                v = kv.group(2).strip("\"'")
                # Attempt numeric coercion
                try:
                    v = int(v.replace(",", ""))
                except ValueError:
                    try:
                        v = float(v.replace(",", ""))
                    except ValueError:
                        pass
                params[k] = v

            if func_name and params:
                key = (func_name, str(sorted(params.items())))
                if key not in seen:
                    seen.add(key)
                    tool_calls.append({"name": func_name, "params": params})
                    logger.debug(f"[Parser] USE: narrative → {func_name}({params})")

        return tool_calls


    def _execute_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single tool call"""
        logger.info(f"Executing tool: {tool_name} with params: {parameters}")

        try:
            result = self.tools.call_tool(tool_name, parameters)
            logger.debug(f"Tool result: {result}")
            return result
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"success": False, "error": str(e)}

    def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple tool calls and return results"""
        results = []

        for tool_call in tool_calls:
            result = self._execute_tool(tool_call["name"], tool_call["params"])
            results.append(
                {
                    "tool": tool_call["name"],
                    "params": tool_call["params"],
                    "result": result,
                }
            )

        return results

    def _format_tool_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Format tool execution results for the LLM to understand"""
        formatted = "\n\n## Tool Execution Results:\n\n"

        for item in tool_results:
            tool_name = item["tool"]
            result = item["result"]

            formatted += f"### {tool_name}\n"
            formatted += f"**Status**: {'✅ Success' if result.get('success') else '❌ Failed'}\n"

            if result.get("success"):
                # Show relevant success info
                if "message" in result:
                    formatted += f"**Result**: {result['message']}\n"

                # Show data if available
                for key in [
                    "spending",
                    "budgets",
                    "goals",
                    "transactions",
                    "accounts",
                    "total_balance",
                    "insights",
                ]:
                    if key in result and result[key]:
                        formatted += f"**{key.title()}**: {json.dumps(result[key], indent=2)[:500]}...\n"
            else:
                formatted += f"**Error**: {result.get('error', 'Unknown error')}\n"

            formatted += "\n"

        return formatted

    def process_message(self, user_message: str) -> Dict[str, Any]:
        """Process user message using AI agent flow"""

        logger.info(f"Processing message: {user_message}")

        # Add to conversation history
        self.conversation_history.append(
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        try:
            # Use LLM as the main decision maker
            response = self._agent_loop(user_message)

            # Add assistant response to history
            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {"success": True, "response": response}

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            error_response = f"Sorry, I encountered an error: {str(e)}"
            return {
                "success": False,
                "error": error_response,
                "response": error_response,
            }

    def _agent_loop(self, user_message: str) -> str:
        """Main agent loop - LLM decides what to do"""

        # Build system prompt with context
        system_prompt = self.get_system_prompt()

        # Add current financial context
        summary = self.tools.get_financial_summary()
        if summary.get("success"):
            sym = CURRENCY_SYMBOLS.get(getattr(self.tools.user, 'preferred_currency', 'USD'), '$')
            system_prompt += f"""
- Total Balance: {sym}{summary.get('total_balance', 0):.2f}
- Monthly Income: {sym}{summary.get('monthly_income', 0):.2f}
- Monthly Expenses: {sym}{summary.get('monthly_expenses', 0):.2f}
- Savings Rate: {summary.get('savings_rate', 0):.1f}%
"""

        # --- LLM Tier Resolution ---
        gemini_ok = gemini_client.enabled and gemini_client.is_available()
        ollama_ok = ollama_client.enabled and ollama_client.is_available()

        if gemini_ok:
            logger.info("[LLM] Using Gemini (primary)")
        elif ollama_ok:
            logger.info("[LLM] Gemini unavailable – falling back to Ollama (secondary)")
        else:
            logger.warning("[LLM] Both Gemini and Ollama unavailable – using regex fallback")
            return self._fallback_handler(user_message)

        attempt = 0
        while attempt < self.max_retries:
            attempt += 1
            logger.debug(f"Agent loop attempt {attempt}/{self.max_retries}")

            try:
                # Call LLM with system prompt
                llm_response = self._call_llm(system_prompt, user_message)

                if not llm_response:
                    logger.warning("LLM returned no response - using fallback handler")
                    return self._fallback_handler(user_message)

                # Parse tool calls from response
                tool_calls = self._parse_tool_calls(llm_response)

                # If tools need to be called
                if tool_calls:
                    logger.debug(f"Found {len(tool_calls)} tool calls")

                    # Execute all tools
                    tool_results = self._execute_tools(tool_calls)

                    # Format results for LLM
                    tool_results_text = self._format_tool_results(tool_results)

                    # Call LLM again to synthesize results into a response
                    final_response = self._call_llm(
                        system_prompt,
                        user_message,
                        context=f"Tool call results:\n{tool_results_text}",
                    )

                    # Clean up tool call syntax from response
                    final_response = re.sub(
                        r"(```[a-z]*\s*)?TOOL_CALL.*?END_TOOL_CALL(\s*```)?",
                        "",
                        final_response,
                        flags=re.DOTALL | re.IGNORECASE,
                    ).strip()
                    # Also strip Ollama/Mistral narrative lines (→ USE: / → RESPOND:)
                    final_response = re.sub(
                        r"^(?:→\s*)?(?:USE|RESPOND):\s*.*$",
                        "",
                        final_response,
                        flags=re.MULTILINE | re.IGNORECASE,
                    ).strip()

                    return (
                        final_response
                        if final_response
                        else self._generate_summary_from_results(tool_results)
                    )

                else:
                    # No tools needed, just return LLM response
                    return llm_response

            except Exception as e:
                logger.error(f"Agent loop error (attempt {attempt}): {e}")
                if attempt < self.max_retries:
                    continue
                else:
                    return (
                        f"I'm having trouble processing your request. Error: {str(e)}"
                    )

        return (
            "I couldn't process your request after multiple attempts. Please try again."
        )

    def _call_llm(
        self, system_prompt: str, user_message: str, context: str = ""
    ) -> Optional[str]:
        """Call the LLM with the given prompts — Gemini first, then Ollama."""

        full_context = f"System Instructions:\n{system_prompt}"
        if context:
            full_context += f"\n\n{context}"

        # --- Tier 1: Gemini ---
        if gemini_client.enabled and gemini_client.is_available():
            try:
                logger.debug("[LLM] Calling Gemini...")
                response = gemini_client.generate_response(
                    prompt=user_message,
                    context=full_context,
                    system_prompt=None,
                )
                if response:
                    logger.debug("[LLM] Gemini responded successfully.")
                    return response
                logger.warning("[LLM] Gemini returned empty response.")
            except Exception as e:
                logger.error(f"[LLM] Gemini error: {e}")

        # --- Tier 2: Ollama ---
        if ollama_client.enabled and ollama_client.is_available():
            try:
                logger.debug("[LLM] Calling Ollama...")
                response = ollama_client.generate_response(
                    prompt=user_message,
                    context=full_context,
                    system_prompt=None,
                )
                if response:
                    logger.debug("[LLM] Ollama responded successfully.")
                    return response
                logger.warning("[LLM] Ollama returned empty response.")
            except Exception as e:
                logger.error(f"[LLM] Ollama error: {e}")

        logger.warning("[LLM] All LLM tiers exhausted, returning None.")
        return None

    def _fallback_handler(self, user_message: str) -> str:
        """Fallback handler when LLM is not available - uses intelligent tool calling"""
        logger.info("Using fallback handler for: " + user_message)
        message_lower = user_message.lower()

        # Try to create a goal first (highest priority)
        creation_patterns = [
            r"(?:create|save|want to save|plan to save)\s+(?:\$|₹)?(\d+(?:[,\.]\d+)?)\s*(?:rs|usd|₹|\$)?\s+for\s+(?:a|an|the)?\s*([a-zA-Z\s]+)",
            r"(?:save|save up)\s+(?:\$|₹)?(\d+(?:[,\.]\d+)?)\s+(?:for)\s+([a-zA-Z\s]+)",
            r"goal.*?(?:\$|₹)?(\d+(?:[,\.]\d+)?)\s+(?:for)\s+([a-zA-Z\s]+)",
        ]
        
        for pattern in creation_patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(",", "").replace(".", "")
                    goal_name = match.group(2).strip().title()
                    
                    # Create the goal
                    result = self.tools.create_savings_goal(
                        goal_name=goal_name,
                        target_amount=float(amount_str),
                        target_date="2025-12-31",  # Default to end of year
                        category="Savings",
                        description=f"Saving for {goal_name}",
                    )
                    
                    if result.get("success"):
                        return f"✅ Goal created! You need to save ${amount_str} for {goal_name}. That's about ${float(amount_str)/12:.0f}/month for 12 months."
                    else:
                        logger.warning(f"Failed to create goal: {result.get('error')}")
                except Exception as e:
                    logger.error(f"Error creating goal: {e}")

        # Try to handle contribution/adding to goal
        contrib_patterns = [
            r"(?:add|contribute|deposit|put)\s+(?:\$|₹)?(\d+(?:[,\.]\d+)?)\s+(?:to|in|into)\s+(?:my\s+)?(?:the\s+)?([a-zA-Z\s]+?)\s*(?:goal|fund|funds)?$",
            r"(?:add|contribute)\s+(?:\$|₹)?(\d+(?:[,\.]\d+)?)\s+to\s+([a-zA-Z\s]+)",
        ]
        
        for pattern in contrib_patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(",", "").replace(".", "")
                    goal_name = match.group(2).strip()
                    
                    # Get all goals to find match
                    goals_result = self.tools.get_all_goals()
                    if goals_result.get("success"):
                        goals = goals_result.get("goals", [])
                        
                        # Try to find matching goal
                        matched_goal = None
                        goal_name_lower = goal_name.lower()
                        
                        for goal in goals:
                            if goal_name_lower in goal["name"].lower():
                                matched_goal = goal
                                break
                        
                        if matched_goal:
                            result = self.tools.add_goal_contribution(
                                goal_id=matched_goal["id"],
                                amount=float(amount_str),
                            )
                            
                            if result.get("success"):
                                return f"✅ Added ${amount_str} to {matched_goal['name']}! Progress: {result.get('progress', 0):.1f}%"
                            else:
                                logger.warning(f"Failed to add contribution: {result.get('error')}")
                        else:
                            return f"❌ No goal found for '{goal_name}'. Your active goals are:\n" + "\n".join([f"- {g['name']}" for g in goals]) if goals else "- No active goals yet."
                except Exception as e:
                    logger.error(f"Error adding contribution: {e}")

        # Try to handle adding transactions (income/expense)
        transaction_patterns = [
            r"(?:spent|paid|bought)\s+(?:\$|₹)?(\d+(?:[,\.]\d+)?)\s+(?:on|for)\s+([a-zA-Z\s]+)",
            r"(?:earned|got|received)\s+(?:\$|₹)?(\d+(?:[,\.]\d+)?)\s+(?:from|for)\s+([a-zA-Z\s]+)"
        ]
        
        for idx, pattern in enumerate(transaction_patterns):
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(",", "").replace(".", "")
                    category_name = match.group(2).strip().title()
                    
                    trans_type = "expense" if idx == 0 else "income"
                    
                    result = self.tools.add_transaction(
                        amount=float(amount_str),
                        transaction_type=trans_type,
                        category_name=category_name,
                        description=f"{trans_type.title()} for {category_name}"
                    )
                    
                    if result.get("success"):
                        return result.get("message")
                    else:
                        logger.warning(f"Failed to add transaction: {result.get('error')}")
                except Exception as e:
                    logger.error(f"Error adding transaction: {e}")

        # Handle savings goals request
        if any(
            word in message_lower for word in ["goal", "saving", "progress", "target"]
        ):
            goals_result = self.tools.get_all_goals()
            if goals_result.get("success"):
                goals = goals_result.get("goals", [])
                if not goals:
                    return "You don't have any active savings goals yet.\n\nWould you like to create one? Try saying:\n- 'I want to save 5000 for vacation'\n- 'Save 10000 for a laptop'"

                response = "🎯 **Your Savings Goals:**\n\n"
                for goal in goals:
                    progress = goal["progress"]
                    status = (
                        "✅" if progress >= 100 else "📈" if progress >= 50 else "⏳"
                    )
                    response += f"{status} **{goal['name']}**\n"
                    response += f"   ${goal['current_amount']:.2f} / ${goal['target_amount']:.2f} ({progress:.1f}%)\n"
                    response += f"   Target: {goal['target_date']}\n\n"

                return response

        # Handle spending request
        if any(
            word in message_lower
            for word in [
                "spending",
                "spent",
                "expenses",
                "analysis",
                "breakdown",
                "pattern",
                "most",
            ]
        ):
            spend_result = self.tools.get_spending_breakdown()
            if spend_result.get("success"):
                spending = spend_result.get("spending", {})

                if spending:
                    response = "📊 **Your Spending Breakdown (Last 30 days):**\n\n"
                    for category, amount in sorted(
                        spending.items(), key=lambda x: x[1], reverse=True
                    ):
                        response += f"- **{category}**: ${amount:.2f}\n"
                    return response
                else:
                    return "No spending data available for the last 30 days."

        # Handle income/expenses
        if any(
            word in message_lower
            for word in ["income", "expense", "earn", "earned", "money", "how much"]
        ):
            income_result = self.tools.get_income_vs_expenses()
            if income_result.get("success"):
                data = income_result
                return f"""💰 **Last 30 Days Summary:**
- Income: ${data["income"]:.2f}
- Expenses: ${data["expenses"]:.2f}
- Net: ${data["net"]:.2f}"""

        # Handle budget request
        if any(word in message_lower for word in ["budget", "limit", "budget"]):
            budget_result = self.tools.get_budget_status()
            if budget_result.get("success"):
                budgets = budget_result.get("budgets", {})
                if not budgets:
                    return "You don't have any active budgets yet."

                response = "📊 **Your Budget Status:**\n\n"
                for category, data in budgets.items():
                    status = (
                        "✅"
                        if data["status"] == "on_track"
                        else "🟡"
                        if data["status"] == "at_risk"
                        else "🔴"
                    )
                    response += f"{status} **{category}**: ${data['spent']:.2f}/${data['budget']:.2f} ({data['percentage']:.0f}%)\n"

                return response

        # Handle summary/overview request
        if any(
            word in message_lower
            for word in ["summary", "overview", "financial", "status"]
        ):
            summary = self.tools.get_financial_summary()
            if summary.get("success"):
                return f"""💰 **Your Financial Summary:**

- Total Balance: ${summary["total_balance"]:.2f}
- Monthly Income: ${summary["monthly_income"]:.2f}
- Monthly Expenses: ${summary["monthly_expenses"]:.2f}
- Net Monthly: ${summary["net_monthly"]:.2f}
- Savings Rate: {summary["savings_rate"]:.1f}%"""

        # Handle bill requests
        if any(word in message_lower for word in ["bill", "bills", "due"]):
            # Check if it's a pay request
            if "pay" in message_lower:
                # We do a basic find-and-pay for fallback
                bills_result = self.tools.get_bills()
                if bills_result.get("success"):
                    bills = bills_result.get("bills", [])
                    if not bills:
                        return "You don't have any pending bills to pay right now."
                    
                    # Try to find a bill name in the message
                    for bill in bills:
                        if bill["name"].lower() in message_lower:
                            pay_res = self.tools.pay_bill(bill["id"])
                            if pay_res.get("success"):
                                return pay_res.get("message")
                    
                    return "I couldn't identify which bill you want to pay. Your pending bills are:\n" + "\n".join([f"- {b['name']}: ${b['amount']}" for b in bills])
            else:
                bills_result = self.tools.get_bills()
                if bills_result.get("success"):
                    bills = bills_result.get("bills", [])
                    if not bills:
                        return "You don't have any pending or upcoming bills."
                    
                    response = "📅 **Your Upcoming Bills:**\n\n"
                    for b in bills:
                        status = "🔴" if b["status"] == "overdue" else "🟡"
                        response += f"{status} **{b['name']}**: ${b['amount']:.2f}\n"
                        response += f"   Due in {b['days_until_due']} days ({b['next_due_date']})\n\n"
                    return response

        # Default helpful response
        return """👋 **Hello! I'm your Smart Finance Assistant.**

I can help you manage your money intelligently. Here is what I can do:
1. **Create goals** - "Save 5000 for vacation"
2. **Add to goals** - "Add 500 to vacation fund"
3. **View goals** - "Show my savings goals"
4. **Log transactions** - "I spent $50 on food" or "I earned $1000 from freelance"
5. **Check spending** - "Show my spending"
6. **Income/Expenses** - "How much did I spend?"
7. **Budgets** - "What's my budget status?"
8. **Bills** - "Find my bills" or "Pay my electric bill"
9. **Financial overview** - "Show my financial summary"

What would you like to do today?"""

    def _generate_summary_from_results(self, tool_results: List[Dict[str, Any]]) -> str:
        """Generate a summary response from tool results"""
        summary = "✅ Done! Here's what I found:\n\n"

        for item in tool_results:
            result = item["result"]
            if result.get("success"):
                if "message" in result:
                    summary += f"• {result['message']}\n"

        return summary if len(summary) > 50 else "✅ Task completed successfully!"
