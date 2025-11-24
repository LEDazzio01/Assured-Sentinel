import asyncio
import time
import os
from commander import Commander
# Import the function directly instead of a class
from analyst import generate_code 

async def main():
    print("=== ASSURED SENTINEL: DAY 4 BUILD (ASYNC INTEGRATION) ===")
    
    # 1. Check Environment (Crucial for Semantic Kernel)
    if not os.getenv("AZURE_OPENAI_API_KEY"):
        print("[!] CRITICAL: AZURE_OPENAI_API_KEY is not set.")
        print("    The Analyst will fail. Please set your env vars.")
        return

    # 2. Initialize The Commander (The Logic Gate)
    # We use a default threshold of 0.15 for this MVP test.
    commander = Commander(default_threshold=0.15)
    
    # 3. Define User Query
    # We use a prompt likely to trigger "safe" code to test the happy path first.
    query = "Write a Python function to calculate the factorial of a number."
    
    # 4. Execution Flow
    print(f"\n>>> User: {query}")
    
    # Step A: Generation (The Analyst)
    # We await the semantic kernel function
    try:
        candidate_code = await generate_code(query)
        print(f"\n[Analyst] Proposed Code:\n{'-'*20}\n{candidate_code.strip()}\n{'-'*20}")
    except Exception as e:
        print(f"\n[!] Analyst Failed: {e}")
        return
    
    # Step B: Verification (The Commander)
    print("\n[Commander] Verifying...")
    decision = commander.verify(candidate_code)
    
    # Step C: Decision Output
    print(f"\n>>> Final Decision: {decision['status']}")
    print(f"    Details: {decision['reason']}")
    print(f"    Metrics: Score={decision['score']} | Threshold={decision['threshold']}")

    if decision['status'] == "REJECT":
        print("\n[System] 🛑 STOP. Trigger Correction Loop (Day 5).")
    else:
        print("\n[System] ✅ PASS. Code delivered to User.")

if __name__ == "__main__":
    # We use asyncio to run the async main loop
    asyncio.run(main())