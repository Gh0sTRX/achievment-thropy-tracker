"""Render the original Atlas application mark (no third-party game artwork)."""
from pathlib import Path
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1]/'assets';root.mkdir(exist_ok=True)
n=1024;image=Image.new('RGBA',(n,n));pixels=image.load()
for y in range(n):
 for x in range(n):
  t=(x+y)/(2*n);pixels[x,y]=(int(16+14*t),int(25+12*t),int(43+17*t),255)
mask=Image.new('L',(n,n));ImageDraw.Draw(mask).rounded_rectangle((12,12,1012,1012),radius=240,fill=255);image.putalpha(mask)
d=ImageDraw.Draw(image)
d.rounded_rectangle((24,24,1000,1000),radius=230,outline=(135,177,246,160),width=12)
d.line([(238,776),(467,242),(550,242),(792,776)],fill=(242,249,255),width=96,joint='curve')
d.line([(355,576),(666,576)],fill=(105,237,224),width=72)
d.ellipse((754,174,852,272),fill=(154,149,255))
image.save(root/'atlas-mark.png');image.save(root/'achievement-atlas.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
(root/'atlas-mark.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><defs><linearGradient id="b" x2="1" y2="1"><stop stop-color="#10192b"/><stop offset="1" stop-color="#1e253c"/></linearGradient></defs><rect x="12" y="12" width="1000" height="1000" rx="240" fill="url(#b)"/><rect x="24" y="24" width="976" height="976" rx="230" fill="none" stroke="#87b1f6" stroke-width="12"/><path d="M238 776 467 242H550L792 776" fill="none" stroke="#f2f9ff" stroke-width="96" stroke-linejoin="round"/><path d="M355 576H666" stroke="#69ede0" stroke-width="72"/><circle cx="803" cy="223" r="49" fill="#9a95ff"/></svg>',encoding='utf-8')
