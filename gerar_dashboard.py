"""
Gera o dashboard.html a partir do Excel em dados/Volumetria_Relatorios.xlsx
Execute: python gerar_dashboard.py

Formato suportado:
  Abas antigas: "Painel Geral" + "Detalhe Completo" + "Clientes CX"
  Abas novas:   "ENVIO CJ" + "ENVIO ÁREA"
    Coluna 0: "Cliente - Área - Envio C.J." ou "Cliente - Área - Envio área"
    Coluna 1: Observações
    Coluna 2: Prazo Interno
    Coluna 3: Prazo Fatal
"""
import pandas as pd
import json
import sys
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

ROOT   = Path(__file__).parent
EXCEL  = ROOT / "dados" / "Volumetria_Relatorios.xlsx"
TEMPLATE = ROOT / "dashboard_template.html"
OUTPUT = ROOT / "dashboard.html"

if not EXCEL.exists():
    sys.exit(f"Erro: arquivo não encontrado em {EXCEL}")

print(f"Lendo {EXCEL.name}...")
xl = pd.ExcelFile(EXCEL)
sheets = xl.sheet_names
print(f"  Abas encontradas: {sheets}")

# ── Helper: formatar data ─────────────────────────────────────────
def fmt_date(val):
    if pd.isna(val) or val == "":
        return ""
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    # already YYYY-MM-DD
    if len(s) == 10 and s[4] == "-":
        return s
    return s

# ── Helper: parse "Cliente - Área - Envio X" ─────────────────────
def parse_providencia(texto, sheet_name):
    texto = str(texto).strip()
    partes = texto.rsplit(" - ", 2)
    if len(partes) == 3:
        cliente, area, envio_raw = partes
    elif len(partes) == 2:
        cliente, area = partes
        envio_raw = ""
    else:
        return None

    envio_raw_lower = envio_raw.lower()
    if "área" in envio_raw_lower or "area" in envio_raw_lower:
        tipo_envio = "Trabalhista"
    elif "c.j" in envio_raw_lower or "cj" in envio_raw_lower:
        tipo_envio = "C.J."
    elif "ÁREA" in sheet_name.upper() or "AREA" in sheet_name.upper():
        tipo_envio = "Trabalhista"
    else:
        tipo_envio = "C.J."

    return cliente.strip(), area.strip(), tipo_envio

# ── Formato NOVO: ENVIO CJ / ENVIO ÁREA ──────────────────────────
def parse_new_format(xl, sheets):
    providencias = []
    for sheet in sheets:
        df = xl.parse(sheet, header=None)
        # Find header row (contains "Providência")
        header_row = None
        for i, row in df.iterrows():
            vals = [str(v).strip() for v in row.values]
            if any("Providência" in v or "Providencia" in v for v in vals):
                header_row = i
                break
        start = (header_row + 1) if header_row is not None else 0

        for _, row in df.iloc[start:].iterrows():
            texto = row.iloc[0]
            if pd.isna(texto) or str(texto).strip() == "":
                continue
            parsed = parse_providencia(texto, sheet)
            if not parsed:
                continue
            cliente, area, tipo_envio = parsed
            obs = "" if pd.isna(row.iloc[1]) else str(row.iloc[1]).replace("\n", " ").strip()
            prazo = fmt_date(row.iloc[3]) if len(row) > 3 else ""
            providencias.append({
                "Cat": "", "Classificacao": "",
                "Cliente": cliente, "TipoEnvio": tipo_envio,
                "Area": area, "PrazoFatal": prazo, "Obs": obs
            })
    return providencias

