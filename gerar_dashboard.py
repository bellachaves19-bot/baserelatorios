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
