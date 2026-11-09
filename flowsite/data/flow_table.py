"""三大法人買賣超 table + 台灣/韓國外資 daily bar charts -> PNG.

Usage: python3 flow_table.py <tw_flows.csv> <kr_flows.csv> <out.png> [email.html] [public_image_url]

tw_flows.csv: date,外資,自營商,投信            (TWD mn, TWSE 上市; 外資 = 外資及陸資不含外資自營商)
kr_flows.csv: date,韓國外資_USDmn              (US$ mn)
A row exists only for a trading day. An empty value on a row = trading day but
figure not yet verified -> shown as 尚未公布. A date missing from one market but
present in the other -> shown as 休市.
"""
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from matplotlib.patches import Rectangle

tw_path, kr_path, out = sys.argv[1:4]
plt.rcParams["font.family"] = "Noto Sans CJK TC"
INK, MUTED, GRID, RED, BLUE, HEAD, LINE = "#1f2328", "#6b7280", "#e5e7eb", "#c62828", "#3b6ea8", "#eef2f7", "#9aa3ad"

tw = pd.read_csv(tw_path, parse_dates=["date"]).set_index("date").sort_index()
tw.columns = ["fi", "de", "tr"]
kr = pd.read_csv(kr_path, parse_dates=["date"]).set_index("date").sort_index().iloc[:, 0]

dates = tw.index.union(kr.index)
last = dates.max()
rows_dates = dates[-5:][::-1]
yr, mo = last.year, last.month
m_start = pd.Timestamp(yr, mo, 1)
q_start = pd.Timestamp(yr, (mo - 1) // 3 * 3 + 1, 1)
y_start = pd.Timestamp(yr, 1, 1)


def cell(v):
    """(text, value-or-None) for a single-day cell."""
    if v is None:
        return "休市", None
    if pd.isna(v):
        return "尚未公布", None
    return f"{v:,.0f}", v


rows = []
for d in rows_dates:
    r = [f"{d.month}/{d.day}"]
    for c in ("fi", "de", "tr"):
        r.append(cell(tw.at[d, c] if d in tw.index else None))
    r.append(cell(kr.at[d] if d in kr.index else None))
    rows.append(r)
for lab, s in (("MTD", m_start), ("QTD", q_start), ("YTD", y_start)):
    t = tw[s:last]
    r = [lab] + [(f"{t[c].sum():,.0f}", t[c].sum()) for c in ("fi", "de", "tr")]
    kv = kr[s:last].sum()
    r.append((f"{kv:,.0f}", kv))
    rows.append(r)

cols = ["NT$ Mn", "外資", "自營商\n(含外資自營商)", "投信", "韓國外資買賣超\n(US$ Mn)"]
H = 13.3
fig = plt.figure(figsize=(10, H), dpi=200, facecolor="white")
ax = fig.add_axes([0.04, (H - 0.644 - 3.96) / H, 0.92, 3.96 / H])
ax.set_axis_off()
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
fig.text(0.04, (H - 0.414) / H, f"三大法人買賣超－{last.month:02d}{last.day:02d}", fontsize=17, weight="bold", color=INK)

xs = [0.0, 0.16, 0.38, 0.60, 0.78, 1.0]
n = len(rows) + 1
rh = 1 / n
ax.add_patch(Rectangle((0, 1 - rh), 1, rh, color=HEAD, lw=0))
for i, c in enumerate(cols):
    ax.text((xs[i] + xs[i + 1]) / 2, 1 - rh / 2, c, ha="center", va="center", fontsize=11, weight="bold", color=INK, linespacing=1.2)
for r, row in enumerate(rows):
    y0 = 1 - rh * (r + 2)
    if r == 0:
        ax.add_patch(Rectangle((0, y0), 1, rh, color="#f6f7f9", lw=0))
    bold = "bold" if r >= 5 else "normal"
    ax.text((xs[0] + xs[1]) / 2, y0 + rh / 2, row[0], ha="center", va="center", fontsize=11.5, color=INK, weight=bold)
    for j, (txt, v) in enumerate(row[1:]):
        color = RED if (v is not None and v < 0) else INK
        ax.text(xs[j + 2] - 0.015, y0 + rh / 2, txt, ha="right", va="center", fontsize=11.5, color=color, weight=bold)
for r in range(n + 1):
    heavy = r in (0, 1, 6, n)
    ax.plot([0, 1], [1 - rh * r] * 2, color=INK if heavy else LINE, lw=1.6 if heavy else 0.6)
for x in xs:
    edge = x in (0.0, 1.0)
    ax.plot([x, x], [0, 1], color=INK if edge else LINE, lw=1.6 if edge else 0.6)

fig.text(0.04, (H - 4.83) / H,
         "註：韓國外資自 2026/10/6 起採韓國媒體 KOSPI 外資買賣超（韓元）÷ 當日 15:30 美元兌韓元收盤匯率換算；之前為原始歷史資料。",
         fontsize=8.5, color=MUTED)


def bar_panel(top_in, s, title, unit, windows):
    s = s.dropna()
    cx = fig.add_axes([0.09, (H - top_in - 3.3) / H, 0.87, 3.3 / H])
    cx.bar(s.index, s.values, width=0.8, color=[BLUE if v >= 0 else RED for v in s], linewidth=0)
    cx.axhline(0, color=INK, lw=0.8)
    cx.set_title(title, fontsize=12.5, weight="bold", color=INK, pad=8)
    cx.grid(axis="y", color=GRID, lw=0.8)
    cx.set_axisbelow(True)
    for sp in ("top", "right"):
        cx.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        cx.spines[sp].set_color(LINE)
    cx.tick_params(colors=MUTED, labelsize=9)
    cx.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, p: f"{v:,.0f}"))
    cx.xaxis.set_major_formatter(mdates.DateFormatter("%-m月"))
    cx.xaxis.set_major_locator(mdates.MonthLocator())
    cx.set_xlim(mdates.date2num(y_start) - 3, mdates.date2num(last) + 6)
    hi = max(s.max(), 0) * 1.35
    cx.set_ylim(min(s.min(), 0) * 1.25, hi)
    for a, b in windows:
        a, b = pd.Timestamp(a), pd.Timestamp(b)
        seg = s[a:b]
        if seg.empty or a < y_start:
            continue
        cx.add_patch(Rectangle((mdates.date2num(a) - 1, seg.min() * 1.08), (b - a).days + 2,
                               -seg.min() * 1.08 + hi * 0.06, fill=False, ec=RED, lw=1.2))
        tot = -seg.sum() / 1000
        amt = f"{tot:,.1f}" if unit == "US$" else f"{tot:,.0f}"
        cx.text(a + (b - a) / 2, hi * 0.62, f"{a.month}/{a.day}~{b.month}/{b.day}\n累計賣超 {unit}{amt}B",
                ha="center", va="center", fontsize=9.5, color=INK, weight="bold", linespacing=1.3)


