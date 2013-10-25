#!/usr/bin/python
# 2013 Kyle Fitzsimmons
'''Module for providing the best possible match between sets of correlated dicts
(e.g., addresses from different sources)'''

import jellyfish as jf


def match(word1, word_list):
    best_lv = 999
    best_jaro = 0
    best_damerau = 999
    best_lvs = []
    best_jaros = []
    best_dameraus = []
    for word2 in word_list:
        # check for NoneTypes
        if word2:
            # test using each method included within jellyfish for a fuzzy
            # string search
            lv = jf.levenshtein_distance(word1, word2)
            jaro = jf.jaro_distance(word1, word2)
            damerau = jf.damerau_levenshtein_distance(word1, word2)
            if lv < best_lv:
                best_lv = lv
                best_lvs = [word2]
            elif lv == best_lv:
                best_lvs.append(word2)
            if jaro > best_jaro:
                best_jaro = jaro
                best_jaros = [word2]
            elif jaro == best_jaro:
                best_jaros.append(word2)
            if damerau < best_damerau:
                best_damerau = damerau
                best_dameraus = [word2]
            elif damerau == best_damerau:
                best_dameraus.append(word2)

    best_matches = []
    best_matches.extend(best_lvs)
    best_matches.extend(best_jaros)
    best_matches.extend(best_dameraus)

    # Return the best neighbor match (most common in the case of multiple) out
    # of the 3 tests
    first_max = max(set(best_matches), key=best_matches.count)
    fmax_occurances = best_matches.count(first_max)
    most_common_matches = [first_max]
    best_matches = filter(lambda a: a != first_max, best_matches)
    while True:
        if not best_matches:
            break
        else:
            next_max = max(set(best_matches), key=best_matches.count)
            if best_matches.count(next_max) == fmax_occurances:
                most_common_matches.append(next_max)
                best_matches = filter(lambda a: a != next_max, best_matches)
            else:
                break
    input_length = len(word1)
    match_dict = {}
    for match in most_common_matches:
        match_dict[match] = abs(input_length - len(match))
    best_match = ('', -1)
    for name in sorted(match_dict, key=match_dict.get):
        if match_dict[name] == best_match[1]:
            print "More than one best fuzzy match."
            return
        else:
            best_match = (name, match_dict[name])
    return best_match[0]    
