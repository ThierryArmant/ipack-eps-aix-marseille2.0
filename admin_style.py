"""Habillage commun des outils privés, limité à leurs conteneurs."""
ADMIN_CSS = '''<style>
div[class*="st-key-hub_admin_"] {
    background: #FFFFFF !important;
    color: #14263D !important;
    border-radius: 14px;
}
div.st-key-hub_admin_tools, div.st-key-hub_admin_comparison {
    border: 2px solid #17365D !important;
    padding: 20px !important;
    margin: 16px 0 !important;
}
div[class*="st-key-hub_admin_"] :is(p, label, h1, h2, h3, h4, small, summary, li) {
    color: #14263D !important;
}
div[class*="st-key-hub_admin_"] [data-testid="stExpander"] details {
    background: #FFFFFF !important;
    border-color: #CBD5E1 !important;
}
div[class*="st-key-hub_admin_"] :is(input, textarea, [data-baseweb="select"], [data-baseweb="select"] > div) {
    background: #F1F5FB !important;
    color: #14263D !important;
    -webkit-text-fill-color: #14263D !important;
}
div[class*="st-key-hub_admin_"] :is([data-testid="stAlert"], [data-testid="stFileUploader"], [data-testid="stFileUploaderDropzone"]) {
    background: #EAF2FC !important;
    opacity: 1 !important;
}
div[class*="st-key-hub_admin_"] button {
    background: #17365D !important;
    color: #FFFFFF !important;
    border: 2px solid #17365D !important;
    opacity: 1 !important;
}
div[class*="st-key-hub_admin_"] button :is(p, span) {
    color: #FFFFFF !important;
}
div[class*="st-key-hub_admin_"] button:hover { background: #245B94 !important; }
div[class*="st-key-hub_admin_"] a { color: #1D4ED8 !important; }
div[class*="st-key-hub_admin_"] :is(pre, code, [data-testid="stJson"]) {
    background: #F1F5FB !important;
    color: #14263D !important;
}
div[class*="st-key-hub_admin_"] [data-testid="stJson"] * { color: #14263D !important; }
</style>'''
