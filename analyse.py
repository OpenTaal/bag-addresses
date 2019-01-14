#!/usr/bin/env python3

#TODO woonplaats Oost West en Middelbeers


from datetime import datetime
from locale import Error, LC_ALL, setlocale, strxfrm
from operator import itemgetter
from os.path import isfile
from re import compile, match
from sys import argv, maxsize
from unicodedata import category, name

#Ij
__author__ = 'Sander van Geloven'
__copyright__ = 'Stichting OpenTaal'
__email__ = 'info@opentaal.org'
__license__ = 'GPL'
__description__ = 'Analyses BAG data for spelling.'

# Add link to list
def add_link(list, name, url, abbrev):
    list.append('<a target="_blank" title="{}" href="{}">{}</a>'.format(name, url, abbrev))

# Decode abbreviated Unicode category
def decode_category(value):
    c = category(value)
    if c[0] == 'C':
        return 'control'
    elif c[0] == 'L':
        return 'letter'
    elif c[0] == 'M':
        return 'mark'
    elif c[0] == 'N':
        return 'number'
    elif c[0] == 'P':
        return 'punctuation'
    elif c[0] == 'S':
        return 'symbol'
    elif c[0] == 'Z':
        return 'whitespace'
    else:
        report.write('Illegal or unsupported abbreviated Unicode category {}\n'.format(c))
        report.flush()
        exit(1)

def remove(value, beginnings, middles, endings, removals):
    for beginning in beginnings:
        if value.startswith(beginning):
            value = value[len(beginning):]
            removals.add((True, beginning)) # True for beginning
            return value
    for middle in middles:
        index = value.find(middle)
        if index > 1:
            ending = value[index:]
            value = value[:index] # only beginning is important
            removals.add((False, ending)) # False for ending
            return value
    for ending in endings:
        if value.endswith(ending):
            value = value[:-len(ending)]
            removals.add((False, ending)) # False for ending
            return value
    return value


# Clean value from irrelevant prefix, infix and suffixes.
def clean(value, beginnings, middles, endings, removals):
    value = remove(value, beginnings, middles, endings, removals)
    # only openbareruimte 'D(avid) v. ...' or 'J(an) v. ...'
    op = value.find('(')
    cl = value.find(')')
    if op != -1 and cl != -1:
        if op < cl and op > 0 and value[op-1] != ' ' and cl < len(value)-1:
            if 'Vianen' in value: #TODO
                print(value)
            value = value[:op] + value[op+1:cl] + value[cl+1:]
    begin = (' ', '-', ',', '/', '.')
    end = (' ', '-', ',', '/', "'")
    if value[0] in begin or value[-1] in end or '(' in value or ')' in value:
        report.write('Unsupported cleaning of value {}\n'.format(value))
        report.flush()
        exit(1)

    return value

# Write process and write results for provincie
def write_provincies(provincies, filename, total, stamp_time):
    out = open('results/{}.provincie.md'.format(filename), 'w')
    out_s = open('results/{}.provincie-sorted.txt'.format(filename), 'w')
    out_r = open('results/{}.provincie-retrograde.txt'.format(filename), 'w')

    # Header    
    out.write('# BAG provincie\n')
    out.write('\n')
    out.write('The data below related to *provincie* has been gathered from '
              'analysing {:,} addresses from *Basisregistraties Adressen en '
              'Gebouwen* (BAG) on {}.\n'.format(total, stamp_time))
    out.write('\n')
    out.write('\n')

    # Post-process    
    chars = {}
    charis = {}
    lengths = {}

    # Values
    out.write('## BAG names for provincie\n')
    out.write('\n')
    out.write('The following distinct names for *provincie* have been found, '
              'totaling a number of {:,}.\n'.format(len(provincies)))
    out.write('\n')
    out.write('| name | links |\n')
    out.write('|---|---|\n')
    for provincie in sorted(provincies, key=strxfrm):
        links = []
        add_link(links, 'Nominatim', 'https://nominatim.openstreetmap.org/search?countrycodes=NL&q={}'.format(provincie), 'N')
        add_link(links, 'Overpass Turbo', 'https://overpass-turbo.eu/?Q=rel[admin_level=4][type=boundary][boundary=administrative][name=%22{}%22];out geom;'.format(provincie), 'O')
        out.write('| `{}` | {} |\n'.format(provincie, ' '.join(links)))
        for char in provincie:
            if char in chars:
                chars[char] += 1
            else:
                chars[char] = 1
            chari = char.lower()
            if chari in charis:
                charis[chari] += 1
            else:
                charis[chari] = 1
        length = len(provincie)
        if length in lengths:
            lengths[length] += 1
        else:
            lengths[length] = 1
#TODO store also values to show in table, as there are not that many
#         if length in lengths:
#             lengths[length]['count'] += 1
#         else:
#             lengths[length] = {}
#             lengths[length]['count'] = 1
#             lengths[length]['values'] = []
#         lengths[length]['values'].append(provincie)
    out.write('\n')
    out.write('\n')

    # Length
    out.write('## BAG lengths for provincie\n')
    out.write('\n')
    tmp = ''
    min = maxsize
    max = 0
    for value, count in sorted(lengths.items(), key=itemgetter(1), reverse=True):
        tmp += '| {} | {} |\n'.format(count, value)
        if value > max:
            max = value
        if value < min:
            min = value
    out.write('The names for *provincie* have the following lengths with a '
              'minimum of {} and a maximum of {}.\n'.format(min, max))
    out.write('\n')
    out.write('| count | length |\n')
    out.write('|--:|--:|\n')
    out.write(tmp)
    out.write('\n')
    out.write('\n')
    
    # Characters
    out.write('## BAG characters for provincie\n')
    out.write('\n')
    out.write('Below is a histogram of {} distinct characters used by all '
              '*provincies*. Here code, category and name relate to the '
              'Unicode codepoint of the character value of the character '
              'value of the character value.\n'.format(len(chars)))
    out.write('\n')
    out.write('| count | character | code | category | name |\n')
    out.write('|--:|---|--:|---|---|\n')
    for value, count in sorted(chars.items(), key=itemgetter(1), reverse=True):#TODO add secondary sort
        out.write('| {} | `{}` | `{}` | {} | {} |\n'.format(count, value, hex(ord(value)), decode_category(value), name(value).lower().replace('latin ', 'Latin ')))
    out.write('\n')
    out.write('The following histogram applies when analysing the data in a '
              'case-insensitive way and only {} distinct characters are '
              'found.\n'.format(len(charis)))
    out.write('\n')
    out.write('| count | character | code | category | name |\n')
    out.write('|--:|---|--:|---|---|\n')
    for value, count in sorted(charis.items(), key=itemgetter(1), reverse=True):
        out.write('| {} | `{}` | `{}` | {} | {} |\n'.format(count, value, hex(ord(value)), decode_category(value), name(value).lower().replace('latin ', 'Latin ')))
    out.write('\n')
    out.write('\n')

    # Sorted and retrograde
    out.write('## Retrograde sorted BAG names for provincie\n')
    out.write('\n')
    keys = set()
    for key in sorted(provincies, key=strxfrm):
        out_s.write('{}\n'.format(key))
        keys.add(key[::-1])
    out.write('| name | \n')
    out.write('|--:|\n')
    for key in sorted(keys, key=strxfrm):
        out.write('| `{}` |\n'.format(key[::-1]))
        out_r.write('{}\n'.format(key[::-1]))

