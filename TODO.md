## Outline:

- User data gathering
    - Hard constraints
        - City
    - Soft constraints
        - Budget, length of time
    - User description
        - Can be prompted or unprompted
Option A:
- Sights data gathering
    - Scrape web for list of sights, description, rating, open times, average time spent at sight
- Recommendation engine
    - Use LLM to conduct content based recommendation based on user description
        - Ideal dataset contants bio -> place description. 
        - Similar: reviews of products online?
    - Use rating as proxy for collaborative filtering
- User feedback
    - Recommend user list of sights. 
    - User select sights they would be interested in, with "hard" and "soft" selections
- Route optimization
    - Based on sights, find geographic centerpoint and find a hotel near that point
    - Generate itinerary based on recommended sights
        - Hard constraints: hotel location, "hard" sight selection, travel time, open time
        - Soft constraints: "soft" sight selection, best time to visit (before/after dark)

Option B:
- Use LLM to generate first version of itinerary based on user prompt 
- User feedback
    - Recommend user list of sights. 
    - User select sights they would be interested in, with "hard" and "soft" selections
- Route optimization
    - Based on sights, find geographic centerpoint and find a hotel near that point
    - Generate itinerary based on recommended sights
        - Hard constraints: hotel location, "hard" sight selection, travel time, open time
        - Soft constraints: "soft" sight selection, best time to visit (before/after dark)

Nice to have
- Factor in weather, traffic
- Use LLM to generate itinerary summary
