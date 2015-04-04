#! /usr/bin/env python3

# Bombier GOST script v2.0

import csv

#
# Configurations
#

# Input and output filenames
inBomName  = 'bom.csv'
outBomName = 'bom-gost.csv'

# Corresponding between BOM and Gost-BOM CSV columns
gostDesColumn  = 'Designator'
gostCompColumn = ['Footprint','Manufacturer','ComponentName','Value','Tolerance','ValueII','ValueIII']
gostNoteColumn = 'Note'


#
# Functions
#

# Get base of designator (R for R12, C for C2, etc)
def base(designator):
        return ''.join([i for i in designator if not i.isdigit()])

# Add comma before string if not empty
def commatize(string):
        if string == '':
                return ''
        else:
                return ', ' + string

# Make component description column
def mkdesc(rawEntry, columns):
        desc = rawEntry[columns[0]]
        for field in columns[1:]:
                desc = desc + commatize(rawEntry[field])
        return desc

# Make designator cell content for GOST bom
def mkdes(first, last, count):
        if count == 1:
                return first
        elif count == 2:
                return first + ', ' + last
        else:
                return first + '...' + last


#
# First conversion pass to temp BOM (without group headers)
#

# Define BOM-conversion structure
class Entry:
    pass

convBomEntry = Entry()          # Conversion BOM entry (maked from input BOM)
tempBomEntry = Entry()          # Temp BOM entry

convBomEntry.desBase  = ''      # Designator base (R for R12, C for C2, etc)
convBomEntry.compDesc = ''      # Component description
convBomEntry.compNote = ''      # Component note

tempBomEntry.desBase   = ''     # Designator base (R for R12, C for C2, etc)
tempBomEntry.desFirst  = ''     # First designator in entry
tempBomEntry.desLast   = ''     # Last designator in entry
tempBomEntry.compDesc  = ''     # Component description
tempBomEntry.compCount = 0      # Component count
tempBomEntry.compNote  = ''     # Component note

# Temporary BOM. Fields: 'Designator', 'Description', 'Count', 'Note', 'Base'
# 'Base' field needed for second conversion pass
tempbom = []

# Reading input BOM csv
with open(inBomName, 'r', encoding='utf-8') as bomcsv:
        bomreader = csv.DictReader(bomcsv, delimiter=',', quotechar='"')
        
        for rawEntry in bomreader:
                # Begin fill tempBomEntry if empty
                if tempBomEntry.compCount == 0:
                        tempBomEntry.desBase   = base(rawEntry[gostDesColumn])
                        tempBomEntry.desFirst  = rawEntry[gostDesColumn]
                        tempBomEntry.desLast   = rawEntry[gostDesColumn]
                        tempBomEntry.compDesc  = mkdesc(rawEntry, gostCompColumn)
                        tempBomEntry.compCount = 1
                        tempBomEntry.compNote  = rawEntry[gostNoteColumn]
                else:
                        # Fill conversion structure
                        convBomEntry.desBase   = base(rawEntry[gostDesColumn])
                        convBomEntry.compDesc  = mkdesc(rawEntry, gostCompColumn)
                        convBomEntry.compNote  = rawEntry[gostNoteColumn]

                        # Update temp entry if data similar
                        if (convBomEntry.desBase + convBomEntry.compDesc + convBomEntry.compNote) == \
                           (tempBomEntry.desBase + tempBomEntry.compDesc + tempBomEntry.compNote):
                                tempBomEntry.desLast   = rawEntry[gostDesColumn]
                                tempBomEntry.compCount = tempBomEntry.compCount + 1
                        else:
                                # Move tempBomEntry to tempbom
                                tempbom.append({'Designator': mkdes(tempBomEntry.desFirst,
                                                                    tempBomEntry.desLast,
                                                                    tempBomEntry.compCount),
                                                'Description': tempBomEntry.compDesc,
                                                'Count': tempBomEntry.compCount,
                                                'Note': tempBomEntry.compNote,
                                                'Base': tempBomEntry.desBase})

                                # Begin fill next tempBomEntry
                                tempBomEntry.desBase   = base(rawEntry[gostDesColumn])
                                tempBomEntry.desFirst  = rawEntry[gostDesColumn]
                                tempBomEntry.desLast   = rawEntry[gostDesColumn]
                                tempBomEntry.compDesc  = mkdesc(rawEntry, gostCompColumn)
                                tempBomEntry.compCount = 1
                                tempBomEntry.compNote  = rawEntry[gostNoteColumn]

        # Move last tempBomEntry to tempbom
        tempbom.append({'Designator': mkdes(tempBomEntry.desFirst,
                                            tempBomEntry.desLast,
                                            tempBomEntry.compCount),
                        'Description': tempBomEntry.compDesc,
                        'Count': tempBomEntry.compCount,
                        'Note': tempBomEntry.compNote,
                        'Base': tempBomEntry.desBase})

