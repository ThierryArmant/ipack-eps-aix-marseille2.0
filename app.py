st.markdown(f"""
    <style>
    /* Couleur de fond globale */
    .stApp {{ background-image: url('{github_url}{img_fond}') !important; background-size: cover !important; }}
    
    /* Couleur du texte principal et des cartes */
    .santorin-card, .general-card, .securite-card {{ 
        background-color: rgba(15, 23, 42, 0.45) !important; 
        color: #FFFFFF !important; 
        padding: 18px; 
        border-radius: 8px; 
    }}
    
    /* Couleur spécifique pour le texte dans les cartes */
    .santorin-card p, .general-card p, .securite-card p, 
    .santorin-card div, .general-card div, .securite-card div {{ 
        color: #FFFFFF !important; 
    }}
    
    /* Liens en orange */
    .santorin-card a, .general-card a, .securite-card a {{ 
        color: #FFB020 !important; 
        text-decoration: underline !important; 
    }}
    </style>
""", unsafe_allow_html=True)
