"""Financial chatbot agent using Gemini LLM with dynamic function calling"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any
from ..tools.function_tools import ChatbotTools
from ..llm.gemini_client import gemini_client
import logging

logger = logging.getLogger(__name__)


class FinancialChatbotAgent:
    """Intelligent financial chatbot agent with dynamic tool calling"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.tools = ChatbotTools(user_id)
        self.conversation_history = []

    def get_tools_context(self) -> str:
        """Get formatted list of available tools for LLM"""
        tools = self.tools.get_available_tools()
        context = "**Available Tools:**\n\n"

        for tool in tools:
            context += f"- `{tool['name']}`: {tool['description']}\n"
            if tool["parameters"]:
                context += f"  Parameters: {json.dumps(tool['parameters'])}\n"
            context += "\n"

        return context

    def get_user_context(self) -> str:
        """Get user's financial context"""
        summary = self.tools.get_financial_summary()

        if not summary["success"]:
            return "Unable to fetch user financial context."

        context = f"""
**User Financial Context:**
- Total Balance: ${summary.get("total_balance", 0):.2f}
- Monthly Income: ${summary.get("monthly_income", 0):.2f}
- Monthly Expenses: ${summary.get("monthly_expenses", 0):.2f}
- Net Monthly: ${summary.get("net_monthly", 0):.2f}
- Savings Rate: {summary.get("savings_rate", 0):.1f}%
"""
        return context

    def parse_tool_calls(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response

        Looks for patterns like:
        TOOL: tool_name
        PARAMS: {"param1": value1, "param2": value2}
        """
        tool_calls = []

        # Pattern to find TOOL: and PARAMS: blocks
        pattern = r"TOOL:\s*(\w+)\s*\nPARAMS:\s*({.*?})"
        matches = re.findall(pattern, response_text, re.DOTALL)

        for tool_name, params_str in matches:
            try:
                params = json.loads(params_str)
                tool_calls.append({"name": tool_name, "params": params})
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse params: {params_str}")

        return tool_calls

    def execute_tool_call(
        self, tool_name: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool call and return result"""
        result = self.tools.call_tool(tool_name, params)
        logger.info(f"Executed tool '{tool_name}' with result: {result}")
        return result

    def generate_smart_response(self, user_message: str) -> str:
        """Generate intelligent response using LLM with function calling"""

        # Build context for LLM
        tools_context = self.get_tools_context()
        user_context = self.get_user_context()

        system_prompt = f"""You are a helpful financial assistant chatbot. You help users manage their finances by:
- Creating and tracking savings goals
- Analyzing spending patterns
- Providing budget recommendations
- Offering personalized financial insights

You have access to the following tools to perform actions:

{tools_context}

{user_context}

**IMPORTANT Instructions:**
1. Analyze the user's message and determine what they want to do
2. If the user wants you to perform an action (create goal, check balance, etc.), use the appropriate tool
3. When using tools, respond with:
   TOOL: tool_name
   PARAMS: {{"param1": value, "param2": value}}
4. You can call multiple tools if needed
5. Always confirm what you're doing and provide helpful context
6. If the user wants something you can do, DO IT - don't just suggest it
7. Be conversational and friendly while being concise

Examples of when to use tools:
- User: "I want to save 12000 for bike" → Use create_savings_goal
- User: "Show me my spending" → Use get_spending_breakdown
- User: "How much have I spent this month?" → Use get_income_vs_expenses
- User: "Add 1000 to my bike fund" → Use add_goal_contribution"""

        # Try LLM first if enabled
        if gemini_client.enabled and gemini_client.is_available():
            try:
                logger.info("Using Gemini LLM for response generation")

                llm_response = gemini_client.generate_financial_response(
                    user_message, system_prompt, self.conversation_history
                )

                if llm_response:
                    # Check if response contains tool calls
                    tool_calls = self.parse_tool_calls(llm_response)

                    if tool_calls:
                        # Execute tools and get results
                        tool_results = []
                        response_text = llm_response

                        for tool_call in tool_calls:
                            result = self.execute_tool_call(
                                tool_call["name"], tool_call["params"]
                            )
                            tool_results.append(
                                {"tool": tool_call["name"], "result": result}
                            )

                        # Remove tool call syntax from response
                        response_text = re.sub(
                            r"TOOL:.*?PARAMS:.*?\n", "", response_text, flags=re.DOTALL
                        ).strip()

                        # Add tool results to response
                        if response_text or tool_results:
                            for tool_result in tool_results:
                                if tool_result["result"].get("success"):
                                    if "message" in tool_result["result"]:
                                        response_text += (
                                            f"\n\n{tool_result['result']['message']}"
                                        )
                                else:
                                    response_text += f"\n\n❌ Error in {tool_result['tool']}: {tool_result['result'].get('error', 'Unknown error')}"

                        return (
                            response_text
                            if response_text
                            else "✅ Done! Let me know if you need anything else."
                        )

                    return llm_response

            except Exception as e:
                logger.error(f"Error generating LLM response: {e}")
                logger.info("Falling back to intelligent tool inference")

        # Fallback: Intelligently infer tools from message
        logger.debug(f"Using intelligent tool inference for: {user_message}")
        message_lower = user_message.lower()

        # Try to extract amounts and goals - improved pattern
        goal_pattern = r"(save|budget|want|planning|need)\s+(?:to\s+)?([\d,\.]+)\s*(?:rs|usd|₹|\$)?\s+(?:for|to|towards)\s+(?:a|an)?\s*([a-zA-Z\s]+)"
        goal_match = re.search(goal_pattern, user_message, re.IGNORECASE)

        if goal_match:
            try:
                amount = float(goal_match.group(2).replace(",", ""))
                goal_name = goal_match.group(3).strip().rstrip(".,!?")

                result = self.execute_tool_call(
                    "create_savings_goal",
                    {"goal_name": goal_name, "target_amount": amount},
                )

                if result.get("success"):
                    return f"✅ {result.get('message', 'Goal created!')}\n\nYour goal is now active on your dashboard!"
                else:
                    return f"❌ Could not create goal: {result.get('error', 'Unknown error')}"
            except (ValueError, AttributeError):
                pass

        # Check for contribution requests - "add 1000 to bike fund", "add 300 in bike funds"
        # More flexible pattern to match various phrasings
        contrib_patterns = [
            r"(?:add|contribute|deposit)\s+(?:rs|usd|₹|\$)?\s*([\d,\.]+)(?:\s+(?:rs|usd|₹|\$))?\s+(?:to|in|into)\s+(?:the\s+)?(?:my\s+)?([a-zA-Z\s]+?)(?:\s+(?:goal|fund|funds))?(?:\s|$|\?)",
            r"(?:add|contribute|deposit)\s+(?:rs|usd|₹|\$)?\s*([\d,\.]+)(?:\s+(?:rs|usd|₹|\$))?\s+(?:to|in|into)\s+([a-zA-Z\s]+?)(?:\s+(?:goal|fund|funds))",
        ]

        contrib_match = None
        for pattern in contrib_patterns:
            contrib_match = re.search(pattern, user_message, re.IGNORECASE)
            if contrib_match:
                logger.debug(f"Matched contribution pattern: {pattern}")
                break

        if contrib_match:
            try:
                # Extract amount - handle both positions
                if contrib_match.group(1):
                    amount = float(
                        contrib_match.group(1).replace(",", "").replace(" ", "")
                    )
                    goal_search = (
                        contrib_match.group(2).strip().lower()
                        if len(contrib_match.groups()) > 1
                        else None
                    )
                else:
                    logger.warning("Could not extract amount from contribution request")
                    pass

                if not goal_search:
                    logger.warning(f"Could not extract goal name from: {user_message}")
                    pass

                logger.debug(
                    f"Contribution request: amount={amount}, goal={goal_search}"
                )

                # Find matching goal (get all goals first)
                goals_result = self.execute_tool_call("get_all_goals", {})
                logger.debug(f"Got goals: {goals_result}")

                if goals_result.get("success"):
                    goals = goals_result.get("goals", [])
                    if not goals:
                        return f"❌ You don't have any savings goals yet. Please create one first!\n\nTry saying: 'I want to save 5000 for a bike'"

                    logger.debug(
                        f"Searching for goal matching '{goal_search}' in {[g['name'] for g in goals]}"
                    )

                    # Find matching goal - be more flexible
                    matched_goal = None
                    for goal in goals:
                        goal_name_lower = goal["name"].lower()
                        # Check various matching strategies
                        if (
                            goal_search.strip() in goal_name_lower
                            or goal_name_lower in goal_search
                            or goal_name_lower.startswith(
                                goal_search.split()[0] if goal_search else ""
                            )
                        ):
                            matched_goal = goal
                            logger.debug(f"Matched goal: {goal['name']}")
                            break

                    if matched_goal:
                        result = self.execute_tool_call(
                            "add_goal_contribution",
                            {"goal_id": matched_goal["id"], "amount": amount},
                        )
                        if result.get("success"):
                            return f"✅ {result['message']}"
                        else:
                            return f"❌ Error adding contribution: {result.get('error', 'Unknown error')}"
                    else:
                        goal_names = ", ".join([g["name"] for g in goals])
                        return f"❌ Could not find a goal matching '{goal_search}'.\n\nYour active goals: {goal_names}\n\nUse the exact goal name to add a contribution."
                else:
                    logger.error(f"Failed to get goals: {goals_result}")
                    return "❌ Could not retrieve your goals. Please try again."
            except (ValueError, AttributeError, IndexError) as e:
                logger.error(f"Error processing contribution: {e}")
                pass

        # Handle spending/analysis requests
        if any(
            word in message_lower
            for word in [
                "spending",
                "spent",
                "expenses",
                "analysis",
                "pattern",
                "most",
                "breakdown",
                "category",
            ]
        ):
            spend_result = self.execute_tool_call("get_spending_breakdown", {})
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
                    return "No spending data available for the last 30 days. You may not have any expenses recorded yet."
            else:
                error = spend_result.get("error", "Unknown error")
                logger.error(f"Spending breakdown failed: {error}")
                return f"I couldn't retrieve your spending data. Error: {error}"

        # Handle income/expenses
        if any(
            word in message_lower
            for word in ["income", "expense", "earned", "much have i", "earn", "money"]
        ):
            income_result = self.execute_tool_call("get_income_vs_expenses", {})
            if income_result.get("success"):
                data = income_result
                return f"""💰 **Last 30 Days Summary:**
- Income: ${data["income"]:.2f}
- Expenses: ${data["expenses"]:.2f}
- Net: ${data["net"]:.2f}"""
            else:
                error = income_result.get("error", "Unknown error")
                logger.error(f"Income/expenses fetch failed: {error}")
                return f"I couldn't retrieve your income/expense data."

        # Handle goals/progress
        if any(
            word in message_lower for word in ["goal", "progress", "saving", "target"]
        ):
            goals_result = self.execute_tool_call("get_all_goals", {})
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
            else:
                return "I couldn't fetch your goals at this moment."

        # Handle budget queries
        if any(
            word in message_lower for word in ["budget", "limit", "how much", "spent"]
        ):
            budget_result = self.execute_tool_call("get_budget_status", {})
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
            else:
                return "I couldn't fetch your budget data."

        # Handle summary
        if any(
            word in message_lower
            for word in [
                "summary",
                "overview",
                "how am i",
                "financial",
                "overall",
                "status",
            ]
        ):
            summary = self.execute_tool_call("get_financial_summary", {})
            if summary.get("success"):
                return f"""💰 **Your Financial Summary:**

- Total Balance: ${summary["total_balance"]:.2f}
- Monthly Income: ${summary["monthly_income"]:.2f}
- Monthly Expenses: ${summary["monthly_expenses"]:.2f}
- Net Monthly: ${summary["net_monthly"]:.2f}
- Savings Rate: {summary["savings_rate"]:.1f}%

You're doing great! Keep monitoring your finances. 📊"""
            else:
                return "I couldn't fetch your financial summary."

        # Handle insights
        if any(
            word in message_lower
            for word in ["insights", "advice", "recommendations", "how can i", "how to"]
        ):
            insights_result = self.execute_tool_call("get_spending_insights", {})
            if insights_result.get("success"):
                insights = insights_result.get("insights", [])
                response = "💡 **Financial Insights & Recommendations:**\n\n"
                for insight in insights:
                    response += f"{insight}\n"
                return response

        # Default helpful response
        return self._get_helpful_suggestions()

    def _get_helpful_suggestions(self) -> str:
        """Provide helpful suggestions"""
        return """
💡 **I can help you with:**

1. **Create savings goals** - "I want to save 5000 for a vacation"
2. **Track spending** - "Show me my spending analysis" / "Where have I spent the most?"
3. **Add contributions** - "Add 1000 to my bike fund"
4. **View goals** - "What are my savings goals?" / "Show my progress"
5. **Check budgets** - "What's my budget status?"
6. **Get insights** - "How can I save more?" / "Give me advice"
7. **Financial summary** - "Show me my financial overview"
8. **Income/Expenses** - "How much have I earned/spent this month?"

What would you like to do?
"""

    def process_message(self, user_message: str) -> Dict[str, Any]:
        """Main method to process user messages"""
        self.conversation_history.append(
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        try:
            # Generate response
            response = self.generate_smart_response(user_message)

            self.conversation_history.append(
                {
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            return {"success": True, "response": response}
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_response = f"Sorry, I encountered an error: {str(e)}"
            return {
                "success": False,
                "error": error_response,
                "response": error_response,
            }
