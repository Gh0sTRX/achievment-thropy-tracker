"""Normalize explicitly identifiable unlock timestamps without guessing locale."""
from __future__ import annotations
from datetime import datetime, timedelta
import re

MONTHS = {name:i for i,names in enumerate(
    ("jan","feb","mar","apr","may","jun","jul","aug","sep","oct","nov","dec"),1)
    for name in (names,)}
MONTHS.update({name:i for i,name in enumerate(('january','february','march','april','may','june','july','august','september','october','november','december'),1)})
MONTHS['sept']=9

def _calendar(y, m, d, time=''):
    try:
        base = datetime(int(y),int(m),int(d))
        if not time:
            return base.date().isoformat()
        time = time.strip()
        if not time: return base.date().isoformat()
        match = re.fullmatch(r'(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)?',time,re.I)
        if not match: return ''
        hh,mm,ss = int(match[1]),int(match[2]),int(match[3] or 0)
        meridiem = (match[4] or '').upper()
        if meridiem:
            if not 1 <= hh <= 12: return ''
            hh = (hh % 12) + (12 if meridiem=='PM' else 0)
        dt=base.replace(hour=hh,minute=mm,second=ss)
        return dt.isoformat(timespec='seconds')
    except (ValueError,OverflowError,TypeError): return ''

def normalize_unlock_date(value):
    """Return ISO-8601 or empty for invalid/ambiguous dates. No assumed timezone."""
    if not isinstance(value,str):return ''
    value=re.sub(r'\s+',' ',value.strip())[:100]
    if not value:return ''
    if re.fullmatch(r'\d{5}(?:\.\d{1,10})?',value):
        serial=float(value)
        if 25569<=serial<=73415:
            result=datetime(1899,12,30)+timedelta(seconds=round(serial*86400))
            return result.date().isoformat() if serial.is_integer() else result.isoformat(timespec='seconds')
        return ''
    iso=re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:?\d{2})?))?',value,re.I)
    if iso:
        y,m,d=map(int,iso.group(1,2,3))
        try:
            if not iso[4]:return datetime(y,m,d).date().isoformat()
            clock=iso[4].replace('Z','+00:00').replace('z','+00:00')
            if re.search(r'[+-]\d{4}$',clock):clock=clock[:-2]+':'+clock[-2:]
            dt=datetime.fromisoformat(f'{y:04d}-{m:02d}-{d:02d}T{clock}')
            return dt.isoformat(timespec='microseconds' if dt.microsecond else 'seconds')
        except ValueError:return ''
    numeric=re.fullmatch(r'(\d{1,4})[/.](\d{1,2})[/.](\d{2,4})(?:\s+(?:at\s+)?(.+))?',value,re.I)
    if numeric:
        a,b,c=numeric.group(1,2,3)
        clock=numeric[4] or ''
        if len(a)==4:return _calendar(a,b,c,clock)
        if len(c)!=4:return ''
        a,b=int(a),int(b)
        if a>12 and b<=12:return _calendar(c,b,a,clock)  # dd/mm
        if b>12 and a<=12:return _calendar(c,a,b,clock)  # mm/dd
        return ''
    english=re.fullmatch(r'(\d{1,2})[ -]([A-Za-z]{3,12})[ ,\-]+(\d{4})(?:\s+(?:at\s+)?(.+))?',value,re.I)
    if english:
        month=MONTHS.get(english[2].lower())
        return _calendar(english[3],month,english[1],english[4] or '') if month else ''
    english=re.fullmatch(r'([A-Za-z]{3,12})\s+(\d{1,2}),?\s+(\d{4})(?:\s+(?:at\s+)?(.+))?',value,re.I)
    if english:
        month=MONTHS.get(english[1].lower())
        return _calendar(english[3],month,english[2],english[4] or '') if month else ''
    return ''


def normalize_unlock(value):
    """Backward-compatible name; all import paths use the same validated parser."""
    return normalize_unlock_date(value)
