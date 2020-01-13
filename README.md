# Twitter_tool.
# Allows you to collect Twitter data and build social networks.
# Based on the Tweepy library.


Some interesting functions (refer to main.py for all functions):

authenticate
- you need login creditials from your developer account.

profile_information_search
- allows you to provide some parameters to collect profile information. 
- you can write away collected information to csv

ID_to_name
- ID to name converter

timeline
- collect timeline information
- you can write away collected information to csv

# Network functions

create_network
- allows you to collect followers, friends or both from a list of egos (either name or ID).
- allows you to write away your data in network format (from -> to) so it can easily be read in e.g. Gephi 

create_bimodal
- creates a bimodal network with egos on the one level and followers or friends on the other.  

create_adjacency_matrix
- converts from -> to data to an adjacency matrix format