# Write process and write results for gemeente
def write_gemeentes(gemeentes, filename, total, stamp_time):
    out = open('results/{}.gemeente.md'.format(filename), 'w')
    out_f = open('results/{}.gemeente-frequency.tsv'.format(filename), 'w')
    out_s = open('results/{}.gemeente-sorted.txt'.format(filename), 'w')
    out_r = open('results/{}.gemeente-retrograde.txt'.format(filename), 'w')

    # Header    
    out.write('# BAG gemeente\n')
    out.write('\n')
    out.write('The data below related to *gemeente* has been gathered from analysing {:,} addresses from *Basisregistraties Adressen en Gebouwen* (BAG) on {}.\n'.format(total, stamp_time))
    out.write('\n')
    out.write('\n')
    
    # Post-process    
    values = {}
    chars = {}
    charis = {}
    lengths = {}
    errors = set()
    form_ij = compile('Ij')
    form_three = compile('(.)\1{2}')
    form_encoding = compile("[^A-Za-z0-9 '-]")
    for gemeente in gemeentes:
        gemeente = gemeente.split('×')[0]
#        if ' ' in gemeente:
#            report.write('Space in gemeente {}\n'.format(gemeente))
        if form_ij.match(gemeente) or form_three.match(gemeente) or form_encoding.match(gemeente) == None:
            errors.add(gemeente)
        if gemeente in values:
            values[gemeente] += 1
        else:
            values[gemeente] = 1

    # Values
    out.write('## BAG names for gemeente\n')
    out.write('\n')
    out.write('The following {:,} distinct names for *gemeente* have been '
              'found, totaling a number of {:,}.\n'.format(len(values), len(gemeentes)))
    out.write('\n')
    out.write('| count | name | links | \n')
    out.write('|--:|---|---|\n')
    for value, count in sorted(values.items(), key=itemgetter(1), reverse=True):
        links = []
        add_link(links, 'Nominatim', 'https://nominatim.openstreetmap.org/search?countrycodes=NL&city={}'.format(value), 'N')
        add_link(links, 'Overpass Turbo', 'https://overpass-turbo.eu/?Q=rel[admin_level=8][type=boundary][boundary=administrative][name=%22{}%22];out geom;'.format(value), 'O')
#        add_link(links, 'Overpass Turbo', 'https://overpass-turbo.eu/?Q=area[name=%22Nederland%22][admin_level=3];(way[name=%22{}%22](area););(._;>;);out;'.format(value), 'O')
        out.write('| {} | `{}` | {} |\n'.format(count, value, ' '.join(links)))
        out_f.write('{}\t{}\n'.format(count, value))
        for char in value:
            if char in chars:
                chars[char] += 1
            else:
                chars[char] = 1
            chari = char.lower()
            if chari in charis:
                charis[chari] += 1
            else:
                charis[chari] = 1
        length = len(value)
        if length in lengths:
            lengths[length] += 1
        else:
            lengths[length] = 1
    out.write('\n')
#FIXME
#    if errors:
#        for err in errors:
#            out.write(err)
#            out.write('\n')
    out.write('\n')
    out.write('\n')

    # Length
    out.write('## BAG lengths for gemeente\n')
    out.write('\n')
    tmp = ''
    min = maxsize
    max = 0
    for value, count in sorted(lengths.items(), key=itemgetter(1), reverse=True):
        tmp += '| {} | {} |\n'.format(count, value)
        if value > max:
            max = value
        if value < min:
            min = value
    out.write('The names for *gemeente* have the following lengths with a minimum of {} and a maximum of {}.\n'.format(min, max))
    out.write('\n')
    out.write('| count | length |\n')
    out.write('|--:|--:|\n')
    out.write(tmp)
    out.write('\n')
    out.write('\n')
    
    # Characters
    out.write('## BAG characters for gemeente\n')
    out.write('\n')
    out.write('Below is a histogram of {} distinct characters used by all *gemeentes*. Here code, category and name relate to the Unicode codepoint of the character value of the character value.\n'.format(len(chars)))
    out.write('\n')
    out.write('| count | character | code | category | name |\n')
    out.write('|--:|---|--:|---|---|\n')
    for value, count in sorted(chars.items(), key=itemgetter(1), reverse=True):#TODO add secondary sort
        out.write('| {} | `{}` | `{}` | {} | {} |\n'.format(count, value, hex(ord(value)), decode_category(value), name(value).lower().replace('latin ', 'Latin ')))
    out.write('\n')
    out.write('The following histogram applies when analysing the data in a case-insensitive way and only {} distinct characters are found.\n'.format(len(charis)))
    out.write('\n')
    out.write('| count | character | code | category | name |\n')
    out.write('|--:|---|--:|---|---|\n')
    for value, count in sorted(charis.items(), key=itemgetter(1), reverse=True):
        out.write('| {} | `{}` | `{}` | {} | {} |\n'.format(count, value, hex(ord(value)), decode_category(value), name(value).lower().replace('latin ', 'Latin ')))
    out.write('\n')
    out.write('\n')

    # Retrograde
    out.write('## Retrograde sorted BAG names for gemeente\n')
    out.write('\n')
    keys = set()
    for key in sorted(values, key=strxfrm):
        out_s.write('{}\n'.format(key))
        keys.add(key[::-1])
    out.write('| name | \n')
    out.write('|--:|\n')
    for key in sorted(keys, key=strxfrm):
        out.write('| `{}` |\n'.format(key[::-1]))
        out_r.write('{}\n'.format(key[::-1]))

