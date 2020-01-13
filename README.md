# Twitter_tool.
This tool allows you to collect Twitter data and build social networks.
Functionality is based on the Tweepy library.


Some interesting functions (refer to main.py for all functions):

1. authenticate
- you need login creditials from your developer account.

2. profile_information_search
- allows you to provide some parameters to collect profile information. 
- you can write away collected information to csv

3. ID_to_name
- ID to name converter

4. timeline
- collect timeline information
- you can write away collected information to csv

# Network functions

1. create_network
- allows you to collect followers, friends or both from a list of egos (either name or ID).
- allows you to write away your data in network format (from -> to) so it can easily be read in e.g. Gephi 

2. create_bimodal
- creates a bimodal network with egos on the one level and followers or friends on the other.  

3. create_adjacency_matrix
- converts from -> to data to an adjacency matrix format

