import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import json
import os
import webbrowser
from collections import defaultdict
from datetime import datetime

# Configuration
HISTORY_FILE = "search_history.json"
PREFERENCES_FILE = "user_prefs.json"
USER_PROFILES = {
    "technology": ["python", "programming", "ai", "machine learning", "coding", "developer", "algorithm"],
    "health": ["fitness", "diet", "nutrition", "exercise", "yoga", "health", "workout"],
    "education": ["learn", "course", "tutorial", "school", "university", "education", "study"],
    "business": ["startup", "entrepreneur", "marketing", "finance", "investment", "business", "money"],
    "entertainment": ["movie", "music", "game", "tv show", "celebrity", "netflix", "sport"]
}

class SearchEngine:
    def __init__(self):
        self.search_history = self.load_data(HISTORY_FILE)
        self.user_prefs = self.load_data(PREFERENCES_FILE)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def load_data(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return defaultdict(int) if "prefs" in filename else []

    def save_data(self):
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.search_history, f)
        with open(PREFERENCES_FILE, 'w') as f:
            json.dump(self.user_prefs, f)

    def fetch_results(self, query):
        url = f"https://www.bing.com/search?q={quote_plus(query)}"
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.select('.b_algo')[:5]  # Get top 5 results
        except Exception as e:
            print(f"Error fetching results: {str(e)}")
            return []

    def process_results(self, results, query):
        processed = []
        for result in results:
            title = result.find('h2').text if result.find('h2') else "No title"
            link = result.find('a')['href'] if result.find('a') else "#"
            snippet = result.find('p').text if result.find('p') else "No description"
            
            priority = self.user_prefs.get(link, 0) + 1
            processed.append({
                'title': title,
                'url': link,
                'snippet': snippet,
                'priority': priority,
                'query': query
            })
        return sorted(processed, key=lambda x: x['priority'], reverse=True)

    def open_url(self, url):
        try:
            webbrowser.open(url)
            print(f"Opening: {url}")
        except Exception as e:
            print(f"Failed to open URL: {str(e)}")

    def analyze_user_profile(self):
        if not self.search_history:
            return {"profile": "New User", "description": "No search history yet"}

        interest_counts = defaultdict(int)
        for entry in self.search_history:
            query = entry['query'].lower()
            for category, keywords in USER_PROFILES.items():
                if any(keyword in query for keyword in keywords):
                    interest_counts[category] += 1
        
        if not interest_counts:
            return {"profile": "General User", "description": "No specific interests detected"}

        top_categories = sorted(interest_counts.items(), key=lambda x: x[1], reverse=True)[:2]
        primary = top_categories[0][0]
        
        descriptions = {
            "technology": "Tech-savvy individual interested in programming and innovation",
            "health": "Health-conscious person focused on wellness and fitness",
            "education": "Knowledge seeker who values learning and self-improvement",
            "business": "Business-minded individual interested in entrepreneurship",
            "entertainment": "Fun-loving person who enjoys pop culture and leisure"
        }
        
        if len(top_categories) > 1 and top_categories[0][1] == top_categories[1][1]:
            profile = "Balanced User"
            desc = f"Equally interested in {primary} and {top_categories[1][0]}"
        else:
            profile = f"{primary.capitalize()} Enthusiast"
            desc = descriptions.get(primary, f"Highly interested in {primary} topics")
        
        return {"profile": profile, "description": desc}

    def display_results(self, results):
        if not results:
            print("\n🔍 No results found. Try a different query.")
            return []
        
        print("\n" + "═" * 60)
        print(" " * 24 + "🔍 SEARCH RESULTS")
        print("═" * 60 + "\n")
        
        urls = []
        for i, result in enumerate(results[:3], 1):
            print(f"┌───────── Result {i} {'★' if result['priority'] > 1 else ''} ─────────┐")
            print(f"│ \033[1;36m{result['title']}\033[0m")
            print(f"│ \033[37m{result['snippet']}\033[0m")
            print(f"│ \033[94m{result['url']}\033[0m")
            print("└" + "─" * 40 + "┘\n")
            urls.append(result['url'])
            self.user_prefs[result['url']] = self.user_prefs.get(result['url'], 0) + 1
        
        return urls

    def show_history(self):
        if not self.search_history:
            print("\nNo search history yet!")
            return
            
        profile = self.analyze_user_profile()
        
        print("\n" + "═" * 60)
        print(" " * 24 + "📜 SEARCH HISTORY & PROFILE")
        print("═" * 60 + "\n")
        
        print(f"👤 User Type: \033[1m{profile['profile']}\033[0m")
        print(f"📝 Description: {profile['description']}\n")
        print("═" * 60 + "\n")
        
        print("Recent Searches:")
        for i, entry in enumerate(reversed(self.search_history[-5:]), 1):
            print(f"\n{i}. [{entry['time']}] {entry['query']}")
            for j, url in enumerate(entry['results'][:2], 1):
                print(f"   {j}) {url}")
        
        print("\n" + "═" * 60)
        print("Options: [o] Open URL  [d] Delete Entry  [c] Clear All  [b] Back")
        choice = input("\nSelect action: ").strip().lower()
        
        if choice == 'c':
            self.search_history = []
            self.save_data()
            print("\nHistory cleared!")
        elif choice == 'd':
            try:
                idx = int(input("\nEnter entry number to delete: ")) - 1
                if 0 <= idx < len(self.search_history):
                    del self.search_history[-(idx+1)]
                    self.save_data()
                    print("\nEntry deleted!")
            except ValueError:
                print("\nInvalid input")
        elif choice == 'o':
            try:
                entry_idx = int(input("\nEnter entry number: ")) - 1
                url_idx = int(input("Enter URL number: ")) - 1
                if 0 <= entry_idx < len(self.search_history) and 0 <= url_idx < len(self.search_history[-(entry_idx+1)]['results']):
                    self.open_url(self.search_history[-(entry_idx+1)]['results'][url_idx])
            except ValueError:
                print("\nInvalid input")

    def search_interface(self):
        while True:
            print("\n" + "╔" + "═" * 58 + "╗")
            print("║" + " " * 20 + "🔎 VELORA SEARCH" + " " * 21 + "║")
            print("╠" + "═" * 58 + "╣")
            print("║ Options: [1] Search  [2] History  [3] Exit        ║")
            print("╚" + "═" * 58 + "╝")
            
            choice = input("\nSelect option (1-3): ").strip()
            
            if choice == '1':
                query = input("\nSearch for: ").strip()
                if not query:
                    continue
                    
                results = self.fetch_results(query)
                if results:
                    processed = self.process_results(results, query)
                    urls = self.display_results(processed)
                    self.search_history.append({
                        'query': query,
                        'time': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'results': urls
                    })
                    self.save_data()
                    
                    while True:
                        action = input("\nOpen link (1-3) or [b]ack: ").strip().lower()
                        if action == 'b':
                            break
                        try:
                            idx = int(action) - 1
                            if 0 <= idx < len(urls):
                                self.open_url(urls[idx])
                        except ValueError:
                            print("\nPlease enter a number (1-3) or 'b' to go back")
                
            elif choice == '2':
                self.show_history()
                
            elif choice == '3':
                print("\nThank you for using Velora Search! Goodbye 👋")
                break

if __name__ == "__main__":
    engine = SearchEngine()
    print("\n" + "═" * 60)
    print(" " * 20 + "🌟 Welcome to Velora Search 🌟")
    print("═" * 60)
    engine.search_interface()