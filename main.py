import os
import telebot
from dotenv import load_dotenv
import unicodedata
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# carregar as variaves do .env
load_dotenv()

#busca o token
TOKEN_BOT = os.getenv('TELEGRAM_TOKEN')
SHEET_KEY = os.getenv('SHEET_KEY')

# cria uma instancia do bot
bot = telebot.TeleBot(TOKEN_BOT)

# --- CONFIGURAÇÃO GOOGLE SHEETS ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)

    # Abrindo a planilha pelo ID e a aba específica pelo nome
    planilha_doc = client.open_by_key(SHEET_KEY)
    planilha = planilha_doc.worksheet("2026")

    print("✅ Conexão com Google Sheets estabelecida!")
except Exception as e:
    print(f"❌ Erro na conexão com Google Sheets: {e}")

map = {
  'Mercado': ['MERCADO', 'FORTIS', 'SUPERSEIS', 'BOX', 'STOCK', 'LA MODERNA', 'SUPERMERCADO', 'LA HUERTA'],
  'Alimentação': ['ALMOÇO', 'ALMUERZO', 'JANTA', 'JANTAR', 'CENA', 'DESAYUNO', 'CAFE', 'CAFETERIA', 'CAFE DA MANHA', 'LANCHE', 'SALGADO',
                  'BUFFET', 'CANTINA', 'CANTINA - UCP', 'RESTAURANTE', 'PIZZARIA', 'PIZZA', 'HAMBURGUER', 'HAMBURGUESA', 'LOMITO', 'FAST FOOD',
                  'MCDONALDS', 'BURGER KING', 'MOSTAZA', 'SUSHI', 'SAKURA', 'ORIGAMI', 'BELINI', 'SAN TELMO', 'DON LUIS', 'CAPITAO BAR',
                  'ARENA', 'TERRAZA', 'PANADERIA', 'BOLERIA', 'CHIPERIA', 'HELADO', 'SORVETE', 'PICOLE', 'TORTA', 'BOLO',
                  'CHOCOLATE', 'BOMBOM', 'AGUA', 'COCA', 'BEBIDA', 'MILKSHAKE', 'ALIMENTACAO'],
  'Casa':  ['DIARISTA', 'LUZ', 'AGUA', 'CASA', 'PROSEGUR', 'ALUGUEL',
            'TIGO', 'CLARO', 'BASURAS', 'ANDE', 'PERSONAL', 'ESSAP', 'ALQUILER', 'CASA'],
  'Transporte': ['ESTACIONAMENTO', 'GASOLINA', 'BOLT', 'PEDAGIOS', 'TROCA DE ACEITE', 'UBER', 'LAVAJATO', 'PEAJE', 'AURIS', 'TROCA DE OLEO', 'TRANSPORTE'],
  'Saúde': ['REMEDIOS', 'HOSPITAL', 'FARMACIA', 'SAUDE'],
  'Atividade Física': ['PILATES', 'ACADEMIA', 'PERFECT GYM', 'FISIOVERT', 'ATIVIDADE FISICA'],
  'Beleza': ['UNHA', 'DEPILACAO', 'ESFOLIANTE', 'CORTE DE CABELO', 'SOBRANCELHAS', 'PRODUTOS DE ROSTO', 'PROTETOR SOLAR', 'MANICURE', 'BELEZA'],
  'Mascota': ['PITANGA', 'RACAO', 'PETZ', 'MASCOTAS', 'MASCOTA'],
  'Assinaturas': ['1PASSWORD', 'ICLOUD', 'CHATGPT', 'GOOGLE ONE', 'AMAZON KINDLE UNLIMITED', 'AMAZON PRIME', 'SPOTIFY DUO', 'SURFSHARK VPN', 'ASSINATURA', 'ASSINATURAS'],
  'Educação': ['ITALKI', 'CURSO', 'COURSERA', 'LIVRO', 'CERTIFICACAO', 'UDEMY', 'EDUCACAO'],
  'Tecnologia': ['TECNOLOGIA'],
  'Lazer': ['KART', 'HOSPEDAGEM', 'AIRBNB', 'CORRIDA', 'LAZER', 'TIRO'],
  'Roupas': ['NIKE', 'ZARA', 'ROUPA', 'SAPATO', 'TENIS', 'ROUPAS', 'BRINCOS'],
  'Presentes': ['PRESENTE'],
  'Doações': ['DOACAO'],
  'Investimentos': ['BITCOIN'],
  'Impostos': ['IMPOSTO', 'TAXA', 'SAQUE', 'IMPOSTOS']
}

