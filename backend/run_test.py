import json
from wrappers.pipeline_aggregator import collect_all_geospatial_data
from alert_system.alert_engine import LandslideRiskEvaluator

import sys
import traceback

print("--- BOOTING TEST SCRIPT ---")

try:
    # We put imports INSIDE the try-block so if an import fails, it prints why.
    from wrappers.pipeline_aggregator import collect_all_geospatial_data
    from alert_system.alert_engine import LandslideRiskEvaluator

    def run_system_test():
        print("Initializing SIH26001 Pipeline...")
        
        # Test coordinates: Cherrapunji Belt, Meghalaya
        test_lat, test_lon = 25.2736, 91.7323
        
        print(f"1. Pulling live geospatial & weather data for ({test_lat}, {test_lon})...")
        raw_data = collect_all_geospatial_data(test_lat, test_lon)
        
        if not raw_data:
            print("ERROR: collect_all_geospatial_data returned None or empty.")
            return

        print("2. Pushing data through Core Geophysics & Empirical Logic...")
        evaluator = LandslideRiskEvaluator()
        
        # Using the new core geophysics engine
        alert_result = evaluator.evaluate_realtime_empirical(raw_data)
        
        print("\n================ FINAL ALERT PAYLOAD ================")
        print(json.dumps(alert_result, indent=2))
        print("=====================================================")

    if __name__ == "__main__":
        run_system_test()

except Exception as e:
    print("\n!!! CRITICAL SYSTEM CRASH !!!")
    traceback.print_exc()
    sys.exit(1)