
import subprocess
import time
import requests
import os
import signal
import sys

# Configuration
NODE_1_PORT = 5000
NODE_2_PORT = 5001
BASE_URL_1 = f"http://127.0.0.1:{NODE_1_PORT}"
BASE_URL_2 = f"http://127.0.0.1:{NODE_2_PORT}"

def start_node(port, peers=None):
    env = os.environ.copy()
    env["FLASK_APP"] = "backend.app:create_app"
    env["FLASK_RUN_PORT"] = str(port)
    if peers:
        env["PEER_SEEDS"] = peers
    
    # Using .venv python
    cmd = [".venv/bin/flask", "run", "--port", str(port)]
    
    print(f"Starting node on port {port}...")
    process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

def wait_for_node(url):
    retries = 10
    for _ in range(retries):
        try:
            requests.get(f"{url}/api/chain")
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

def run_test():
    node1 = None
    node2 = None
    
    try:
        # Start Node 1
        node1 = start_node(NODE_1_PORT)
        if not wait_for_node(BASE_URL_1):
            print("Failed to start Node 1")
            return False
            
        # Start Node 2 (peered with Node 1)
        node2 = start_node(NODE_2_PORT, peers=BASE_URL_1)
        if not wait_for_node(BASE_URL_2):
            print("Failed to start Node 2")
            return False
            
        print("Both nodes started.")
        time.sleep(5) # Give PubNub time to connect

        # --- Test 1: Block Sync (Node 1 mines -> Node 2 receives) ---
        print("\n--- Test 1: Block Synchronization ---")
        print(f"Mining block on Node 1 ({BASE_URL_1})...")
        requests.post(f"{BASE_URL_1}/api/blocks")
        
        # Give time for propagation
        time.sleep(5)
        
        chain1 = requests.get(f"{BASE_URL_1}/api/chain").json()
        chain2 = requests.get(f"{BASE_URL_2}/api/chain").json()
        
        len1 = chain1["length"]
        len2 = chain2["length"]
        hash1 = chain1["chain"][-1]["hash"]
        hash2 = chain2["chain"][-1]["hash"]
        
        print(f"Node 1 Chain Length: {len1}, Last Hash: {hash1[:10]}...")
        print(f"Node 2 Chain Length: {len2}, Last Hash: {hash2[:10]}...")
        
        if len1 == len2 and hash1 == hash2 and len1 > 1:
            print("SUCCESS: Block synced.")
        else:
            print("FAILURE: Block sync failed.")
            return False

        # --- Test 2: Transaction Sync (Node 2 creates -> Node 1 receives) ---
        print("\n--- Test 2: Transaction Synchronization ---")
        print(f"Creating transaction on Node 2 ({BASE_URL_2})...")
        recipient = "test-recipient"
        amount = 10
        requests.post(f"{BASE_URL_2}/api/transactions", json={"recipient": recipient, "amount": amount})
        
        # Give time for propagation
        time.sleep(5)
        
        pool1 = requests.get(f"{BASE_URL_1}/api/transactions").json()
        pool2 = requests.get(f"{BASE_URL_2}/api/transactions").json()
        
        txs1 = pool1["transactions"]
        txs2 = pool2["transactions"]
        
        print(f"Node 1 Pool Count: {len(txs1)}")
        print(f"Node 2 Pool Count: {len(txs2)}")
        
        if len(txs1) == 1 and len(txs2) == 1 and txs1[0]["id"] == txs2[0]["id"]:
             print("SUCCESS: Transaction synced.")
        else:
             print("FAILURE: Transaction sync failed.")
             return False
             
        return True

    finally:
        print("\nShutting down nodes...")
        if node1:
            os.kill(node1.pid, signal.SIGTERM)
        if node2:
            os.kill(node2.pid, signal.SIGTERM)

if __name__ == "__main__":
    success = run_test()
    if success:
        print("\nOVERALL RESULT: SUCCESS")
        sys.exit(0)
    else:
        print("\nOVERALL RESULT: FAILURE")
        sys.exit(1)
