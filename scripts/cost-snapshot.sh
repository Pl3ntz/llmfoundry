#!/usr/bin/env bash
# cost-snapshot.sh — congela baseline de uso de tokens do opencode.db
# Uso: scripts/cost-snapshot.sh [--json PATH]
# Saída: agregado por dia e por agente (tokens input/output/cache/custo), salvo em evals/tokens/
set -euo pipefail

DB="${OPENCODE_DB:-$HOME/.local/share/opencode/opencode.db}"
OUT_DIR="$(cd "$(dirname "$0")/.." && pwd)/evals/tokens"
mkdir -p "$OUT_DIR"

# Backup WAL-safe (nunca cp em banco com WAL)
BACKUP="$OUT_DIR/opencode-snapshot.db"
sqlite3 "$DB" ".backup '$BACKUP'"

NOW="$(date +%Y-%m-%d_%H%M%S)"
JSON="${1:-$OUT_DIR/baseline.json}"

python3 - "$BACKUP" "$JSON" <<'PYEOF'
import json, sqlite3, sys
from datetime import datetime, timezone

db, out = sys.argv[1], sys.argv[2]
con = sqlite3.connect(db)
cur = con.cursor()

def q(sql):
    return cur.execute(sql).fetchall()

# Total histórico
tot = q("""SELECT COUNT(*), COALESCE(SUM(tokens_input),0), COALESCE(SUM(tokens_output),0),
  COALESCE(SUM(tokens_reasoning),0), COALESCE(SUM(tokens_cache_read),0),
  COALESCE(SUM(tokens_cache_write),0), COALESCE(SUM(cost),0)
  FROM session""")[0]

# Últimos 14 dias, por dia
daily = []
for r in q("""SELECT date(time_created/1000,'unixepoch','localtime'), COUNT(*),
  COALESCE(SUM(tokens_input),0), COALESCE(SUM(tokens_output),0),
  COALESCE(SUM(tokens_cache_read),0), COALESCE(SUM(cost),0)
  FROM session
  WHERE time_created > (strftime('%s','now') - 14*86400)*1000
  GROUP BY date(time_created/1000,'unixepoch','localtime')
  ORDER BY 1 DESC"""):
    daily.append({"dia": r[0], "sessoes": r[1], "input": r[2], "output": r[3],
                  "cache_read": r[4], "custo": round(r[5], 4)})

# Por agente (todo histórico)
agents = []
for r in q("""SELECT agent, COUNT(*), ROUND(AVG(tokens_input),0), ROUND(AVG(tokens_output),0),
  ROUND(AVG(tokens_cache_read),0), COALESCE(SUM(tokens_input),0), COALESCE(SUM(cost),0)
  FROM session GROUP BY agent ORDER BY 6 DESC"""):
    agents.append({"agent": r[0], "sessoes": r[1], "avg_input": r[2], "avg_output": r[3],
                   "avg_cache_read": r[4], "tot_input": r[5], "custo": round(r[6], 4)})

# Por agente (últimos 4 dias — período free)
recent = []
for r in q("""SELECT agent, COUNT(*), ROUND(AVG(tokens_input),0), ROUND(AVG(tokens_output),0),
  ROUND(AVG(tokens_cache_read),0), COALESCE(SUM(tokens_input),0)
  FROM session
  WHERE time_created > (strftime('%s','now') - 4*86400)*1000
  GROUP BY agent ORDER BY 6 DESC"""):
    recent.append({"agent": r[0], "sessoes": r[1], "avg_input": r[2], "avg_output": r[3],
                   "avg_cache_read": r[4], "tot_input": r[5]})

# Sessões outlier (top 5 por input)
outliers = []
for r in q("""SELECT substr(slug,1,40), datetime(time_created/1000,'unixepoch','localtime'),
  tokens_input, tokens_cache_read, tokens_output
  FROM session ORDER BY tokens_input DESC LIMIT 5"""):
    outliers.append({"sessao": r[0], "criada": r[1], "input": r[2], "cache_read": r[3], "output": r[4]})

snapshot = {
    "gerado_em": datetime.now(timezone.utc).isoformat(),
    "fonte": db,
    "total_historico": {
        "sessoes": tot[0], "input": tot[1], "output": tot[2],
        "reasoning": tot[3], "cache_read": tot[4], "cache_write": tot[5],
        "custo_usd": round(tot[6], 4),
    },
    "ultimos_14_dias": daily,
    "por_agente_historico": agents,
    "por_agente_4_dias": recent,
    "outliers_top5": outliers,
}

with open(out, "w") as f:
    json.dump(snapshot, f, indent=2, ensure_ascii=False)
print(f"baseline salvo em {out}")
print(f"historico: {tot[0]} sessoes, {tot[1]:,} input, {tot[3]:,} cache_read, ${round(tot[6],4)}")
con.close()
PYEOF