# Write process and write results for woonplaats
def write_woonplaatsen(woonplaatsen, filename, total, stamp_time):
    out = open('results/{}.woonplaats.md'.format(filename), 'w')
    out_f = open('results/{}.woonplaats-frequency.tsv'.format(filename), 'w')
    out_s = open('results/{}.woonplaats-sorted.txt'.format(filename), 'w')
    out_r = open('results/{}.woonplaats-retrograde.txt'.format(filename), 'w')

    # Header    
    out.write('# BAG woonplaats\n')
    out.write('\n')
    out.write('The data below related to *woonplaats* has been gathered from analysing {:,} addresses from *Basisregistraties Adressen en Gebouwen* (BAG) on {}.\n'.format(total, stamp_time))
    out.write('\n')
    out.write('\n')
    
    # Post-process    
    values = {}
    chars = {}
    charis = {}
    lengths = {}
    errors = set()
    form_ij = compile('Ij')
    form_three = compile('(.)\1{2}')
    form_encoding = compile("[^A-Za-z0-9 '-]")
    for woonplaats in woonplaatsen:
        woonplaats = woonplaats.split('×')[0]
#        if ' ' in woonplaats:
#            report.write('Space in woonplaats {}\n'.format(woonplaats))
        if form_ij.match(woonplaats) or form_three.match(woonplaats) or form_encoding.match(woonplaats) != None:
            errors.add(woonplaats)
        if woonplaats in values:
            values[woonplaats] += 1
        else:
            values[woonplaats] = 1

    # Values
    out.write('## BAG names for woonplaats\n')
    out.write('\n')
    out.write('The following {:,} distinct values for *woonplaats* have been found, totaling a number of {:,}.\n'.format(len(values), len(woonplaatsen)))
    out.write('\n')
    out.write('| count | name | links |\n')
    out.write('|--:|---|---|\n')
    for value, count in sorted(values.items(), key=itemgetter(1), reverse=True):
        links = []
        add_link(links, 'Nominatim', 'https://nominatim.openstreetmap.org/search?countrycodes=NL&q={}'.format(value), 'N')
        add_link(links, 'Overpass Turbo', 'https://overpass-turbo.eu/?Q=rel[admin_level=10][type=boundary][boundary=administrative][name=%22{}%22];out geom;'.format(value), 'O')
        out.write('| {} | `{}` | {} |\n'.format(count, value, ' '.join(links)))
        out_f.write('{}\t{}\n'.format(count, value))
        for char in value:
            if char in chars:
                chars[char] += 1
            else:
                chars[char] = 1
            chari = char.lower()
            if chari in charis:
                charis[chari] += 1
            else:
                charis[chari] = 1
        length = len(value)
        if length in lengths:
            lengths[length] += 1
        else:
            lengths[length] = 1
    out.write('\n')
#FIXME
#    if errors:
#        for err in errors:
#            out.write(err)
#            out.write('\n')
    out.write('\n')
    out.write('\n')

    # Length
    out.write('## BAG lengths for woonplaats\n')
    out.write('\n')
    tmp = ''
    min = maxsize
    max = 0
    for value, count in sorted(lengths.items(), key=itemgetter(1), reverse=True):
        tmp += '| {} | {} |\n'.format(count, value)
        if value > max:
            max = value
        if value < min:
            min = value
    out.write('The names for *woonplaats* have the following lengths with a minimum of {} and a maximum of {}.\n'.format(min, max))
    out.write('\n')
    out.write('| count | length |\n')
    out.write('|--:|--:|\n')
    out.write(tmp)
    out.write('\n')
    out.write('\n')
    
    # Characters
    out.write('## BAG characters for woonplaats\n')
    out.write('\n')
    out.write('Below is a histogram of {} distinct characters used by all '
              '*woonplaatsen*. Here code, category and name relate to the '
              'Unicode codepoint of the character value.\n'.format(len(chars)))
    out.write('\n')
    out.write('| count | character | code | category | name |\n')
    out.write('|--:|---|--:|---|---|\n')
    for value, count in sorted(chars.items(), key=itemgetter(1), reverse=True):#TODO add secondary sort
        out.write('| {} | `{}` | `{}` | {} | {} |\n'.format(count, value, hex(ord(value)), decode_category(value), name(value).lower().replace('latin ', 'Latin ')))
    out.write('\n')
    out.write('The following histogram applies when analysing the data in a '
              'case-insensitive way and only {} distinct characters are '
              'found.\n'.format(len(charis)))
    out.write('\n')
    out.write('| count | character | code | category | name |\n')
    out.write('|--:|---|--:|---|---|\n')
    for value, count in sorted(charis.items(), key=itemgetter(1), reverse=True):
        out.write('| {} | `{}` | `{}` | {} | {} |\n'.format(count, value, hex(ord(value)), decode_category(value), name(value).lower().replace('latin ', 'Latin ')))
    out.write('\n')
    out.write('\n')

    # Sorted and retrograde sorted
    keys = set()
    for key in sorted(values, key=strxfrm):
        out_s.write('{}\n'.format(key))
        keys.add(key[::-1])
    for key in sorted(keys, key=strxfrm):
        out_r.write('{}\n'.format(key[::-1]))
    
    out.write('## Retrograde sorted BAG names for woonplaats\n')
    out.write('\n')
    out.write('| name | \n')
    out.write('|--:|\n')
    for key in sorted(keys, key=strxfrm):
        out.write('| `{}` |\n'.format(key[::-1]))

