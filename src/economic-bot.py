# -*- coding: utf-8 -*-

'''
Criado em 06/2020
Autor: Paulo https://github.com/alpdias
'''

# bibliotecas utilizadas para o tratamento e o webscraping do calendario economico
from datetime import datetime, timezone, timedelta
import datetime as DT
from time import sleep
import arrow 
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from secret import economiCalendar
# bibliotecas para a API do telegram 'telepot' https://github.com/nickoala/telepot
import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

# bibliotecas complementares
import emoji

token = economiCalendar.token() # token de acesso
usuario = economiCalendar.user() # numero inteiro (Telegram ID user)
channelID = economiCalendar.channel() # numero inteiro (Telegram ID channel)

bot = telepot.Bot(token) # telegram bot

def calendario(url): 
    
    """
    -> Funçao para obter as noticas do calendario economico a partir de um webscraping e tratando o html
    """

    url = 'https://br.investing.com/economic-calendar/' # site utilizado no webscraping
    cabecalho = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'} # cabecalho para obter a requisicao do site (site só aceita acesso por navegador(simulação))
    requisicao = requests.get(url, headers=cabecalho) # requisicao dentro do site
    soup = BeautifulSoup(requisicao.text, 'html.parser') # tratamento do html com o modulo 'bs4'
    tabela = soup.find('table', {'id': 'economicCalendarData'}) # apenas a tabela com o id especifico
    corpo = tabela.find('tbody') # apenas o corpo da tabela
    linhas = corpo.findAll('tr', {'class': 'js-event-item'}) # apenas as linhas da tabela

    calendario = [] # lista para as noticias
    
    for tr in linhas:
        horario = tr.attrs['data-event-datetime'] # separando o horario da noticia pela tag html 'data-event-datetime'
        horario = arrow.get(horario, 'YYYY/MM/DD HH:mm:ss') # converter uma string de horario em um formato aceito pelo python
        """
        -> funções desatualizadas

        horario = arrow.get(horario, 'YYYY/MM/DD HH:mm:ss').timestamp # converter uma string de horario em um formato aceito pelo python
        horario = datetime.utcfromtimestamp(horario).strftime('%H:%M')
        """
        horario = horario.strftime('%H:%M')
        calendario.append(horario)

        horario = tr.attrs['data-event-datetime'] # separando o horario da noticia pela tag html 'data-event-datetime'
        """
        -> funções desatualizadas

        horario = arrow.get(horario, 'YYYY/MM/DD HH:mm:ss').timestamp # converter uma string de horario em um formato aceito pelo python
        """
        horario = arrow.get(horario, 'YYYY/MM/DD HH:mm:ss') # converter uma string de horario em um formato aceito pelo python
        horas = (int(horario.strftime('%H')) * 60)
        minutos = int(horario.strftime('%M'))
        verificacao = horas + minutos # horario em minutos para verrificar o tempo em minutos para envio da noticia
        calendario.append(verificacao)

        coluna = tr.find('td', {'class': 'flagCur'}) # separando o pais da noticia pela tag html 'flagCur'
        bandeira = coluna.find('span')
        calendario.append(bandeira.get('title'))

        impacto = tr.find('td', {'class': 'sentiment'})
        touro = impacto.findAll('i', {'class': 'grayFullBullishIcon'}) # separando o impacto da noticia pela tag html 'grayFullBullishIcon' e sua quantidade respectiva
        calendario.append(len(touro))

        evento = tr.find('td', {'class': 'event'})
        a = evento.find('a') # separando a tag html especifica 'a' para obter o nome e a url da noticia

        calendario.append('{}{}'.format(url, a['href'])) # separando a url da noticia com o url do site e tag de referencia html 'href'

        calendario.append(a.text.strip()) # separando a chamada na notica pela tag html 'a' (texto dentro da tag)

    return calendario # retorna a lista com as noticias


def enviarMensagens(msgID, texto, botao=''): 
    
    """
    -> Funçao para enviar as mensagens atravez do bot
    """
    
    bot.sendChatAction(msgID, 'typing') # mostra a açao de 'escrever' no chat
    
    sleep(1)
    
    bot.sendMessage(msgID, texto, reply_markup=botao, disable_notification=False) # retorna uma mensagem pelo ID da conversa + um texto + um botao


