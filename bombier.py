#! /usr/bin/env python3

import csv

# Add comma before string if not empty
def commatize(string):
        if string == '':
                return ''
        else:
                return ', ' + string

# Make designator cell for GOST bom
def des(first, last, count):
        if count == 1:
                return first
        elif count == 2:
                return first + ', ' + last
        else:
                return first + '...' + last

# Conversion structure
cBase  = '' # Designator base: 'C', 'R', 'DA', 'VD', ...
cFirst = '' # First component with same data
cLast  = '' # Last component with same data
cDesc  = '' # Component description
cCount = 0  # Same component counter
cNote  = '' # Component note

# Comparsion 'current' structure
curBase  = ''
curDesc  = ''
curNote  = ''

# Temporary BOM (no group headers)
tempbom = []

# Reading original BOM csv
with open('bom.csv', 'r', encoding='utf-8') as bomcsv:
        bomreader = csv.DictReader(bomcsv, delimiter=',', quotechar='"')
        # Fields: Designator, Footprint, Manufacturer, ComponentName, Value, Tolerance, ValueII, ValueIII, Note
        for entry in bomreader:
                # Fill conversion structure if empty
                if cCount == 0:
                        cBase  = ''.join([i for i in entry['Designator'] if not i.isdigit()])
                        cFirst = entry['Designator']
                        cLast  = entry['Designator']
                        cDesc  = entry['Footprint'] + \
                                 commatize(entry['Manufacturer']) + commatize(entry['ComponentName']) + \
                                 commatize(entry['Value']) + commatize(entry['Tolerance']) + \
                                 commatize(entry['ValueII']) + commatize(entry['ValueIII'])
                        cCount = 1
                        cNote  = entry['Note']
                else:
                        # Fill comparsion structure
                        curBase  = ''.join([i for i in entry['Designator'] if not i.isdigit()])
                        curDesc  = entry['Footprint'] + \
                                   commatize(entry['Manufacturer']) + commatize(entry['ComponentName']) + \
                                   commatize(entry['Value']) + commatize(entry['Tolerance']) + \
                                   commatize(entry['ValueII']) + commatize(entry['ValueIII'])
                        curNote  = entry['Note']

                        # Update conversion structure if data similar
                        if (curBase + curDesc + curNote) == (cBase + cDesc + cNote):
                                cLast  = entry['Designator']
                                cCount = cCount + 1
                        else:
                                tempbom.append({'Designator': des(cFirst, cLast, cCount),
                                                'Description': cDesc,
                                                'Count': cCount,
                                                'Note': cNote,
                                                'Base': cBase})
                                cBase  = ''.join([i for i in entry['Designator'] if not i.isdigit()])
                                cFirst = entry['Designator']
                                cLast  = entry['Designator']
                                cDesc  = entry['Footprint'] + \
                                         commatize(entry['Manufacturer']) + commatize(entry['ComponentName']) + \
                                         commatize(entry['Value']) + commatize(entry['Tolerance']) + \
                                         commatize(entry['ValueII']) + commatize(entry['ValueIII'])
                                cCount = 1
                                cNote  = entry['Note']
                                
        tempbom.append({'Designator': des(cFirst, cLast, cCount),
                        'Description': cDesc,
                        'Count': cCount,
                        'Note': cNote,
                        'Base': cBase})

# Read component groups csv
cgroups = []

with open('cgroups.csv', 'r', encoding='utf-8') as cgroupscsv:
        cgroupsreader = csv.reader(cgroupscsv, delimiter=',', quotechar='"')
        for entry in cgroupsreader:
                cgroups.append({'Base': entry[0], 'Single': entry[1], 'Multi': entry[2]})

# Generate out BOM
outbom = []      # Output BOM
lastgroup = []   # Last component group
singletitle = '' # Last goup titles
multititle = ''


def getsingle(base):
        global cgroups
        for entry in cgroups:
                if entry['Base'] == base:
                        return entry['Single']
        return "Неизвестный компонент"

def getmulti(base):
        global cgroups
        for entry in cgroups:
                if entry['Base'] == base:
                        return entry['Multi']
        return "Неизвестные компоненты"

def outputgroup():
        global lastgroup
        global outbom
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

for entry in tempbom:
        # First iteration
        if multititle == '':
                lastgroup.append({'Designator': entry['Designator'],
                                  'Description': entry['Description'],
                                  'Count': entry['Count'],
                                  'Note': entry['Note']})
                singletitle = getsingle(entry['Base'])
                multititle =  getmulti(entry['Base'])
        # Extend group
        elif getmulti(entry['Base']) == multititle:
                lastgroup.append({'Designator': entry['Designator'],
                                  'Description': entry['Description'],
                                  'Count': entry['Count'],
                                  'Note': entry['Note']})
        # Output group, make new group
        else:
                # Output group
                outputgroup()
                
                # Flush and fill group
                lastgroup = []
                lastgroup.append({'Designator': entry['Designator'],
                                  'Description': entry['Description'],
                                  'Count': entry['Count'],
                                  'Note': entry['Note']})
                singletitle = getsingle(entry['Base'])
                multititle =  getmulti(entry['Base'])
# Output group
outputgroup()

# Result print
for entry in outbom:
        print(entry['Designator'], '|',
              entry['Description'], '|',
              entry['Count'], '|',
              entry['Note'])

# Write gost-bom.csv
with open('gost-bom.csv', 'w', encoding='utf-8', newline='') as gostbomcsv:
    fieldnames = ['Designator', 'Description', 'Count', 'Note']
    writer = csv.DictWriter(gostbomcsv, fieldnames=fieldnames)

    writer.writeheader()
    for entry in outbom:
            writer.writerow({'Designator': entry['Designator'],
                             'Description': entry['Description'],
                             'Count': entry['Count'],
                             'Note': entry['Note']})
    