# ── Formato ANTIGO: Painel Geral / Detalhe Completo / Clientes CX ─
def parse_old_format(xl):
    df = xl.parse("Painel Geral", header=None).iloc[2:]
    df.columns = ["Cat","Classificacao","Nr","Cliente","KeyAccount","TipoEnvio","Areas_CJ","Areas_Trab","NrAreas"]
    df = df[df["Cliente"].notna() & (df["Cliente"] != "Cliente")].fillna("")
    df["NrAreas"] = pd.to_numeric(df["NrAreas"], errors="coerce").fillna(0).astype(int)
    clientes = df[["Cat","Classificacao","Nr","Cliente","KeyAccount","TipoEnvio","Areas_CJ","Areas_Trab","NrAreas"]].to_dict("records")

    dd = xl.parse("Detalhe Completo", header=None).iloc[2:]
    dd.columns = ["Cat","Classificacao","Cliente","TipoEnvio","Area","PrazoFatal","Obs"]
    dd = dd[dd["Cliente"].notna() & (dd["Cliente"] != "Cliente")].fillna("")
    providencias = dd[["Cat","Classificacao","Cliente","TipoEnvio","Area","PrazoFatal","Obs"]].to_dict("records")

    cx = xl.parse("Clientes CX", header=None).iloc[2:]
    cx.columns = ["EmpresaCX","KeyAccount","Cliente","TipoEnvio","Areas","NrAreas"]
    cx = cx[cx["Cliente"].notna() & (cx["Cliente"] != "Cliente (cadastro)")].fillna("")
    cx_map = {row["Cliente"]: row["EmpresaCX"] for _, row in cx.iterrows()}

    return clientes, providencias, cx_map

# ── Derive clientes from providências (novo formato) ─────────────
def derive_clientes(providencias):
    cli_areas  = defaultdict(set)
    cli_tipo   = defaultdict(set)
    for p in providencias:
        c = p["Cliente"]
        cli_areas[c].add(p["Area"])
        cli_tipo[c].add(p["TipoEnvio"])

    clientes = []
    for i, (c, areas) in enumerate(sorted(cli_areas.items()), start=1):
        tipos = cli_tipo[c]
        if "C.J." in tipos and "Trabalhista" in tipos:
            tipo_envio = "C.J. + Trabalhista"
            cls = "Multi-área · C.J."
        elif "Trabalhista" in tipos:
            tipo_envio = "Trabalhista"
            cls = "Área única" if len(areas) == 1 else "Multi-área · Trabalhista"
        else:
            tipo_envio = "C.J."
            cls = "Área única" if len(areas) == 1 else "Multi-área · C.J."

        areas_cj   = " | ".join(a for a in sorted(areas) if tipo_envio != "Trabalhista") or "—"
        areas_trab = " | ".join(a for a in sorted(areas) if tipo_envio != "C.J.")       or "—"
        clientes.append({
            "Cat": "○", "Classificacao": cls, "Nr": i, "Cliente": c,
            "KeyAccount": "", "TipoEnvio": tipo_envio,
            "Areas_CJ": areas_cj, "Areas_Trab": areas_trab, "NrAreas": len(areas)
        })
    return clientes

# ── Detect format and parse ───────────────────────────────────────
NEW_SHEETS = {"ENVIO CJ", "ENVIO ÁREA", "ENVIO AREA"}
if any(s.upper() in {x.upper() for x in NEW_SHEETS} for s in sheets):
    print("  Formato detectado: NOVO (ENVIO CJ / ENVIO ÁREA)")
    providencias = parse_new_format(xl, sheets)
    clientes     = derive_clientes(providencias)
    cx_map       = {}
else:
    print("  Formato detectado: ANTIGO (Painel Geral / Detalhe Completo)")
    clientes, providencias, cx_map = parse_old_format(xl)

# ── Estatísticas ──────────────────────────────────────────────────
total_clientes = len(clientes)
total_provs    = len(providencias)
total_cx       = sum(1 for c in clientes if c["Classificacao"] == "CX")
total_trab_cli = len({p["Cliente"] for p in providencias if p["TipoEnvio"] == "Trabalhista"})

cat_counts = {}
for c in clientes:
    cat_counts[c["Classificacao"]] = cat_counts.get(c["Classificacao"], 0) + 1

envio_counts = {}
for c in clientes:
    envio_counts[c["TipoEnvio"]] = envio_counts.get(c["TipoEnvio"], 0) + 1