bar_panel(5.34, tw.loc[y_start:last, "fi"], "台灣外資買賣超 (NT$ Mn)", "NT$",
          [("2026-02-26", "2026-03-31"), ("2026-06-23", "2026-07-17")])
bar_panel(9.45, kr.loc[y_start:last], "韓國外資買賣超 (US$ Mn)", "US$",
          [("2026-02-23", "2026-03-31"), ("2026-05-07", "2026-06-05")])

fig.savefig(out, facecolor="white")
print("saved", out, "| last date", last.date())

# Optional 4th arg: write an email-ready HTML table (inline styles only, Gmail-safe); 5th arg adds a link to the public PNG.
if len(sys.argv) > 4:
    ART = "https://claude.ai/artifact/NaAcnrVBtfhtF6QgT9QFND"
    td = "padding:6px 12px;border:1px solid #9aa3ad;font-variant-numeric:tabular-nums;"
    hdr = "".join(f'<th style="{td}background:#eef2f7;text-align:center;">{c.replace(chr(10), "<br>")}</th>' for c in cols)
    body = []
    for r, row in enumerate(rows):
        w = "font-weight:bold;" if r >= 5 else ""
        top = "border-top:2px solid #1f2328;" if r == 5 else ""
        bg = "background:#f6f7f9;" if r == 0 else ""
        cells = [f'<td style="{td}{w}{top}{bg}text-align:center;">{row[0]}</td>']
        for txt, v in row[1:]:
            color = "#c62828" if (v is not None and v < 0) else "#1f2328"
            cells.append(f'<td style="{td}{w}{top}{bg}text-align:right;color:{color};">{txt}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    img_url = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] else ""
    note = "註：韓國外資自 2026/10/6 起採韓國媒體 KOSPI 外資買賣超（韓元）÷ 當日 15:30 美元兌韓元收盤匯率換算；之前為原始歷史資料。"
    # Gmail's send tool strips <img>, so the email carries the table plus a clickable link to the PNG.
    link = (
        f'<p style="font-size:15px;margin:14px 0 0;"><a href="{img_url}" style="font-weight:bold;">點此開啟完整圖（含台灣／韓國外資每日買賣超長條圖）</a></p>'
        if img_url else ""
    )
    html = (
        f'<div style="font-family:Arial,\'Microsoft JhengHei\',\'PingFang TC\',sans-serif;color:#1f2328;">'
        f'<h2 style="margin:0 0 12px;font-size:20px;">三大法人買賣超－{last.month:02d}{last.day:02d}</h2>'
        f'<table style="border-collapse:collapse;font-size:14px;">\n<tr>{hdr}</tr>\n{chr(10).join(body)}\n</table>\n'
        f'<p style="font-size:12px;color:#6b7280;margin:8px 0 0;">{note}</p>'
        f'{link}'
        f'<p style="font-size:14px;margin:{"8px" if img_url else "14px"} 0 0;">資料與更新紀錄：<a href="{ART}">{ART}</a></p>'
        "</div>"
    )
    open(sys.argv[4], "w", encoding="utf-8").write(html)
    print("saved", sys.argv[4], len(html), "chars")
