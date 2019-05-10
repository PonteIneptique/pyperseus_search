from perseus_search.hopper import search


for match_index, match in enumerate(search("Amiens", "English")):
    print(match_index, repr(match))
