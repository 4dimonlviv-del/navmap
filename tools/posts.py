#!/usr/bin/env python3
"""Стаціонарні пости поліції з OSM (відповідь Overpass у JSON) -> posts.csv у форматі бази камер застосунку:
lat,lon,-1,,id,назва  (-1 у полі обмеження = «пост поліції», id від'ємний, щоб не збігся з камерами).
Беремо amenity=police з police=traffic_police або з назвою поста ДАІ/ДПС/патрульної поліції.
НЕ беремо (ст. 114-2 КК: жодних блокпостів/КПП/військових чи прикордонних об'єктів): police=checkpoint, назви з
«блок», «КПП», «кордон», «військ», «ЗСУ», «митн». Також без контор і будівель (управління, відділ, МРЕВ, ТСЦ, полк...).
"""
import json, re, sys, datetime
d = json.load(open(sys.argv[1], encoding='utf-8'))
# назва має прямо вказувати на дорожню поліцію (просто «Пост» біля кордону може бути прикордонним -- не беремо)
INC = re.compile(r'поліц|полиц|ДАІ|ДАI|ДАЇ|ДАИ|ГАИ|ДПС(?!У)|патрульн|\bПП\b', re.I)
EXC = re.compile(r'блок|КПП|кордон|військ|воєнкомат|військкомат|ТЦК|ДПСУ|полігон|ЗСУ|митн|checkpoint'
                 r'|покинут|залишен|зачинен|закрит'
                 r'|управлін|управлен|відділ|отдел|МРЕВ|МРЕО|ТСЦ|УДАІ|ВДАІ|УМВС|ГУМВС|сервісн|центр|філія|дільниц|пункт|інспекц|Національн'
                 r'|батальйон|батальон|полк|район|р-н|міськ|муніц|охорон|департамент|академ|училищ|штаб', re.I)
TYPE = {'n': 1, 'w': 2, 'r': 3}
rows = []
for e in d.get('elements', []):
    t = e.get('tags', {})
    if t.get('amenity') != 'police': continue
    kind = t.get('police', '')
    if kind == 'checkpoint' or t.get('military') or t.get('barrier') == 'border_control': continue
    name = (t.get('name') or t.get('name:uk') or '').replace(',', ' ').strip()
    if not (kind == 'traffic_police' or INC.search(name)): continue
    if EXC.search(name): continue
    la = e.get('lat') or (e.get('center') or {}).get('lat'); lo = e.get('lon') or (e.get('center') or {}).get('lon')
    if la is None or lo is None: continue
    rows.append((la, lo, -(e['id'] * 10 + TYPE.get(e['type'][0], 0)), name))
rows.sort()
with open(sys.argv[2], 'w', encoding='utf-8', newline='\n') as f:
    f.write('# стаціонарні пости поліції з OpenStreetMap (© учасники OpenStreetMap, ODbL); %s; %d шт.\n' % (datetime.date.today().isoformat(), len(rows)))
    f.write('lat,lon,maxspeed,dir,osm_id,name\n')
    for r in rows: f.write('%.6f,%.6f,-1,,%d,%s\n' % r)
print('постів: %d' % len(rows))
for r in rows: print('%.5f,%.5f %s' % (r[0], r[1], r[3]))