# Write process and write results for postcode
def write_postcodes(postcodes, filename, total, stamp_time):
    out = open('results/{}.postcode.md'.format(filename), 'w')

    # Header    
    out.write('# BAG postcode\n')
    out.write('\n')
    out.write('The data below related to *postcode* has been gathered from '
              'analysing {:,} addresses from *Basisregistraties Adressen en '
              'Gebouwen* (BAG) on {}.\n'.format(total, stamp_time))
    out.write('\n')
    out.write('\n')
    
    # Post-process
    chars = {}
    lengths = {}
    errors = set()
    form = compile('^[1-9][0-9]{3}[A-Z]{2}$')
    form_illegal = compile('^[1-9][0-9]{3}S[ADS]$')
    for postcode in postcodes:
        if form.match(postcode):
            if form_illegal.match(postcode):
                errors.append(postcode)
#            elif postcode == '2500NA'
#                has_n_a = True
        else:
            errors.append(postcode)
        for char in postcode:
            if char in chars:
                chars[char] += 1
            else:
                chars[char] = 1
        length = len(postcode)
        if length in lengths:
            lengths[length] += 1
        else:
            lengths[length] = 1

    # Values
    out.write('## BAG values for postcode\n')
    out.write('\n')
    out.write('The list of {:,} distinct values for *postcode* is too long to '
              'show here.\n'.format(len(postcodes)))
    out.write('\n')
#FIXME
#    if errors:
#        for err in errors:
#            out.write(err)
#            out.write('\n')
    out.write('\n')
    out.write('\n')

    # Length
    out.write('## BAG lengths for postcode\n')
    out.write('\n')
    tmp = ''
    min = maxsize
    max = 0
    for value, count in sorted(lengths.items(), key=itemgetter(1), reverse=True):
        tmp += '| {} | {} |\n'.format(count, value)
        if value > max:
            max = value
        if value < min:
            min = value
    out.write('The values for *postcode* have the following lengths with a '
              'minimum of {} and a maximum of {}.\n'.format(min, max))
    out.write('\n')
    out.write('| count | length |\n')
    out.write('|--:|--:|\n')
    out.write(tmp)
    out.write('\n')
    out.write('\n')
    
    # Characters
    out.write('## BAG characters for postcode\n')
    out.write('\n')
    out.write('Below is a histogram of {} distinct characters used by all '
              '*postcodes*. Here code, category and name relate to the '
              'Unicode codepoint of the character value of the character '
              'value of the character value of the character value.\n'.format(len(chars)))
    out.write('\n')
    out.write('| count | character | code | category | name |\n')
    out.write('|--:|---|--:|---|---|\n')
    for value, count in sorted(chars.items(), key=itemgetter(1), reverse=True):#TODO add secondary sort
        out.write('| {} | `{}` | `{}` | {} | {} |\n'.format(count, value, hex(ord(value)), decode_category(value), name(value).lower().replace('latin ', 'Latin ')))

# Write process and write results for openbareruimte
def write_openbareruimtes(openbareruimtes, filename, total, stamp_time):
    out = open('results/{}.openbareruimte.md'.format(filename), 'w')
    out_f = open('results/{}.openbareruimte-frequency.tsv'.format(filename), 'w')
    out_s = open('results/{}.openbareruimte-sorted.txt'.format(filename), 'w')
    out_r = open('results/{}.openbareruimte-retrograde.txt'.format(filename), 'w')

    # Header    
    out.write('# BAG openbareruimte\n')
    out.write('\n')
    out.write('The data below related to *openbareruimte*, or more '
              'colloquially *straatnaam*, has been gathered from analysing '
              '{:,} addresses from *Basisregistraties Adressen en Gebouwen* '
              '(BAG) on {}.\n'.format(total, stamp_time))
    out.write('\n')
    out.write('\n')
    
    # Post-process    
    values = {}
    chars = {}
    charis = {}
    lengths = {}
    errors = set()
    form_ij = compile('Ij')
    form_three = compile('(.)\1{2}')
    form_encoding = compile("[^A-Za-z0-9 '-]")
    abbreviations = {}
    prefixes = {}
    suffixes = {}
    for openbareruimte in openbareruimtes:
        openbareruimte = openbareruimte.split('×')[0]
        if '.' in openbareruimte:
            for part in openbareruimte.split(' '):
                abbrs = part.replace('.', '. ').replace('  ', ' ')
                if len(abbrs) == 0:
                    continue
                if abbrs[-1] == ' ':
                    abbrs = abbrs[:-1]
                for abbreviation in abbrs.split(' '):
                    if len(abbreviation) == 0 or abbreviation[-1] != '.':
                        continue
                    if len(abbreviation) > 2:
                        if abbreviation in abbreviations:
                            abbreviations[abbreviation] += 1
                        else:
                            abbreviations[abbreviation] = 1
        if ' ' in openbareruimte:
