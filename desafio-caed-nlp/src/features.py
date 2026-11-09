import pyphen
import re


dic = pyphen.Pyphen(lang='pt_BR')

def eh_canonica(silaba):
    """
    Verifica se a sílaba segue estritamente o padrão CV (Consoante-Vogal).
    Exemplos CV: 'ca', 'be', 'ça'.
    Exemplos Não-CV: 'a', 'luz', 'pra'.
    """
    vogais = "aeiouáéíóúâêôãõ"
    silaba = silaba.lower().strip('.,!?();:"\'')
    
    
    if len(silaba) != 2:
        return False
        
    consoante, vogal = silaba[0], silaba[1]
    
    
    return (consoante not in vogais) and (vogal in vogais)

def calcular_taxa_nao_canonica(texto):
    """
    Retorna o percentual de palavras de um texto que possuem 
    pelo menos uma sílaba não-canônica.
    """
    
    palavras = re.findall(r'\b[a-zA-ZáéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]+\b', texto)
    
    if not palavras:
        return 0.0
        
    contagem_nao_canonica = 0
    
    for palavra in palavras:
        
        silabas = dic.inserted(palavra).split('-')
        
        
        if any(not eh_canonica(s) for s in silabas):
            contagem_nao_canonica += 1
            
    
    return contagem_nao_canonica / len(palavras)

if __name__ == "__main__":
    
    texto_teste = "O abajur está quebrado."
    print(f"Texto: '{texto_teste}'")
    print(f"Taxa não canônica: {calcular_taxa_nao_canonica(texto_teste):.2f}")