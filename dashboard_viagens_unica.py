import io
import re
import unicodedata
from urllib.parse import quote
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='BI de Viagens | Única Atacadista', page_icon='🚕', layout='wide', initial_sidebar_state='expanded')
st.markdown("""<style>
.stApp{background:#f5f7fb;color:#18263b}
section[data-testid="stSidebar"]{background:#ffffff;border-right:1px solid #e1e7ef}
.block-container{padding-top:1.2rem;max-width:1900px}
/* Escala visual compacta, sem alterar o zoom do navegador. */
html{font-size:12px}
.stApp p,.stApp label{font-size:.91rem}
div[data-testid="stMetric"]{padding:12px;border-radius:13px}
div[data-testid="stMetricValue"]{font-size:1.65rem}
section[data-testid="stSidebar"]{min-width:235px!important;max-width:235px!important}
[data-testid="stDataFrame"]{box-shadow:0 5px 22px rgba(24,44,75,.06)}
div[data-testid="stMetric"]{background:#ffffff;border:1px solid #e1e7ef;border-radius:16px;padding:18px;box-shadow:0 3px 14px rgba(24,44,75,.05)}
div[data-testid="stMetricLabel"]{color:#617187}
div[data-testid="stMetricValue"]{color:#163c68}
h1,h2,h3{color:#183657!important}
.stTabs [data-baseweb="tab-list"]{gap:8px}
.stTabs [data-baseweb="tab"]{background:#eaf0f8;border-radius:10px 10px 0 0;padding:10px 15px}
.stTabs [aria-selected="true"]{background:#ffffff!important}
div[data-testid="stDataFrame"]{border:1px solid #dce5f0;border-radius:12px;overflow:hidden}
</style>""",unsafe_allow_html=True)
BRL=lambda v: f'R$ {v:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
NUM=lambda v: f'{v:,.0f}'.replace(',','.')
MES={1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}

def norm(s):
    s=unicodedata.normalize('NFKD',str(s)).encode('ascii','ignore').decode().upper()
    return re.sub(r'\s+',' ',s).strip()

def parse_csv(data):
    raw=data.decode('utf-8-sig',errors='replace')
    lines=raw.splitlines()
    pos=next((i for i,l in enumerate(lines) if l.startswith('Data da solicitação (UTC);')),None)
    if pos is None: raise ValueError('Cabeçalho do relatório Uber não encontrado.')
    return pd.read_csv(io.StringIO('\n'.join(lines[pos:])),sep=';',dtype=str)

def load_files(files):
    frames=[]
    for file in files:
        try:
            raw=file.getvalue() if hasattr(file,'getvalue') else Path(file).read_bytes()
            d=parse_csv(raw)
            d['_arquivo']=getattr(file,'name',Path(file).name if isinstance(file,(str,Path)) else 'arquivo')
            frames.append(d)
        except Exception as e: st.warning(f'Arquivo ignorado: {getattr(file,"name",file)} — {e}')
    if not frames:return pd.DataFrame()
    df=pd.concat(frames,ignore_index=True)
    required=['Data da solicitação (UTC)','Nome','Sobrenome','Valor da transação: BRL','Tipo de transação']
    missing=[c for c in required if c not in df.columns]
    if missing: st.error('Colunas ausentes: '+', '.join(missing));return pd.DataFrame()
    df['Data']=pd.to_datetime(df['Data da solicitação (UTC)'],format='%m/%d/%Y',errors='coerce')
    df['Hora']=df.get('Hora da solicitação (UTC)',pd.Series('',index=df.index)).fillna('')
    df['Usuário']=(df['Nome'].fillna('')+' '+df['Sobrenome'].fillna('')).map(norm)
    df['Valor']=pd.to_numeric(df['Valor da transação: BRL'].fillna('').str.replace(',','.',regex=False),errors='coerce')
    for orig,new in [('Endereço de partida','Origem'),('Endereço de destino','Destino'),('Serviço','Serviço'),('Cidade','Cidade')]:
        df[new]=df[orig].fillna('Não informado') if orig in df.columns else 'Não informado'
    df['Tipo']=df['Tipo de transação'].fillna('Não informado').str.strip()
    df=df.dropna(subset=['Data','Valor'])
    # Elimina linhas repetidas quando um mesmo período é exportado em dois arquivos.
    dedup=['Data','Hora','Usuário','Origem','Destino','Tipo','Valor','Serviço']
    df=df.drop_duplicates(subset=dedup).copy()
    df['Mês']=df['Data'].dt.to_period('M').astype(str)
    df['Ano']=df['Data'].dt.year
    return df.sort_values(['Data','Hora'])

