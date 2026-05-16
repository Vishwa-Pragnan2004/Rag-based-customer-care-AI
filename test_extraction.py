import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.agent import AgentPipeline

# Simulate the exact user conversation
print("=" * 60)
print("TEST: Simulating real booking flow")
print("=" * 60)

# Create a minimal agent (just test extraction, skip LLM init)
import backend.services.agent as agent_mod

text = 'Book AC installation my full name is "ABCD" monile number is 9898955555 full address flat no 599, gg residency, high colony, bb city'

print(f"\nInput text:\n  {text}\n")

# Test extraction directly 
a = AgentPipeline.__new__(AgentPipeline)
details = a._extract_booking_details(text)

print("Extracted details:")
for k, v in details.items():
    status = "[OK]" if v else "[MISS]"
    print(f"  {status} {k}: {v}")

missing = [f for f in agent_mod.BOOKING_FIELDS if not details.get(f)]
if missing:
    print(f"\n[FAIL] Still missing: {missing}")
else:
    print(f"\n[PASS] ALL FIELDS PRESENT - ready to book!")

print()

# Test with a second message that includes pincode
text2 = text + " pincode is 440009"
print(f"With pincode added: '...pincode is 440009'")
details2 = a._extract_booking_details(text2)
print("Extracted details:")
for k, v in details2.items():
    status = "[OK]" if v else "[MISS]"
    print(f"  {status} {k}: {v}")

missing2 = [f for f in agent_mod.BOOKING_FIELDS if not details2.get(f)]
if missing2:
    print(f"\n[FAIL] Still missing: {missing2}")
else:
    print(f"\n[PASS] ALL FIELDS PRESENT - ready to book!")