def receberMensagens(msg): 
    
    """
    -> Funçao para buscar as mensagens recebidas pelo bot e executar os comandos
    """
    
    msgID = msg['chat']['id'] # variavel para receber o ID da conversa
    nome = msg['chat']['first_name'] # variavel para receber o nome do usuario que enviou a msg
    botao = '' # variavel para receber o botao a ser enviado dentro da interface do telegram

    if msg['text'] == '/start' and msgID != usuario:
        bemvindo = (emoji.emojize(f'Olá {nome}, esse bot serve somente para controlar e atualizar o envio de mensagens em um canal no telegram sobre notícias do calendário econômico, se quiser \
saber mais sobre o meu funcionamento ou quiser relatar alguma coisa, entre em contato com o meu desenvolvedor, é só clicar no botão abaixo :backhand_index_pointing_down:', use_aliases=True)) # msg dando boas vindas e explicando o funcionamento do bot
        botao = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=(emoji.emojize('+ INFO :mobile_phone_with_arrow:', use_aliases=True)), url='https://t.me/alpdias')]]) # botao com link para ajuda
        enviarMensagens(msgID, bemvindo, botao)
        
    elif msg['text'] == '/start' and msgID == usuario:
        solicitar = (emoji.emojize(f'Olá {nome}, o que deseja fazer? :thinking_face:', use_aliases=True)) # msg dando boas vindas e solicitando uma açao
        botao = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=(emoji.emojize('ATUALIZAR :globe_with_meridians:', use_aliases=True)), callback_data='atualizar')], [InlineKeyboardButton(text=(emoji.emojize('AGENDAR :timer_clock:', use_aliases=True)), callback_data='agendar')], [InlineKeyboardButton(text=(emoji.emojize('LOOP :counterclockwise_arrows_button:', use_aliases=True)), callback_data='loop')]]) # botoes par atualizaçao
        enviarMensagens(msgID, solicitar, botao)

    elif msg['text'] != '/start' and msgID == usuario:
        erro = (emoji.emojize(f'{nome}, não entendi o seu comando :confused_face:', use_aliases=True))
        enviarMensagens(msgID, erro)

    else:
        info = (emoji.emojize(f'{nome}, desculpe mas não entendi seu comando, meu uso é exclusivo para atualização de um canal no telegram, para saber mais entre \
em contato com meu desenvolvedor :backhand_index_pointing_down:', use_aliases=True)) # msg para mais informaçoes
        botao = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=(emoji.emojize('+ INFO :mobile_phone_with_arrow:', use_aliases=True)), url='https://t.me/alpdias')]]) # botao com link para ajuda
        enviarMensagens(msgID, info, botao)


