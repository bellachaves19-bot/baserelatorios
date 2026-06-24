"""
Gera o dashboard.html a partir do Excel em dados/Volumetria_Relatorios.xlsx
Execute: python gerar_dashboard.py
"""
import pandas as pd
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
EXCEL = ROOT / "dados" / "Volumetria_Relatorios.xlsx"
TEMPLATE = ROOT / "dashboard_template.html"
OUTPUT = ROOT / "dashboard.html"

if not EXCEL.exists():
    sys.exit(f"Erro: arquivo não encontrado em {EXCEL}")

print(f"Lendo {EXCEL.name}...")
xl = pd.ExcelFile(EXCEL)

# ── Painel Geral ──────────────────────────────────────────────────────
df = xl.parse("Painel Geral", header=None).iloc[2:]
df.columns = ["Cat","Classificacao","Nr","Cliente","KeyAccount","TipoEnvio","Areas_CJ","Areas_Trab","NrAreas"]
df = df[df["Cliente"].notna() & (df["Cliente"] != "Cliente")].fillna("")
df["NrAreas"] = pd.to_numeric(df["NrAreas"], errors="coerce").fillna(0).astype(int)
clientes = df[["Cat","Classificacao","Nr","Cliente","KeyAccount","TipoEnvio","Areas_CJ","Areas_Trab","NrAreas"]].to_dict("records")

# ── Detalhe Completo ──────────────────────────────────────────────────
dd = xl.parse("Detalhe Completo", header=None).iloc[2:]
dd.columns = ["Cat","Classificacao","Cliente","TipoEnvio","Area","PrazoFatal","Obs"]
dd = dd[dd["Cliente"].notna() & (dd["Cliente"] != "Cliente")].fillna("")
providencias = dd[["Cat","Classificacao","Cliente","TipoEnvio","Area","PrazoFatal","Obs"]].to_dict("records")

# ── Clientes CX ───────────────────────────────────────────────────────
cx = xl.parse("Clientes CX", header=None).iloc[2:]
cx.columns = ["EmpresaCX","KeyAccount","Cliente","TipoEnvio","Areas","NrAreas"]
cx = cx[cx["Cliente"].notna() & (cx["Cliente"] != "Cliente (cadastro)")].fillna("")
cx_map = {row["Cliente"]: row["EmpresaCX"] for _, row in cx.iterrows()}

# ── Estatísticas ───────────────────────────────────────────────────────
total_clientes  = len(clientes)
total_provs     = len(providencias)
total_cx        = sum(1 for c in clientes if c["Classificacao"] == "CX")
total_trab      = sum(1 for p in providencias if p["TipoEnvio"] == "Trabalhista")
total_trab_cli  = len({p["Cliente"] for p in providencias if p["TipoEnvio"] == "Trabalhista"})

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

# ── Inject nos placeholders do template ──────────────────────────────
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