area_counts = {}
for p in providencias:
    area_counts[p["Area"]] = area_counts.get(p["Area"], 0) + 1
area_counts_sorted = dict(sorted(area_counts.items(), key=lambda x: -x[1]))

hoje = date.today().strftime("%d/%m/%Y")

# ── Inject nos placeholders do template ──────────────────────────
template = TEMPLATE.read_text(encoding="utf-8")

# ── Design v2: patch visual antes dos placeholders ────────────────
_CSS_V2 = """<style id="design-v2">
.container{padding:32px 36px 64px}
.sec{display:block;margin-bottom:24px;padding-bottom:10px;border-bottom:1px solid rgba(0,158,219,.18)}
.sec::after{display:none}
.kpi-grid{grid-template-columns:2fr 1fr 1fr 1fr;gap:16px;margin-bottom:32px}
.kpi{padding:28px 28px 22px;transition:border-color .2s}
.kpi:hover{border-color:rgba(0,158,219,.4);transform:none}
.kpi-bar{display:none}
.kpi-label{font-size:9px;letter-spacing:.9px;margin-bottom:12px}
.kpi-value{font-size:48px;font-family:Georgia,'Times New Roman',serif;font-variant-numeric:tabular-nums;margin:0 0 8px}
.kpi.kpi-primary .kpi-value{font-size:64px}
.kpi-accent-line{width:24px;height:3px;background:var(--c,var(--fius));border-radius:2px;margin-bottom:16px}
.card-hdr-bar{display:none}
.card-hdr h3{font-size:10px;letter-spacing:1px}
.card-hdr{margin-bottom:20px}
.charts-grid{gap:16px;margin-bottom:16px}
.card{padding:24px}
.card-hdr .cnt{font-variant-numeric:tabular-nums}
.trab-mini:hover{transform:none;border-color:rgba(0,158,219,.5)}
.cx-card:hover{transform:none;border-color:rgba(0,158,219,.65)}
.vd-kpi-value{font-family:Georgia,'Times New Roman',serif;font-variant-numeric:tabular-nums}
</style>"""
template = template.replace("</head>", _CSS_V2 + "\n</head>", 1)

# KPI grid: reorder (Providências → destaque) + trocar kpi-bar por kpi-accent-line
template = template.replace(
    '    <div class="kpi-grid">\n'
    '      <div class="kpi" style="--c:#009edb"><div class="kpi-bar"></div><div class="kpi-label">Total de Clientes</div><div class="kpi-value">{{TOTAL_CLIENTES}}</div><div class="kpi-sub">5 categorias ativas</div></div>\n'
    '      <div class="kpi" style="--c:#68c4d4"><div class="kpi-bar"></div><div class="kpi-label">Total de Providências</div><div class="kpi-value">{{TOTAL_PROVIDENCIAS}}</div><div class="kpi-sub">Cadastradas e ativas</div></div>\n'
    '      <div class="kpi" style="--c:#efc517"><div class="kpi-bar"></div><div class="kpi-label">Clientes CX — Cat. 1</div><div class="kpi-value">{{TOTAL_CX}}</div><div class="kpi-sub">Com Key Account dedicado</div></div>\n'
    '      <div class="kpi" style="--c:#8ebf22"><div class="kpi-bar"></div><div class="kpi-label">Fluxo Trabalhista</div><div class="kpi-value">{{TOTAL_TRAB_CLI}}</div><div class="kpi-sub">Envio diferenciado</div></div>\n'
    '    </div>',
    '    <div class="kpi-grid">\n'
    '      <div class="kpi kpi-primary" style="--c:#009edb"><div class="kpi-accent-line"></div><div class="kpi-label">Total de Providências</div><div class="kpi-value">{{TOTAL_PROVIDENCIAS}}</div><div class="kpi-sub">Cadastradas e ativas</div></div>\n'
    '      <div class="kpi" style="--c:#68c4d4"><div class="kpi-accent-line" style="background:#68c4d4"></div><div class="kpi-label">Total de Clientes</div><div class="kpi-value">{{TOTAL_CLIENTES}}</div><div class="kpi-sub">5 categorias ativas</div></div>\n'
    '      <div class="kpi" style="--c:#efc517"><div class="kpi-accent-line" style="background:#efc517"></div><div class="kpi-label">Clientes CX — Cat. 1</div><div class="kpi-value">{{TOTAL_CX}}</div><div class="kpi-sub">Com Key Account dedicado</div></div>\n'
    '      <div class="kpi" style="--c:#8ebf22"><div class="kpi-accent-line" style="background:#8ebf22"></div><div class="kpi-label">Fluxo Trabalhista</div><div class="kpi-value">{{TOTAL_TRAB_CLI}}</div><div class="kpi-sub">Envio diferenciado</div></div>\n'
    '    </div>'
)

