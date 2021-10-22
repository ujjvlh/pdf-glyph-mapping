import pdftotext
import PyPDF2
import pdfplumber
import re
from pathlib import Path

i = 0

s = []

fixed = '../../gp-mbh/unabridged.fixed.pdf'

pypdf = PyPDF2.PdfFileReader(open(fixed, 'rb'))
plumber = pdfplumber.open(fixed)

#for pg in pdftotext.PDF(open(fixed, 'rb'), raw=True):
#for n in range(pypdf.numPages):
for page in plumber.pages:
  #pg = pypdf.getPage(n).extractText()
  pg = page.extract_text()
  print(pg)
  r = [
    ('\[sl\]', '<i>'),
    ('\[\/sl\]', '</i>'),
    (r'\[\/[^\[\]]*-Bold\]', '</b>'),
    (r'\[[^\[\]]*-Bold\]', '<b>'),
    (r'\[[!-Z\\^-~]+\]', ''),
    (r'<\/([^>]*)>([ \n]*)<\1>', r'\2'),
    #(r' +', ' '),
  ]
  for x in r:
    pg = re.sub(x[0], x[1], pg)
  a = ''
  c = pg
  while a != c:
    a = c
    c = re.sub(r'(.)<CCsucc>(([क-हक़-य़]़?्)*[क-हक़-य़]़?)', r'\2\1', a)
    c = re.sub(r'(([क-हक़-य़]़?्)*[क-हक़-य़ऋ][^क-हक़-य़ऋ]*)र्<CCprec>', r'र्\1', c)
    c = c.replace('र्ऋ', 'रृ')
  i += 1
  Path("../../ujjvlh/gp-mbh/txt/").mkdir(parents=True, exist_ok=True)
  with open('../../ujjvlh/gp-mbh/txt/' + str(i).rjust(5, '0') + '.txt', 'w+') as f:
    f.write(a)
  s.append(f'<PAGE {i} BEGIN>\n' + a + f'\n<PAGE {i} END>')
  print(i)

with open('out.txt', 'w+') as f:
  f.write('\n'.join(s))
