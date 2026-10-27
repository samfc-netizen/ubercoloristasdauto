import io
import html
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
:root{--navy:#173456;--muted:#718096;--line:#e4eaf2;--blue:#2563eb}
.stApp{background:#f5f7fb;color:#1d304a}
section[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}
.block-container{padding-top:1.2rem;padding-bottom:3rem;max-width:1780px}
html{font-size:13px}
h1,h2,h3{color:#183657!important;letter-spacing:-.02em}
h1{font-weight:800!important}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:17px;padding:18px;box-shadow:0 5px 18px rgba(22,44,78,.045)}
[data-testid="stMetricLabel"]{color:#66788f}
[data-testid="stMetricValue"]{color:#163c68;font-size:1.65rem}
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid var(--line)}
.stTabs [data-baseweb="tab"]{border-radius:11px 11px 0 0;padding:11px 16px;color:#50647d}
.stTabs [aria-selected="true"]{background:#fff!important;color:#1555a1!important}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 4px 14px rgba(22,44,78,.035)}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:17px!important}
.bi-section{padding:13px 0 8px}.bi-section h3{margin:0;font-size:1.18rem;font-weight:750}.bi-section p{color:#74849a;font-size:.85rem;margin:4px 0 0}
.bi-table-wrap{overflow-x:auto;border:1px solid #e1e8f1;border-radius:16px;background:white;box-shadow:0 6px 20px rgba(20,48,80,.04)}
.bi-table{width:100%;border-collapse:separate;border-spacing:0;min-width:820px;font-size:12px}
.bi-table th{background:#f1f5fa;color:#61738b;text-transform:uppercase;font-size:10px;letter-spacing:.065em;text-align:left;padding:13px 14px;white-space:nowrap;border-bottom:1px solid #e2e9f1}
.bi-table td{padding:13px 14px;border-bottom:1px solid #edf1f6;vertical-align:middle;color:#233852}
.bi-table tbody tr:nth-child(even){background:#fbfcfe}.bi-table tbody tr:hover{background:#f0f6ff}.bi-table tbody tr:last-child td{border-bottom:0}
.bi-name{font-weight:700;color:#173456}.bi-sub{color:#8290a2;font-size:11px;margin-top:4px}
.bi-route{display:flex;flex-direction:column;gap:7px;min-width:235px;max-width:640px}
.bi-route-line{display:flex;align-items:baseline;gap:8px}.bi-route-line span:last-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block;max-width:580px}
.bi-dot{color:#12a67b;font-size:15px}.bi-pin{color:#ef6574;font-size:15px}
.bi-money{font-weight:750;color:#173f70;white-space:nowrap}
.bi-action{display:inline-block;padding:7px 10px;border:1px solid #dce7f8;border-radius:8px;background:#f3f7ff;color:#1c5caf!important;text-decoration:none!important;font-size:11px;font-weight:700;white-space:nowrap;margin:2px}
.bi-action:hover{background:#dfeaff}.bi-muted{color:#8492a3}.bi-pill{display:inline-block;border-radius:20px;background:#eaf3ff;color:#2863aa;padding:4px 9px;font-weight:700}
/* Cartão e tabela de viagens no padrão executivo compacto */
.bi-table-wrap{border:0;border-radius:0;box-shadow:none;overflow-x:auto}
.bi-table{min-width:0;width:100%;table-layout:fixed;font-size:12px}
.bi-table th{background:#fff;color:#7a8390;font-size:10px;padding:12px 10px;border-bottom:1px solid #e6e9ed}
.bi-table td{padding:15px 10px;border-bottom:1px solid #e9edf2}
.bi-table tbody tr:nth-child(even){background:#fff}
.bi-table tbody tr:hover{background:#f6f9ff}
.bi-table th:first-child,.bi-table td:first-child{width:23%}
.bi-table th:nth-child(2),.bi-table td:nth-child(2){width:51%}
.bi-table th:nth-child(3),.bi-table td:nth-child(3){width:13%}
.bi-table th:nth-child(4),.bi-table td:nth-child(4){width:13%}
.bi-name{font-size:11px;color:#243347}
.bi-route{min-width:0;max-width:100%;gap:7px}
.bi-route-line{align-items:center;min-width:0;gap:7px}
.bi-route-line span:last-child{max-width:100%;font-size:11px}
.bi-map-actions{display:flex;align-items:center;gap:6px;white-space:nowrap}
.bi-icon-link{display:inline-flex;align-items:center;justify-content:center;min-width:25px;height:27px;border-radius:7px;text-decoration:none!important;color:#2563eb!important;font-size:17px;font-weight:700}
.bi-icon-link:hover{background:#eaf2ff}
.bi-money{font-size:12px}
.bi-card-head{background:white;border:1px solid #e1e7ef;border-radius:17px;padding:16px 18px 10px;margin-top:12px}
.bi-card-title{font-size:18px;font-weight:750;color:#1d304a}
.bi-card-sub{font-size:12px;color:#7a889b;margin-top:3px}
.bi-card-count{background:#dff7e9;color:#17834c;padding:5px 10px;border-radius:30px;font-size:11px;font-weight:700}
@media(max-width:900px){.bi-table{min-width:620px}}
</style>""",unsafe_allow_html=True)

def section(title, description=''):
    st.markdown(f'<div class="bi-section"><h3>{html.escape(title)}</h3><p>{html.escape(description)}</p></div>',unsafe_allow_html=True)

def maps_url(address):
    address=str(address).strip()
    if not address or address.casefold() in ('nan','não informado','nao informado'):return None
    return 'https://www.google.com/maps/search/?api=1&query='+quote(address,safe='')

def directions_url(origin,destination):
    if not maps_url(origin) or not maps_url(destination):return None
    return 'https://www.google.com/maps/dir/?api=1&origin='+quote(str(origin),safe='')+'&destination='+quote(str(destination),safe='')

def short_address(address,limit=85):
    s=str(address).strip()
    return s if len(s)<=limit else s[:limit-1].rstrip()+'…'

def map_link(url,label,icon='↗'):
    if not url:return '<span class="bi-muted">—</span>'
    return f'<a class="bi-icon-link" href="{html.escape(url,quote=True)}" target="_blank" rel="noopener noreferrer" title="{html.escape(label,quote=True)}" aria-label="{html.escape(label,quote=True)}">{icon}</a>'

def route_cell(origin,destination):
    return (f'<div class="bi-route"><div class="bi-route-line"><span class="bi-dot">●</span><span title="{html.escape(str(origin),quote=True)}">{html.escape(short_address(origin,58))}</span></div>'
            f'<div class="bi-route-line"><span class="bi-pin">●</span><span title="{html.escape(str(destination),quote=True)}">{html.escape(short_address(destination,58))}</span></div></div>')

def render_table(headers,rows):
    if not rows:st.info('Nenhuma viagem encontrada.');return
    head=''.join('<th>'+html.escape(str(h))+'</th>' for h in headers)
    body=''.join('<tr>'+''.join('<td>'+str(c)+'</td>' for c in row)+'</tr>' for row in rows)
    st.markdown('<div class="bi-table-wrap"><table class="bi-table"><thead><tr>'+head+'</tr></thead><tbody>'+body+'</tbody></table></div>',unsafe_allow_html=True)

def maps_actions(origin,dest):
    return ('<div class="bi-map-actions">'+map_link(maps_url(origin),'Abrir origem no Google Maps','⌖')+
            map_link(maps_url(dest),'Abrir destino no Google Maps','◉')+
            map_link(directions_url(origin,dest),'Abrir rota completa no Google Maps','↗')+'</div>')

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
    # Converte data e hora UTC para horário de Brasília (UTC-3),
    # incluindo a mudança de dia quando o horário UTC é anterior às 03:00.
    data_utc = pd.to_datetime(df['Data da solicitação (UTC)'], format='%m/%d/%Y', errors='coerce')
    hora_utc = df.get('Hora da solicitação (UTC)', pd.Series('', index=df.index)).fillna('').astype(str).str.strip()
    duracao = pd.to_timedelta(hora_utc, errors='coerce')
    instante_local = data_utc + duracao - pd.Timedelta(hours=3)
    df['Data'] = instante_local.dt.normalize().where(duracao.notna(), data_utc)
    df['Hora'] = instante_local.dt.strftime('%H:%M:%S').where(duracao.notna(), hora_utc)
    # Mantém o formato HH:MM quando a origem não informa segundos.
    sem_segundos = hora_utc.str.fullmatch(r'\d{1,2}:\d{2}')
    df.loc[sem_segundos & duracao.notna(), 'Hora'] = instante_local.dt.strftime('%H:%M').loc[sem_segundos & duracao.notna()]
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
    section('Consulta individual de viagens','Selecione um colaborador, pesquise endereços e abra os locais ou o trajeto completo no Google Maps.')
    person=st.selectbox('Colaborador', ['Todos os usuários']+sorted(trips['Usuário'].unique().tolist()))
    detail=trips if person=='Todos os usuários' else trips[trips['Usuário']==person]
    search=st.text_input('Pesquisar origem ou destino',placeholder='Ex.: SIA, Sofnorte, Ceilândia...')
    if search:
        detail=detail[detail['Origem'].str.contains(search,case=False,na=False,regex=False)|detail['Destino'].str.contains(search,case=False,na=False,regex=False)]
    p,q,r=st.columns(3)
    p.metric('Gasto nas viagens',BRL(detail['Valor'].sum()))
    q.metric('Viagens encontradas',NUM(len(detail)))
    r.metric('Ticket médio',BRL(detail['Valor'].mean() if len(detail) else 0))
    st.markdown(f'<div class="bi-card-head"><div style="display:flex;justify-content:space-between;align-items:center;gap:12px"><div><div class="bi-card-title">Detalhamento de viagens</div><div class="bi-card-sub">Consulta de viagens e localização dos trajetos</div></div><span class="bi-card-count">{len(detail)} viagens</span></div></div>',unsafe_allow_html=True)
    ordered=detail.sort_values(['Data','Hora'],ascending=False)
    col_search,col_export=st.columns([5,1])
    with col_search:
        table_search=st.text_input('Buscar usuário ou endereço na tabela',placeholder='Buscar usuário ou endereço...',key='table_search')
    if table_search:
        mask=(ordered['Usuário'].str.contains(table_search,case=False,na=False,regex=False)|ordered['Origem'].str.contains(table_search,case=False,na=False,regex=False)|ordered['Destino'].str.contains(table_search,case=False,na=False,regex=False))
        ordered=ordered[mask]
    with col_export:
        st.write('')
        st.download_button('⬇ Excel',excel_bytes({'Viagens':ordered[['Data','Hora','Usuário','Origem','Destino','Serviço','Tipo','Valor']]}),'viagens_detalhadas.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',use_container_width=True)
    per_page=20
    pages=max(1,(len(ordered)+per_page-1)//per_page)
    pg=st.number_input('Página das viagens',min_value=1,max_value=pages,value=1,step=1,key='page_trips')
    page=ordered.iloc[(pg-1)*per_page:pg*per_page]
    rows=[]
    for _,r in page.iterrows():
        origin,dest=r['Origem'],r['Destino']
        rows.append(['<div class="bi-name">'+html.escape(str(r['Usuário']))+'</div><div class="bi-sub">'+r['Data'].strftime('%d/%m/%Y')+' · '+html.escape(str(r['Hora']))+'</div>',
            route_cell(origin,dest),'<span class="bi-money">'+BRL(r['Valor'])+'</span>',maps_actions(origin,dest)])
    render_table(['COLABORADOR','TRAJETO','VALOR','MAPA'],rows)
    st.caption(f'Exibindo {len(page)} de {len(ordered)} viagens · Página {pg} de {pages}. Ícones: origem, destino e rota completa. Passe o cursor no endereço para vê-lo completo.')
    section('Trajetos mais recorrentes','Ranking de rotas por frequência, com localização e rota completa no Google Maps.')
    routes=detail.groupby(['Origem','Destino'],as_index=False).agg(Viagens=('Valor','size'),Gasto=('Valor','sum'),Ticket_médio=('Valor','mean')).sort_values(['Viagens','Gasto'],ascending=False).head(25)
    route_rows=[]
    for i,(_,r) in enumerate(routes.iterrows(),1):
        origin,dest=r['Origem'],r['Destino']
        route_rows.append(['<span class="bi-pill">#'+str(i)+'</span>',route_cell(origin,dest),'<strong>'+NUM(r['Viagens'])+' viagens</strong><div class="bi-sub">'+BRL(r['Gasto'])+' · média '+BRL(r['Ticket_médio'])+'</div>',maps_actions(origin,dest)])
    render_table(['POSIÇÃO','TRAJETO','GASTO / VIAGENS','MAPA'],route_rows)
with v5:
    st.subheader('Exportar análise completa')
    st.write('O Excel reúne resumo mensal, usuários, usuário por mês, viagens e transações de ajuste.')
    sheets={'Resumo mensal':monthly,'Por usuario':byuser,'Usuario por mes':user_month,'Viagens':trips[['Data','Hora','Usuário','Origem','Destino','Cidade','Serviço','Tipo','Valor']],'Ajustes':adjustments[['Data','Hora','Usuário','Tipo','Valor']]}
    st.download_button('📥 Baixar relatório BI em Excel',excel_bytes(sheets),'analise_viagens_unica.xlsx',mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',type='primary')
    st.subheader('Conferência de ajustes e reembolsos')
    st.metric('Ajustes (líquido)',BRL(adjustments['Valor'].sum()))
    if not adjustments.empty:st.dataframe(adjustments[['Data','Usuário','Tipo','Valor','_arquivo']],use_container_width=True,hide_index=True)
    st.caption('Fonte: arquivos CSV importados. Datas e horários convertidos de UTC para Brasília (UTC−3), inclusive quando ocorre mudança de dia. Viagens são linhas Fare; demais tipos são ajustes. Não representa necessariamente viagens únicas caso o provedor gere múltiplos lançamentos Fare por corrida.')