# VD KPIs: substituir kpi-bar por kpi-accent-line
for _old, _new in [
    ('<div class="kpi" style="--c:var(--fius)"><div class="kpi-bar"></div><div class="kpi-label">Total</div>',
     '<div class="kpi" style="--c:var(--fius)"><div class="kpi-accent-line"></div><div class="kpi-label">Total</div>'),
    ('<div class="kpi" style="--c:var(--green)"><div class="kpi-bar"></div><div class="kpi-label">Mensal</div>',
     '<div class="kpi" style="--c:var(--green)"><div class="kpi-accent-line" style="background:var(--green)"></div><div class="kpi-label">Mensal</div>'),
    ('<div class="kpi" style="--c:var(--teal)"><div class="kpi-bar"></div><div class="kpi-label">Trimestral</div>',
     '<div class="kpi" style="--c:var(--teal)"><div class="kpi-accent-line" style="background:var(--teal)"></div><div class="kpi-label">Trimestral</div>'),
    ('<div class="kpi" style="--c:var(--purple)"><div class="kpi-bar"></div><div class="kpi-label">PPT / Outros</div>',
     '<div class="kpi" style="--c:var(--purple)"><div class="kpi-accent-line" style="background:var(--purple)"></div><div class="kpi-label">PPT / Outros</div>'),
]:
    template = template.replace(_old, _new)