#
# Second conversion pass to output BOM
#

# Read BOM headers before conversion
# cgroups fields: 'Base', 'Single', 'Multiple'
cgroups = []

with open('cgroups.csv', 'r', encoding='utf-8') as cgcsv:
        cgreader = csv.DictReader(cgcsv, delimiter=',', quotechar='"')
        for entry in cgreader:
                cgroups.append(entry)

# Output BOM generation data

outbom      = []    # Output BOM
lastgroup   = []    # Last component group
singletitle = ''    # Last group titles
multititle  = ''


# Second pass functions

def getsingle(base, cgroups):
        for entry in cgroups:
                if entry['Base'] == base:
                        return entry['Single']
        return "Неизвестный компонент"

def getmulti(base, cgroups):
        for entry in cgroups:
                if entry['Base'] == base:
                        return entry['Multiple']
        return "Неизвестные компоненты"

def outputgroup(outbom, lastgroup):
        if len(lastgroup) == 1:
                outbom.append({'Designator': '',
                               'Description': '',
                               'Count': '',
                               'Note': ''})
                outbom.append({'Designator': lastgroup[0]['Designator'],
                               'Description': singletitle + ' ' + lastgroup[0]['Description'],
                               'Count': lastgroup[0]['Count'],
                               'Note': lastgroup[0]['Note']})
        else:
                outbom.append({'Designator': '',
                               'Description': '',
                               'Count': '',
                               'Note': ''})
                outbom.append({'Designator': '',
                               'Description': multititle,
                               'Count': '',
                               'Note': ''})
                for row in lastgroup:
                        outbom.append({'Designator': row['Designator'],
                                       'Description': row['Description'],
                                       'Count': row['Count'],
                                       'Note': row['Note']})

# Output BOM generation

for entry in tempbom:
        # First iteration
        if multititle == '':
                lastgroup.append({'Designator': entry['Designator'],
                                  'Description': entry['Description'],
                                  'Count': entry['Count'],
                                  'Note': entry['Note']})
                singletitle = getsingle(entry['Base'], cgroups)
                multititle =  getmulti(entry['Base'], cgroups)
        # Extend group
        elif getmulti(entry['Base'], cgroups) == multititle:
                lastgroup.append({'Designator': entry['Designator'],
                                  'Description': entry['Description'],
                                  'Count': entry['Count'],
                                  'Note': entry['Note']})
        # Output group, make new group
        else:
                # Output group
                outputgroup(outbom, lastgroup)

                # Flush and fill group
                lastgroup = []
                lastgroup.append({'Designator': entry['Designator'],
                                  'Description': entry['Description'],
                                  'Count': entry['Count'],
                                  'Note': entry['Note']})
                singletitle = getsingle(entry['Base'], cgroups)
                multititle =  getmulti(entry['Base'], cgroups)
# Output group
outputgroup(outbom, lastgroup)

# Print result
for entry in outbom:
        print(entry['Designator'], '\t',
              entry['Description'], '\t',
              entry['Count'], '\t',
              entry['Note'])

# Write output BOM
with open(outBomName, 'w', encoding='utf-8', newline='') as gostbomcsv:
    fieldnames = ['Designator', 'Description', 'Count', 'Note']
    writer = csv.DictWriter(gostbomcsv, fieldnames=fieldnames)

    writer.writeheader()
    for entry in outbom:
            writer.writerow({'Designator': entry['Designator'],
                             'Description': entry['Description'],
                             'Count': entry['Count'],
                             'Note': entry['Note']})


