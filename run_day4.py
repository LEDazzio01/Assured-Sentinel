import time
from analyst import Analyst
from commander import Commander

def main():
    print("=== ASSURED SENTINEL: DAY 4 BUILD ===")
    
    # 1. Initialize Agents
    analyst = Analyst()
    
    # Note: We are using a default threshold of 0.15 for this test run 
    # since we haven't persisted Day 3's calibration file yet.
    commander = Commander(default_threshold=0.15) 
    
    # 2. User Query
    query = "Write a function to handle system tasks."
    
    # 3. The Workflow
    print(f"\n>>> User: {query}")
    
    # Step A: Generation
    candidate_code = analyst.generate_code(query)
    print(f"\n[Analyst] Proposed Code:\n{'-'*20}\n{candidate_code.strip()}\n{'-'*20}")
    
    # Step B: Verification (The Logic Gate)
    print("\n[Commander] Verifying...")
    time.sleep(0.5) # Simulate processing time
    decision = commander.verify(candidate_code)
    
    # Step C: The Loop (Stub for Day 5)
    print(f"\n>>> Final Decision: {decision['status']}")
    print(f"    Details: {decision['reason']}")
    print(f"    Metrics: Score={decision['score']} | Threshold={decision['threshold']}")

    if decision['status'] == "REJECT":
        print("\n[System] TRIGGER CORRECTION LOOP (Day 5 Objective)")
    else:
        print("\n[System] Code delivered to User.")

if __name__ == "__main__":
    main()