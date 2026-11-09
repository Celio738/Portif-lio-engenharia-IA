import pickle
import numpy as np
import nltk
from nltk.corpus import wordnet
from features import calcular_taxa_nao_canonica


nltk.download('wordnet', quiet=True)
nltk.download('omw-1.4', quiet=True)
nltk.download('omw-2.0', quiet=True)
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)


with open('../data/processed/modelo_random_forest.pkl', 'rb') as f:
    modelo = pickle.load(f)
with open('../data/processed/vetorizador_tfidf.pkl', 'rb') as f:
    vetorizador = pickle.load(f)

def prever_complexidade(texto):
    """Passa um texto pelo pipeline e retorna o nível previsto e as probabilidades."""
    taxa_nc = calcular_taxa_nao_canonica(texto)
    vec_texto = vetorizador.transform([texto]).toarray()
    features_finais = np.hstack((vec_texto, [[taxa_nc]]))
    
    previsao = modelo.predict(features_finais)[0]
    probabilidades = modelo.predict_proba(features_finais)[0]
    
    return previsao, probabilidades

def mutacao_sinonimos(texto):
    """Substitui palavras do texto por seus sinônimos usando WordNet (Português)."""
    palavras = nltk.word_tokenize(texto, language='portuguese')
    novo_texto = []
    mutacoes_feitas = 0
    
    for p in palavras:
        
        if not p.isalpha() or len(p) < 4:
            novo_texto.append(p)
            continue
            
        
        sinonimos = wordnet.synsets(p, lang='por')
        if sinonimos:
            lemas = sinonimos[0].lemma_names('por')
            
            substituto = next((lema for lema in lemas if lema.lower() != p.lower()), None)
            
            if substituto:
                novo_texto.append(substituto.replace('_', ' '))
                mutacoes_feitas += 1
            else:
                novo_texto.append(p)
        else:
            novo_texto.append(p)
            
    
    texto_mutado = " ".join(novo_texto).replace(" ,", ",").replace(" .", ".")
    return texto_mutado, mutacoes_feitas

def testar_exemplo(texto_original, numero_exemplo):
    print(f"\n{'='*40}")
    print(f"EXEMPLO {numero_exemplo}")
    print(f"{'='*40}")
    
    print("--- TEXTO ORIGINAL ---")
    print(texto_original)
    prev_orig, prob_orig = prever_complexidade(texto_original)
    print(f"Classificação: {prev_orig}\n")
    
    print("--- APLICANDO MUTAÇÃO (Troca de Palavras) ---")
    texto_mutado, qtd = mutacao_sinonimos(texto_original)
    print(texto_mutado)
    print(f"(Foram substituídas {qtd} palavras)")
    
    prev_mut, prob_mut = prever_complexidade(texto_mutado)
    print(f"Nova Classificação: {prev_mut}\n")
    
    if prev_orig != prev_mut:
        print("💡 A mutação foi forte o suficiente para alterar a classificação do modelo!")
    else:
        print("📊 A classificação se manteve, mas as características internas mudaram.")

if __name__ == "__main__":
    
    
    
    texto1 = "A fotossíntese é um processo biológico complexo realizado pelas plantas para obtenção de energia celular."
    testar_exemplo(texto1, 1)
    
    
    texto2 = "O menino pegou a bola amarela e foi brincar com seus amigos no parque."
    testar_exemplo(texto2, 2)