#            report.write('Space in openbareruimte {}\n'.format(openbareruimte))
            splits = openbareruimte.split(' ')
            prefix = splits[0]
            suffix = splits[len(splits)-1]
            if prefix[-1] != '.':
                if prefix in prefixes:
                    prefixes[prefix] += 1
                else:
                    prefixes[prefix] = 1
            if len(suffix) < 9:
                if suffix in suffixes:
                    suffixes[suffix] += 1
                else:
                    suffixes[suffix] = 1
        if form_ij.match(openbareruimte) or form_three.match(openbareruimte) or form_encoding.match(openbareruimte) != None:
            errors.add(openbareruimte)
        if openbareruimte in values:
            values[openbareruimte] += 1
        else:
            values[openbareruimte] = 1

    # Values
    out.write('## BAG names for openbareruimte\n')
    out.write('\n')
    out.write('The following {:,} distinct values for *openbareruimte* have been found, totaling a '
              'number of {:,}.\n'.format(len(values), len(openbareruimtes)))
    out.write('\n')
    
    for value, count in sorted(values.items(), key=itemgetter(1), reverse=True):
        out_f.write('{}\t{}\n'.format(count, value))
        for char in value:
            if char in chars:
                chars[char] += 1
            else:
                chars[char] = 1
            chari = char.lower()
            if chari in charis:
                charis[chari] += 1
            else:
                charis[chari] = 1
        length = len(value)
        if length in lengths:
            lengths[length] += 1
        else:
            lengths[length] = 1

    out.write('| count | name | links |\n')
    out.write('|--:|---|---|\n')
    if len(values) > 2048 + 8 + 1:
        for value, count in sorted(values.items(), key=itemgetter(1), reverse=True)[:2048]:
            links = []
            add_link(links, 'Nominatim', 'https://nominatim.openstreetmap.org/search?countrycodes=NL&q={}'.format(value), 'N')
            add_link(links, 'Overpass Turbo', 'https://overpass-turbo.eu/?Q=rel[admin_level=10][type=boundary][boundary=administrative][name=%22{}%22];out geom;'.format(value), 'O')
            out.write('| {} | `{}` | {} |\n'.format(count, value, ' '.join(links)))
        out.write('| ... | ... | ... |\n')
        for value, count in sorted(values.items(), key=itemgetter(1), reverse=True)[-8:]:
            links = []
            add_link(links, 'Nominatim', 'https://nominatim.openstreetmap.org/search?countrycodes=NL&q={}'.format(value), 'N')
            add_link(links, 'Overpass Turbo', 'https://overpass-turbo.eu/?Q=rel[admin_level=10][type=boundary][boundary=administrative][name=%22{}%22];out geom;'.format(value), 'O')
            out.write('| {} | `{}` | {} |\n'.format(count, value, ' '.join(links)))
    else:
        for value, count in sorted(values.items(), key=itemgetter(1), reverse=True):
            links = []
            add_link(links, 'Nominatim', 'https://nominatim.openstreetmap.org/search?countrycodes=NL&q={}'.format(value), 'N')
            add_link(links, 'Overpass Turbo', 'https://overpass-turbo.eu/?Q=rel[admin_level=10][type=boundary][boundary=administrative][name=%22{}%22];out geom;'.format(value), 'O')
            out.write('| {} | `{}` | {} |\n'.format(count, value, ' '.join(links)))
    out.write('\n')
#FIXME
#    if errors:
#        for err in errors:
#            out.write(err)
#            out.write('\n')
    out.write('\n')
    out.write('\n')

    # Length
    out.write('## BAG lengths for openbareruimte\n')
    out.write('\n')
    tmp = ''
    min = maxsize
    max = 0
    for value, count in sorted(lengths.items(), key=itemgetter(1), reverse=True):
        tmp += '| {} | {} |\n'.format(count, value)
        if value > max:
            max = value
        if value < min:
            min = value
    out.write('The names for *straatnaam* have the following lengths with a '
              'minimum of {} and a maximum of {}.\n'.format(min, max))
    out.write('\n')
    out.write('| count | length |\n')
    out.write('|--:|--:|\n')
    out.write(tmp)
    out.write('\n')
    out.write('\n')
    
    # Characters
    out.write('## BAG characters for openbareruimte\n')
    out.write('\n')
    out.write('Below is a histogram of {} distinct characters used by all '
              '*openbareruimte*. Here code, category and name relate to the '
              'Unicode codepoint of the character value.\n'.format(len(chars)))
    out.write('\n')
    out.write('| count | character | code | category | name |\n')
    out.write('|--:|---|--:|---|---|\n')
    for value, count in sorted(chars.items(), key=itemgetter(1), reverse=True):#TODO add secondary sort
        out.write('| {} | `{}` | `{}` | {} | {} |\n'.format(count, value, hex(ord(value)), decode_category(value), name(value).lower().replace('latin ', 'Latin ')))
    out.write('\n')
    out.write('The following histogram applies when analysing the data in a case-insensitive way and only {} distinct characters are found.\n'.format(len(charis)))
    out.write('\n')
    out.write('| count | character | code | category | name |\n')
    out.write('|--:|---|--:|---|---|\n')
    for value, count in sorted(charis.items(), key=itemgetter(1), reverse=True):
        out.write('| {} | `{}` | `{}` | {} | {} |\n'.format(count, value, hex(ord(value)), decode_category(value), name(value).lower().replace('latin ', 'Latin ')))
    out.write('\n')
    out.write('\n')

    # Abbreviations
    out.write('## BAG name abbreviations for openbareruimte\n')
    out.write('\n')
    out.write('Only abbreviations that are two characters or more in length.\n')
    out.write('\n')
    out.write('| count | abbreviation |\n')
    out.write('|--:|---|\n')
    if len(abbreviations) > 64 + 1:
        for value, count in sorted(abbreviations.items(), key=itemgetter(1), reverse=True)[:64]:
            out.write('| {} | `{}` |\n'.format(count, value))
        out.write('| ... | ... |\n')
    else:
        for value, count in sorted(abbreviations.items(), key=itemgetter(1), reverse=True):
            out.write('| {} | `{}` |\n'.format(count, value))
    out.write('\n')
    out.write('\n')

    # Prefixes
    out.write('## BAG name prefixes for openbareruimte\n')
    out.write('\n')
    out.write('Prefixes which are not ending on a period `.`.\n')
    out.write('\n')
    out.write('| count | name |\n')
    out.write('|--:|---|\n')
    if len(prefixes) > 64 + 1:
        for value, count in sorted(prefixes.items(), key=itemgetter(1), reverse=True)[:64]:
            out.write('| {} | `{}` |\n'.format(count, value))
        out.write('| ... | ... |\n')
    else:
        for value, count in sorted(prefixes.items(), key=itemgetter(1), reverse=True):
            out.write('| {} | `{}` |\n'.format(count, value))
    out.write('\n')
    out.write('\n')

    # Suffixes
    out.write('## BAG name suffixes for openbareruimte\n')
    out.write('\n')
    out.write('Suffixes that are not longer than 8 characters.\n')
    out.write('\n')
    out.write('| count | name |\n')
    out.write('|--:|---|\n')
    if len(suffixes) > 32 + 1:
        for value, count in sorted(suffixes.items(), key=itemgetter(1), reverse=True)[:32]:
            out.write('| {} | `{}` |\n'.format(count, value))
        out.write('| ... | ... |\n')
    else:
        for value, count in sorted(suffixes.items(), key=itemgetter(1), reverse=True):
            out.write('| {} | `{}` |\n'.format(count, value))
    out.write('\n')
    out.write('\n')

    # Sorted and retrograde sorted
    keys = set()
