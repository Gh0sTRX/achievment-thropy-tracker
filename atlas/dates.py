"""Deterministic import dates. Ambiguous locale numbers are deliberately omitted."""
from datetime import datetime,timedelta
import re
MONTHS={m:i+1 for i,m in enumerate(('jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'))}
def normalize_unlock(value):
    text=str(value or '').strip()
    if not text:return ''
    try:
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:?\d{2})?)?',text):
            date=datetime.fromisoformat(text.replace('Z','+00:00'))
            return date.date().isoformat() if len(text)==10 else date.isoformat()
        # Explicit English month is independent of operating-system locale.
        m=re.fullmatch(r'(\d{1,2})[ -]([A-Za-z]{3})[ ,\-]+(\d{4})(?: (\d{2}:\d{2}(?::\d{2})?))?',text)
        if m and m[2].lower() in MONTHS:
            date=datetime(int(m[3]),MONTHS[m[2].lower()],int(m[1]))
            if m[4]:date=datetime.combine(date.date(),datetime.fromisoformat('2000-01-01T'+m[4]).time())
            return date.isoformat() if m[4] else date.date().isoformat()
        # Excel 1900-date-system serials only; exclude the fictitious 1900-02-29.
        if re.fullmatch(r'\d{5}(?:\.\d{1,10})?',text):
            serial=float(text)
            if 25569<=serial<=73415:
                date=datetime(1899,12,30)+timedelta(days=serial)
                return date.date().isoformat() if serial.is_integer() else date.isoformat(timespec='seconds')
    except (ValueError,OverflowError):pass
    return ''
