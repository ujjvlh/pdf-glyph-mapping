"""See Makefile (doit.sh) for how this is meant to be called.
"""

import glob
import os.path
import pathlib
import random
import re
import sys
import unicodedata
from collections import defaultdict
from typing import List, TypeVar

import toml

import devnagri_pdf_text
import validate_maps

T = TypeVar('T')


def split_list(big_list: List[T], delimiter: T) -> List[List[T]]:
    """Like string.split(foo), except for lists."""
    cur_list: List[T] = []
    parts: List[List[T]] = []
    for item in big_list:
        if item == delimiter:
            if cur_list:
                parts.append(cur_list)
                cur_list = []
        else:
            cur_list.append(item)
    if cur_list:
        parts.append(cur_list)
    return parts


class HtmlWriter:
    def __init__(self, font_id_main, num_glyphs, to_unicode) -> None:
        self.font_id_main = font_id_main
        self.num_glyphs = num_glyphs
        self.to_unicode = to_unicode
        self.added = 0

        self.html = r'''
<!doctype html>
<html>
<style>
body {
    background-color: #999999;
}
* {
    box-sizing: border-box;
}
.glyph-main {
    background-color: white;
    border:1px solid red;
}
.glyph-other {
    background-color: #888888;
    border: 1px dashed #111111;
}
</style>
<body>
''' + rf'''
<h1>{font_name}</h1>
<p>Using helper font ....</p>
<dl>'''
        self.footer = r'''
</body>
</html>'''

    def img_for_glyph(self, main_glyph, glyph):
        filename = f'../../glyphs/font-{self.font_id_main}.ttf/glyph-{glyph}.png'
        classname = "glyph-main" if glyph == main_glyph else "glyph-other"
        return f'<img title="{glyph}" src="{filename}" class="{classname}"/>'

    def run(self, main_glyph, sample_run):
        return f'<dd>{"".join(self.img_for_glyph(main_glyph, glyph) for glyph in sample_run)}</dd>'

    def add_glyph_id(self, glyph_id_str, times_seen, sample_runs):
        uni = self.to_unicode.get(glyph_id_str)
        if uni:
            print(f'{glyph_id_str} -> {uni}')
            assert isinstance(uni, list) and len(uni) == 1 and isinstance(uni[0], int), uni
            uni = uni[0]
            c = chr(uni)
            name = unicodedata.name(c)
            mapped_pdf = f'mapped in the PDF to 0x{uni} = {c} = {name}.'
        else:
            mapped_pdf = f'Not mapped in the PDF.'
        self.added += 1
        self.html += fr'''
<hr>
<dt>
  <p>Glyph ID {glyph_id_str} (Seen {times_seen} times; glyph {self.added} of {self.num_glyphs})</p>
  <p>{mapped_pdf}</p>
        '''
        for font in helpers:
            glyph_name_for_glyph_id, equivalents = helpers[font]
            if glyph_name_for_glyph_id:
                glyph_id = int(glyph_id_str, 16)
                name = glyph_name_for_glyph_id.get(glyph_id)
                if name:
                    mapped_helper = f'Mapped using the helper font {font} to name {name}:'
                    sequences = equivalents.get(name, [])
                    mapped_helper_sequences = []
                    for sequence in sequences:
                        print(f'Sequence for {name}: {sequence}')
                        if not all(isinstance(c, int) for c in sequence):
                            print(f'Skipping')
                            continue
                        as_str = ''.join(chr(c) for c in sequence)
                        as_names = ' followed by '.join(
                            f'{c:04X} (={unicodedata.name(chr(c))})' for c in sequence)
                        # Add the "helped" equivalent for this glyph id.
                        if glyph_id_str not in self.to_unicode:
                            self.to_unicode[glyph_id_str] = sequence
                        mapped_helper_sequences.append(f'{as_str} ({as_names})')
                else:
                    mapped_helper = f'(no name in helper font {font} for {glyph_id_str})'
                    mapped_helper_sequences = []
            else:
                mapped_helper = f'(no mapping for {font})'
                mapped_helper_sequences = []
            self.html += f'''
  <p>{mapped_helper} {f'({len(mapped_helper_sequences)} sequences)' if len(mapped_helper_sequences) > 1 else ''}</p>
  {chr(10).join('<li>' + sequence + '</li>' for sequence in mapped_helper_sequences)}
            '''
            if mapped_helper_sequences:
                pass
        self.html += f'''
</dt>
{chr(10).join(self.run(glyph_id_str, sample_run) for sample_run in sample_runs)}
<hr>
</div>
        '''