#    eindes = {}
#    me = 16
#    for i in range(3, me):
#        eindes[i] = {}
    for key in sorted(values, key=strxfrm):
        out_s.write('{}\n'.format(key))
        keys.add(key[::-1])
#        for i in range(3, me):
#            if len(key) < i:
#                break
#            einde = key[-i:]
#            if ' ' not in einde:
#                if einde in eindes[i]:
#                    eindes[i][einde] += 1
#                else:
#                    eindes[i][einde] = 1
#    for i in range(3, me):
#        for einde, count in sorted(eindes[i].items(), key=itemgetter(1), reverse=True)[47:64]:
#            report.write('{} {} {}'.format(i, count, einde))

    for key in sorted(keys, key=strxfrm):
        out_r.write('{}\n'.format(key[::-1]))

    out.write('## Catogirized/Retrograde sorted BAG names for openbareruimte\n')
    out.write('\n')
    out.write('TODO not under 0.05% \n')
    out.write('\n')
    endings = {}
    max = len(values)
    # remove ' zuid' ' Zuid' '-zuid' '-Zuid' etc? but putting it in front with comma e.g. '-Zuid, Stationstraat'
    for key in values:
        # move up? also strip ' zuid' and ' 20' and ' 2000' ?
        if key.endswith('str'):
            key = key[:-3] + 'straat'
        elif key.endswith('str.'):
            key = key[:-4] + 'straat'
        for ending in (
           'akker', 'akkers', 'allee',
           'bocht', 'bos', 'baan', 'donk', 'brink', 'broek', 'beek', 'boulevard',
           'dam', 'dreef', 'dijk', 'drift', 'dorp', 'diep', 'daal',
           'erf', 'einde', # erf geen werf! lasting met bereklauwerf
           'gracht', 'gaarde', 
           'hof', 'horst', 'hout', 'huis', 'haven', 'heuvel', 'hoek',
           'kant', 'kwartier', 'kamp', 'kampen', #camp 
           'lust', 'laan', 'laantje', 'laar', 'loop', 'land', 'landen', 
           'markt', 'meer', 'molen', 'mond'
           'oever', 
           'pad', 'poort', 'plein', 'plaats', 'polder', 'plantsoen', 'park', 'passage',
           'ring', 'ruwe', 
           'spoor', 'straat', 'singel', 'steeg', 'schans', 'sluis', 'sloot', 'schip', 'schap', 'stein', 'stroom', 'strjitte', 'straatje',
           'tocht', 'tuin',
           'vliet', 'voort', 'vaart', 'veer', 'veen', 'veld', 'velden', 'ven' # ven lasting met erven en hoven 
           'weg', 'wei', 'wijk', 'wetering', 'watering', #ring
           'zicht', 'zoom', 'zaal',
           ):
            if key.lower().endswith(ending):
#                 if ending == 'weg' and key.lower().endswith('straatweg'):
#                     straatweg += 1
#                 elif ending == 'weg' and key.lower().endswith('kampweg'):
#                     kampweg += 1
#TODO note that these are not reported seperately
                if ending in endings:
                    endings[ending] += 1 
                else:
                    endings[ending] = 1 
    out.write('| count | percentage | name type | \n')
    out.write('|--:|--:|---|\n')
    for value, count in sorted(endings.items(), key=itemgetter(1), reverse=True):
        percentage = count / max * 100
        if percentage >= 0.05:
            out.write('| {} | {:5.2f}% | `{}` |\n'.format(count, percentage, value))


# setlocale(LC_ALL, 'nl_NL.UTF-8')
# lastnames_firstnames_groups =[
#     ["Bange", "Chris", 2],
#     ["Änger", "Ämma", 2],
#     ["Amman", "Anton", 1],
#     ["Änger", "Michael", 2],
#     ["Zelch", "Sven", 1],
#     ["Ösbach", "Carl", 1]
# ]
# for i in sorted(
#         lastnames_firstnames_groups,
#         key=lambda t: (t[2], strxfrm(t[0]), strxfrm(t[1]))
#     ):
#     print(i)
# exit(0)

# Check input file in command line argument
filename = 'bagadres.csv'
if len(argv) == 2:
    filename = argv[1]
else:
    if not isfile(filename):
        report.write('Missing argument for input CSV file containing BAG addresses\n')
        report.flush()
        exit(1)

# Set locale for sorting
try:
    setlocale(LC_ALL, 'nl_NL.UTF-8')
except Error:
    report.write('After failing locale nl_NL.UTF-8, falling back to locale '
            'en_US.UTF-8\n')
    report.flush()
    try:
        setlocale(LC_ALL, 'en_US.UTF-8')
    except Error:
        report.write('After failing locale en_US.UTF-8, falling back to locale '
                'en_GB.UTF-8\n')
        report.flush()
        # Error is must have when next line fails. Sort is otherwise useless.
        setlocale(LC_ALL, 'en_GB.UTF-8')
stamp_time = datetime.now().strftime('%Y-%m-%d at %H:%M:%S')

# Initialize histogram data structures
provincies = set()
gemeentes = set()
woonplaatsen = set()
postcodes = set()
openbareruimtes = set()
huisnummers = set()
huisletters = set()
huisnummertoevoegingen = set()

removals_gemeentes = set()
removals_woonplaatsen = set()
removals_openbareruimtes = set()

beginnings_gemeente = ()
middles_gemeente = ()
endings_gemeente = (' (L.)', # provincie 'Limburg'
                    ' (NH.)', # provincie 'Noord-Holland'
                   )

