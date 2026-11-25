#!/usr/bin/env python3
"""Стаціонарні пости поліції з OSM (відповідь Overpass у JSON) -> posts.csv (lat,lon,kind,osm_id,name).
Беремо лише те, що вже позначено на карті OpenStreetMap:
 - amenity=police з police=checkpoint або police=traffic_police;
 - amenity=police, у назві якого «пост»/«ДАІ»/«ДПС»/«КПП».
"""
import json, re, sys, datetime
d = json.load(open(sys.argv[1], encoding='utf-8'))
rows = []
for e in d.get('elements', []):
    t = e.get('tags', {})
    if t.get('amenity') != 'police': continue
    name = (t.get('name') or t.get('name:uk') or '').replace(',', ' ').strip()
    kind = t.get('police', '')
    if not (kind in ('checkpoint', 'traffic_police') or re.search(r'пост|ДАІ|ДАI|ДПС|КПП', name, re.I)): continue
    la = e.get('lat') or (e.get('center') or {}).get('lat'); lo = e.get('lon') or (e.get('center') or {}).get('lon')
    if la is None or lo is None: continue
    rows.append((la, lo, kind or 'name', '%s%d' % (e['type'][0], e['id']), name))
rows.sort()
with open(sys.argv[2], 'w', encoding='utf-8', newline='\n') as f:
    f.write('# стаціонарні пости поліції з OpenStreetMap (© учасники OpenStreetMap, ODbL); %s; %d шт.\n' % (datetime.date.today().isoformat(), len(rows)))
    f.write('lat,lon,kind,osm_id,name\n')
    for r in rows: f.write('%.6f,%.6f,%s,%s,%s\n' % r)
print('постів: %d' % len(rows))