def identificar_categoria(descricao, mapeamento):
    # remove acentos
    descricao_limpa = "".join(
        c for c in unicodedata.normalize('NFD', descricao)
        if unicodedata.category(c) != 'Mn'
    )
    

    for categoria, palavras in mapeamento.items():
        for palavra in palavras:
            if palavra in descricao_limpa:
                return categoria
    return "OUTRA"        

# --- HANDLER 2: OUVINTE GERAL (FINANÇAS) ---
@bot.message_handler(func=lambda message: True)
def processar_gastos(message):
    print(f"NOME DO CHAT: {message.chat.title} | ID: {message.chat.id}")
    # mensagem original
    mensagem_bruta = message.text

    # transforma a mensagem em uma lista para colocar em partes, elimina espaços extras e maiscula
    partes = [" ".join(p.split()) for p in mensagem_bruta.split(';')]    
    

    #identificacao da data
    fecha = datetime.now().strftime('%d/%m/%Y')

    mensagem_resposta = ""

    # Se for guarani
    if len(partes) == 5:
        desc = partes[0].upper()
        cat = identificar_categoria(desc, map).upper()
        valor = float(partes[1].replace('.', '').replace(',', '.'))
        moeda = "Gs"
        cotizacao = 1
        valor_final = valor * cotizacao
        banco_bruto = partes[2].upper().strip()
        banco = "".join(c for c in unicodedata.normalize('NFD', banco_bruto) if unicodedata.category(c) != 'Mn')
        forma_bruta = partes[3].upper().strip()
        forma = "".join(c for c in unicodedata.normalize('NFD', forma_bruta) if unicodedata.category(c) != 'Mn')
        factura = partes[4].upper()

        valor_final_format = f"{valor_final:,.0f}".replace(',', '.')


        dados_linha = [desc, valor, moeda, cotizacao, valor_final_format, 
                        fecha, cat, banco, forma, factura]
        planilha.append_row(dados_linha)

        mensagem_resposta = f"""
        ✅ *Gasto registrado!*

        📝 *Descrição:* {desc}
        🏷️ *Categoria:* {cat}
        💵 *Valor:* {valor_final_format} Gs
        📅 *Data:* {fecha}
        🏦 *Banco:* {banco}
        💳 *Forma:* {forma}
        🧾 *Factura:* {factura}
        """

    # Outra moeda
    elif len(partes) == 7:
        desc = partes[0].upper()
        cat = identificar_categoria(desc, map).upper()
        moeda = partes[1].upper()
        valor = float(partes[2].replace('.', '').replace(',', '.'))
        cotizacao = int(partes[3].replace('.', '').replace(',', '.'))
        valor_final = valor * cotizacao
        banco_bruto = partes[4].upper().strip()
        banco = "".join(c for c in unicodedata.normalize('NFD', banco_bruto) if unicodedata.category(c) != 'Mn')
        forma_bruta = partes[5].upper().strip()
        forma = "".join(c for c in unicodedata.normalize('NFD', forma_bruta) if unicodedata.category(c) != 'Mn')
        factura = partes[6].upper()

        valor_final_format = f"{valor_final:,.0f}".replace(',', '.')

        dados_linha = [desc, valor, moeda, cotizacao, valor_final_format, 
                        fecha, cat, banco, forma, factura]
        planilha.append_row(dados_linha)

        mensagem_resposta = f"""
        ✅ *Gasto registrado!*
        
        📝 *Descrição:* {desc}
        🏷️ *Categoria:* {cat}
        💰 *Origem:* {moeda} {valor}
        📈 *Cotação:* {cotizacao}
        💵 *Final:* {valor_final_format} Gs
        📅 *Data:* {fecha}
        🏦 *Banco:* {banco}
        💳 *Forma:* {forma}
        🧾 *Factura:* {factura}"""

    else:
        bot.reply_to(message, "❌ Mensagem fora do padrão! Use 5 partes para Gs ou 7 para outras moedas.")
        print(f"\n--- ERRO ---")
        print(f"Mensagem fora do padrão! Use 5 partes para Gs ou 7 para outras moedas.")
        print(f"Mensagem: {mensagem_bruta}")
        return

    print(f"\n--- NOVO GASTO ---")
    print(f"Data: {fecha} | Cat: {cat}")
    print(f"Valor Final: {valor_final_format}")
    
    bot.reply_to(message, mensagem_resposta, parse_mode="Markdown")

if __name__ == "__main__":
    print("✅ Bot iniciado com sucesso")
    bot.infinity_polling()