import pdftotext
import re

i = 0

s = []

for pg in pdftotext.PDF(open('../../gp-mbh/unabridged.fixed.pdf', 'rb')):
  a = ''
  c = pg
  while a != c:
    a = c
    c = re.sub(r'(.)<CCsucc>(([क-हक़-य़]़?्)*[क-हक़-य़]़?)', r'\2\1', a)
    c = re.sub(r'(([क-हक़-य़]़?्)*[क-हक़-य़ऋ][^क-हक़-य़ऋ]*)र्<CCprec>', r'र्\1', c)
    c = c.replace('र्ऋ', 'रृ')
  i += 1
  with open('../../ujjvlh/gp-mbh/txt/' + str(i).rjust(5, '0') + '.txt', 'w+') as f:
    f.write(a)
  s.append(f'<PAGE {i} BEGIN>\n' + a + f'\n<PAGE {i} END>')
  print(i)

with open('out.txt', 'w+') as f:
  f.write('\n'.join(s))
