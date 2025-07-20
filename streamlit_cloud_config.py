# Configuration pour déploiement Streamlit Cloud
# Ce fichier explique comment configurer Firebase pour le cloud

STREAMLIT_SECRETS_EXAMPLE = {
    "firebase": {
        "type": "service_account",
        "project_id": "votre-project-id",
        "private_key_id": "votre-private-key-id",
        "private_key": "-----BEGIN PRIVATE KEY-----\nvotre-private-key\n-----END PRIVATE KEY-----\n",
        "client_email": "votre-client-email@project.iam.gserviceaccount.com",
        "client_id": "votre-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "votre-cert-url"
    }
}

# Pour déployer sur Streamlit Cloud :
# 1. Allez sur https://share.streamlit.io
# 2. Connectez votre repo GitHub
# 3. Dans les secrets, ajoutez la configuration Firebase
# 4. Utilisez st.secrets["firebase"] dans le code
