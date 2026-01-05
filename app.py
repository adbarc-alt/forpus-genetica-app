import streamlit as st
from collections import defaultdict, Counter
from itertools import product

st.set_page_config(page_title="Calculadora Genética Forpus (OBJO)", layout="wide")

# =========================
# COLE AQUI O SEU CÓDIGO COMPLETO
# (o que te passei na última versão)
# - Você vai colar tudo, MENOS o bloco:
#   if __name__ == "__main__": main()
#
# E no lugar do main(), vamos criar a UI abaixo.
# =========================

# --------- (Cole aqui as funções do seu código) ---------
# DICA: cole desde "def gametes_pair" até "def cruzar" inclusive.
# --------------------------------------------------------


# =========================
# Interface (UI)
# =========================

st.title("🧬 Calculadora Genética – Forpus coelestis (padrão OBJO)")
st.caption("Escolha os genótipos do macho e da fêmea. O app calcula fenótipos, PS e portadores (quando aplicável).")

with st.sidebar:
    st.header("Entradas")

    def pick(title, options):
        return st.selectbox(title, options)

    # LinhaBase
    linha_opts = ["G/G","G/T","G/B","T/T","T/B","B/B"]
    male = {}
    female = {}

    male["LinhaBase"] = pick("LinhaBase do MACHO", linha_opts)
    female["LinhaBase"] = pick("LinhaBase da FÊMEA", linha_opts)

    # Autosômicos
    auto_opts = ["N/N","N/m","m/m"]
    male["Cinza"] = pick("Cinza do MACHO", auto_opts)
    female["Cinza"] = pick("Cinza da FÊMEA", auto_opts)

    male["FatorEscuro"] = pick("Fator Escuro do MACHO", auto_opts)
    female["FatorEscuro"] = pick("Fator Escuro da FÊMEA", auto_opts)

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

    # Sex-linked
    sex_m_opts = ["N/N","N/m","m/m"]
    sex_f_opts = ["N","m"]
    male["Canela"] = pick("Canela do MACHO (sex-linked)", sex_m_opts)
    female["Canela"] = pick("Canela da FÊMEA (sex-linked)", sex_f_opts)

    male["Fulvo"] = pick("Fulvo do MACHO (sex-linked)", sex_m_opts)
    female["Fulvo"] = pick("Fulvo da FÊMEA (sex-linked)", sex_f_opts)

    run = st.button("▶️ Calcular")

if run:
    # chama sua função cruzar (a versão que retorna dist e geno_bucket)
    dist, geno_bucket = cruzar(male, female)

    # ordena por prob
    items = sorted(dist.items(), key=lambda x: (-x[1], x[0]))

    st.subheader("📊 Resultados (por PS / descrição / sexo)")
    for (linha, ps, desc, sex), p in items:
        st.markdown(f"### {p*100:.2f}% — {ps} — {desc}")

        total_cat = p
        cols = st.columns(2)

        # bloco 1: genótipo mais provável
        with cols[0]:
            st.markdown("**Genótipo mais provável (por locus)**")
            for locus, counter in geno_bucket[(linha, ps, desc, sex)].items():
                if total_cat <= 0:
                    continue
                geno, w = max(counter.items(), key=lambda kv: kv[1])
                st.write(f"- {locus}: {geno} ({(w/total_cat)*100:.1f}%)")

        # bloco 2: portadores
        with cols[1]:
            st.markdown("**Portadores (quando aplicável)**")
            # autos recessivos: N/m
            for locus in ["Cinza","Americano","Marm1","Marm2","Ino","ArleqRec"]:
                counter = geno_bucket[(linha, ps, desc, sex)].get(locus, Counter())
                if total_cat > 0:
                    p_car = counter.get("N/m", 0.0)/total_cat
                    st.write(f"- {locus}: portador N/m = {p_car*100:.1f}%")

            # sex-linked
            if sex == "Macho":
                for locus in ["Canela","Fulvo"]:
                    counter = geno_bucket[(linha, ps, desc, sex)].get(locus, Counter())
                    if total_cat > 0:
                        p_car = counter.get("N/m", 0.0)/total_cat
                        st.write(f"- {locus} (ZZ): portador N/m = {p_car*100:.1f}%")
            else:
                st.write("- Sex-linked fêmea (ZW): não existe “portadora” (ou é N ou é m no Z).")
else:
    st.info("Escolha os genótipos na barra lateral e clique em **Calcular**.")
