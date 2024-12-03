import pandas as pd
from fuzzywstring import fuzz

class BursaryRecommender:
    def __init__(self, bursary_data):
        self.bursary_data = bursary_data

    def filter_by_field(self, field):
        return self.bursary_data[self.bursary_data['fields'].str.contains(field, case=False)]

    def filter_by_eligibility(self, eligibility_criteria):
        return self.bursary_data[self.bursary_data['eligibility'].str.contains(eligibility_criteria, case=False)]

    def find_best_match(self, user_profile):
        matches = self.bursary_data.copy()

        # Filter by field of study
        if user_profile['field']:
            matches = self.filter_by_field(user_profile['field'])

        # Filter by eligibility criteria
        if user_profile['citizenship'] and user_profile['gender'] and user_profile['race']:
            eligibility_criteria = f"You must be a {user_profile['citizenship']} citizen, female, and {user_profile['race']}"
            matches = self.filter_by_eligibility(eligibility_criteria)

        # Sort by similarity to user profile
        matches['similarity'] = matches['name'].apply(lambda x: fuzz.token_sort_ratio(x, user_profile['name']))
        matches = matches.sort_values('similarity', ascending=False)

        return matches.head(5)