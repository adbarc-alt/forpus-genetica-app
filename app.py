# app.py
# Calculadora Genética – Forpus coelestis (padrão OBJO)
# Versão com interface (Streamlit) + probabilidades + genótipo provável/portadores

import streamlit as st
from itertools import product
from collections import defaultdict, Counter

st.set_page_config(page_title="Calculadora Genética Forpus (OBJO)", layout="wide")

# ============================================================
# MOTOR GENÉTICO (modelo compatível com a planilha/versão anterior)
# ============================================================

def gametes_pair(a: str, b: str):
    if a == b:
        return [(a, 1.0)]
    return [(a, 0.5), (b, 0.5)]

def parse_pair(geno: str):
    a, b = geno.split("/")
    return a.strip(), b.strip()

def parse_linhabase(geno: str):
    a, b = parse_pair(geno.upper())
    if a not in ("G", "T", "B") or b not in ("G", "T", "B"):
        raise ValueError("LinhaBase deve ser G/G, G/T, G/B, T/T, T/B, B/B.")
    return a, b

def linhabase_ph(a: str, b: str):
    # dominância: G > T > B
    order = {"G": 3, "T": 2, "B": 1}
    best = max((a, b), key=lambda x: order[x])
    return "Verde" if best == "G" else ("Turquesa" if best == "T" else "Azul")

def ph_autosomal_recessive(a: str, b: str):
    return (a == "m" and b == "m")

def ph_autosomal_dominant(a: str, b: str):
    return (a == "m" or b == "m")

def dark_factor_dose(a: str, b: str):
    # 0/1/2 conforme dose de "m"
    if a == "m" and b == "m": return 2
    if a == "m" or b == "m": return 1
    return 0

def geno_auto_from_alleles(a: str, b: str) -> str:
    # normaliza para N/N, N/m, m/m
    if a == "m" and b == "m": return "m/m"
    if a == "N" and b == "N": return "N/N"
    return "N/m"

def geno_sex_male_from_alleles(a: str, b: str) -> str:
    return geno_auto_from_alleles(a, b)

def ph_sexlinked_recessive(sex: str, z_from_father: str, maternal_gamete_type: str, maternal_z: str | None):
    # Fêmea (ZW): depende apenas do Z do pai
    if sex == "Fêmea":
        return (z_from_father == "m")
    # Macho (ZZ): precisa m do pai e m do Z materno
    assert maternal_gamete_type == "Z" and maternal_z is not None
    return (z_from_father == "m" and maternal_z == "m")

