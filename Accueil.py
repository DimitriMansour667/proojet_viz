import streamlit as st

st.set_page_config(page_title="Crise du logement au Canada", layout="wide")

FONT = '"Inter", "Helvetica Neue", Arial, sans-serif'

CSS = """
<style>
  .hero-title {
    font-size: 2.6rem; font-weight: 800; color: #f9fafb;
    text-align: center; margin-bottom: .4rem;
  }
  .hero-subtitle {
    font-size: 1.15rem; color: #9ca3af;
    text-align: center; margin-bottom: 2.5rem; line-height: 1.6;
  }
  .card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    height: 100%;
  }
  .card-num {
    font-size: 2rem; font-weight: 700; color: #60a5fa;
    margin-bottom: .3rem;
  }
  .card-title {
    font-size: 1.05rem; font-weight: 600; color: #f3f4f6;
    margin-bottom: .5rem;
  }
  .card-desc {
    font-size: .9rem; color: #9ca3af; line-height: 1.55;
  }
  .divider { border-top: 1px solid rgba(255,255,255,0.08); margin: 2rem 0; }
  .context-title {
    font-size: 1.2rem; font-weight: 600; color: #f3f4f6; margin-bottom: .8rem;
  }
  .context-text {
    font-size: .95rem; color: #9ca3af; line-height: 1.7;
  }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown('<p class="hero-title">Crise du logement au Canada</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-subtitle">'
    'Analyse de l\'évolution des loyers, des revenus et de la pression financière<br>'
    'dans les grandes villes canadiennes de 1992 à 2024.'
    '</p>',
    unsafe_allow_html=True,
)

c1, c2 = st.columns(2)

with c1:
    st.markdown("""
    <div class="card">
      <div class="card-num">01</div>
      <div class="card-title">Loyer vs Revenu</div>
      <div class="card-desc">
        Évolution du loyer moyen mensuel et du revenu médian mensuel par ville et type de logement.
        Observe comment l'écart entre les deux s'est creusé au fil des années.
      </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div class="card">
      <div class="card-num">02</div>
      <div class="card-title">Taux d'effort locatif</div>
      <div class="card-desc">
        Part du revenu médian annuel consacrée au loyer, par ville et type de logement.
        La heatmap permet de comparer d'un coup d'œil quelles villes sont les plus sous pression.
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

st.markdown('<p class="context-title">Contexte</p>', unsafe_allow_html=True)
st.markdown("""
<p class="context-text">
Le marché locatif canadien a subi une transformation profonde depuis les années 1990.
Dans plusieurs grandes villes, les loyers ont augmenté bien plus vite que les revenus,
réduisant considérablement l'accessibilité au logement pour les ménages à revenu médian.
Le <b style="color:#f3f4f6">taux d'effort</b> — soit la part du revenu consacrée au loyer — est un indicateur clé :
au-delà de <b style="color:#fb7185">30 %</b>, un ménage est considéré en situation de tension financière liée au logement.
</p>
<p class="context-text" style="margin-top:.8rem;">
Les données proviennent de <b style="color:#f3f4f6">Statistique Canada</b> :
l'enquête sur les logements locatifs (SCHL) et les données sur le revenu des particuliers.
</p>
""", unsafe_allow_html=True)
