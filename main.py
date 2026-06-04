import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.network.urlrequest import UrlRequest
from kivy.graphics import Color, RoundedRectangle
from datetime import datetime, timedelta

# =========================================================
# COLOQUE A SUA CHAVE DA API ENTRE AS ASPAS ABAIXO:
MINHA_API_KEY = "cb68bec4ddaf9f52abed04e245718776"
# =========================================================

# --- COMPONENTE VISUAL: CARTÃO DE JOGO ADAPTÁVEL ---
class JogoCard(BoxLayout):
    def __init__(self, time_casa, time_fora, status, palpite_p, palpite_g, **kwargs):
        super(JogoCard, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        # Em vez de altura fixa, usamos a altura mínima baseada nos filhos + padding
        self.padding = 15
        self.spacing = 10

        # Desenha o fundo arredondado do cartão usando o Canvas do Kivy
        with self.canvas.before:
            Color(0.15, 0.15, 0.18, 1) # Cor cinza-azulada escura
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
        self.bind(pos=self.atualizar_retangulo, size=self.atualizar_retangulo)

        # 1. Linha do Status / Tempo Real
        lbl_status = Label(
            text=status,
            font_size='13sp',
            bold=True,
            halign='left',
            size_hint_y=None,
            height=25
        )
        lbl_status.bind(size=lbl_status.setter('text_size'))
        self.add_widget(lbl_status)

        # 2. Linha das Equipas (Visual de Placar)
        lbl_equipas = Label(
            text=f"{time_casa}  vs  {time_fora}",
            font_size='18sp',
            bold=True,
            halign='center',
            size_hint_y=None,
            height=35
        )
        lbl_equipas.bind(size=lbl_equipas.setter('text_size'))
        self.add_widget(lbl_equipas)

        # Separador interno discreto
        lbl_linha = Label(text="----------------------------------------", color=(0.3, 0.3, 0.3, 0.5), size_hint_y=None, height=10)
        self.add_widget(lbl_linha)

        # 3. Bloco de Palpites da IA (Destacado)
        lbl_palpite1 = Label(
            text=palpite_p,
            font_size='14sp',
            color=(0.2, 0.8, 1, 1), # Azul claro para o resultado
            halign='left',
            size_hint_y=None,
            height=25
        )
        lbl_palpite1.bind(size=lbl_palpite1.setter('text_size'))
        self.add_widget(lbl_palpite1)

        lbl_palpite2 = Label(
            text=palpite_g,
            font_size='13sp',
            color=(0.2, 1, 0.6, 1), # Verde claro para os golos
            halign='left',
            size_hint_y=None,
            height=25
        )
        lbl_palpite2.bind(size=lbl_palpite2.setter('text_size'))
        self.add_widget(lbl_palpite2)

        # Faz com que a altura do cartão seja a soma exata de todos os elementos internos automaticamente
        self.bind(minimum_height=self.setter('height'))

    def atualizar_retangulo(self, instance, value):
        self.rect.pos = self.pos
        self.rect.size = self.size


class PredictorHome(BoxLayout):
    def __init__(self, **kwargs):
        super(PredictorHome, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 12
        self.spacing = 12

        # Altera o fundo geral do app para um tom grafite elegante
        with self.canvas.before:
            Color(0.08, 0.08, 0.1, 1)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.atualizar_bg, size=self.atualizar_bg)

        # --- ABAS DE NAVEGAÇÃO + BOTÃO ATUALIZAR ---
        self.barra_abas = BoxLayout(size_hint_y=None, height=50, spacing=6)
        
        self.btn_aba_principais = Button(
            text="🏆 Principais", 
            bold=True,
            background_color=(0, 0.4, 0.8, 1)
        )
        self.btn_aba_todos = Button(
            text="🌍 Todos os Jogos", 
            bold=True,
            background_color=(0.2, 0.2, 0.25, 1)
        )
        self.btn_atualizar = Button(
            text="🔄", 
            bold=True,
            size_hint_x=None,
            width=60,
            background_color=(0.1, 0.6, 0.3, 1)
        )
        
        self.btn_aba_principais.bind(on_press=self.ativar_modo_principais)
        self.btn_aba_todos.bind(on_press=self.ativar_modo_todos)
        self.btn_atualizar.bind(on_press=self.forcar_atualizacao)
        
        self.barra_abas.add_widget(self.btn_aba_principais)
        self.barra_abas.add_widget(self.btn_aba_todos)
        self.barra_abas.add_widget(self.btn_atualizar)
        self.add_widget(self.barra_abas)

        # --- FILTRO DE PAÍSES ---
        self.filtro_paises = BoxLayout(size_hint_y=None, height=45, spacing=8)
        
        self.traducao_paises = {
            "Mundo": "Mundo",
            "Brasil": "Brazil",
            "Inglaterra": "England",
            "Espanha": "Spain",
            "Itália": "Italy"
        }
        paises = list(self.traducao_paises.keys())
        self.botoes_paises = {}
        
        for p in paises:
            btn = Button(
                text=p, 
                size_hint_x=None, 
                width=100,
                background_color=(0.18, 0.18, 0.22, 1)
            )
            btn.bind(on_press=self.filtrar_por_pais)
            self.filtro_paises.add_widget(btn)
            self.botoes_paises[p] = btn
            
        self.botoes_paises["Mundo"].background_color = (0, 0.5, 0.3, 1)
        self.add_widget(self.filtro_paises)

        # --- ÁREA DE CONTEÚDO COM SCROLL ---
        self.scroll = ScrollView(size_hint=(1, 1))
        
        self.container_dinamico = BoxLayout(
            orientation='vertical', 
            size_hint_y=None, 
            spacing=14
        )
        self.container_dinamico.bind(
            minimum_height=self.container_dinamico.setter('height')
        )
        
        self.lbl_mensagem = Label(
            text="Toque em 'Mundo' ou escolha um país para listar as opções.",
            font_size='16sp',
            color=(0.7, 0.7, 0.7, 1),
            halign='center',
            size_hint_y=None,
            height=100
        )
        
        self.container_dinamico.add_widget(self.lbl_mensagem)
        self.scroll.add_widget(self.container_dinamico)
        self.add_widget(self.scroll)

        self.modo_atual = "principais"
        self.pais_selecionado = "Mundo"
        self.ligas_armazenadas = {}
        
        self.dados_cache = None
        self.ultima_atualizacao = None

    def atualizar_bg(self, instance, value):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def ativar_modo_principais(self, instance):
        self.modo_atual = "principais"
        self.btn_aba_principais.background_color = (0, 0.4, 0.8, 1)
        self.btn_aba_todos.background_color = (0.2, 0.2, 0.25, 1)
        self.executar_busca_api()

    def ativar_modo_todos(self, instance):
        self.modo_atual = "todos"
        self.btn_aba_principais.background_color = (0.2, 0.2, 0.25, 1)
        self.btn_aba_todos.background_color = (0, 0.4, 0.8, 1)
        self.executar_busca_api()

    def filtrar_por_pais(self, instance):
        for btn in self.botoes_paises.values():
            btn.background_color = (0.18, 0.18, 0.22, 1)
        instance.background_color = (0, 0.5, 0.3, 1)
        self.pais_selecionado = instance.text
        self.executar_busca_api()

    def forcar_atualizacao(self, instance):
        self.dados_cache = None
        self.ultima_atualizacao = None
        self.executar_busca_api()

    def executar_busca_api(self):
        if self.dados_cache and self.ultima_atualizacao:
            tempo_passado = datetime.now() - self.ultima_atualizacao
            if tempo_passado < timedelta(minutes=5):
                self.processar_ligas(None, self.dados_cache)
                return

        self.container_dinamico.clear_widgets()
        self.lbl_mensagem.text = "⏳ Sincronizando dados com o servidor..."
        self.container_dinamico.add_widget(self.lbl_mensagem)
        
        data_hoje = datetime.now().strftime('%Y-%m-%d')
        url = f"https://v3.football.api-sports.io/fixtures?date={data_hoje}"
        
        headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': MINHA_API_KEY
        }
        
        UrlRequest(
            url, 
            on_success=self.salvar_cache_e_processar, 
            on_failure=self.erro_requisicao,
            on_error=self.erro_requisicao,
            req_headers=headers
        )

    def salvar_cache_e_processar(self, req, resultado):
        if resultado and resultado.get('response'):
            self.dados_cache = resultado
            self.ultima_atualizacao = datetime.now()
        self.processar_ligas(req, resultado)

    def criar_label_cache(self):
        tempo_str = self.ultima_atualizacao.strftime('%H:%M:%S') if self.ultima_atualizacao else ""
        return Label(
            text=f"Dados atualizados às: {tempo_str}",
            font_size='12sp',
            color=(0.5, 0.5, 0.6, 1),
            size_hint_y=None,
            height=25
        )

    def processar_ligas(self, req, resultado):
        self.container_dinamico.clear_widgets()
        self.ligas_armazenadas.clear()

        if not resultado or not resultado.get('response') or len(resultado['response']) == 0:
            self.lbl_mensagem.text = "Nenhum jogo disponível na API para hoje."
            self.container_dinamico.add_widget(self.lbl_mensagem)
            return

        lista_jogos = resultado['response']
        ligas_principais_ids = [39, 71, 140, 135, 78, 2, 3] 

        for item in lista_jogos:
            nome_liga = item['league']['name'].upper()
            id_liga = item['league']['id']
            pais_liga = item['league']['country']
            
            if self.modo_atual == "principais" and id_liga not in ligas_principais_ids:
                continue
                
            if self.pais_selecionado != "Mundo":
                pais_esperado = self.traducao_paises.get(self.pais_selecionado, "")
                if pais_liga.lower() != pais_esperado.lower():
                    continue

            if nome_liga not in self.ligas_armazenadas:
                self.ligas_armazenadas[nome_liga] = []
            self.ligas_armazenadas[nome_liga].append(item)

        if not self.ligas_armazenadas:
            self.lbl_mensagem.text = "Nenhuma liga encontrada para este filtro."
            self.container_dinamico.add_widget(self.lbl_mensagem)
            return

        self.container_dinamico.add_widget(self.criar_label_cache())

        if self.pais_selecionado == "Mundo":
            for nome_liga in sorted(self.ligas_armazenadas.keys()):
                btn_liga = Button(
                    text=f"🏆 {nome_liga} ({len(self.ligas_armazenadas[nome_liga])} jogos)",
                    size_hint_y=None,
                    height=50,
                    background_color=(0.14, 0.14, 0.18, 1),
                    bold=True
                )
                btn_liga.bind(on_press=lambda inst, liga=nome_liga: self.mostrar_jogos_da_liga(liga))
                self.container_dinamico.add_widget(btn_liga)
        else:
            self.mostrar_todas_as_ligas_direto()

    def calcular_palpite_ia(self, jogo):
        forma_casa = jogo['teams']['home'].get('form', 'WWWWW') or 'WWWWW'
        forma_fora = jogo['teams']['away'].get('form', 'WWWWW') or 'WWWWW'
        
        pontos_casa = forma_casa.count('W') * 3 + forma_casa.count('D') * 1
        pontos_fora = forma_fora.count('W') * 3 + forma_fora.count('D') * 1
        pontos_casa += 3 
        
        golos_casa_marcados = jogo['goals']['home'] if jogo['goals']['home'] is not None else 1
        golos_fora_marcados = jogo['goals']['away'] if jogo['goals']['away'] is not None else 1
        
        diferenca = pontos_casa - pontos_fora
        time_casa = jogo['teams']['home']['name']
        time_fora = jogo['teams']['away']['name']
        
        if diferenca > 4:
            palpite_principal = f"🏆 Vitória: {time_casa} (Confiança Alta)"
        elif diferenca < -4:
            palpite_principal = f"🏆 Vitória: {time_fora} (Confiança Alta)"
        elif diferenca > 0:
            palpite_principal = f"⚖️ Dupla Chance: {time_casa} ou Empate"
        else:
            palpite_principal = f"⚖️ Dupla Chance: {time_fora} ou Empate"
            
        total_estimado_goles = golos_casa_marcados + golos_fora_marcados
        if total_estimado_goles >= 3:
            palpite_goles = "🎯 Golos: Mais de 2.5 | ⚽ Ambas Marcam: SIM"
        elif total_estimado_goles == 0 or total_estimado_goles == 1:
            palpite_goles = "🎯 Golos: Menos de 2.5 | ⚽ Ambas Marcam: NÃO"
        else:
            palpite_goles = "🎯 Golos: Mais de 1.5 | ⚽ Ambas Marcam: Neutro"
            
        return palpite_principal, palpite_goles

    def obter_status_ao_vivo(self, jogo):
        status_code = jogo['fixture']['status']['short']
        tempo_decorrido = jogo['fixture']['status']['elapsed']
        
        golos_casa = jogo['goals']['home']
        golos_fora = jogo['goals']['away']
        if golos_casa is None: golos_casa = 0
        if golos_fora is None: golos_fora = 0

        if status_code in ["1H", "2H"]:
            return f"🟢 AO VIVO - {tempo_decorrido}' Min | {golos_casa} - {golos_fora}"
        elif status_code == "HT":
            return f"🟡 INTERVALO | {golos_casa} - {golos_fora}"
        elif status_code == "FT":
            return f"🔴 TERMINADO | FINAL: {golos_casa} - {golos_fora}"
        else:
            hora_jogo = jogo['fixture']['date'].split("T")[1][:5]
            return f"⚫ AGENDADO - Às {hora_jogo}"

    def mostrar_jogos_da_liga(self, nome_liga):
        self.container_dinamico.clear_widgets()
        
        btn_voltar = Button(
            text="⬅️ Voltar para as Ligas",
            size_hint_y=None,
            height=45,
            background_color=(0.6, 0.15, 0.15, 1),
            bold=True
        )
        btn_voltar.bind(on_press=lambda inst: self.restaurar_lista_ligas())
        self.container_dinamico.add_widget(btn_voltar)

        jogos = self.ligas_armazenadas.get(nome_liga, [])
        
        for jogo in jogos[:10]:
            time_casa = jogo['teams']['home']['name']
            time_fora = jogo['teams']['away']['name']
            p_principal, p_goles = self.calcular_palpite_ia(jogo)
            placar_tempo_real = self.obter_status_ao_vivo(jogo)
            
            card = JogoCard(time_casa, time_fora, placar_tempo_real, p_principal, p_goles)
            self.container_dinamico.add_widget(card)

    def mostrar_todas_as_ligas_direto(self):
        for nome_liga, games in self.ligas_armazenadas.items():
            lbl_seccao = Label(
                text=f"🏆 LIGA: {nome_liga}",
                font_size='14sp',
                bold=True,
                color=(0.9, 0.8, 0.3, 1),
                size_hint_y=None,
                height=30,
                halign='left'
            )
            lbl_seccao.bind(size=lbl_seccao.setter('text_size'))
            self.container_dinamico.add_widget(lbl_seccao)
            
            for jogo in games[:10]:
                time_casa = jogo['teams']['home']['name']
                time_fora = jogo['teams']['away']['name']
                p_principal, p_goles = self.calcular_palpite_ia(jogo)
                placar_tempo_real = self.obter_status_ao_vivo(jogo)
                
                card = JogoCard(time_casa, time_fora, placar_tempo_real, p_principal, p_goles)
                self.container_dinamico.add_widget(card)

    def restaurar_lista_ligas(self):
        self.container_dinamico.clear_widgets()
        self.container_dinamico.add_widget(self.criar_label_cache())
        
        for nome_liga in sorted(self.ligas_armazenadas.keys()):
            btn_liga = Button(
                text=f"🏆 {nome_liga} ({len(self.ligas_armazenadas[nome_liga])} jogos)",
                size_hint_y=None,
                height=50,
                background_color=(0.14, 0.14, 0.18, 1),
                bold=True
            )
            btn_liga.bind(on_press=lambda inst, liga=nome_liga: self.mostrar_jogos_da_liga(liga))
            self.container_dinamico.add_widget(btn_liga)

    def erro_requisicao(self, req, erro):
        self.container_dinamico.clear_widgets()
        self.lbl_mensagem.text = "Erro de conexão ou chave inválida."
        self.container_dinamico.add_widget(self.lbl_mensagem)

class PredictorApp(App):
    def build(self):
        return PredictorHome()

if __name__ == '__main__':
    PredictorApp().run()
