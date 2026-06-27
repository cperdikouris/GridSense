import urllib.request
import time
import json

# The endpoints we are going to race against each other
TESTS = {
    "MongoDB (Equipment)": "http://localhost:8000/equipment/TX_001_A",
    "Postgres (Billing)": "http://localhost:8000/billing/account/PREM_10001",
    "Cassandra (Sensors)": "http://localhost:8000/sensors/SENSOR_1/readings?limit=10",
    "Neo4j (Grid Graph)": "http://localhost:8000/grid/fault-impact/SS_1"
}

def run_benchmark():
    print("🏁 STARTING DATABASE PERFORMANCE RACE...\n")
    
    for name, url in TESTS.items():
        print(f"Testing {name}...")
        
        # Warm-up request (databases are slow on the very first try)
        try:
            urllib.request.urlopen(url)
        except Exception as e:
            print(f"  ❌ Failed to connect: {e}")
            continue

        # Run 50 requests and measure the time
        start_time = time.time()
        for _ in range(50):
            urllib.request.urlopen(url)
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = (total_time / 50) * 1000 # Convert to milliseconds
        
        print(f"  ✅ Average Response Time: {avg_time:.2f} ms\n")

if __name__ == "__main__":
    run_benchmark()