# Injetar JS v2: arcAtraso() + redefinir kpiMini() + pendTable() com arco
_JS_V2 = """<script id="design-v2-js">
function arcAtraso(dias) {
  var pct = Math.min(dias / 90, 1);
  var sweep = pct * 270;
  var r = 14, cx = 18, cy = 18, sz = 36;
  var startAngle = -225 * Math.PI / 180;
  var endAngle = startAngle + sweep * Math.PI / 180;
  var x1 = cx + r * Math.cos(startAngle), y1 = cy + r * Math.sin(startAngle);
  var x2 = cx + r * Math.cos(endAngle),   y2 = cy + r * Math.sin(endAngle);
  var large = sweep > 180 ? 1 : 0;
  var col = dias > 30 ? '#bb274b' : dias > 7 ? '#ea5627' : '#efc517';
  var arcPath = sweep < 1 ? '' :
    'M '+x1.toFixed(2)+' '+y1.toFixed(2)+
    ' A '+r+' '+r+' 0 '+large+' 1 '+x2.toFixed(2)+' '+y2.toFixed(2);
  return '<svg width="'+sz+'" height="'+sz+'" viewBox="0 0 '+sz+' '+sz+'" aria-hidden="true" style="flex-shrink:0">'+
    (arcPath ? '<path d="'+arcPath+'" fill="none" stroke="'+col+'" stroke-width="3" stroke-linecap="round"/>' : '')+
  '</svg>';
}
function kpiMini(label, val, color) {
  return '<div class="kpi" style="--c:'+color+'">'+
    '<div class="kpi-accent-line" style="background:'+color+'"></div>'+
    '<div class="kpi-label">'+label+'</div>'+
    '<div class="kpi-value" style="font-size:36px">'+val+'</div></div>';
}
function pendTable(list, today) {
  if (!list.length) return '<div style="padding:20px;color:var(--gray);font-size:12px;text-align:center">Nenhum atraso ✓</div>';
  var sorted = list.slice().sort(function(a,b){ return a.PrazoFatal < b.PrazoFatal ? -1 : 1; });
  var rows = sorted.map(function(p){
    var dias = daysBetween(p.PrazoFatal, today);
    var cor = dias > 30 ? 'var(--red)' : dias > 7 ? 'var(--orange)' : 'var(--yellow)';
    return '<tr>'+
      '<td style="font-weight:700;font-size:12px">'+p.Cliente+'</td>'+
      '<td>'+p.Area+'</td>'+
      '<td>'+(p.PrazoFatal ? p.PrazoFatal.split('-').reverse().join('/') : '—')+'</td>'+
      '<td><div style="display:flex;align-items:center;gap:8px">'+
        arcAtraso(dias)+
        '<span style="color:'+cor+';font-weight:700;font-size:11px;font-variant-numeric:tabular-nums">+'+dias+' dia'+(dias!==1?'s':'')+'</span>'+
      '</div></td>'+
      '<td><button class="pend-done-btn"'+
        ' data-c="'+p.Cliente.replace(/"/g,'&quot;')+'"'+
        ' data-a="'+p.Area.replace(/"/g,'&quot;')+'"'+
        ' data-pf="'+p.PrazoFatal+'"'+
        ' data-te="'+p.TipoEnvio+'"'+
        ' data-ob="'+encodeURIComponent(p.Obs||'')+'"'+
        ' style="background:rgba(88,176,49,.15);border:1px solid rgba(88,176,49,.4);border-radius:6px;padding:4px 10px;color:var(--green2);font-size:10px;font-weight:700;cursor:pointer;font-family:Verdana,sans-serif">'+
        '✓ Marcar cumprido</button>'+
      '</td></tr>';
  }).join('');
  return '<table><thead><tr><th>Cliente</th><th>Área</th><th>Prazo</th><th>Atraso</th><th></th></tr></thead><tbody>'+rows+'</tbody></table>';
}
</script>"""
template = template.replace("</body>", _JS_V2 + "\n</body>", 1)
# ── Fim design v2 ─────────────────────────────────────────────────

template = template.replace("{{DATA_ATUALIZACAO}}", hoje)
template = template.replace("{{TOTAL_CLIENTES}}", str(total_clientes))
template = template.replace("{{TOTAL_PROVIDENCIAS}}", str(total_provs))
template = template.replace("{{TOTAL_CX}}", str(total_cx))
template = template.replace("{{TOTAL_TRAB_CLI}}", str(total_trab_cli))
template = template.replace("{{CLIENTES_JSON}}", json.dumps(clientes, ensure_ascii=False))
template = template.replace("{{PROVIDENCIAS_JSON}}", json.dumps(providencias, ensure_ascii=False))
template = template.replace("{{CX_MAP_JSON}}", json.dumps(cx_map, ensure_ascii=False))
template = template.replace("{{CAT_VALUES_JSON}}", json.dumps([
    cat_counts.get("CX", 0),
    cat_counts.get("Trabalhista", 0),
    cat_counts.get("Multi-área · Trabalhista", 0),
    cat_counts.get("Multi-área · C.J.", 0),
    cat_counts.get("Área única", 0),
], ensure_ascii=False))
template = template.replace("{{ENVIO_VALUES_JSON}}", json.dumps([
    envio_counts.get("C.J.", 0),
    envio_counts.get("Trabalhista", 0),
    envio_counts.get("C.J. + Trabalhista", 0),
], ensure_ascii=False))
template = template.replace("{{AREA_COUNTS_JSON}}", json.dumps(area_counts_sorted, ensure_ascii=False))

OUTPUT.write_text(template, encoding="utf-8")
print(f"✓ dashboard.html gerado com sucesso ({total_clientes} clientes, {total_provs} providências) — {hoje}")
