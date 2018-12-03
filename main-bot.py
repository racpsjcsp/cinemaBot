# -*- coding: utf-8 -*-
import telegram
import json
import requests
from bs4 import BeautifulSoup as bs
from time import sleep

BOT_TOKEN ='635166790:AAFp9qp0cX0Kdh7aHCeOkPEkpLNMp3lvyEg' 
data_filmes = []

#raspagem
def raspagem():
    '''
       Coleta os dados de filmes em cartaz da url do cinemark 
       @return film_list: lista dos filmes concatenadas em uma string
    '''
    prefix = "https://www.cinemark.com.br"
    url_pagina = prefix + "/sao-jose-dos-campos/filmes/em-cartaz?pagina="    
    npagina=1
    global data_filmes
    data_filmes = []
    while True:
        p = requests.get(url_pagina+str(npagina))
        s = bs(p.content, "html.parser")    #usando o bs do comentario anterior
        results = s.findAll('a',{'class':'movie-image'})       
        if len(results)==0:
            break;     
        for f in results: 
            filme = {}
            filme["title"] =  f['title'][6:]            
            filme["href"] =  f['href']         
            data_filmes.append(filme)             
        npagina += 1     
        
    return data_filmes

def raspagem_sinopse_trailer(filme_url):
    
    prefix = "https://www.cinemark.com.br"
    url_pagina = prefix + filme_url
    p = requests.get(url_pagina)
    s = bs(p.content, "html.parser")    #usando o bs do comentario anterior    
    url_trailer = ''
    sinopse = ''
    # busca sinopse
    try:
        result = s.find('div',{'class':'movie-sinopse'})  
        if result is not None:
            sinopse = result.find('div', {'class': 'accordion-content'}) 
            if sinopse is not None:
               sinopse = sinopse.p.text.strip("<p>\r\n ")
    except:
        sinopse = 'indisponível'
    
    
    # busca link trailer
    try:
        result = s.find('aside',{'id':'trailer'})    
        if result is not None:
            url_trailer = result.find('a', {'class': 'btn btn-trailer-play'}) 
            if url_trailer is not None:
               url_trailer = url_trailer.get('href')
    except:
        url_trailer = 'indisponível'
 
    
    return sinopse if sinopse is not None or sinopse != '' else 'indisponível', \
           url_trailer if url_trailer is not None else 'indisponível'
    
        

def echo(bot,chat,mensagem,keyboard=''):
    if keyboard:
        bot.sendMessage(chat_id=chat,text=mensagem,reply_markup=keyboard, parse_mode='html') 
    else:
        bot.sendMessage(chat_id=chat,text=mensagem, parse_mode='html')

def bot_keyboard(url): 
   
    btn_row = [[telegram.InlineKeyboardButton(text="Trailer", url=("http:" + url))]]
   
    return telegram.InlineKeyboardMarkup(btn_row)

    
def run_bot(wIds):
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
    
    # TODO -  filtrar mensagens com a chave 'callback_query'    
    d_sorted = sorted(results, key=lambda k: k['update_id'], reverse=True) 
    c_ids = [] # vetor de ids dos chats (contatos)
    m_ids = [] # vetor de ids das mensagens
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
            
            # verifica se a mesagem vem de um contato (q nao eh bot)
            # verifica se se o contato jah foi processado
            # verifica se a mensagem jah foi processada
            if not d_isbot and d_id not in c_ids:
                if m_id in wIds: # msg ja processada em outro loop
                    continue            
                if d_text in ["/start"]: # contato iniciou conversa com bot
                    continue
                # contato enviou um texto qualquer
                elif not d_text.isdigit() and d_text not in ["filmes", "dicas de filmes", "cinema"]:
                    echo(bot,d_id,hello_msg.format(d_chat["first_name"]))
                    print("{0} enviou uma mensagem".format(d_chat["first_name"]))
                # contato pediu por info de filmes
                elif d_text in ["filmes", "dicas de filmes", "cinema"]:
                    r_filmes = "<b>Filmes em cartaz:</b>\n"
                    film_list = raspagem() # peoga os dados coletados na raspagem                    
                    count = 1
                    for f in film_list:
                        r_filmes += "{0}: {1}\n".format(str(count),str(f["title"])) 
                        count += 1
                    # r_keyboards = bot_keyboard(film_list[0])                     
                    echo(bot,d_id,r_filmes + '\n<b>(Envie o número para sinopse e trailer)</b>\n') # envia a lista para o contato
                    print("{0} pediu por filmes".format(d_chat["first_name"]))
                else:
                    if d_text.isdigit() and len(data_filmes)>0 and len(data_filmes)>= int(d_text):
                        pos = int(d_text) - 1
                        ret = raspagem_sinopse_trailer(data_filmes[pos]["href"])
                        trailer = ret[1] if ret[1] else '//youtube.com/results?search_query='+ data_filmes[pos]["title"]
                        sinopse = ret[0] if ret[0] else 'indisponível'
                        r_keyboards = bot_keyboard(trailer)
                        r_text = '\n<b>' + data_filmes[pos]["title"] + '</b>\n' + sinopse + '\n<i>Veja o trailer abaixo:</i>' 
                        r_text += '\nhttps:'+ trailer
                        echo(bot,d_id,r_text, r_keyboards) 
                               
            c_ids.append(d_id)  # salva id do usuario (primeira msg valida)
            m_ids.append(m_id)  # salva id da mensagem (prox execucao)         
      
    return m_ids


try:
    message_ids  = []
    print("Executando script")
    # cria o loop para execucao do script
    while True:
        
        print("Bot na escuta...")
        ret_ids = run_bot(message_ids)
        message_ids += ret_ids # salva os ids (evita msgs repetidas)
        sleep(1) # espera um segundo para prox execucao
        
        # raspagem()     
except Exception as we:
    print (we)







        
