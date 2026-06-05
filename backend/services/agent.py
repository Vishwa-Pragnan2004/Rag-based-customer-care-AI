import re, json, logging
from services.llm import LLMService
from services.rag import RAGService
from services.tools import call_tool
from models.schemas import ToolCall

logger = logging.getLogger(__name__)

# Fields required to complete a booking
BOOKING_FIELDS = ["name", "mobile", "address", "pincode", "service_type"]
VALID_SERVICES = ["installation", "repair", "amc", "gas_refill"]

# Human-friendly labels for asking about missing fields
FIELD_PROMPTS = {
    "name": "your full name",
    "mobile": "your mobile number (10 digits)",
    "address": "your full address",
    "pincode": "your area pincode (6 digits)",
    "service_type": f"the type of service you need ({', '.join(VALID_SERVICES)})",
}


class AgentPipeline:
    def __init__(self):
        self.llm = LLMService()
        self.rag = RAGService()

    # ------------------------------------------------------------------
    # Extract booking details using PURE REGEX — no LLM dependency.
    # ------------------------------------------------------------------
    def _extract_booking_details(self, text: str) -> dict:
        details = {}
        text_lower = text.lower()

        # === SERVICE TYPE ===
        for svc in VALID_SERVICES:
            if svc in text_lower:
                details["service_type"] = svc
                break
        if "service_type" not in details:
            if "install" in text_lower:
                details["service_type"] = "installation"
            elif any(w in text_lower for w in ["repair", "fix", "not working", "broken"]):
                details["service_type"] = "repair"
            elif any(w in text_lower for w in ["amc", "annual", "maintenance"]):
                details["service_type"] = "amc"
            elif any(w in text_lower for w in ["gas", "refill", "coolant"]):
                details["service_type"] = "gas_refill"

        # === MOBILE NUMBER ===
        # Match 10-digit Indian mobile numbers, with or without +91 prefix
        mob_match = re.search(r'(?:\+91[\s\-]?)?(\d[\s\-]?)?\b([6-9]\d{9})\b', text)
        if mob_match:
            details["mobile"] = mob_match.group(2).strip()

        # === PINCODE (6-digit number) ===
        # Find all 6-digit numbers, exclude the mobile number
        mobile_str = details.get("mobile", "")
        for pin_match in re.finditer(r'\b(\d{6})\b', text):
            candidate = pin_match.group(1)
            # Make sure it's not part of the mobile number
            if candidate not in mobile_str:
                details["pincode"] = candidate
                break

        # === NAME ===
        # Try multiple patterns people commonly use
        name_patterns = [
            # "my name is X" / "full name is X" — stop at common next-field words
            r'(?:my\s+)?(?:full\s+)?name\s+is\s+["\']?([A-Za-z][A-Za-z\s\.]{1,40}?)["\']?\s*(?:[,\.\!]|$|\bmo[bn]ile|\bphone|\bnumber|\baddress|\bpincode|\bfull\b|\bmy\b|\b\d)',
            # "i am X" / "i'm X" / "this is X"
            r'(?:i\s+am|i\'m|this\s+is)\s+([A-Za-z][A-Za-z\s\.]{1,30}?)\s*(?:[,\.\!]|$|\bmo[bn]ile|\bphone|\bnumber|\baddress|\bmy\b|\b\d)',
            # "name: X" or "name = X"
            r'name\s*[:=]\s*["\']?([A-Za-z][A-Za-z\s\.]{1,40}?)["\']?\s*(?:[,\.\!]|$|\b\d)',
        ]
        for pattern in name_patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                name = m.group(1).strip().rstrip(',. ')
                # Filter out words that are clearly not names
                skip_words = {"is", "my", "the", "and", "for", "book", "ac", "installation", "repair",
                              "mobile", "monile", "number", "address", "pincode", "phone", "flat", "house"}
                if name.lower() not in skip_words and len(name) >= 2:
                    details["name"] = name
                    break

        # === ADDRESS ===
        # Try multiple patterns
        addr_patterns = [
            # "address is ..." or "address: ..."
            r'(?:full\s+)?address\s+(?:is\s+)?[:\-]?\s*(.+?)(?:\s*(?:pincode|pin\s*code|pin\s+is|my\s+pincode|\b\d{6}\b)|$)',
            # "flat no / house no / house number ..."
            r'((?:flat|house|door|plot)\s*(?:no|number|num)?\.?\s*\d+[\w\s,\.\-\/]+?)(?:\s*(?:pincode|pin\s*code|pin\s+is|\b\d{6}\b)|$)',
        ]
        for pattern in addr_patterns:
            m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if m:
                addr = m.group(1).strip().rstrip(',.')
                # Clean up: remove leading/trailing junk
                addr = re.sub(r'^\s*[,\.\-:]+\s*', '', addr)
                addr = re.sub(r'\s*[,\.\-:]+\s*$', '', addr)
                if len(addr) >= 5:  # Minimum viable address
                    details["address"] = addr
                    break

        logger.info(f"[Agent] Extracted details: {details}")
        return details

    # ------------------------------------------------------------------
    # Build a friendly message asking for missing booking fields
    # ------------------------------------------------------------------
    def _build_missing_fields_response(self, details: dict, service_type: str = None) -> str:
        missing = [f for f in BOOKING_FIELDS if not details.get(f)]

        svc_label = service_type or details.get("service_type", "AC service")
        greeting = f"I'd be happy to help you book an **{svc_label}** appointment! 🛠️\n\n"

        if not missing:
            return None  # All fields present — proceed to booking

        collected = {k: v for k, v in details.items() if k in BOOKING_FIELDS and v}

        if len(collected) <= 1:
            # First message — ask for everything
            return (
                f"{greeting}"
                "To schedule your appointment, I'll need a few details:\n\n"
                "1. 📛 **Full Name**\n"
                "2. 📱 **Mobile Number** (10 digits)\n"
                "3. 🏠 **Full Address**\n"
                "4. 📍 **Area Pincode** (6 digits)\n"
                + (f"5. 🔧 **Service Type** ({', '.join(VALID_SERVICES)})\n" if not details.get("service_type") else "")
                + "\nPlease provide these details and I'll get your appointment booked right away!"
            )
        else:
            # Show what we collected + ask for remaining
            got_lines = []
            if details.get("name"):
                got_lines.append(f"  ✅ Name: **{details['name']}**")
            if details.get("mobile"):
                got_lines.append(f"  ✅ Mobile: **{details['mobile']}**")
            if details.get("address"):
                got_lines.append(f"  ✅ Address: **{details['address']}**")
            if details.get("pincode"):
                got_lines.append(f"  ✅ Pincode: **{details['pincode']}**")
            if details.get("service_type"):
                got_lines.append(f"  ✅ Service: **{details['service_type']}**")

            still_need = [FIELD_PROMPTS[f] for f in missing]

            return (
                "Thanks! Here's what I have so far:\n\n"
                + "\n".join(got_lines)
                + "\n\nI still need:\n\n"
                + "\n".join([f"  ❓ {item}" for item in still_need])
                + "\n\nPlease provide the missing details."
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

        # Check if we're in the middle of a booking conversation
        if intent == "general" and history:
            last_bot = next((h.get("content", "") for h in reversed(history) if h.get("role") == "bot"), "")
            if any(phrase in last_bot.lower() for phrase in [
                "to complete your booking", "i'll need a few details",
                "mobile number", "full name", "full address", "area pincode",
                "i still need", "provide the missing", "provide these details",
                "booked right away"
            ]):
                intent = "appointment"

        tool_calls = []
        tool_outputs = []

        # --- Appointment booking flow ---
        if intent == "appointment":
            # Gather ALL user messages from history + current query
            user_msgs = [h.get("content", "") for h in history if h.get("role") == "user"]
            user_msgs.append(query)
            ctx = " ".join(user_msgs)

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

                    answer = (
                        f"✅ **Appointment Booked Successfully!**\n\n"
                        f"📋 **Ticket ID:** {res['ticket_id']}\n"
                        f"🔧 **Service:** {details['service_type'].replace('_', ' ').title()}\n"
                        f"👨‍🔧 **Technician:** {res['technician']}\n"
                        f"📅 **Scheduled:** {res['date']}\n"
                        f"📊 **Status:** {res['status'].replace('_', ' ').title()}\n\n"
                        f"You can track your appointment anytime by asking me:\n"
                        f'*"Check status of {res["ticket_id"]}"*'
                    )
                    return {"answer": answer, "sources": [], "tool_calls": tool_calls, "intent": intent}
                except Exception as e:
                    logger.error(f"Booking error: {e}")
                    return {"answer": f"Sorry, there was an error booking your appointment: {str(e)}", "sources": [], "tool_calls": [], "intent": intent}
            else:
                # Ask for missing details
                svc = details.get("service_type")
                if not svc:
                    if "install" in ctx.lower():
                        svc = "installation"
                    elif "repair" in ctx.lower():
                        svc = "repair"
                response = self._build_missing_fields_response(details, svc)
                return {"answer": response, "sources": [], "tool_calls": [], "intent": intent}

        # --- Ticket status flow ---
        elif intent == "ticket_status":
            # Search in both the query and recent history for ticket IDs
            search_text = query + " " + " ".join([h.get("content", "") for h in history[-4:]])
            m = re.search(r'TKT-\d+', search_text, re.IGNORECASE)
            if m:
                ticket_id = m.group(0).upper()
                res = call_tool("get_ticket_status", {"ticket_id": ticket_id})
                tool_calls.append(ToolCall(name="get_ticket_status", arguments={"ticket_id": ticket_id}, result=res))

                if res.get("status") == "not_found":
                    answer = f"❌ Ticket **{ticket_id}** was not found. Please double-check the ticket ID."
                else:
                    answer = (
                        f"📋 **Ticket Status: {ticket_id}**\n\n"
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