if __name__ == '__main__':
    random.seed(42)
    (font_usage_dir, glyphs_dir, helper_dir, out_dir) = sys.argv[1:]

    helpers = {}
    for helper_font in glob.glob(os.path.join(helper_dir, "*.ttx")):
        basename = pathlib.Path(pathlib.Path(helper_font).name).with_suffix('')
        helpers[basename] = devnagri_pdf_text.unicode_codepoints_for_glyph_id(open(helper_font).read())

    matches = glob.glob(os.path.join(font_usage_dir, '*.Tjs'))
    print(f'Found these Tj files: {matches}')
    assert len(matches) > 1
    for filename_tjs in matches:
        print(f'{filename_tjs=}')
        basename = pathlib.Path(filename_tjs).name
        print(f'{basename=}')
        font_id_main, font_id_generation = re.search(f'^font-([0-9]*)-([0-9]*)-(.*).Tjs$', basename).groups()[:2]
        font_id = f'font-{font_id_main}-{font_id_generation}'
        print(f'{font_id=}')
        assert font_id_generation == '0'
        font_name = pathlib.Path(basename).with_suffix('')
        print(f'{font_name=}')
        assert str(font_name).startswith(str(font_id)), (font_name, font_id)
        out_filename_html = pathlib.Path(out_dir).joinpath(basename).with_suffix('.html')
        print(f'{out_filename_html=}')
        out_filename_toml = out_filename_html.with_suffix('.toml')
        in_filename_toml = pathlib.Path(filename_tjs).with_suffix(".toml")
        print(f'{in_filename_toml=}')
        to_unicode = toml.load(open(in_filename_toml))
        lines = open(filename_tjs).readlines()
        samples_max = 20
        reservoir = defaultdict(list)  # A few samples for each glyph.
        seen = defaultdict(int)  # How many times each glyph was seen.
        for (n, line) in enumerate(lines):
            if n > 0 and n % 100000 == 0:
                print(f'({n * 100.0 / len(lines):05.2f}%) Done {n:7} lines of {len(lines)}.')
            # s = line.strip()
            # assert len(s) % 4 == 0
            # all_parts = [s[i:i+4] for i in range(0, len(s), 4)]
            s = line.strip().split()
            assert all(len(g) == 4 for g in s)
            all_parts = s
            actual_parts = split_list(all_parts, '0003')
            for parts in actual_parts:
                for glyph_id_str in parts:
                    seen[glyph_id_str] += 1
                    r = reservoir[glyph_id_str]
                    # The second condition here makes it slightly different from the usual.
                    if len(r) < samples_max:
                        if parts not in r:
                            r.append(parts)
                    else:
                        m = random.randrange(0, seen[glyph_id_str])
                        # If seen[glyph] = N, then m is uniformly distributed over the N values [0..N).
                        # So the probability that m < samples_max is samples_max / N,
                        # which is precisely what we want.
                        if m < samples_max and parts not in r:
                            r[m] = parts

        h = HtmlWriter(font_id_main, len(seen), to_unicode)
        for glyph_id_str in sorted(seen, key=lambda k: (seen[k], k), reverse=True):
            h.add_glyph_id(glyph_id_str, seen[glyph_id_str], reservoir[glyph_id_str])
        pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
        open(out_filename_html, 'w').write(h.html + h.footer)
        mapping = validate_maps.validate({key: {'replacement_codes': list(value)} for (key, value) in h.to_unicode.items()})
        toml.dump(mapping, open(out_filename_toml, 'w'))
