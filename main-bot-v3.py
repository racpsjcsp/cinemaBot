import telegram
import json
import requests
import os
import time
from bs4 import BeautifulSoup as bs
from time import sleep

BOT_TOKEN ='635166790:AAFp9qp0cX0Kdh7aHCeOkPEkpLNMp3lvyEg'

#raspagem
def raspagem():
    '''
       Coleta os dados de filmes em cartaz da url do cinemark 
       @return film_list: lista dos filmes concatenadas em uma string
    '''
    prefix = "https://www.cinemark.com.br"
    url_pagina = prefix + "/sao-jose-dos-campos/filmes/em-cartaz?pagina="
    filmes = set()
    film_list = "Filmes em cartaz:\n"
    for npagina in (1, 2):    
        p = requests.get(url_pagina+str(npagina))
        s = bs(p.content, "html.parser")    #usando o bs do comentario anterior
        for filme in s.findAll('a',{'class':'movie-image'}):                     
            filmes.add(filme['title'][6:])

    for f in filmes:
        film_list += "{0}\n".format(str(f))      
        
    return film_list if len(filmes)>0 else ""
        

def echo(bot,chat,mensagem):
    bot.sendMessage(chat_id=chat,text=mensagem) 
    
def run_bot(last_update):
    '''
       Executa o bot pegando as atualizacoes de mensagens recebidas 
       e respondendo a ultima mensagem do contato de acordo com os comandos:
       */start: contato iniciou conversa, nao devolve resposta
       *texto qualquer: devolve a reposta padrao com os comandos
       *"filmes", "dicas de filmes", "cinema": comando que recebe os dados coletados na raspagem

       @params wIds: salva os ids das mensagens que ja foram processadas, evita o envio de mensagens repetidas
       aos contatos
       @return m_ids: devolve os ids das mensagens que ja foram processdas, eh necessario ate os updates do bot sejam 
       atualizados, na api do telegram os updates sao resetados em 24hrs
    '''
    
    # Utiliza o token da api para receber as mensagens recebidas pelo bot
    url_updates = 'https://api.telegram.org/bot{0}/getUpdates'.format(BOT_TOKEN)
    # cria uma instancia de conexao a api do telegram utilizando o token
    bot=telegram.Bot(token=BOT_TOKEN)    
    # envia a requisicao para as atualizacoes (mensagens recebidas)
    resp = requests.get(url_updates)    
    results = json.loads(resp.content)
    # faz o parse do resultado se receber OK da requisicao
    results = results["result"] if results["ok"] else []   
    # ordena a lista de mensagens pela data
    d_sorted = sorted(results, key=lambda k: k['message']['date'], reverse=True) 
    c_ids = [] # vetor de ids dos chats (contatos)    
    # cria mensagem padrao para qualquer texto que for recebido
    hello_msg = 'Ola {0}, digite filmes, dicas de filmes ou cinema!'
    for data in d_sorted:
        # faz parse das informacoes da mensagem recebida
        d_id = data["message"]["from"]["id"]
        m_id = data["message"]["message_id"]
        d_from = data["message"]["from"]  
        d_isbot = data["message"]["from"]["is_bot"]
        d_text = data["message"]["text"]
        d_chat = data["message"]["chat"]
        d_date = data["message"]["date"]   
        # remove caracteres como . e / do comando e converte p letras minusculas                   
        d_text = d_text.replace(".","").replace("/","").lower()        
        # verifica se a msg foi processada em loop anterior
        if last_update is not None and d_date < int(last_update): 
            continue  
        # verifica se a mesagem vem de um contato (q nao eh bot)
        # verifica se se o contato jah foi processado     
        if not d_isbot and d_id not in c_ids:                      
            if d_text in ["/start"]: # contato iniciou conversa com bot
                continue
            # contato enviou um texto qualquer
            elif d_text not in ["filmes", "dicas de filmes", "cinema"]:
                echo(bot,d_id,hello_msg.format(d_chat["first_name"]))
                print("{0} enviou uma mensagem".format(d_chat["first_name"]))
            # contato pediu por info de filmes
            elif d_text in ["filmes", "dicas de filmes", "cinema"]:
                d_filmes = raspagem() # peoga os dados coletados na raspagem
                echo(bot,d_id,d_filmes) # envia a lista para o contato
                print("{0} pediu por filmes".format(d_chat["first_name"]))
                           
        c_ids.append(d_id)  # salva id do usuario (primeira msg valida)           
  
try:   
    print("Executando script")
    # cria o loop para execucao do script
    while True:
        print("Bot na escuta...")
        run_bot(os.environ.get("LAST_UPDATE"))      
        os.environ["LAST_UPDATE"] = str(int(time.time()))
        sleep(1) # espera um segundo para prox execucao
                
except Exception as we:
    print (we)







        
