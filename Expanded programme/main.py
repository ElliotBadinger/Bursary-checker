from bursary_manager import BursaryManager
from bursary_recommender import BursaryRecommender

def main():
    base_url = "https://www.zabursaries.co.za"
    manager = BursaryManager(base_url)
    manager.scrape_bursaries()
    manager.save_data()

    recommender = BursaryRecommender(manager.bursary_data)

    user_profile = {
        'name': 'John Doe',
        'field': 'Computer Science',
        'citizenship': 'South African',
        'gender': 'Female',
        'race': 'Black'
    }

    print("Top 5 Bursary Recommendations:")
    print(recommender.find_best_match(user_profile))

if __name__ == "__main__":
    main()