def plot(fig,height=420):
    fig.update_layout(template='plotly_white',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',font=dict(color='#243b55'),height=height,margin=dict(l=15,r=15,t=45,b=20),legend_title_text='')
    st.plotly_chart(fig,use_container_width=True)

def excel_bytes(sheets):
    out=io.BytesIO()
    with pd.ExcelWriter(out,engine='openpyxl') as w:
        for name,data in sheets.items():data.to_excel(w,sheet_name=name[:31],index=False)
    return out.getvalue()

st.title('🚕 Inteligência de Viagens')
st.caption('ÚNICA ATACADISTA  /  Gestão de mobilidade corporativa  /  Relatórios Uber for Business')
with st.sidebar:
    st.header('⚙️ Fonte de dados')
    uploaded=st.file_uploader('Importar relatórios Uber CSV',type=['csv'],accept_multiple_files=True,help='Aceita vários arquivos; consolida e remove transações duplicadas.')
    st.caption('Para carregar dados automaticamente no Streamlit Cloud, coloque os arquivos CSV no diretório principal do repositório, nomeados 1.csv, 2.csv, 3.csv etc.')
    data_dir=Path(__file__).resolve().parent
    local=sorted(data_dir.glob('*.csv'), key=lambda p:(0,int(p.stem)) if p.stem.isdigit() else (1,p.name.lower())) if data_dir.exists() else []
    files=local+list(uploaded or [])
    st.caption(f'{len(local)} arquivo(s) CSV no repositório. Arquivos enviados aqui são somados à base, com remoção de duplicatas.')
    df=load_files(files) if files else pd.DataFrame()
    if df.empty:
        st.info('Importe os dois arquivos CSV no menu lateral para iniciar a análise. Você também pode deixar os arquivos CSV no diretório principal para carregamento automático.')
        st.stop()
    st.success(f'{NUM(len(df))} transações únicas carregadas')
    st.header('🔎 Filtros')
    dmin,dmax=df['Data'].min().date(),df['Data'].max().date()
    periodo=st.date_input('Período (início e fim)',value=(dmin,dmax),min_value=dmin,max_value=dmax,format='DD/MM/YYYY')
    if not isinstance(periodo,(list,tuple)) or len(periodo)!=2:
        st.info('Selecione também a data final.');st.stop()
    inicio,fim=periodo
    usuarios=sorted(df['Usuário'].unique().tolist())
    selected=st.multiselect('Usuários',usuarios,default=usuarios)
    tipos=sorted(df['Tipo'].unique().tolist())
    selected_tipos=st.multiselect('Tipos de transação',tipos,default=tipos)
    st.caption('Viagens = transações do tipo Fare. Reembolsos e ajustes são contabilizados separadamente.')

filtered=df[df['Data'].dt.date.between(inicio,fim)&df['Usuário'].isin(selected)&df['Tipo'].isin(selected_tipos)].copy()
trips=filtered[filtered['Tipo'].str.casefold()=='fare'].copy()
adjustments=filtered[filtered['Tipo'].str.casefold()!='fare'].copy()
if filtered.empty:st.warning('Nenhuma transação encontrada para os filtros selecionados.');st.stop()

n=len(trips); total=trips['Valor'].sum();users=trips['Usuário'].nunique();ticket=total/n if n else 0
net=filtered['Valor'].sum()
a,b,c,d,e=st.columns(5)
a.metric('Gasto em viagens',BRL(total));b.metric('Viagens',NUM(n));c.metric('Usuários ativos',NUM(users));d.metric('Ticket por viagem',BRL(ticket));e.metric('Saldo com ajustes',BRL(net),help='Soma de todas as transações, inclusive Rebate e outros ajustes.')

monthly=trips.groupby('Mês',as_index=False).agg(Valor=('Valor','sum'),Viagens=('Valor','size'),Usuários=('Usuário','nunique'))
monthly['Ticket médio']=monthly['Valor']/monthly['Viagens']
byuser=trips.groupby('Usuário',as_index=False).agg(Valor=('Valor','sum'),Viagens=('Valor','size'),Primeira=('Data','min'),Última=('Data','max'))
byuser['Ticket médio']=byuser['Valor']/byuser['Viagens']
byuser['Participação %']=np.where(total,byuser['Valor']/total*100,0)
byuser=byuser.sort_values('Valor',ascending=False)
user_month=trips.groupby(['Mês','Usuário'],as_index=False).agg(Valor=('Valor','sum'),Viagens=('Valor','size'))
user_month['Ticket médio']=user_month['Valor']/user_month['Viagens']

v1,v2,v3,v4,v5=st.tabs(['📊 Visão geral','👥 Por usuário','📅 Usuário × mês','🧭 Viagens detalhadas','📥 Exportação'])
with v1:
    x,y=st.columns([1.4,1])
    with x:
        st.subheader('Evolução mensal de despesas')
        if not monthly.empty:plot(px.bar(monthly,x='Mês',y='Valor',text='Valor',color_discrete_sequence=['#46a9ff'],labels={'Valor':'Gasto (R$)'}))
    with y:
        st.subheader('Participação dos usuários')
        if not byuser.empty:plot(px.pie(byuser.head(10),names='Usuário',values='Valor',hole=.63))
    x,y=st.columns(2)
    with x:
        st.subheader('Quantidade de viagens por mês')
        if not monthly.empty:plot(px.line(monthly,x='Mês',y='Viagens',markers=True))
    with y:
        st.subheader('Ticket médio mensal')
        if not monthly.empty:plot(px.bar(monthly,x='Mês',y='Ticket médio',color_discrete_sequence=['#35c7b5']))
    st.subheader('Resumo mensal')
    display=monthly.copy();display['Valor']=display['Valor'].map(BRL);display['Ticket médio']=display['Ticket médio'].map(BRL)
    st.dataframe(display,use_container_width=True,hide_index=True)
    if len(monthly)>1:
        last,prev=monthly.iloc[-1],monthly.iloc[-2]
        if prev['Valor']!=0:st.caption(f'Variação entre os últimos meses exibidos ({prev["Mês"]} → {last["Mês"]}): {(last["Valor"]/prev["Valor"]-1)*100:+.1f}% em gastos. O período pode conter meses parciais.')
with v2:
    st.subheader('Ranking financeiro por usuário')
    if not byuser.empty:plot(px.bar(byuser.sort_values('Valor'),x='Valor',y='Usuário',orientation='h',color='Ticket médio',color_continuous_scale='Blues'),max(390,35*len(byuser)+100))
    view=byuser.copy()
    for col in ['Valor','Ticket médio']:view[col]=view[col].map(BRL)
    view['Participação %']=view['Participação %'].map(lambda v:f'{v:.1f}%')
    for col in ['Primeira','Última']:view[col]=view[col].dt.strftime('%d/%m/%Y')
    st.dataframe(view,use_container_width=True,hide_index=True)
    st.subheader('Ticket médio por colaborador')
    if not byuser.empty:plot(px.bar(byuser.sort_values('Ticket médio'),x='Ticket médio',y='Usuário',orientation='h',color_discrete_sequence=['#35c7b5']),max(390,35*len(byuser)+100))
with v3:
    st.subheader('Matriz de gastos: mês × usuário')
    if not user_month.empty:
        matrix=user_month.pivot(index='Usuário',columns='Mês',values='Valor').fillna(0)
        plot(px.imshow(matrix,text_auto='.0f',aspect='auto',color_continuous_scale='Blues',labels={'color':'R$'}),max(350,40*len(matrix)+130))
        st.dataframe(matrix.style.format(BRL),use_container_width=True)
        st.subheader('Comparativo mensal por colaborador')
        plot(px.bar(user_month,x='Mês',y='Valor',color='Usuário',barmode='group'),480)
        st.subheader('Indicadores por usuário e mês')
        v=user_month.rename(columns={'Mês':'Mês','Usuário':'Usuário','Valor':'Gasto total','Viagens':'Nº de viagens'}).copy()
        v['Participação no mês (%)']=v['Gasto total']/v.groupby('Mês')['Gasto total'].transform('sum').replace(0,np.nan)*100
        v=v[['Mês','Usuário','Nº de viagens','Gasto total','Ticket médio','Participação no mês (%)']].sort_values(['Mês','Gasto total'],ascending=[False,False])
        st.dataframe(v,use_container_width=True,hide_index=True,height=510,
            column_config={
                'Mês':st.column_config.TextColumn('Mês',width='small'),
                'Usuário':st.column_config.TextColumn('Usuário',width='medium'),
                'Nº de viagens':st.column_config.NumberColumn('Viagens',format='%d'),
                'Gasto total':st.column_config.NumberColumn('Gasto total (R$)',format='R$ %.2f'),
                'Ticket médio':st.column_config.NumberColumn('Ticket médio (R$)',format='R$ %.2f'),
                'Participação no mês (%)':st.column_config.ProgressColumn('Participação no mês',format='%.1f%%',min_value=0,max_value=100)
            })
with v4:
    st.subheader('Consulta individual de viagens')
    person=st.selectbox('Escolha um usuário', ['Todos os usuários']+sorted(trips['Usuário'].unique().tolist()))
    detail=trips if person=='Todos os usuários' else trips[trips['Usuário']==person]
    p,q,r=st.columns(3)
    p.metric('Total do filtro',BRL(detail['Valor'].sum()));q.metric('Viagens do filtro',NUM(len(detail)));r.metric('Ticket do filtro',BRL(detail['Valor'].mean() if len(detail) else 0))
    search=st.text_input('Buscar endereço de origem ou destino',placeholder='Ex.: SIA, Sofnorte, Ceilândia...')
    if search:
        detail=detail[detail['Origem'].str.contains(search,case=False,na=False,regex=False)|detail['Destino'].str.contains(search,case=False,na=False,regex=False)]
    show=detail[['Data','Hora','Usuário','Origem','Destino','Cidade','Serviço','Valor']].sort_values(['Data','Hora'],ascending=False).copy()
    show['Data']=show['Data'].dt.strftime('%d/%m/%Y');show['Valor']=show['Valor'].map(BRL)
    # Links de pesquisa do Google Maps para abrir o endereço em uma nova guia.
    # A busca é textual; o ponto exato depende da precisão do endereço fornecido pelo Uber.
    def maps_url(address):
        address=str(address).strip()
        if not address or address.casefold() in ('nan','não informado','nao informado'):
            return None
        return 'https://www.google.com/maps/search/?api=1&query='+quote(address,safe='')
    show['Mapa origem']=detail.loc[show.index,'Origem'].map(maps_url)
    show['Mapa destino']=detail.loc[show.index,'Destino'].map(maps_url)
    st.caption('Endereços com acesso ao Google Maps. Clique em **📍 Origem** ou **📍 Destino**.')
    st.dataframe(show,use_container_width=True,hide_index=True,height=480,column_config={
        'Data':st.column_config.TextColumn('Data',width='small'),
        'Hora':st.column_config.TextColumn('Hora',width='small'),
        'Usuário':st.column_config.TextColumn('Colaborador',width='medium'),
        'Origem':st.column_config.TextColumn('📍 Endereço de origem',width='large'),
        'Destino':st.column_config.TextColumn('🏁 Endereço de destino',width='large'),
        'Valor':st.column_config.TextColumn('Valor da viagem',width='small'),
        'Mapa origem':st.column_config.LinkColumn('📍 Origem',display_text='Abrir mapa',width='small'),
        'Mapa destino':st.column_config.LinkColumn('📍 Destino',display_text='Abrir mapa',width='small')
    })
    st.subheader('Trajetos mais recorrentes')
    routes=detail.groupby(['Origem','Destino'],as_index=False).agg(Viagens=('Valor','size'),Gasto=('Valor','sum'),Ticket_médio=('Valor','mean')).sort_values(['Viagens','Gasto'],ascending=False).head(25)
    routes['Mapa origem']=routes['Origem'].map(maps_url)
    routes['Mapa destino']=routes['Destino'].map(maps_url)
    routes=routes.rename(columns={'Ticket_médio':'Ticket médio'})
    st.caption('Ranking de rotas por frequência. Os botões de mapa abrem cada endereço no Google Maps.')
    st.dataframe(routes,use_container_width=True,hide_index=True,height=460,column_config={
        'Origem':st.column_config.TextColumn('📍 Origem',width='large'),
        'Destino':st.column_config.TextColumn('🏁 Destino',width='large'),
        'Viagens':st.column_config.NumberColumn('Viagens',format='%d',width='small'),
        'Gasto':st.column_config.NumberColumn('Gasto total',format='R$ %.2f',width='small'),
        'Ticket médio':st.column_config.NumberColumn('Ticket médio',format='R$ %.2f',width='small'),
        'Mapa origem':st.column_config.LinkColumn('📍 Mapa origem',display_text='Ver mapa',width='small'),
        'Mapa destino':st.column_config.LinkColumn('📍 Mapa destino',display_text='Ver mapa',width='small')
    })
    st.download_button('⬇️ Baixar viagens exibidas (Excel)',excel_bytes({'Viagens':detail[['Data','Hora','Usuário','Origem','Destino','Serviço','Tipo','Valor']]}),'viagens_detalhadas.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
with v5:
    st.subheader('Exportar análise completa')
    st.write('O Excel reúne resumo mensal, usuários, usuário por mês, viagens e transações de ajuste.')
    sheets={'Resumo mensal':monthly,'Por usuario':byuser,'Usuario por mes':user_month,'Viagens':trips[['Data','Hora','Usuário','Origem','Destino','Cidade','Serviço','Tipo','Valor']],'Ajustes':adjustments[['Data','Hora','Usuário','Tipo','Valor']]}
    st.download_button('📥 Baixar relatório BI em Excel',excel_bytes(sheets),'analise_viagens_unica.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',type='primary')
    st.subheader('Conferência de ajustes e reembolsos')
    st.metric('Ajustes (líquido)',BRL(adjustments['Valor'].sum()))
    if not adjustments.empty:st.dataframe(adjustments[['Data','Usuário','Tipo','Valor','_arquivo']],use_container_width=True,hide_index=True)
    st.caption('Fonte: arquivos CSV importados. Datas e horários mantidos em UTC conforme relatório de origem. Viagens são linhas Fare; demais tipos são ajustes. Não representa necessariamente viagens únicas caso o provedor gere múltiplos lançamentos Fare por corrida.')