beginnings_woonplaats = ('Winterswijk ', ) # trailing comma is essential!
middles_woonplaats = (' gem. ', ' gem ', ) # gemeente '*'
endings_woonplaats = (' (GLD)', ' (Gld)', ' Gld', # provincie 'Gelderland'
                      ' (NB)', ' NB', # provincie 'Noord-Brabant'
                      ' (NH)', ' NH', # provincie 'Noord-Holland'
                      ' Gn', # provincioe 'Groningen'
                      ' Ut', # provincie 'Utrecht'
                      ' L', # provincie 'Limburg'
                      ' Rotterdam', # gemeente 'Rotterdam'
                      ' Oldebroek', # gemeente 'Oldebroek'
                      ' GN', # gemeente 'Groningen'
                      ' AC', # gemeente 'Alphen-Chaam'
                      ' ca', #  is ' c.a.' stands for ' en Hofwegen'
                     )

beginnings_openbareruimte = ()
middles_openbareruimte = ()
endings_openbareruimte = (' N',
                          ' NZ', ' Nz'' N.Z.', ' N.z.', ' nz',
                          ' O',
                          ' OZ', ' Oz', ' O.Z.', ' O.z.', ' oz',
                          ' Z',
                          ' ZZ', ' Zz', ' Z.Z.', ' Z.z.', ' zz',
                          ' W',
                          ' WZ', ' Wz', ' W.Z.', ' W.z.', ' wz',
                          ' N.O.', '-NO',
                          ' Z.O.', '-ZO',
                          ' Z.W.', '-ZW',
                          ' N.W.', '-NW',
                          ' (noord)', ' (oost)', ' (zuid)', ' (west)', 
                          ' (Noord)', ' (Oost)', ' (Zuid)', ' (West)', 
                          ' (oast)', ' (Oast)',
                          ' (Rucphen)', )

# Following columns from the CSV file will be analysed:
# - openbareruimte: street name (lit. public space)
# - huisnummer: house number, only one or more numerals
# - huisletter: optional house letter, zero or more letters
# - huisnummertoevoeging: optional house number addition
# - postcode: postal code, always four numerals and two upper case letters
# - woonplaats: settlement
# - gemeente: city
# - provincie: province
#
# Not process are:
# - object_id
# - object_type: object type, only 'VBO', 'STA' or 'LIG'
# - nevenadres: side address, only 't' (true) or 'f' (false)
# - x
# - y
# - lon
# - lat


# Read CSV file
##reader = DictReader(open(filename, newline=''), delimiter=';')
total = 0
uniq = ''
prev = ''
report = open('results/{}.report.txt'.format(filename), 'w')
with open(filename) as addresses:    
    for address in addresses:
        address = address[:-1]
        openbareruimte, huisnummer, huisletter, huisnummertoevoeging, postcode, woonplaats, gemeente, provincie, *remaining = address.split(';') 
        total += 1
        if total % 250000 == 0:
            report.write('Read {:,} addresses...\n'.format(total))
            report.flush()
#        if total > 1250000: # debug
#            break
        uniq = '{}×{}×{}×{}×{}'.format(provincie, gemeente, woonplaats,
                                       postcode, openbareruimte)
        if uniq == prev or prev == '':
            prev = uniq
            continue # optimise for speed and skip header
        prev = uniq

        gemeente = '{}×{}'.format(clean(gemeente, beginnings_gemeente,
                    middles_gemeente, endings_gemeente, removals_gemeentes),
                    provincie)
        woonplaats = '{}×{}×{}'.format(clean(woonplaats,
                     beginnings_woonplaats, middles_woonplaats,
                     endings_woonplaats, removals_woonplaatsen), gemeente,
                     provincie)
        openbareruimte = '{}×{}'.format(clean(openbareruimte,
                          beginnings_openbareruimte, middles_openbareruimte,
                          endings_openbareruimte, removals_openbareruimtes),
                          woonplaats)
#     huisnummer = '{}×{}'.format(row['huisnummer'], openbareruimte)
#     huisletter = '{}×{}'.format(row['openbareruimte'], huisnummer)
#     huisnummertoevoeging = '{}×{}'.format(row['openbareruimte'], huisnummer)

        provincies.add(provincie)
        gemeentes.add(gemeente)
        woonplaatsen.add(woonplaats)
        postcodes.add(postcode)
        openbareruimtes.add(openbareruimte)
#     huisnummers.add(huisnummer)
#     huisletters.add(huisletter)
#     huisnummertoevoegingen.add(huisnummertoevoeging)
    

report.write('Reporting on {} provincies...\n'.format(len(provincies)))
report.flush()
write_provincies(provincies, filename, total, stamp_time)
del provincies
report.write('Reporting on {} gemeentes...\n'.format(len(gemeentes)))
report.flush()
write_gemeentes(gemeentes, filename, total, stamp_time)
del gemeentes
report.write('Reporting on {} woonplaatsen...\n'.format(len(woonplaatsen)))
report.flush()
write_woonplaatsen(woonplaatsen, filename, total, stamp_time)
del woonplaatsen
report.write('Reporting on {} postcodes...\n'.format(len(postcodes)))
report.flush()
##write_postcodes(postcodes, filename, total, stamp_time)
del postcodes
report.write('Reporting on {} openbareruimtes...\n'.format(len(openbareruimtes)))
report.flush()
write_openbareruimtes(openbareruimtes, filename, total, stamp_time)
del openbareruimtes

for i in removals_gemeentes:
    report.write('Removed {} from gemeente\n'.format(i))
    report.flush()
for i in removals_woonplaatsen:
    report.write('Removed {} from woonplaats\n'.format(i))
    report.flush()
for i in removals_openbareruimtes:
    report.write('Removed {} from openbareruimte\n'.format(i))
    report.flush()



exit(0)

