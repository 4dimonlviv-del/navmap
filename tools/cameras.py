#!/usr/bin/env python3
"""Камери контролю швидкості з OSM -> cameras.csv (lat,lon,maxspeed,dir,osm_id) для NavLogger.

Вхід -- файл OSM (.pbf/.osm), уже відфільтрований osmium tags-filter (n/highway=speed_camera r/type=enforcement),
разом із вузлами-учасниками відношень.
 - відношення type=enforcement + enforcement=maxspeed: кожен вузол device -> рядок; напрямок -- від вузла from до
   камери (або від камери до to); обмеження -- maxspeed відношення (або самої камери);
 - вузли highway=speed_camera, що не входять у такі відношення -> рядок без напрямку (попереджати в обидва боки).
Тег direction=* на камері ігноруємо: в OSM ним позначають то напрямок об'єктива, то напрямок руху.
"""
import math, re, sys, datetime
import osmium

def kmh(v):
    if not v: return 0
    m = re.match(r'^\s*(\d+(?:\.\d+)?)\s*(mph)?\s*$', v)
    if not m: return 0
    x = float(m.group(1)) * (1.609344 if m.group(2) else 1.0)
    return int(round(x)) if 5 <= x <= 200 else 0

def bearing(a, b):
    (la1, lo1), (la2, lo2) = a, b
    kx = math.cos(math.radians((la1 + la2) / 2))
    return (math.degrees(math.atan2((lo2 - lo1) * kx, la2 - la1)) + 360) % 360

class H(osmium.SimpleHandler):
    def __init__(self):
        super().__init__(); self.loc = {}; self.cam = {}; self.rel = []
    def node(self, n):
        if not n.location.valid(): return
        self.loc[n.id] = (n.location.lat, n.location.lon)
        if n.tags.get('highway') == 'speed_camera': self.cam[n.id] = kmh(n.tags.get('maxspeed'))
    def relation(self, r):
        if r.tags.get('type') != 'enforcement' or r.tags.get('enforcement') != 'maxspeed': return
        mem = [(m.type, m.ref, m.role) for m in r.members]
        self.rel.append((r.id, kmh(r.tags.get('maxspeed')), mem))

def main(src, dst):
    h = H(); h.apply_file(src)
    rows, used = [], set()
    for rid, ms, mem in h.rel:
        dev = [ref for t, ref, role in mem if t == 'n' and role == 'device' and ref in h.loc]
        fr = next((ref for t, ref, role in mem if t == 'n' and role == 'from' and ref in h.loc), None)
        to = next((ref for t, ref, role in mem if t == 'n' and role == 'to' and ref in h.loc), None)
        for d in dev:
            p = h.loc[d]
            if fr is not None and fr != d: dr = '%.0f' % bearing(h.loc[fr], p)
            elif to is not None and to != d: dr = '%.0f' % bearing(p, h.loc[to])
            else: dr = ''
            rows.append((p[0], p[1], ms or h.cam.get(d, 0), dr, d)); used.add(d)
    for nid, ms in h.cam.items():
        if nid in used: continue
        p = h.loc[nid]; rows.append((p[0], p[1], ms, '', nid))
    rows.sort(key=lambda r: (round(r[0], 3), r[1]))
    with open(dst, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# камери контролю швидкості з OpenStreetMap (© учасники OpenStreetMap, ODbL); %s; %d шт.\n'
                % (datetime.date.today().isoformat(), len(rows)))
        f.write('lat,lon,maxspeed,dir,osm_id\n')
        for la, lo, ms, dr, i in rows: f.write('%.6f,%.6f,%d,%s,%d\n' % (la, lo, ms, dr, i))
    print('камер: %d (з напрямком %d, з обмеженням %d)' % (len(rows), sum(1 for r in rows if r[3]), sum(1 for r in rows if r[2])))
    if len(rows) < 1: sys.exit('порожньо -- щось не так з даними')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
