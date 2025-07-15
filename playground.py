import requests
import json

API_KEY = "3375f2b8b7e01a825ecb0fed97cdc792"
BASE_URL = "https://api.scripture.api.bible/v1"

def get_bible_versions(api_key):
    endpoint = f"{BASE_URL}/bibles"
    headers = {
        "api-key": api_key,
        "Accept": "application/json"
    }
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Bible versions: {e}")
        return None

def find_bible_ids_for_versions(bible_versions, target_versions):
    found_ids = {}
    # Convert target_versions to a set of lowercase strings for faster lookup
    target_set_lower = {v.lower() for v in target_versions}

    if bible_versions:
        for bible in bible_versions:
            bible_name_lower = bible.get("name", "").lower()
            bible_abbr_lower = bible.get("abbreviation", "").lower()

            # Check for exact matches in name or abbreviation
            if bible_name_lower in target_set_lower or \
               bible_abbr_lower in target_set_lower:
                found_ids[bible.get("name", bible.get("abbreviation", "Unknown"))] = bible.get("id")
            # Check if any target string is a substring of the Bible's name or abbreviation
            # This is more flexible for finding "King James Version" if your target is just "KJV"
            elif any(tv_part in bible_name_lower for tv_part in target_set_lower) or \
                 any(tv_part in bible_abbr_lower for tv_part in target_set_lower):
                found_ids[bible.get("name", bible.get("abbreviation", "Unknown"))] = bible.get("id")

    return found_ids

if __name__ == "__main__":
    if API_KEY == "YOUR_API_KEY_HERE":
        print("Please replace 'YOUR_API_KEY_HERE' with your actual API.Bible key.")
    else:
        print("Fetching available Bible versions...")
        all_bibles = get_bible_versions(API_KEY)

        if all_bibles:
            print(f"Successfully fetched {len(all_bibles)} Bible versions.")

            # Your target Bible versions - refined to be more specific or include common full names
            target_versions = [
                "King James Version", "KJV",
                "World English Bible", "WEB",
                "American Standard Version", "ASV",
                "English Standard Version", "ESV",
                "New Living Translation", "NLT",
                # Add any other common variations you can think of
                "The Holy Bible, King James Version",
                "English Standard",
                "New Living"
            ]

            bible_ids = find_bible_ids_for_versions(all_bibles, target_versions)

            if bible_ids:
                print("\n--- Found Bible IDs for specified versions ---")
                for version_name, bible_id in bible_ids.items():
                    print(f"{version_name}: {bible_id}")
            else:
                print("\nNo specific Bible versions found among the available ones or names didn't match closely.")
                print("Proceeding to list all available Bibles for manual inspection...")

            # --- Section to print ALL available Bibles ---
            print("\n--- Full List of All Available Bible Versions (Name, Abbreviation, ID) ---")
            for bible in all_bibles:
                name = bible.get('name', 'N/A')
                abbreviation = bible.get('abbreviation', 'N/A')
                bible_id = bible.get('id', 'N/A')
                print(f"Name: {name}, Abbreviation: {abbreviation}, ID: {bible_id}")
            print("-----------------------------------------------------------------------")

        else:
            print("Could not retrieve Bible versions. Please check your API key and network connection.")
            