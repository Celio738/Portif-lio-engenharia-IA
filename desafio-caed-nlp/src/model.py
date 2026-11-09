import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from features import calcular_taxa_nao_canonica


caminho_csv = '../data/processed/dataset_fragmentado.csv'
print(f"Carregando dados de: {caminho_csv}")
df = pd.read_csv(caminho_csv)


print("Calculando a taxa de canonicidade para cada fragmento... (Isso pode demorar um pouco)")
df['taxa_nao_canonica'] = df['texto'].apply(calcular_taxa_nao_canonica)


print("Dividindo os dados em Treino e Teste...")
X_texto = df['texto']
X_feature_extra = df[['taxa_nao_canonica']]
y = df['nivel']


X_train_texto, X_test_texto, y_train, y_test, X_train_extra, X_test_extra = train_test_split(
    X_texto, y, X_feature_extra, test_size=0.2, random_state=42, stratify=y
)


print("Convertendo texto para matrizes numéricas (TF-IDF)...")

vetorizador = TfidfVectorizer(max_features=1500) 
X_train_vec = vetorizador.fit_transform(X_train_texto).toarray()
X_test_vec = vetorizador.transform(X_test_texto).toarray()


print("Combinando features de texto com a feature de canonicidade...")
X_train_final = np.hstack((X_train_vec, X_train_extra.values))
X_test_final = np.hstack((X_test_vec, X_test_extra.values))


print("Treinando o modelo RandomForestClassifier...")
modelo = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
modelo.fit(X_train_final, y_train)


print("\n--- Resultados da Avaliação ---")
y_pred = modelo.predict(X_test_final)
print(classification_report(y_test, y_pred))


print("Salvando o modelo treinado...")
with open('../data/processed/modelo_random_forest.pkl', 'wb') as f:
    pickle.dump(modelo, f)
    
with open('../data/processed/vetorizador_tfidf.pkl', 'wb') as f:
    pickle.dump(vetorizador, f)

print("Processo de treinamento finalizado com sucesso!")