# iterate all entries
c = 0
for row in csvreader:
    c += 1
    if c > 1000000:
        break
    # process only certain columns
    for i in range(num_cols_proc):
        if i == 0:
            # value openbareruimte
            value = ' × '.join((row[0], row[5], row[6], row[7]))  
            if value in histograms_values[i]:
                histograms_values[i][value] += 1
            else:
                histograms_values[i][value] = 1
        if i == 7:
            # value provincie
            if row[i] not in histograms_values[i]:
                histograms_values[i][row[i]] = 1
                # value length provincie
                histograms_lengths[i][len(row[i])] = 1
                # value charters provincie
                for char in row[i]:
                    if char in histograms_chars[i]:
                        histograms_chars[i][char] += 1
                    else:
                        histograms_chars[i][char] = 1
        else:
            # value
            if row[i] in histograms_values[i]:
                histograms_values[i][row[i]] += 1
            else:
                histograms_values[i][row[i]] = 1
        # value length
        length = len(row[i])
        if i != 7:
            if length in histograms_lengths[i]:
                histograms_lengths[i][length] += 1
            else:
                histograms_lengths[i][length] = 1
        # value first lower
        if i in txt_cols and row[i][0].islower():
            if row[i] in histograms_first_lowers[i]:
                histograms_first_lowers[i][row[i]] += 1
            else:
                histograms_first_lowers[i][row[i]] = 1
        # value all lower
        if i in txt_cols and row[i].islower():
            if row[i] in histograms_lowers[i]:
                histograms_lowers[i][row[i]] += 1
            else:
                histograms_lowers[i][row[i]] = 1
        # value all upper
        if i in txt_cols and row[i].isupper() and len(row[i]) > 1 and row[i] != 'IJ' and row[i] != 'ABC':
            if row[i] in histograms_uppers[i]:
                histograms_uppers[i][row[i]] += 1
            else:
                histograms_uppers[i][row[i]] = 1
        # value charters
        if i != 7:
            for char in row[i]:
                if char in histograms_chars[i]:
                    histograms_chars[i][char] += 1
                else:
                    histograms_chars[i][char] = 1
    
print('# Analysis of BAG address')
print('')
print('The analysis below only concerns the spelling of BAG addresses. Any derived statistics do not always relate to the total amount of addresses in general. Where needed omissions or aggregations have been made.')
print('')

for i in reversed(range(num_cols_proc)):

    # column    
    print('## {} {}'.format(i+2-num_cols_proc, headers[i]))
    print('')
    
    # value
    print('### {}.1 Histogram values {}'.format(i+2-num_cols_proc, headers[i]))
    print('')
    if i in (1, 4, ):
        print('_Table is empty, too long or not applicable._')
    else:
        if i == 0:
            # value openbareruimte
            print('| count | value | links |')
            print('|--:|---|---|')
            histogram = {}
            for value in histograms_values[i]:
                short = value.split(' × ')[0]
                if short in histogram:
                    histogram[short] += 1
                else:
                    histogram[short] = 1
            for value, count in sorted(histogram.items(), key=itemgetter(1), reverse=True):
                link = '<a target="_blank" title="Overpass Turbo" href="https://overpass-turbo.eu/?Q=area[name=%22Nederland%22][admin_level=3];(way[name=%22{}%22](area););(._;>;);out;">TO</a>'.format(value)
                if value == '':
                    value = '_empty_'
                    url = ''
                else:
                    value = '`{}`'.format(value)
                print('| {} | {} | {} |'.format(count, value, link))
        elif i == 7:
            # value provincie
            print('| value | links |')
            print('|---|')
            for value in sorted(histograms_values[i]):
                link = '<a target="_blank" title="Nominatim" href="https://nominatim.openstreetmap.org/search.php?q={}">N</a>'.format(value)              
                print('| {} | {} |'.format(value, link))
        else:
            print('| count | value |')
            print('|--:|---|')
            for value, count in sorted(histograms_values[i].items(), key=itemgetter(1), reverse=True):                                         
                if value == '':
                    value = '_empty_'
                else:
                    value = '`{}`'.format(value)
                print('| {} | {} |'.format(count, value))
    print('')
    
    # value length 
    print('### {}.2 Histogram lengths {}'.format(i+2-num_cols_proc, headers[i]))
    print('')
    if i in (4, ):
        print('_Table is empty, too long or not applicable._')
    else:
        print('| count | length |')
        print('|--:|--:|')
        for value, count in sorted(histograms_lengths[i].items(), key=itemgetter(1), reverse=True):                                         
            print('| {} | {} |'.format(count, value))
        print('')
        
    # value start lower
    print('### {}.3 Histogram values starting with lower case {}'.format(i+2-num_cols_proc, headers[i]))
    print('')
    if i != 4 and histograms_first_lowers[i]:
        print('| count | value |')
        print('|--:|---|')
        for value, count in sorted(histograms_first_lowers[i].items(), key=itemgetter(1), reverse=True):                                         
            print('| {} | `{}` |'.format(count, value))
    else:
        print('_Table is empty, too long or not applicable._')
    print('')

    # value all lower
    print('### {}.4 Histogram values in all lower case {}'.format(i+2-num_cols_proc, headers[i]))
    print('')
    if i != 4 and histograms_lowers[i]:
        print('| count | value |')
        print('|--:|---|')
        for value, count in sorted(histograms_lowers[i].items(), key=itemgetter(1), reverse=True):                                         
            print('| {} | `{}` |'.format(count, value))
    else:
        print('_Table is empty, too long or not applicable._')
    print('')

    # value all upper    
    print('### {}.5 Histogram values in all upper case {}'.format(i+2-num_cols_proc, headers[i]))
    print('')
    if i != 4 and histograms_uppers[i]:
        print('Ignoring values of a single characters and values of only `IJ` or `ABC`.')
        print('')
        print('| count | value |')
        print('|--:|---|')
        for value, count in sorted(histograms_uppers[i].items(), key=itemgetter(1), reverse=True):                                         
            print('| {} | `{}` |'.format(count, value))
    else:
        print('_Table is empty, too long or not applicable._')
    print('')

    # value characters
    print('### {}.6 Histogram characters {}'.format(i+2-num_cols_proc, headers[i]))
    print('')
    print('| count | character | code | category | name |')
    print('|--:|---|--:|---|')
    for value, count in sorted(histograms_chars[i].items(), key=itemgetter(1), reverse=True):
        print('| {} | `{}` | `{}` | {} | {} |'.format(count, value, hex(ord(value)), decode_category(value), name(value).lower().replace('latin ', 'Latin ')))
    print('')



# todo Amsterdam-Duivendrecht, Rotterdam-Albrandswaard