def objo_category(sex: str, linha: str, cinza: bool, df: int, canela: bool, fulvo: bool,
                  americano: bool, marm1: bool, marm2: bool, arleq: bool, ino: bool):
    # Isabel (neste modelo): Canela + Ino
    isabel = canela and ino

    # Ino -> Lutino / Albino / Cremino (padrão OBJO)
    if ino:
        if linha == "Verde":
            return (f"Coelestis lutino {sex.lower()}", "PS 05.01.25" if sex == "Fêmea" else "PS 05.01.26")
        if linha == "Azul":
            return (f"Coelestis albino {sex.lower()}", "PS 05.02.25")  # OBJO lista junto (f/m)
        if linha == "Turquesa":
            return (f"Coelestis cremino {sex.lower()}", "PS 05.03.23" if sex == "Fêmea" else "PS 05.03.24")

    # Arlequim
    if arleq:
        extras = (canela or fulvo or americano or marm1 or marm2)
        if extras:
            if linha == "Verde":
                return (f"Coelestis verde arlequim outras combinações {sex.lower()}",
                        "PS 05.01.23" if sex == "Fêmea" else "PS 05.01.24")
            if linha == "Azul":
                return (f"Coelestis azul arlequim outras combinações {sex.lower()}",
                        "PS 05.02.23" if sex == "Fêmea" else "PS 05.02.24")
            return (f"Coelestis turquesa arlequim outras combinações {sex.lower()}",
                    "PS 05.03.21" if sex == "Fêmea" else "PS 05.03.22")
        else:
            if linha == "Verde":
                return (f"Coelestis verde arlequim {sex.lower()}",
                        "PS 05.01.21" if sex == "Fêmea" else "PS 05.01.22")
            if linha == "Azul":
                return (f"Coelestis azul arlequim {sex.lower()}",
                        "PS 05.02.21" if sex == "Fêmea" else "PS 05.02.22")
            return (f"Coelestis turquesa arlequim {sex.lower()}",
                    "PS 05.03.19" if sex == "Fêmea" else "PS 05.03.20")

    # Descrição
    parts = [f"Coelestis {linha.lower()}"]
    if cinza: parts.append("cinza")
    if df == 1: parts.append("1 fator escuro")
    if df == 2: parts.append("2 fatores escuro")
    if isabel: parts.append("Isabel")
    elif canela: parts.append("canela")
    if marm1: parts.append("marmorizado (tipo1) (pastel)")
    if marm2: parts.append("marmorizado (tipo 2 mesclado) (pastel)")
    if americano: parts.append("americano")
    if fulvo: parts.append("fulvo")
    parts.append(sex.lower())
    desc = " ".join(parts)

    # Mapeamento PS essencial; demais vão para "outras combinações"
    def ps_pair(v_f, v_m): return v_f if sex == "Fêmea" else v_m

    if linha == "Verde":
        if not any([cinza, df, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.01.01","PS 05.01.02"))
        if cinza and not any([df, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.01.03","PS 05.01.04"))
        if df == 1 and not any([cinza, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.01.05","PS 05.01.06"))
        if df == 2 and not any([cinza, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.01.07","PS 05.01.08"))
        if canela and not any([cinza, df, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.01.09","PS 05.01.10"))
        if marm1 and not any([cinza, df, canela, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.01.13","PS 05.01.14"))
        if marm2 and not any([cinza, df, canela, marm1, americano, fulvo]): return (desc, ps_pair("PS 05.01.15","PS 05.01.16"))
        if americano and not any([cinza, df, canela, marm1, marm2, fulvo]): return (desc, ps_pair("PS 05.01.17","PS 05.01.18"))
        if fulvo and not any([cinza, df, canela, marm1, marm2, americano]): return (desc, ps_pair("PS 05.01.19","PS 05.01.20"))
        return (desc, ps_pair("PS 05.01.50","PS 05.01.51"))

    if linha == "Azul":
        if not any([cinza, df, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.02.01","PS 05.02.02"))
        if cinza and not any([df, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.02.03","PS 05.02.04"))
        if df == 1 and not any([cinza, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.02.05","PS 05.02.06"))
        if df == 2 and not any([cinza, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.02.07","PS 05.02.08"))
        if canela and not any([cinza, df, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.02.09","PS 05.02.10"))
        if marm1 and not any([cinza, df, canela, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.02.13","PS 05.02.14"))
        if marm2 and not any([cinza, df, canela, marm1, americano, fulvo]): return (desc, ps_pair("PS 05.02.15","PS 05.02.16"))
        if americano and not any([cinza, df, canela, marm1, marm2, fulvo]): return (desc, ps_pair("PS 05.02.17","PS 05.02.18"))
        if fulvo and not any([cinza, df, canela, marm1, marm2, americano]): return (desc, ps_pair("PS 05.02.19","PS 05.02.20"))
        return (desc, ps_pair("PS 05.02.50","PS 05.02.51"))

    # Turquesa
    if not any([cinza, df, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.03.01","PS 05.03.02"))
    if cinza and not any([df, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.03.03","PS 05.03.04"))
    if df == 1 and not any([cinza, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.03.05","PS 05.03.06"))
    if df == 2 and not any([cinza, canela, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.03.07","PS 05.03.08"))
    if canela and not any([cinza, df, marm1, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.03.09","PS 05.03.10"))
    if marm1 and not any([cinza, df, canela, marm2, americano, fulvo]): return (desc, ps_pair("PS 05.03.11","PS 05.03.12"))
    if marm2 and not any([cinza, df, canela, marm1, americano, fulvo]): return (desc, ps_pair("PS 05.03.13","PS 05.03.14"))
    if americano and not any([cinza, df, canela, marm1, marm2, fulvo]): return (desc, ps_pair("PS 05.03.15","PS 05.03.16"))
    if fulvo and not any([cinza, df, canela, marm1, marm2, americano]): return (desc, ps_pair("PS 05.03.17","PS 05.03.18"))
    return (desc, ps_pair("PS 05.03.50","PS 05.03.51"))

AUTO_LOCI = ["Cinza","Americano","Marm1","Marm2","Ino","ArleqDom","ArleqRec","FatorEscuro"]
SEX_LOCI  = ["Canela","Fulvo"]

def cruzar(male: dict[str,str], female: dict[str,str]):
    # prob por categoria
    dist = defaultdict(float)

    # genótipos agregados por categoria: cat_key -> locus -> Counter(geno_str) acumulado por prob
    geno_bucket = defaultdict(lambda: defaultdict(Counter))

    # LinhaBase
    ma, mb = parse_linhabase(male["LinhaBase"])
    fa, fb = parse_linhabase(female["LinhaBase"])
    mg = gametes_pair(ma, mb)
    fg = gametes_pair(fa, fb)

    # Autosômicos
    auto_g = {}
    for loc in AUTO_LOCI:
        a1, a2 = parse_pair(male[loc])
        b1, b2 = parse_pair(female[loc])
        auto_g[loc] = (gametes_pair(a1, a2), gametes_pair(b1, b2))

    # Sex-linked
    def sex_m_g(geno: str):
        a1, a2 = parse_pair(geno)
        return gametes_pair(a1, a2)

    def sex_f_g(allele: str):
        # Z ou W com 50%
        if allele not in ("N", "m"):
            raise ValueError("Fêmea sex-linked deve ser N ou m")
        return [("Z", allele, 0.5), ("W", None, 0.5)]

    mz_can = sex_m_g(male["Canela"]); fz_can = sex_f_g(female["Canela"])
    mz_ful = sex_m_g(male["Fulvo"]);  fz_ful = sex_f_g(female["Fulvo"])

    for (g_m, pg_m), (g_f, pg_f) in product(mg, fg):
        linha = linhabase_ph(g_m, g_f)
        p0 = pg_m * pg_f

        # expand autosômicos (guardando genótipo)
        states = [({"auto_geno": {}, "auto_ph": {}}, p0)]
        for loc in AUTO_LOCI:
            new = []
            mg_loc, fg_loc = auto_g[loc]
            for st, p_st in states:
                for (am, pam), (af, paf) in product(mg_loc, fg_loc):
                    st2 = {"auto_geno": dict(st["auto_geno"]), "auto_ph": dict(st["auto_ph"])}

                    g = geno_auto_from_alleles(am, af)
                    st2["auto_geno"][loc] = g

                    if loc == "FatorEscuro":
                        st2["auto_ph"]["df"] = dark_factor_dose(am, af)
                    elif loc == "ArleqDom":
                        st2["auto_ph"]["arleq_dom"] = ph_autosomal_dominant(am, af)
                    elif loc == "ArleqRec":
                        st2["auto_ph"]["arleq_rec"] = ph_autosomal_recessive(am, af)
                    else:
                        st2["auto_ph"][loc] = ph_autosomal_recessive(am, af)

                    new.append((st2, p_st * pam * paf))
            states = new

        for st, p_st in states:
            arleq = bool(st["auto_ph"].get("arleq_dom")) or bool(st["auto_ph"].get("arleq_rec"))

            for (z_can, pz_can) in mz_can:
                for (typ_can, mzcan, p_can_g) in fz_can:
                    for (z_ful, pz_ful) in mz_ful:
                        for (typ_ful, mzful, p_ful_g) in fz_ful:

                            sex = "Fêmea" if (typ_can == "W" or typ_ful == "W") else "Macho"

                            canela = ph_sexlinked_recessive(sex, z_can, typ_can, mzcan)
                            fulvo  = ph_sexlinked_recessive(sex, z_ful, typ_ful, mzful)

                            # genótipos sex-linked do filhote
                            if sex == "Fêmea":
                                geno_can = z_can  # N ou m
                                geno_ful = z_ful
                            else:
                                assert typ_can == "Z" and mzcan in ("N", "m")
                                assert typ_ful == "Z" and mzful in ("N", "m")
                                geno_can = geno_sex_male_from_alleles(z_can, mzcan)  # N/N, N/m, m/m
                                geno_ful = geno_sex_male_from_alleles(z_ful, mzful)

                            cinza = bool(st["auto_ph"].get("Cinza"))
                            americano = bool(st["auto_ph"].get("Americano"))
                            marm1 = bool(st["auto_ph"].get("Marm1"))
                            marm2 = bool(st["auto_ph"].get("Marm2"))
                            ino = bool(st["auto_ph"].get("Ino"))
                            df = int(st["auto_ph"].get("df", 0))

                            desc, ps = objo_category(sex, linha, cinza, df, canela, fulvo, americano, marm1, marm2, arleq, ino)

                            p = p_st * pz_can * p_can_g * pz_ful * p_ful_g
                            key = (linha, ps, desc, sex)

                            dist[key] += p

                            # agrega genótipos por locus dentro da categoria
                            for loc in AUTO_LOCI:
                                geno_bucket[key][loc][st["auto_geno"][loc]] += p
                            geno_bucket[key]["Canela"][geno_can] += p
                            geno_bucket[key]["Fulvo"][geno_ful] += p

    return dist, geno_bucket

# ============================================================
# INTERFACE (STREAMLIT)
# ============================================================

st.title("🧬 Calculadora Genética – Forpus coelestis (padrão OBJO)")
st.caption("Selecione os genótipos do macho e da fêmea. O app calcula fenótipos/PS e mostra genótipo provável (portadores).")

with st.sidebar:
    st.header("Entradas (dropdowns)")

    def pick(title, options, help_txt=None):
        return st.selectbox(title, options, help=help_txt)

    # LinhaBase
    linha_opts = ["G/G","G/T","G/B","T/T","T/B","B/B"]
    auto_opts = ["N/N","N/m","m/m"]
    sex_m_opts = ["N/N","N/m","m/m"]
    sex_f_opts = ["N","m"]

    male = {}
    female = {}

    st.subheader("Linha Base")
    male["LinhaBase"] = pick("LinhaBase do MACHO (G=verde, T=turquesa, B=azul)", linha_opts)
    female["LinhaBase"] = pick("LinhaBase da FÊMEA (G=verde, T=turquesa, B=azul)", linha_opts)

    st.subheader("Autosômicos")
    male["Cinza"] = pick("Cinza do MACHO", auto_opts)
    female["Cinza"] = pick("Cinza da FÊMEA", auto_opts)

    male["FatorEscuro"] = pick("Fator Escuro do MACHO (0/1/2 fatores)", auto_opts)
    female["FatorEscuro"] = pick("Fator Escuro da FÊMEA (0/1/2 fatores)", auto_opts)

    male["Americano"] = pick("Americano do MACHO", auto_opts)
    female["Americano"] = pick("Americano da FÊMEA", auto_opts)

    male["Marm1"] = pick("Marmorizado Tipo 1 (Pastel) do MACHO", auto_opts)
    female["Marm1"] = pick("Marmorizado Tipo 1 (Pastel) da FÊMEA", auto_opts)

    male["Marm2"] = pick("Marmorizado Tipo 2 (Pastel mesclado) do MACHO", auto_opts)
    female["Marm2"] = pick("Marmorizado Tipo 2 (Pastel mesclado) da FÊMEA", auto_opts)

    male["ArleqDom"] = pick("Arlequim DOMINANTE do MACHO", auto_opts)
    female["ArleqDom"] = pick("Arlequim DOMINANTE da FÊMEA", auto_opts)

    male["ArleqRec"] = pick("Arlequim RECESSIVO do MACHO", auto_opts)
    female["ArleqRec"] = pick("Arlequim RECESSIVO da FÊMEA", auto_opts)

    male["Ino"] = pick("Ino do MACHO", auto_opts)
    female["Ino"] = pick("Ino da FÊMEA", auto_opts)

    st.subheader("Sex-linked (ligadas ao sexo)")
    male["Canela"] = pick("Canela do MACHO (ZZ)", sex_m_opts)
    female["Canela"] = pick("Canela da FÊMEA (ZW)", sex_f_opts)

    male["Fulvo"] = pick("Fulvo do MACHO (ZZ)", sex_m_opts)
    female["Fulvo"] = pick("Fulvo da FÊMEA (ZW)", sex_f_opts)

    run = st.button("▶️ Calcular", use_container_width=True)

# helpers
def fmt_pct(p: float) -> str:
    return f"{p*100:.2f}%"

def most_probable(counter: Counter, total: float):
    if total <= 0 or not counter:
        return ("-", 0.0)
    geno, w = max(counter.items(), key=lambda kv: kv[1])
    return geno, (w / total)

def carrier_prob(counter: Counter, total: float):
    # recessivo autosômico: portador = N/m
    if total <= 0:
        return 0.0
    return counter.get("N/m", 0.0) / total

if run:
    dist, geno_bucket = cruzar(male, female)
    items = sorted(dist.items(), key=lambda x: (-x[1], x[0]))

    st.subheader("📊 Resultados (por PS / descrição / sexo)")
    st.caption("Clique e role: abaixo de cada resultado, aparecem genótipos mais prováveis e probabilidades de portadores.")

    for (linha, ps, desc, sex), p in items:
        with st.expander(f"{fmt_pct(p)} — {ps} — {desc}", expanded=False):
            total_cat = p

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### 🧬 Genótipo mais provável (condicionado a este fenótipo)")
                # mostrar todos os loci
                for locus, counter in geno_bucket[(linha, ps, desc, sex)].items():
                    g, pr = most_probable(counter, total_cat)
                    st.write(f"- **{locus}**: `{g}` ({pr*100:.1f}%)")

            with col2:
                st.markdown("### 🧾 Portadores (quando aplicável)")
                # autos recessivos
                for locus in ["Cinza","Americano","Marm1","Marm2","Ino","ArleqRec"]:
                    counter = geno_bucket[(linha, ps, desc, sex)].get(locus, Counter())
                    st.write(f"- **{locus}**: portador `N/m` = {carrier_prob(counter, total_cat)*100:.1f}%")

                # sex-linked
                if sex == "Macho":
                    for locus in ["Canela", "Fulvo"]:
                        counter = geno_bucket[(linha, ps, desc, sex)].get(locus, Counter())
                        st.write(f"- **{locus} (ZZ)**: portador `N/m` = {carrier_prob(counter, total_cat)*100:.1f}%")
                else:
                    st.write("- **Sex-linked fêmea (ZW)**: não existe “portadora” (ou é `N` ou é `m` no Z).")

    total = sum(dist.values())
    st.info(f"Checagem: soma total = {fmt_pct(total)} (deve ficar ~100%)")
else:
    st.info("➡️ Selecione os genótipos na barra lateral e clique em **Calcular**.")
```0