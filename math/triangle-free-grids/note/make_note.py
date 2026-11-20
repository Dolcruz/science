"""Build the readable note (HTML with KaTeX) from the final alphabet and the results table.
usage: python3 make_note.py final.alpha results.tsv out.html"""
import sys, math, html

alpha_file, table_file, out = sys.argv[1:4]
rows = [l.split() for l in open(alpha_file) if l.strip()]
u, v = map(int, rows[0]); N = u * u + v * v
P = [(int(a), int(b)) for a, b in rows[1:]]
q = len(P)
alpha = 2 * math.log(q) / math.log(N)
R = max(math.hypot(*p) for p in P)

# count triangles
pos = {p: k for k, p in enumerate(P)}
ntri = 0
for (bx, by) in P:
    for (ax, ay) in P:
        c = (bx - (ay - by), by + (ax - bx))
        if c in pos and (ax, ay) != (bx, by):
            ntri += 1

# SVG figure: digits coloured by position in the peeling order
S = int(math.ceil(R)) + 1
cell = 11
W = (2 * S + 1) * cell
def col(t):  # t in [0,1] -> colour from deep blue to amber
    a = (40, 60, 140); b = (235, 160, 40)
    return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
svg = [f'<svg viewBox="0 0 {W} {W}" width="100%" style="max-width:440px" role="img" aria-label="digit alphabet">']
svg.append(f'<rect x="0" y="0" width="{W}" height="{W}" fill="none"/>')
for x in range(-S, S + 1):
    for y in range(-S, S + 1):
        cx = (x + S) * cell + cell / 2; cy = (S - y) * cell + cell / 2
        if (x, y) in pos:
            t = pos[(x, y)] / (q - 1)
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="{cell*0.42:.1f}" fill="{col(t)}"/>')
        else:
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="1" fill="var(--faint)"/>')
svg.append('</svg>')
svg = '\n'.join(svg)

table = [l.rstrip('\n').split('\t') for l in open(table_file) if l.strip() and not l.startswith('#')]
trs = '\n'.join('<tr>' + ''.join(f'<td>{html.escape(c)}</td>' for c in r) + '</tr>' for r in table)

digits = ''.join(f'<span>({x},&thinsp;{y})</span>' for x, y in P)

page = open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'note_template.html')).read()
for k, val in dict(U=u, V=v, N=N, Q=q, ALPHA=f'{alpha:.10f}', ALPHA4=f'{alpha:.4f}', NTRI=ntri,
                   NSOL=ntri + q, Q3=f'{q**3:,}', RMAX=f'{R:.2f}', SVG=svg, TABLE=trs, DIGITS=digits,
                   LOGQ=f'{math.log(q):.6f}', LOGN=f'{math.log(N):.6f}').items():
    page = page.replace('{{' + k + '}}', str(val))
open(out, 'w').write(page)
print('alpha', alpha, 'q', q, 'N', N, 'triangles', ntri)
