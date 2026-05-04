import re, json
from .llm import LLMService
from .rag import RAGService
from .tools import call_tool
from ..models.schemas import ToolCall

# Fields required to complete a booking
BOOKING_FIELDS = ["name", "mobile", "address", "pincode", "service_type"]
VALID_SERVICES = ["installation", "repair", "amc", "gas_refill"]

# Human-friendly labels for asking about missing fields
FIELD_PROMPTS = {
    "name": "your full name",
    "mobile": "your mobile number (10 digits)",
    "address": "your full address",
    "pincode": "your area pincode",
    "service_type": f"the type of service you need ({', '.join(VALID_SERVICES)})",
}


class AgentPipeline:
    def __init__(self):
        self.llm = LLMService()
        self.rag = RAGService()

    # ------------------------------------------------------------------
    # Extract booking details using regex + simple parsing (more reliable
    # than asking the small LLM to produce JSON).
    # ------------------------------------------------------------------
    def _extract_booking_details(self, text: str) -> dict:
        details = {}
        text_lower = text.lower()

        # --- service_type ---
        for svc in VALID_SERVICES:
            if svc in text_lower:
                details["service_type"] = svc
                break
        # common synonyms
        if "service_type" not in details:
            if "install" in text_lower:
                details["service_type"] = "installation"
            elif "repair" in text_lower or "fix" in text_lower or "not working" in text_lower:
                details["service_type"] = "repair"
            elif "amc" in text_lower or "annual" in text_lower or "maintenance" in text_lower:
                details["service_type"] = "amc"
            elif "gas" in text_lower or "refill" in text_lower or "coolant" in text_lower:
                details["service_type"] = "gas_refill"

        # --- mobile ---
        mob = re.search(r'(?:\+91[\s-]?)?([6-9]\d{9})\b', text)
        if mob:
            details["mobile"] = mob.group(0).strip()

        # --- pincode ---
        pin = re.search(r'\b(\d{6})\b', text)
        if pin and pin.group(1) != details.get("mobile", "")[-6:]:
            details["pincode"] = pin.group(1)

        # --- name (try LLM only for name/address since regex is unreliable) ---
        # We'll also try a quick LLM extraction as fallback
        try:
            llm_details = self._extract_booking_details_llm(text)
            for field in BOOKING_FIELDS:
                if field not in details and llm_details.get(field):
                    details[field] = llm_details[field]
        except Exception:
            pass

        return details

    def _extract_booking_details_llm(self, text: str) -> dict:
        prompt = (
            "Extract these fields from the conversation as JSON: name, mobile, address, pincode, service_type.\n"
            "Valid service_types: installation, repair, amc, gas_refill.\n"
            "If a field is not mentioned, set it to null. Output ONLY the JSON object.\n"
            f"Text: {text}"
        )
        res = self.llm.complete([{"role": "user", "content": prompt}])
        try:
            s = res[res.find('{'):res.rfind('}') + 1]
            return json.loads(s)
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Build a friendly message asking for missing booking fields
    # ------------------------------------------------------------------
    def _build_missing_fields_response(self, details: dict, service_type: str = None) -> str:
        missing = [f for f in BOOKING_FIELDS if not details.get(f)]

        svc_label = service_type or details.get("service_type", "AC service")
        greeting = f"I'd be happy to help you book an **{svc_label}** appointment! 🛠️\n\n"

        if not missing:
            return None  # All fields present — proceed to booking

        if len(missing) == len(BOOKING_FIELDS) - (1 if details.get("service_type") else 0):
            # First message — ask for everything
            return (
                f"{greeting}"
                "To schedule your appointment, I'll need a few details:\n\n"
                "1. 📛 **Full Name**\n"
                "2. 📱 **Mobile Number**\n"
                "3. 🏠 **Full Address**\n"
                "4. 📍 **Area Pincode**\n"
                + (f"5. 🔧 **Service Type** ({', '.join(VALID_SERVICES)})\n" if not details.get("service_type") else "")
                + "\nPlease provide these details and I'll get your appointment booked right away!"
            )
        else:
            # Some fields collected, ask for remaining
            still_need = [FIELD_PROMPTS[f] for f in missing]
            return (
                "Thanks! I still need the following to complete your booking:\n\n"
                + "\n".join([f"• {item}" for item in still_need])
                + "\n\nPlease provide these details."
            )

    # ------------------------------------------------------------------
    # Main pipeline
    # ------------------------------------------------------------------
    def run(self, query: str, history: list):
        q_lower = query.lower()

        # --- Intent detection ---
        intent = "general"
        if any(kw in q_lower for kw in ["book", "appointment", "install", "repair", "fix", "amc", "gas refill", "schedule", "service needed"]):
            intent = "appointment"
        elif any(kw in q_lower for kw in ["status", "ticket", "tkt", "track", "where is", "check my"]):
            intent = "ticket_status"
        elif any(kw in q_lower for kw in ["escalate", "human", "agent", "talk to", "speak to", "real person"]):
            intent = "escalation"

        # Also check if we're in the middle of a booking conversation
        if intent == "general" and history:
            last_bot = next((h["content"] for h in reversed(history) if h.get("role") == "bot"), "")
            if any(phrase in last_bot.lower() for phrase in ["to complete your booking", "i'll need a few details", "mobile number", "full name", "full address", "area pincode"]):
                intent = "appointment"

        tool_calls = []
        tool_outputs = []

        # --- Appointment booking flow ---
        if intent == "appointment":
            # Gather context from full conversation
            ctx = " ".join([h["content"] for h in history[-6:]]) + " " + query
            details = self._extract_booking_details(ctx)

            missing = [f for f in BOOKING_FIELDS if not details.get(f)]

            if not missing:
                # All details present — book it!
                try:
                    res = call_tool("book_appointment", {
                        "name": details["name"],
                        "mobile": details["mobile"],
                        "address": details["address"],
                        "pincode": details["pincode"],
                        "service_type": details["service_type"],
                    })
                    tool_calls.append(ToolCall(name="book_appointment", arguments=details, result=res))
                    tool_outputs.append(json.dumps(res))

                    # Build a nice confirmation message directly
                    answer = (
                        f"✅ **Appointment Booked Successfully!**\n\n"
                        f"📋 **Ticket ID:** {res['ticket_id']}\n"
                        f"🔧 **Service:** {details['service_type'].replace('_', ' ').title()}\n"
                        f"👨‍🔧 **Technician:** {res['technician']}\n"
                        f"📅 **Scheduled:** {res['date']}\n"
                        f"📊 **Status:** {res['status'].title()}\n\n"
                        f"You can track your appointment anytime by asking me:\n"
                        f'*"Check status of {res["ticket_id"]}"*'
                    )
                    return {"answer": answer, "sources": [], "tool_calls": tool_calls, "intent": intent}
                except Exception as e:
                    return {"answer": f"Sorry, there was an error booking your appointment: {str(e)}", "sources": [], "tool_calls": [], "intent": intent}
            else:
                # Ask for missing details
                svc = None
                for s in VALID_SERVICES:
                    if s in q_lower or s in " ".join([h.get("content", "") for h in history]).lower():
                        svc = s
                        break
                if "install" in q_lower:
                    svc = "installation"
                response = self._build_missing_fields_response(details, svc)
                return {"answer": response, "sources": [], "tool_calls": [], "intent": intent}

        # --- Ticket status flow ---
        elif intent == "ticket_status":
            m = re.search(r'TKT-\d+', query, re.IGNORECASE)
            if m:
                res = call_tool("get_ticket_status", {"ticket_id": m.group(0).upper()})
                tool_calls.append(ToolCall(name="get_ticket_status", arguments={"ticket_id": m.group(0).upper()}, result=res))
                tool_outputs.append(json.dumps(res))

                if res.get("status") == "not_found":
                    answer = f"❌ Ticket **{m.group(0).upper()}** was not found. Please double-check the ticket ID."
                else:
                    answer = (
                        f"📋 **Ticket Status: {m.group(0).upper()}**\n\n"
                        f"🔧 **Service:** {res.get('service', 'N/A').replace('_', ' ').title()}\n"
                        f"👨‍🔧 **Technician:** {res.get('tech', 'Not assigned')}\n"
                        f"📅 **Scheduled:** {res.get('date', 'TBD')}\n"
                        f"📊 **Status:** {res.get('status', 'Unknown').replace('_', ' ').title()}\n"
                    )
                    if res.get("arrival_date"):
                        answer += f"🚗 **Arrival Date:** {res['arrival_date']}\n"
                    if res.get("notes"):
                        answer += f"📝 **Notes:** {res['notes']}\n"
                return {"answer": answer, "sources": [], "tool_calls": tool_calls, "intent": intent}
            else:
                return {
                    "answer": "I can check your ticket status! Please provide your **Ticket ID** (e.g., TKT-123456).",
                    "sources": [], "tool_calls": [], "intent": intent
                }

        # --- General query — use RAG + LLM ---
        chunks = self.rag.retrieve(query)
        ctx_str = "\n".join([c["content"] for c in chunks])

        sys_prompt = (
            "You are FrostGuard AC Services customer support assistant. "
            "You help customers with AC installation, repair, AMC, and gas refill services. "
            "Be helpful, friendly, and concise. "
            "If the customer wants to book a service, tell them to say 'Book AC installation' or 'Book AC repair'. "
            "FrostGuard services: Installation (₹1500), Repair (₹500 + parts), AMC (₹2500/year), Gas Refill (₹2000). "
            "Warranty: Installation 30 days, Repair 90 days parts & labor."
        )
        msgs = [{"role": "system", "content": sys_prompt}]
        if ctx_str:
            msgs.append({"role": "system", "content": f"Knowledge:\n{ctx_str}"})
        msgs.extend([{"role": h["role"], "content": h["content"]} for h in history[-4:]])
        msgs.append({"role": "user", "content": query})

        ans = self.llm.complete(msgs)
        return {"answer": ans, "sources": chunks, "tool_calls": tool_calls, "intent": intent}