def responderMensagens(msg): 
    
    """
    -> Funçao para interagir com os botoes do bot dentro do telegram
    """
    
    msgID, respostaID, resposta = telepot.glance(msg, flavor='callback_query') # variaveis que recebem o 'callback query' da resposta (necessario 3 variaveis, o ID da conversa e o da resposta sao diferentes)
    
    if resposta == 'atualizar':
        try:
            bot.answerCallbackQuery(msgID, text=(emoji.emojize('Atualizando... :globe_with_meridians:', use_aliases=True))) # mostra um texto/alerta na tela do chat
            sleep(2)
            
            dados = calendario('https://br.investing.com/economic-calendar/')
            
            atualizado = (emoji.emojize('Atualizado com sucesso :thumbs_up:', use_aliases=True))
            enviarMensagens(respostaID, atualizado)
            
            trabalhando = (emoji.emojize('Enviando notícias :man_technologist:', use_aliases=True))
            enviarMensagens(respostaID, trabalhando)

            quantidade = (len(dados) / 6) # quantidade de noticias

            while True: # mostra o horario atual da maquina para verificar junto com o horario da noticia (adicionado correçao de fuso horario)
                
                fuso = timedelta(hours=-3)
                zona = timezone(fuso)
                agora = datetime.now()
                correçao = agora.astimezone(zona)
                minutos = (correçao.minute)
                atual = ((correçao.hour * 60) + minutos)
                
                horario = dados[0] # dado especifico para o horario da noticia
                verificacao = dados[1]# dado especifico para verificar o horario da noticia em minutos

                if verificacao == 0:
                    verificacao = verificacao

                else:
                    verificacao = (verificacao - 5)

                local = dados[2] # dado especifico para o pais da noticia

                # adiçao do emoji da bandeira do local -->
                if local == 'Argentina':
                    bandeira = (emoji.emojize('\U0001F1E6\U0001F1F7', use_aliases=True))

                elif local == 'Austrália':
                    bandeira = (emoji.emojize('\U0001F1E6\U0001F1FA', use_aliases=True))

                elif local == 'Brasil':
                    bandeira = (emoji.emojize('\U0001F1E7\U0001F1F7', use_aliases=True))

                elif local == 'Canadá':
                    bandeira = (emoji.emojize('\U0001F1E8\U0001F1E6', use_aliases=True))

                elif local == 'Suíça':
                    bandeira = (emoji.emojize('\U0001F1E8\U0001F1ED', use_aliases=True))
                
                elif local == 'China':
                    bandeira = (emoji.emojize('\U0001F1E8\U0001F1F3', use_aliases=True))
                
                elif local == 'Alemanha':
                    bandeira = (emoji.emojize('\U0001F1E9\U0001F1EA', use_aliases=True))

                elif local == 'Espanha':
                    bandeira = (emoji.emojize('\U0001F1EA\U0001F1F8', use_aliases=True))

                elif local == 'Zona Euro':
                    bandeira = (emoji.emojize('\U0001F1EA\U0001F1FA', use_aliases=True))

                elif local == 'França':
                    bandeira = (emoji.emojize('\U0001F1EB\U0001F1F7', use_aliases=True))

                elif local == 'Reino Unido':
                    bandeira = (emoji.emojize('\U0001F1EC\U0001F1E7', use_aliases=True))

                elif local == 'Hong Kong':
                    bandeira = (emoji.emojize('\U0001F1ED\U0001F1F0', use_aliases=True))

                elif local == 'Indonésia':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1E9', use_aliases=True))

                elif local == 'Irlanda':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1EA', use_aliases=True))

                elif local == 'Índia':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1F3', use_aliases=True))

                elif local == 'Itália':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1F9', use_aliases=True))

                elif local == 'Japão':
                    bandeira = (emoji.emojize('\U0001F1EF\U0001F1F5', use_aliases=True))

                elif local == 'Coreia do Norte':
                    bandeira = (emoji.emojize('\U0001F1F0\U0001F1F5', use_aliases=True))

                elif local == 'Coreia do Sul':
                    bandeira = (emoji.emojize('\U0001F1F0\U0001F1F7', use_aliases=True))

                elif local == 'México':
                    bandeira = (emoji.emojize('\U0001F1F2\U0001F1FD', use_aliases=True))

                elif local == 'Países Baixos':
                    bandeira = (emoji.emojize('\U0001F1F3\U0001F1F1', use_aliases=True))

                elif local == 'Noruega':
                    bandeira = (emoji.emojize('\U0001F1F3\U0001F1F4', use_aliases=True))

                elif local == 'Nova Zelândia':
                    bandeira = (emoji.emojize('\U0001F1F3\U0001F1FF', use_aliases=True))

                elif local == 'Portugal':
                    bandeira = (emoji.emojize('\U0001F1F5\U0001F1F9', use_aliases=True))

                elif local == 'Rússia':
                    bandeira = (emoji.emojize('\U0001F1F7\U0001F1FA', use_aliases=True))

                elif local == 'Suécia':
                    bandeira = (emoji.emojize('\U0001F1F8\U0001F1EA', use_aliases=True))

                elif local == 'Cingapura':
                    bandeira = (emoji.emojize('\U0001F1F8\U0001F1EC', use_aliases=True))

                elif local == 'Turquia':
                    bandeira = (emoji.emojize('\U0001F1F9\U0001F1F7', use_aliases=True))

                elif local == 'EUA':
                    bandeira = (emoji.emojize('\U0001F1FA\U0001F1F8', use_aliases=True))

                elif local == 'África do Sul':
                    bandeira = (emoji.emojize('\U0001F1FF\U0001F1E6', use_aliases=True))

                elif local == 'Inglaterra':
                    bandeira = (emoji.emojize('\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F', use_aliases=True))

                else:
                    bandeira = (emoji.emojize(':globe_showing_Americas:', use_aliases=True))
                # adiçao do emoji da bandeira do local <--
                
                impacto = dados[3] # dado especifico para o impacto da noticia
                impacto = (emoji.emojize(int(impacto) * f':cow_face:', use_aliases=True)) # transformando dado em emoji
                link = dados[4] # dado especifico para o link da noticia
                chamada = dados[5] # dado especifico para a chamada da noticia

                noticia = (emoji.emojize(f'Local: {local} {bandeira}\
\nHorário: {horario}\
\nImpacto da notícia: {impacto}\
\n:loudspeaker: {chamada.strip()}\
\n\
\nPara ver mais acesse :backhand_index_pointing_down:', use_aliases=True)).strip() # noticia formatada 

                botao = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=(emoji.emojize('+ NOTÍCIA :receipt:', use_aliases=True)), url=f'{link.strip()}')]]) # botao com link acesso a noticia
                
                if verificacao == 0 and atual == 0:
                    enviarMensagens(channelID, noticia, botao)
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                    
                elif verificacao == 0 and verificacao < atual:
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes

                elif verificacao == atual:
                    enviarMensagens(channelID, noticia, botao)
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                
                elif verificacao <= atual:
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                
                else:
                    pass

                if quantidade == 0:
                    terminado = (emoji.emojize('Todas as notícias já foram enviadas, processo finalizado :beaming_face_with_smiling_eyes::thumbs_up:', use_aliases=True))
                    enviarMensagens(respostaID, terminado)
                    break

                else:
                    pass

        except:
            desatualizado = (emoji.emojize('Erro inesperado ao atualizar! :pensive_face:', use_aliases=True)) # msg de erro na atualizaçao
            enviarMensagens(respostaID, desatualizado)

    elif resposta == 'agendar':

        # mostra o horario atual da maquina para verificar junto com o horario da noticia (adicionado correçao de fuso horario)
        fuso = timedelta(hours=-3)
        zona = timezone(fuso)
        agora = datetime.now()
        correçao = agora.astimezone(zona)
        minutos = (correçao.minute)
        atual = ((correçao.hour * 60) + minutos)

        # agenda o tempo em que o script sera atualizado de acordo com o horario atual e o que falta para o final do dia
        agendar = (1440 - atual)
        agendado = (emoji.emojize(f'O envio das notícias se iniciara em {agendar} minutos :hourglass_not_done:', use_aliases=True))
        enviarMensagens(respostaID, agendado)
        agendar = (agendar * 60) + 5
        sleep(agendar)
        atualizando = (emoji.emojize('Atualizando... :globe_with_meridians:', use_aliases=True)) # msg de atualizaçao dos dados
        enviarMensagens(respostaID, atualizando)

        try:
            '''
            bot.answerCallbackQuery(usuario, text=(emoji.emojize('Atualizando... :globe_with_meridians:', use_aliases=True)))

            Requisição removida por causa do tempo de espera para a utilizaçao que o script necessita, a API retorna o erro:
            'Bad Request: query is too old and response timeout expired or query ID is invalid'
            '''
            dados = calendario('https://br.investing.com/economic-calendar/')
            atualizado = (emoji.emojize('Atualizado com sucesso :thumbs_up:', use_aliases=True))
            enviarMensagens(respostaID, atualizado)
            trabalhando = (emoji.emojize('Enviando notícias :man_technologist:', use_aliases=True))
            enviarMensagens(respostaID, trabalhando)

            quantidade = (len(dados) / 6) # quantidade de noticias

            while True: # mostra o horario atual da maquina para verificar junto com o horario da noticia (adicionado correçao de fuso horario)
                
                fuso = timedelta(hours=-3)
                zona = timezone(fuso)
                agora = datetime.now()
                correçao = agora.astimezone(zona)
                minutos = (correçao.minute)
                atual = ((correçao.hour * 60) + minutos)
                
                horario = dados[0] # dado especifico para o horario da noticia
                verificacao = dados[1]# dado especifico para verificar o horario da noticia em minutos

                if verificacao == 0:
                    verificacao = verificacao

                else:
                    verificacao = (verificacao - 5)

                local = dados[2] # dado especifico para o pais da noticia

                # adiçao do emoji da bandeira do local -->
                if local == 'Argentina':
                    bandeira = (emoji.emojize('\U0001F1E6\U0001F1F7', use_aliases=True))

                elif local == 'Austrália':
                    bandeira = (emoji.emojize('\U0001F1E6\U0001F1FA', use_aliases=True))

                elif local == 'Brasil':
                    bandeira = (emoji.emojize('\U0001F1E7\U0001F1F7', use_aliases=True))

                elif local == 'Canadá':
                    bandeira = (emoji.emojize('\U0001F1E8\U0001F1E6', use_aliases=True))

                elif local == 'Suíça':
                    bandeira = (emoji.emojize('\U0001F1E8\U0001F1ED', use_aliases=True))
                
                elif local == 'China':
                    bandeira = (emoji.emojize('\U0001F1E8\U0001F1F3', use_aliases=True))
                
                elif local == 'Alemanha':
                    bandeira = (emoji.emojize('\U0001F1E9\U0001F1EA', use_aliases=True))

                elif local == 'Espanha':
                    bandeira = (emoji.emojize('\U0001F1EA\U0001F1F8', use_aliases=True))

                elif local == 'Zona Euro':
                    bandeira = (emoji.emojize('\U0001F1EA\U0001F1FA', use_aliases=True))

                elif local == 'França':
                    bandeira = (emoji.emojize('\U0001F1EB\U0001F1F7', use_aliases=True))

                elif local == 'Reino Unido':
                    bandeira = (emoji.emojize('\U0001F1EC\U0001F1E7', use_aliases=True))

                elif local == 'Hong Kong':
                    bandeira = (emoji.emojize('\U0001F1ED\U0001F1F0', use_aliases=True))

                elif local == 'Indonésia':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1E9', use_aliases=True))

                elif local == 'Irlanda':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1EA', use_aliases=True))

                elif local == 'Índia':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1F3', use_aliases=True))

                elif local == 'Itália':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1F9', use_aliases=True))

                elif local == 'Japão':
                    bandeira = (emoji.emojize('\U0001F1EF\U0001F1F5', use_aliases=True))

                elif local == 'Coreia do Norte':
                    bandeira = (emoji.emojize('\U0001F1F0\U0001F1F5', use_aliases=True))

                elif local == 'Coreia do Sul':
                    bandeira = (emoji.emojize('\U0001F1F0\U0001F1F7', use_aliases=True))

                elif local == 'México':
                    bandeira = (emoji.emojize('\U0001F1F2\U0001F1FD', use_aliases=True))

                elif local == 'Países Baixos':
                    bandeira = (emoji.emojize('\U0001F1F3\U0001F1F1', use_aliases=True))

                elif local == 'Noruega':
                    bandeira = (emoji.emojize('\U0001F1F3\U0001F1F4', use_aliases=True))

                elif local == 'Nova Zelândia':
                    bandeira = (emoji.emojize('\U0001F1F3\U0001F1FF', use_aliases=True))

                elif local == 'Portugal':
                    bandeira = (emoji.emojize('\U0001F1F5\U0001F1F9', use_aliases=True))

                elif local == 'Rússia':
                    bandeira = (emoji.emojize('\U0001F1F7\U0001F1FA', use_aliases=True))

                elif local == 'Suécia':
                    bandeira = (emoji.emojize('\U0001F1F8\U0001F1EA', use_aliases=True))

                elif local == 'Cingapura':
                    bandeira = (emoji.emojize('\U0001F1F8\U0001F1EC', use_aliases=True))

                elif local == 'Turquia':
                    bandeira = (emoji.emojize('\U0001F1F9\U0001F1F7', use_aliases=True))

                elif local == 'EUA':
                    bandeira = (emoji.emojize('\U0001F1FA\U0001F1F8', use_aliases=True))

                elif local == 'África do Sul':
                    bandeira = (emoji.emojize('\U0001F1FF\U0001F1E6', use_aliases=True))

                elif local == 'Inglaterra':
                    bandeira = (emoji.emojize('\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F', use_aliases=True))

                else:
                    bandeira = (emoji.emojize(':globe_showing_Americas:', use_aliases=True))
                # adiçao do emoji da bandeira do local <--
                
                impacto = dados[3] # dado especifico para o impacto da noticia
                impacto = (emoji.emojize(int(impacto) * f':cow_face:', use_aliases=True)) # transformando dado em emoji
                link = dados[4] # dado especifico para o link da noticia
                chamada = dados[5] # dado especifico para a chamada da noticia

                noticia = (emoji.emojize(f'Local: {local} {bandeira}\
\nHorário: {horario}\
\nImpacto da notícia: {impacto}\
\n:loudspeaker: {chamada.strip()}\
\n\
\nPara ver mais acesse :backhand_index_pointing_down:', use_aliases=True)).strip() # noticia formatada 
                
                botao = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=(emoji.emojize('+ NOTÍCIA :receipt:', use_aliases=True)), url=f'{link.strip()}')]]) # botao com link acesso a noticia
                
                if verificacao == 0 and atual == 0:
                    enviarMensagens(channelID, noticia, botao)
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                    
                elif verificacao == 0 and verificacao < atual:
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes

                elif verificacao == atual:
                    enviarMensagens(channelID, noticia, botao)
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                
                elif verificacao <= atual:
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                
                else:
                    pass

                if quantidade == 0:
                    terminado = (emoji.emojize('Todas as notícias já foram enviadas, processo finalizado :beaming_face_with_smiling_eyes::thumbs_up:', use_aliases=True))
                    enviarMensagens(respostaID, terminado)
                    break

                else:
                    pass

        except:
            desatualizado = (emoji.emojize('Erro inesperado ao atualizar! :pensive_face:', use_aliases=True)) # msg de erro na atualizaçao
            enviarMensagens(respostaID, desatualizado)
    
    elif resposta == 'loop':

        loop = (emoji.emojize('Entrando em loop... :counterclockwise_arrows_button:', use_aliases=True))
        enviarMensagens(respostaID, loop)

        atualizando = (emoji.emojize('Atualizando... :globe_with_meridians:', use_aliases=True)) # msg de atualizaçao dos dados
        enviarMensagens(respostaID, atualizando)

        try:
            dados = calendario('https://br.investing.com/economic-calendar/')
            atualizado = (emoji.emojize('Atualizado com sucesso :thumbs_up:', use_aliases=True))
            enviarMensagens(respostaID, atualizado)
            trabalhando = (emoji.emojize('Enviando notícias :man_technologist:', use_aliases=True))
            enviarMensagens(respostaID, trabalhando)

            quantidade = (len(dados) / 6) # quantidade de noticias

            while True: # mostra o horario atual da maquina para verificar junto com o horario da noticia (adicionado correçao de fuso horario)

                fuso = timedelta(hours=-3)
                zona = timezone(fuso)
                agora = datetime.now()
                correçao = agora.astimezone(zona)
                minutos = (correçao.minute)
                atual = ((correçao.hour * 60) + minutos)
                
                horario = dados[0] # dado especifico para o horario da noticia
                verificacao = dados[1]# dado especifico para verificar o horario da noticia em minutos

                if verificacao == 0:
                    verificacao = verificacao

                else:
                    verificacao = (verificacao - 5)

                local = dados[2] # dado especifico para o pais da noticia

                # adiçao do emoji da bandeira do local -->
                if local == 'Argentina':
                    bandeira = (emoji.emojize('\U0001F1E6\U0001F1F7', use_aliases=True))

                elif local == 'Austrália':
                    bandeira = (emoji.emojize('\U0001F1E6\U0001F1FA', use_aliases=True))

                elif local == 'Brasil':
                    bandeira = (emoji.emojize('\U0001F1E7\U0001F1F7', use_aliases=True))

                elif local == 'Canadá':
                    bandeira = (emoji.emojize('\U0001F1E8\U0001F1E6', use_aliases=True))

                elif local == 'Suíça':
                    bandeira = (emoji.emojize('\U0001F1E8\U0001F1ED', use_aliases=True))
                
                elif local == 'China':
                    bandeira = (emoji.emojize('\U0001F1E8\U0001F1F3', use_aliases=True))
                
                elif local == 'Alemanha':
                    bandeira = (emoji.emojize('\U0001F1E9\U0001F1EA', use_aliases=True))

                elif local == 'Espanha':
                    bandeira = (emoji.emojize('\U0001F1EA\U0001F1F8', use_aliases=True))

                elif local == 'Zona Euro':
                    bandeira = (emoji.emojize('\U0001F1EA\U0001F1FA', use_aliases=True))

                elif local == 'França':
                    bandeira = (emoji.emojize('\U0001F1EB\U0001F1F7', use_aliases=True))

                elif local == 'Reino Unido':
                    bandeira = (emoji.emojize('\U0001F1EC\U0001F1E7', use_aliases=True))

                elif local == 'Hong Kong':
                    bandeira = (emoji.emojize('\U0001F1ED\U0001F1F0', use_aliases=True))

                elif local == 'Indonésia':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1E9', use_aliases=True))

                elif local == 'Irlanda':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1EA', use_aliases=True))

                elif local == 'Índia':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1F3', use_aliases=True))

                elif local == 'Itália':
                    bandeira = (emoji.emojize('\U0001F1EE\U0001F1F9', use_aliases=True))

                elif local == 'Japão':
                    bandeira = (emoji.emojize('\U0001F1EF\U0001F1F5', use_aliases=True))

                elif local == 'Coreia do Norte':
                    bandeira = (emoji.emojize('\U0001F1F0\U0001F1F5', use_aliases=True))

                elif local == 'Coreia do Sul':
                    bandeira = (emoji.emojize('\U0001F1F0\U0001F1F7', use_aliases=True))

                elif local == 'México':
                    bandeira = (emoji.emojize('\U0001F1F2\U0001F1FD', use_aliases=True))

                elif local == 'Países Baixos':
                    bandeira = (emoji.emojize('\U0001F1F3\U0001F1F1', use_aliases=True))

                elif local == 'Noruega':
                    bandeira = (emoji.emojize('\U0001F1F3\U0001F1F4', use_aliases=True))

                elif local == 'Nova Zelândia':
                    bandeira = (emoji.emojize('\U0001F1F3\U0001F1FF', use_aliases=True))

                elif local == 'Portugal':
                    bandeira = (emoji.emojize('\U0001F1F5\U0001F1F9', use_aliases=True))

                elif local == 'Rússia':
                    bandeira = (emoji.emojize('\U0001F1F7\U0001F1FA', use_aliases=True))

                elif local == 'Suécia':
                    bandeira = (emoji.emojize('\U0001F1F8\U0001F1EA', use_aliases=True))

                elif local == 'Cingapura':
                    bandeira = (emoji.emojize('\U0001F1F8\U0001F1EC', use_aliases=True))

                elif local == 'Turquia':
                    bandeira = (emoji.emojize('\U0001F1F9\U0001F1F7', use_aliases=True))

                elif local == 'EUA':
                    bandeira = (emoji.emojize('\U0001F1FA\U0001F1F8', use_aliases=True))

                elif local == 'África do Sul':
                    bandeira = (emoji.emojize('\U0001F1FF\U0001F1E6', use_aliases=True))

                elif local == 'Inglaterra':
                    bandeira = (emoji.emojize('\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F', use_aliases=True))

                else:
                    bandeira = (emoji.emojize(':globe_showing_Americas:', use_aliases=True))
                # adiçao do emoji da bandeira do local <--

                impacto = dados[3] # dado especifico para o impacto da noticia
                impacto = (emoji.emojize(int(impacto) * f':cow_face:', use_aliases=True)) # transformando dado em emoji
                link = dados[4] # dado especifico para o link da noticia
                chamada = dados[5] # dado especifico para a chamada da noticia

                noticia = (emoji.emojize(f'Local: {local} {bandeira}\
\nHorário: {horario}\
\nImpacto da notícia: {impacto}\
\n:loudspeaker: {chamada.strip()}\
\n\
\nPara ver mais acesse :backhand_index_pointing_down:', use_aliases=True)).strip() # noticia formatada 

                botao = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=(emoji.emojize('+ NOTÍCIA :receipt:', use_aliases=True)), url=f'{link.strip()}')]]) # botao com link acesso a noticia
                
                if verificacao == 0 and atual == 0:
                    enviarMensagens(channelID, noticia, botao)
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                    
                elif verificacao == 0 and verificacao < atual:
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes

                elif verificacao == atual:
                    enviarMensagens(channelID, noticia, botao)
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                
                elif verificacao <= atual:
                    quantidade = quantidade - 1

                    for item in range(0, 6):
                        del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                
                else:
                    pass

                if quantidade == 0:
                    terminado = (emoji.emojize('Todas as notícias já foram enviadas, processo finalizado :beaming_face_with_smiling_eyes::thumbs_up:', use_aliases=True))
                    enviarMensagens(respostaID, terminado)
                    break

                else:
                    pass

        except:
            desatualizado = (emoji.emojize('Erro inesperado ao atualizar! :pensive_face:', use_aliases=True)) # msg de erro na atualizaçao
            enviarMensagens(respostaID, desatualizado)

        while True:

            if quantidade == 0:
                # mostra o horario atual da maquina para verificar junto com o horario da noticia (adicionado correçao de fuso horario)
                fuso = timedelta(hours=-3)
                zona = timezone(fuso)
                agora = datetime.now()
                correçao = agora.astimezone(zona)
                minutos = (correçao.minute)
                atual = ((correçao.hour * 60) + minutos)

                # agenda o tempo em que o script sera atualizado de acordo com o horario atual e o que falta para o final do dia
                agendar = (1440 - atual)
                agendado = (emoji.emojize(f'O envio das notícias se iniciara em {agendar} minutos :hourglass_not_done:', use_aliases=True))
                enviarMensagens(respostaID, agendado)
                agendar = (agendar * 60) + 5
                sleep(agendar)
                atualizando = (emoji.emojize('Atualizando... :globe_with_meridians:', use_aliases=True)) # msg de atualizaçao dos dados
                enviarMensagens(respostaID, atualizando)

                try:
                    '''
                    bot.answerCallbackQuery(usuario, text=(emoji.emojize('Atualizando... :globe_with_meridians:', use_aliases=True)))

                    Requisição removida por causa do tempo de espera para a utilizaçao que o script necessita, a API retorna o erro:
                    'Bad Request: query is too old and response timeout expired or query ID is invalid'
                    '''
                    dados = calendario('https://br.investing.com/economic-calendar/')
                    atualizado = (emoji.emojize('Atualizado com sucesso :thumbs_up:', use_aliases=True))
                    enviarMensagens(respostaID, atualizado)
                    trabalhando = (emoji.emojize('Enviando notícias :man_technologist:', use_aliases=True))
                    enviarMensagens(respostaID, trabalhando)

                    quantidade = (len(dados) / 6) # quantidade de noticias

                    while True: # mostra o horario atual da maquina para verificar junto com o horario da noticia (adicionado correçao de fuso horario)

                        
                        fuso = timedelta(hours=-3)
                        zona = timezone(fuso)
                        agora = datetime.now()
                        correçao = agora.astimezone(zona)
                        minutos = (correçao.minute)
                        atual = ((correçao.hour * 60) + minutos)
                        
                        horario = dados[0] # dado especifico para o horario da noticia
                        verificacao = dados[1]# dado especifico para verificar o horario da noticia em minutos

                        if verificacao == 0:
                            verificacao = verificacao

                        else:
                            verificacao = (verificacao - 5)

                        local = dados[2] # dado especifico para o pais da noticia

                        # adiçao do emoji da bandeira do local -->
                        if local == 'Argentina':
                            bandeira = (emoji.emojize('\U0001F1E6\U0001F1F7', use_aliases=True))

                        elif local == 'Austrália':
                            bandeira = (emoji.emojize('\U0001F1E6\U0001F1FA', use_aliases=True))

                        elif local == 'Brasil':
                            bandeira = (emoji.emojize('\U0001F1E7\U0001F1F7', use_aliases=True))

                        elif local == 'Canadá':
                            bandeira = (emoji.emojize('\U0001F1E8\U0001F1E6', use_aliases=True))

                        elif local == 'Suíça':
                            bandeira = (emoji.emojize('\U0001F1E8\U0001F1ED', use_aliases=True))
                        
                        elif local == 'China':
                            bandeira = (emoji.emojize('\U0001F1E8\U0001F1F3', use_aliases=True))
                        
                        elif local == 'Alemanha':
                            bandeira = (emoji.emojize('\U0001F1E9\U0001F1EA', use_aliases=True))

                        elif local == 'Espanha':
                            bandeira = (emoji.emojize('\U0001F1EA\U0001F1F8', use_aliases=True))

                        elif local == 'Zona Euro':
                            bandeira = (emoji.emojize('\U0001F1EA\U0001F1FA', use_aliases=True))

                        elif local == 'França':
                            bandeira = (emoji.emojize('\U0001F1EB\U0001F1F7', use_aliases=True))

                        elif local == 'Reino Unido':
                            bandeira = (emoji.emojize('\U0001F1EC\U0001F1E7', use_aliases=True))

                        elif local == 'Hong Kong':
                            bandeira = (emoji.emojize('\U0001F1ED\U0001F1F0', use_aliases=True))

                        elif local == 'Indonésia':
                            bandeira = (emoji.emojize('\U0001F1EE\U0001F1E9', use_aliases=True))

                        elif local == 'Irlanda':
                            bandeira = (emoji.emojize('\U0001F1EE\U0001F1EA', use_aliases=True))

                        elif local == 'Índia':
                            bandeira = (emoji.emojize('\U0001F1EE\U0001F1F3', use_aliases=True))

                        elif local == 'Itália':
                            bandeira = (emoji.emojize('\U0001F1EE\U0001F1F9', use_aliases=True))

                        elif local == 'Japão':
                            bandeira = (emoji.emojize('\U0001F1EF\U0001F1F5', use_aliases=True))

                        elif local == 'Coreia do Norte':
                            bandeira = (emoji.emojize('\U0001F1F0\U0001F1F5', use_aliases=True))

                        elif local == 'Coreia do Sul':
                            bandeira = (emoji.emojize('\U0001F1F0\U0001F1F7', use_aliases=True))

                        elif local == 'México':
                            bandeira = (emoji.emojize('\U0001F1F2\U0001F1FD', use_aliases=True))

                        elif local == 'Países Baixos':
                            bandeira = (emoji.emojize('\U0001F1F3\U0001F1F1', use_aliases=True))

                        elif local == 'Noruega':
                            bandeira = (emoji.emojize('\U0001F1F3\U0001F1F4', use_aliases=True))

                        elif local == 'Nova Zelândia':
                            bandeira = (emoji.emojize('\U0001F1F3\U0001F1FF', use_aliases=True))

                        elif local == 'Portugal':
                            bandeira = (emoji.emojize('\U0001F1F5\U0001F1F9', use_aliases=True))

                        elif local == 'Rússia':
                            bandeira = (emoji.emojize('\U0001F1F7\U0001F1FA', use_aliases=True))

                        elif local == 'Suécia':
                            bandeira = (emoji.emojize('\U0001F1F8\U0001F1EA', use_aliases=True))

                        elif local == 'Cingapura':
                            bandeira = (emoji.emojize('\U0001F1F8\U0001F1EC', use_aliases=True))

                        elif local == 'Turquia':
                            bandeira = (emoji.emojize('\U0001F1F9\U0001F1F7', use_aliases=True))

                        elif local == 'EUA':
                            bandeira = (emoji.emojize('\U0001F1FA\U0001F1F8', use_aliases=True))

                        elif local == 'África do Sul':
                            bandeira = (emoji.emojize('\U0001F1FF\U0001F1E6', use_aliases=True))

                        elif local == 'Inglaterra':
                            bandeira = (emoji.emojize('\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F', use_aliases=True))

                        else:
                            bandeira = (emoji.emojize(':globe_showing_Americas:', use_aliases=True))
                        # adiçao do emoji da bandeira do local <--

                        impacto = dados[3] # dado especifico para o impacto da noticia
                        impacto = (emoji.emojize(int(impacto) * f':cow_face:', use_aliases=True)) # transformando dado em emoji
                        link = dados[4] # dado especifico para o link da noticia
                        chamada = dados[5] # dado especifico para a chamada da noticia

                        noticia = (emoji.emojize(f'Local: {local} {bandeira}\
\nHorário: {horario}\
\nImpacto da notícia: {impacto}\
\n:loudspeaker: {chamada.strip()}\
\n\
\nPara ver mais acesse :backhand_index_pointing_down:', use_aliases=True)).strip() # noticia formatada 
                        
                        botao = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=(emoji.emojize('+ NOTÍCIA :receipt:', use_aliases=True)), url=f'{link.strip()}')]]) # botao com link acesso a noticia
                        
                        if verificacao == 0 and atual == 0:
                            enviarMensagens(channelID, noticia, botao)
                            quantidade = quantidade - 1

                            for item in range(0, 6):
                                del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                            
                        elif verificacao == 0 and verificacao < atual:
                            quantidade = quantidade - 1

                            for item in range(0, 6):
                                del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes

                        elif verificacao == atual:
                            enviarMensagens(channelID, noticia, botao)
                            quantidade = quantidade - 1

                            for item in range(0, 6):
                                del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                        
                        elif verificacao <= atual:
                            quantidade = quantidade - 1

                            for item in range(0, 6):
                                del dados[0] # apaga as ultimas informaçoes ja usadas(6 primeiros itens na lista), para nao ter repetiçoes
                        
                        else:
                            pass

                        if quantidade == 0:
                            terminado = (emoji.emojize('Todas as notícias já foram enviadas, processo finalizado :beaming_face_with_smiling_eyes::thumbs_up:', use_aliases=True))
                            enviarMensagens(respostaID, terminado)
                            break

                        else:
                            pass

                except:
                    desatualizado = (emoji.emojize('Erro inesperado ao atualizar! :pensive_face:', use_aliases=True)) # msg de erro na atualizaçao
                    enviarMensagens(respostaID, desatualizado)

            else:
                pass

    else:
        pass

### loop do modulo 'telepot' para procurar e receber novas mensagens, executando as funçoes ###
bot.message_loop({'chat': receberMensagens, 'callback_query': responderMensagens}) 

### loop em python para manter o programa rodando ###
while True:
    pass
